# Sonoria Voice Assistant Implementation

## Overview

Complete Django implementation of voice AI assistant using OpenAI Realtime API with Twilio integration. The system dynamically builds conversation prompts from database configuration.

## Architecture

```
Twilio Phone Call → Django Assistant App → OpenAI Realtime API
                   ↓
              WebSocket (Channels)
                   ↓
         Real-time Audio Streaming
                   ↓
            Function Execution
      (SMS, Notify, Transfer)
```

## Components Created

### 1. Django App: `assistant/`

```
assistant/
├── prompt_builder.py      # Dynamic prompt generation from DB
├── views.py              # HTTP endpoints (incoming call, SMS, transfer)
├── websocket_handler.py  # WebSocket consumer for real-time audio
├── routing.py            # WebSocket URL routing
├── urls.py              # HTTP URL routing
└── README.md            # Setup and usage guide
```

### 2. Prompt Builder (`prompt_builder.py`)

**Function**: `build_system_prompt(organization_id)`

Dynamically generates AI assistant prompts using:
- Organization details (name, industry)
- Assistant configuration (name, voice, greeting)
- Business hours and exceptional closings
- Services and add-ons with pricing
- FAQs from database
- Booking rules and policies
- Communication templates

**Example Output**:
```
# Role & Objective
- You are Clara, the virtual receptionist for Serenity Yoga Studio.
- Success means: answer questions, send SMS links, take messages, or transfer calls
...
## Services
- Vinyasa Yoga (60 min) - $100
- Hatha Yoga (60 min) - $100
...
```

### 3. Views (`views.py`)

**Endpoints**:

1. `POST /assistant/incoming-call/?org_id=<id>` - Twilio webhook handler
2. `GET /assistant/session-token/` - OpenAI ephemeral token
3. `POST /assistant/send-sms/` - Send SMS via Twilio
4. `GET /assistant/get-prompt/?org_id=<id>` - View generated prompt
5. `POST /assistant/transfer-call/` - Transfer to fallback number

### 4. WebSocket Handler (`websocket_handler.py`)

**Class**: `MediaStreamConsumer`

Handles real-time audio streaming:
- Connects to OpenAI Realtime API
- Streams audio bidirectionally (Twilio ↔ OpenAI)
- Executes functions (booking, update, cancel, notify, transfer)
- Manages conversation interruptions
- Logs full transcripts

**Functions Available**:
- `book_service`: Sends booking SMS to customer
- `update_booking`: Sends reschedule SMS
- `cancel_booking`: Sends cancellation SMS
- `notify_owner`: Forwards message to business owner
- `transfer_call`: Transfers to human (fallback number)

## Database Integration

Uses existing models from `gabby_booking` app:
- ✅ Organization
- ✅ Assistant (name, voice_type, greeting_message)
- ✅ Service
- ✅ Option (add-ons)
- ✅ BusinessHours
- ✅ ExceptionalClosing
- ✅ OrganizationFAQ
- ✅ BookingRule
- ✅ CommunicationTemplate
- ✅ FallbackNumber

## Environment Variables Required

```bash
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

## Setup Instructions

### 1. Install Dependencies
```bash
cd sonoria_backend
source venv/bin/activate
pip install channels twilio openai requests websockets
```

### 2. Update Settings
Added to `INSTALLED_APPS`:
- `'assistant'`
- `'channels'`
1
Added ASGI configuration in `settings.py`.

### 3. Configure ASGI
Updated `asgi.py` with WebSocket routing.

### 4. Run Server
```bash
# Terminal 1: Django with Channels
python manage.py runserver

# Terminal 2: Ngrok
ngrok http 8000
```

### 5. Configure Twilio
1. Copy ngrok URL: `https://abc123.ngrok.io`
2. Twilio Console → Phone Numbers → Your Number
3. Voice webhook: `https://abc123.ngrok.io/assistant/incoming-call/?org_id=1`
4. Method: POST

## Testing

### Test Prompt Generation
```bash
python test_assistant.py
```

### Test Live Call
1. Call your Twilio number
2. Assistant responds with greeting from database
3. Say: "I want to book an appointment"
4. Receive SMS with booking link
5. Check Django logs for transcript

### Test API Endpoints
```bash
# Get prompt for organization 1
curl http://localhost:8000/assistant/get-prompt/?org_id=1

# Send SMS
curl -X POST http://localhost:8000/assistant/send-sms/ \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Test message"}'
```

## Voice Options

Supports all OpenAI Realtime voices (stored in `assistant.voice_type`):
- alloy
- ash
- ballad
- coral
- sage
- echo
- shimmer
- verse

## Call Flow Example

1. **Customer calls** → Twilio receives call
2. **Webhook triggered** → `/assistant/incoming-call/?org_id=1`
3. **TwiML response** → Contains WebSocket URL
4. **WebSocket connects** → `/assistant/media-stream`
5. **OpenAI connects** → With dynamic system prompt
6. **Audio streams** → Twilio ↔ Django ↔ OpenAI
7. **Customer speaks** → "I want to book"
8. **AI detects intent** → Calls `book_service` function
9. **SMS sent** → Via Twilio to customer
10. **AI confirms** → "I've sent you the booking link by SMS"
11. **Transcript logged** → Full conversation saved

## Function Call Handling

When AI calls a function:
1. WebSocket receives function call event
2. Handler executes corresponding action (SMS, notify, transfer)
3. Result sent back to OpenAI
4. AI speaks confirmation to customer

Example:
```python
# AI calls: book_service(caller_number="+1234567890")
# Handler sends: Booking SMS to customer
# AI says: "I've sent you the booking link by SMS. Anything else?"
```

## SMS Templates

Uses `CommunicationTemplate` from database:
- **Booking SMS**: `booking_sms_content` field
- **Update SMS**: Customer portal link
- **Cancel SMS**: Customer portal link
- **Notify Owner**: Custom message

## Fallback & Transfer

When customer asks for manager or AI fails 3 times:
1. Retrieves `FallbackNumber` for organization
2. Uses Twilio API to transfer call
3. Customer connected to business owner

## Logs & Transcripts

Full conversation transcripts logged:
```
User: I want to book an appointment
Agent: All of our classes are booked online — I've sent you the booking link by SMS. Anything else?
User: No, that's all
Agent: Thank you for calling Serenity Yoga Studio. Have a wonderful day!
```

## Integration with Dashboard

Everything configured in dashboard is used:
- ✅ Step 1-2: Organization details
- ✅ Step 3-4: Services and locations
- ✅ Step 5: Business hours
- ✅ Step 6: Add-ons
- ✅ Step 7: Team members
- ✅ Step 8-9: Booking rules
- ✅ Step 10: Communication templates
- ✅ Step 11: FAQs
- ✅ Step 12: Assistant settings (name, voice, greeting)
- ✅ Step 13: Fallback number

## Production Deployment

For production (replace ngrok):
1. Deploy Django with Daphne or Uvicorn (for ASGI/WebSocket support)
2. Use WSS (secure WebSocket) with SSL certificate
3. Update Twilio webhook to production domain
4. Set environment variables on server
5. Use Redis for channel layer (instead of in-memory)

## Files Modified

- `sonoria_backend/settings.py` - Added assistant app and channels
- `sonoria_backend/asgi.py` - Added WebSocket routing
- `sonoria_backend/urls.py` - Added assistant URLs
- `requirements.txt` - Added dependencies

## Files Created

- `assistant/prompt_builder.py`
- `assistant/views.py`
- `assistant/websocket_handler.py`
- `assistant/routing.py`
- `assistant/urls.py`
- `assistant/README.md`
- `test_assistant.py`

## Next Steps

1. ✅ Test with real Twilio number
2. ✅ Verify SMS delivery
3. ✅ Test function calls (booking, update, cancel, notify, transfer)
4. ✅ Monitor transcripts in logs
5. Deploy to production with proper WebSocket server
