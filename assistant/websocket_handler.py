import json
import asyncio
import websockets
import os
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from .prompt_builder import build_system_prompt
from gabby_booking.models import Organization, Assistant, CommunicationTemplate
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class MediaStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        self.stream_sid = None
        self.call_sid = None
        self.organization_id = None
        self.caller_number = None
        self.greeting_message = None
        self.openai_ws = None
        self.openai_ws_ready = False
        self.queued_first_message = None
        self.latest_media_timestamp = 0
        self.last_assistant_item = None
        self.mark_queue = []
        self.response_start_timestamp_twilio = None
        self.transcript = ""

        logger.info("Client connected to media-stream")

    async def disconnect(self, close_code):
        if self.openai_ws:
            await self.openai_ws.close()

        logger.info(f"Client disconnected. Transcript:\n{self.transcript}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            if data.get('event') == 'start':
                await self.handle_start(data)
            elif data.get('event') == 'media':
                await self.handle_media(data)
            elif data.get('event') == 'mark':
                await self.handle_mark(data)

        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")

    async def handle_start(self, data):
        self.stream_sid = data['start']['streamSid']
        self.call_sid = data['start']['callSid']

        custom_params = data['start'].get('customParameters', {})
        self.organization_id = custom_params.get('organization_id')
        self.caller_number = custom_params.get('caller_number', 'Unknown')
        self.greeting_message = custom_params.get('greeting_message', 'Hello')

        logger.info(f"Call started: {self.call_sid}, Org: {self.organization_id}")

        # Connect to OpenAI Realtime API
        await self.connect_to_openai()

    async def handle_media(self, data):
        if self.openai_ws:
            try:
                audio_append = {
                    "type": "input_audio_buffer.append",
                    "audio": data['media']['payload']
                }
                await self.openai_ws.send(json.dumps(audio_append))

                self.latest_media_timestamp = int(data['media'].get('timestamp', 0))
            except Exception as e:
                logger.error(f"Error sending audio to OpenAI: {str(e)}")

    async def handle_mark(self, data):
        if self.mark_queue:
            self.mark_queue.pop(0)

    async def connect_to_openai(self):
        try:
            # Get assistant voice
            organization = await sync_to_async(Organization.objects.get)(id=self.organization_id)
            assistant = await sync_to_async(
                lambda: Assistant.objects.filter(organization=organization).first()
            )()
            voice = assistant.voice_type if assistant else 'alloy'

            # Build system prompt
            system_prompt = await sync_to_async(build_system_prompt)(self.organization_id)

            # Connect to OpenAI
            self.openai_ws = await websockets.connect(
                "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview",
                additional_headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "OpenAI-Beta": "realtime=v1"
                }
            )

            # Send session update
            session_update = {
                "type": "session.update",
                "session": {
                    "turn_detection": {"type": "server_vad"},
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw",
                    "voice": voice,
                    "instructions": system_prompt,
                    "modalities": ["text", "audio"],
                    "temperature": 0.6,
                    "input_audio_transcription": {"model": "whisper-1"},
                    "tools": [
                        {
                            "type": "function",
                            "name": "book_service",
                            "description": "Send booking SMS to customer",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "caller_number": {"type": "string"}
                                },
                                "required": ["caller_number"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "update_booking",
                            "description": "Send update booking SMS to customer",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "caller_number": {"type": "string"}
                                },
                                "required": ["caller_number"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "cancel_booking",
                            "description": "Send cancel booking SMS to customer",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "caller_number": {"type": "string"}
                                },
                                "required": ["caller_number"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "notify_owner",
                            "description": "Notify owner with message",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "reason": {"type": "string"}
                                },
                                "required": ["reason"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "transfer_call",
                            "description": "Transfer call to human",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "caller_number": {"type": "string"}
                                },
                                "required": ["caller_number"]
                            }
                        }
                    ],
                    "tool_choice": "auto"
                }
            }

            await self.openai_ws.send(json.dumps(session_update))

            # Send first message
            first_message_event = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": f'Start the call by saying exactly: "{self.greeting_message}"'
                }
            }
            await self.openai_ws.send(json.dumps(first_message_event))

            self.openai_ws_ready = True

            # Start listening to OpenAI responses
            asyncio.create_task(self.listen_to_openai())

        except Exception as e:
            logger.error(f"Error connecting to OpenAI: {str(e)}")

    async def listen_to_openai(self):
        try:
            async for message in self.openai_ws:
                response = json.loads(message)

                # Send audio back to Twilio
                if response.get('type') == 'response.audio.delta' and response.get('delta'):
                    await self.send(text_data=json.dumps({
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {"payload": response['delta']}
                    }))

                    if response.get('item_id'):
                        self.last_assistant_item = response['item_id']

                    await self.send_mark()

                # Handle speech interruption
                if response.get('type') == 'input_audio_buffer.speech_started':
                    await self.handle_speech_started()

                # Handle function calls
                if response.get('type') == 'response.function_call_arguments.done':
                    await self.handle_function_call(response)

                # Log transcripts
                if response.get('type') == 'response.done':
                    agent_message = self.extract_transcript(response)
                    if agent_message:
                        self.transcript += f"Agent: {agent_message}\n"
                        logger.info(f"Agent: {agent_message}")

                if response.get('type') == 'conversation.item.input_audio_transcription.completed':
                    user_message = response.get('transcript', '').strip()
                    if user_message:
                        self.transcript += f"User: {user_message}\n"
                        logger.info(f"User: {user_message}")

        except Exception as e:
            logger.error(f"Error in listen_to_openai: {str(e)}")

    async def handle_function_call(self, response):
        function_name = response.get('name')
        args = json.loads(response.get('arguments', '{}'))

        logger.info(f"Function called: {function_name} with args: {args}")

        try:
            if function_name == 'book_service':
                await self.send_booking_sms()
                response_message = "All of our classes are booked online — I've sent you the booking link by SMS. Anything else?"

            elif function_name == 'update_booking':
                await self.send_update_sms()
                response_message = "Rescheduling is handled online — I've sent you the update link by SMS. Anything else?"

            elif function_name == 'cancel_booking':
                await self.send_cancel_sms()
                response_message = "Cancellations must be done online — I've sent you the cancellation link by SMS. Anything else?"

            elif function_name == 'notify_owner':
                reason = args.get('reason', 'Customer message')
                await self.notify_owner(reason)
                response_message = "Your message has been forwarded to the team — they'll follow up shortly. Anything else?"

            elif function_name == 'transfer_call':
                await self.transfer_call_to_human()
                response_message = "I'm transferring your call now."

            else:
                response_message = "I've processed your request."

            # Send function output back to OpenAI
            function_output = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "role": "system",
                    "output": response_message
                }
            }
            await self.openai_ws.send(json.dumps(function_output))

            # Trigger AI response
            await self.openai_ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": f"Inform the user: {response_message}"
                }
            }))

        except Exception as e:
            logger.error(f"Error handling function call: {str(e)}")

    async def send_booking_sms(self):
        # Import here to avoid circular imports
        from .views import twilio_client, TWILIO_PHONE_NUMBER
        import os

        try:
            # Get organization and assistant data
            organization = await sync_to_async(Organization.objects.get)(id=self.organization_id)
            assistant = await sync_to_async(
                lambda: Assistant.objects.filter(organization=organization).first()
            )()

            # Get assistant name
            assistant_name = assistant.name if assistant else "Clara"

            # Get frontend URL from environment
            frontend_url = os.getenv('FRONTEND_URL', 'https://sonoria-frontend-9cay.vercel.app')
            booking_link = f"{frontend_url}/booking-portal?org={organization.id}"

            # Use the exact message format specified
            message_body = f"""Hi this is {assistant_name} from {organization.name}. Here's the link to book your appointment easily:
{booking_link}
Let me know if you need anything, I'm happy to help."""

            if twilio_client:
                await sync_to_async(twilio_client.messages.create)(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=self.caller_number
                )
                logger.info(f"Booking SMS sent successfully to {self.caller_number}")
        except Exception as e:
            logger.error(f"Error sending booking SMS: {str(e)}")

    async def send_update_sms(self):
        from .views import twilio_client, TWILIO_PHONE_NUMBER
        import os

        try:
            # Get organization and assistant data
            organization = await sync_to_async(Organization.objects.get)(id=self.organization_id)
            assistant = await sync_to_async(
                lambda: Assistant.objects.filter(organization=organization).first()
            )()

            # Get assistant name
            assistant_name = assistant.name if assistant else "Clara"

            # Get frontend URL from environment
            frontend_url = os.getenv('FRONTEND_URL', 'https://sonoria-frontend-9cay.vercel.app')
            customer_portal_link = f"{frontend_url}/customer-portal?org={organization.id}"

            # Use the exact message format specified
            message_body = f"""Hi this is {assistant_name} from {organization.name}. Here's the link to reschedule your appointment easily:
{customer_portal_link}
Let me know if you need anything, I'm happy to help."""

            if twilio_client:
                await sync_to_async(twilio_client.messages.create)(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=self.caller_number
                )
                logger.info(f"Update SMS sent successfully to {self.caller_number}")
        except Exception as e:
            logger.error(f"Error sending update SMS: {str(e)}")

    async def send_cancel_sms(self):
        from .views import twilio_client, TWILIO_PHONE_NUMBER
        import os

        try:
            # Get organization and assistant data
            organization = await sync_to_async(Organization.objects.get)(id=self.organization_id)
            assistant = await sync_to_async(
                lambda: Assistant.objects.filter(organization=organization).first()
            )()

            # Get assistant name
            assistant_name = assistant.name if assistant else "Clara"

            # Get frontend URL from environment
            frontend_url = os.getenv('FRONTEND_URL', 'https://sonoria-frontend-9cay.vercel.app')
            customer_portal_link = f"{frontend_url}/customer-portal?org={organization.id}"

            # Use the exact message format specified
            message_body = f"""Hi this is {assistant_name} from {organization.name}. Here's the link to cancel your appointment:
{customer_portal_link}
You can easily manage your booking there. Let me know if you need any help!"""

            if twilio_client:
                await sync_to_async(twilio_client.messages.create)(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=self.caller_number
                )
                logger.info(f"Cancel SMS sent successfully to {self.caller_number}")
        except Exception as e:
            logger.error(f"Error sending cancel SMS: {str(e)}")

    async def notify_owner(self, reason):
        from .views import twilio_client, TWILIO_PHONE_NUMBER
        from gabby_booking.models import FallbackNumber

        try:
            fallback = await sync_to_async(
                lambda: FallbackNumber.objects.filter(organization_id=self.organization_id).first()
            )()

            if fallback and twilio_client:
                message_body = f"Customer message from {self.caller_number}: {reason}"
                await sync_to_async(twilio_client.messages.create)(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=fallback.phone_number
                )
                logger.info("Owner notified successfully")
        except Exception as e:
            logger.error(f"Error notifying owner: {str(e)}")

    async def transfer_call_to_human(self):
        from .views import twilio_client
        from gabby_booking.models import FallbackNumber

        try:
            fallback = await sync_to_async(
                lambda: FallbackNumber.objects.filter(organization_id=self.organization_id).first()
            )()

            if fallback and twilio_client:
                await sync_to_async(twilio_client.calls(self.call_sid).update)(
                    twiml=f'<Response><Dial>{fallback.phone_number}</Dial></Response>'
                )
                logger.info(f"Call transferred to {fallback.phone_number}")
        except Exception as e:
            logger.error(f"Error transferring call: {str(e)}")

    async def handle_speech_started(self):
        if self.mark_queue and self.response_start_timestamp_twilio is not None:
            elapsed_time = self.latest_media_timestamp - self.response_start_timestamp_twilio

            if self.last_assistant_item:
                truncate_event = {
                    "type": "conversation.item.truncate",
                    "item_id": self.last_assistant_item,
                    "content_index": 0,
                    "audio_end_ms": elapsed_time
                }
                await self.openai_ws.send(json.dumps(truncate_event))

            await self.send(text_data=json.dumps({
                "event": "clear",
                "streamSid": self.stream_sid
            }))

            self.mark_queue = []
            self.last_assistant_item = None
            self.response_start_timestamp_twilio = None

    async def send_mark(self):
        if self.stream_sid:
            await self.send(text_data=json.dumps({
                "event": "mark",
                "streamSid": self.stream_sid,
                "mark": {"name": "responsePart"}
            }))
            self.mark_queue.append("responsePart")

    def extract_transcript(self, response):
        try:
            output = response.get('response', {}).get('output', [])
            for item in output:
                content = item.get('content', [])
                for c in content:
                    if c.get('transcript'):
                        return c['transcript']
        except:
            pass
        return None
