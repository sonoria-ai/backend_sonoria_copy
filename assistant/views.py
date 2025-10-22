import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.rest import Client
from .prompt_builder import build_system_prompt
from gabby_booking.models import Organization, Assistant, FallbackNumber
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Twilio credentials from Django settings
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# OpenAI credentials
OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def incoming_call(request):
    """
    Handle incoming calls from Twilio
    """
    try:
        # Get organization_id from query params OR from phone number lookup
        organization_id = request.GET.get('org_id') or request.POST.get('org_id')

        # If no org_id, try to find organization by phone number
        if not organization_id:
            to_number = request.POST.get('To')
            if to_number:
                try:
                    assistant = Assistant.objects.filter(twilio_phone_number=to_number).first()
                    if assistant:
                        organization_id = assistant.organization.id
                except Exception as e:
                    logger.error(f"Error finding organization by phone: {str(e)}")

        if not organization_id:
            logger.error("No organization_id provided and couldn't find by phone")
            return HttpResponse("Organization ID required", status=400)

        # Get caller details
        caller_number = request.POST.get('From', 'Unknown')
        call_sid = request.POST.get('CallSid', 'Unknown')

        logger.info(f"Incoming call from {caller_number} for organization {organization_id}")

        # Get organization and assistant
        try:
            organization = Organization.objects.get(id=organization_id)
            assistant = Assistant.objects.filter(organization=organization).first()
        except Organization.DoesNotExist:
            logger.error(f"Organization {organization_id} not found")
            return HttpResponse("Organization not found", status=404)

        # Get greeting message
        greeting_message = assistant.greeting_message if assistant else f"Thank you for calling {organization.name}. How can I help you today?"

        # Get WebSocket URL (using ngrok or your deployed URL)
        ngrok_url = os.getenv('NGROK_URL')

        if ngrok_url:
            # Use ngrok URL for WebSocket - convert https to wss
            ws_host = ngrok_url.replace('https://', '').replace('http://', '')
            ws_url = f"wss://{ws_host}/assistant/media-stream"
        else:
            # Fallback to request host
            host = request.get_host()
            ws_url = f"wss://{host}/assistant/media-stream"

        # Create TwiML response
        response = VoiceResponse()
        connect = Connect()
        stream = Stream(url=ws_url)
        stream.parameter(name='organization_id', value=str(organization_id))
        stream.parameter(name='caller_number', value=caller_number)
        stream.parameter(name='call_sid', value=call_sid)
        stream.parameter(name='greeting_message', value=greeting_message)
        connect.append(stream)
        response.append(connect)

        return HttpResponse(str(response), content_type='text/xml')

    except Exception as e:
        logger.error(f"Error in incoming_call: {str(e)}")
        return HttpResponse("Internal server error", status=500)


@api_view(['GET'])
def get_session_token(request):
    """
    Get OpenAI ephemeral session token for voice chat
    """
    try:
        import requests

        if not OPENAI_API_KEY:
            return Response({'error': 'OpenAI API key not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get ephemeral token from OpenAI
        response = requests.post(
            'https://api.openai.com/v1/realtime/sessions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-4o-mini-realtime-preview-2024-12-17',
                'voice': request.GET.get('voice', 'alloy')
            }
        )

        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to get session token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error getting session token: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_sms(request):
    """
    Send SMS using Twilio
    """
    try:
        if not twilio_client:
            return Response({'error': 'Twilio not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        to_number = request.data.get('to')
        message_body = request.data.get('message')

        if not to_number or not message_body:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )

        logger.info(f"SMS sent with SID: {message.sid}")
        return Response({'success': True, 'message_sid': message.sid}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_prompt(request):
    """
    Get the system prompt for an organization
    """
    try:
        organization_id = request.GET.get('org_id')

        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        prompt = build_system_prompt(organization_id)

        if not prompt:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'prompt': prompt}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting prompt: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def transfer_call(request):
    """
    Transfer call to fallback number
    """
    try:
        if not twilio_client:
            return Response({'error': 'Twilio not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        organization_id = request.data.get('organization_id')
        call_sid = request.data.get('call_sid')

        if not organization_id or not call_sid:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Get fallback number
        fallback = FallbackNumber.objects.filter(organization_id=organization_id).first()

        if not fallback:
            return Response({'error': 'No fallback number configured'}, status=status.HTTP_404_NOT_FOUND)

        # Transfer the call
        twilio_client.calls(call_sid).update(
            twiml=f'<Response><Dial>{fallback.phone_number}</Dial></Response>'
        )

        logger.info(f"Call {call_sid} transferred to {fallback.phone_number}")
        return Response({'success': True}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error transferring call: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_assistant_status(request):
    """
    Get assistant status and phone number
    """
    try:
        organization_id = request.GET.get('org_id')

        if not organization_id:
            return Response({'error': 'organization_id required'}, status=status.HTTP_400_BAD_REQUEST)

        assistant = Assistant.objects.filter(organization_id=organization_id).first()

        if not assistant:
            return Response({
                'exists': False,
                'is_active': False,
                'phone_number': None
            }, status=status.HTTP_200_OK)

        return Response({
            'exists': True,
            'is_active': assistant.is_active,
            'phone_number': assistant.twilio_phone_number,
            'phone_sid': assistant.twilio_phone_sid,
            'name': assistant.name,
            'voice_type': assistant.voice_type
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting assistant status: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_assistant_with_number(request):
    """
    Create assistant and buy Twilio phone number
    """
    try:
        from .twilio_manager import buy_phone_number

        organization_id = request.data.get('organization_id')
        name = request.data.get('name')
        voice_type = request.data.get('voice_type')
        greeting_message = request.data.get('greeting_message', '')

        if not all([organization_id, name, voice_type]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        organization = Organization.objects.get(id=organization_id)

        # Check if assistant already exists
        assistant = Assistant.objects.filter(organization=organization).first()

        # Build webhook URL - Use NGROK_URL from env if available
        ngrok_url = os.getenv('NGROK_URL')

        if ngrok_url:
            # Use ngrok URL for webhooks
            webhook_url = f"{ngrok_url}/assistant/incoming-call/"
        else:
            # Fallback to request host
            host = request.get_host()

            # Check if using localhost - Twilio requires HTTPS
            if 'localhost' in host or '127.0.0.1' in host:
                return Response({
                    'error': 'Cannot create assistant with localhost URL. Please use ngrok or deploy to a server with HTTPS.',
                    'help': 'Run: ngrok http 8000, then add NGROK_URL to .env'
                }, status=status.HTTP_400_BAD_REQUEST)

            protocol = 'https' if request.is_secure() else 'http'
            webhook_url = f"{protocol}://{host}/assistant/incoming-call/"

        # Buy phone number
        phone_number, phone_sid = buy_phone_number(organization_id, webhook_url)

        if not phone_number:
            return Response({'error': 'Failed to purchase phone number. Check server logs for details.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if assistant:
            # Update existing assistant
            assistant.name = name
            assistant.voice_type = voice_type
            assistant.greeting_message = greeting_message
            assistant.twilio_phone_number = phone_number
            assistant.twilio_phone_sid = phone_sid
            assistant.is_active = True
            assistant.save()
        else:
            # Create new assistant
            assistant = Assistant.objects.create(
                organization=organization,
                name=name,
                voice_type=voice_type,
                greeting_message=greeting_message,
                twilio_phone_number=phone_number,
                twilio_phone_sid=phone_sid,
                is_active=True
            )

        # Update organization step and mark assistant as created
        organization.current_step = 13
        organization.assistant_created = True
        organization.save()

        logger.info(f"Created assistant with phone {phone_number} for organization {organization_id}")

        return Response({
            'success': True,
            'assistant_id': assistant.id,
            'phone_number': phone_number,
            'phone_sid': phone_sid
        }, status=status.HTTP_200_OK)

    except Organization.DoesNotExist:
        return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating assistant: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
