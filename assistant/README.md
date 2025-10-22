# Sonoria Assistant - Voice AI with OpenAI Realtime API

## Setup

### 1. Install ngrok
```bash
brew install ngrok  # macOS
# or download from https://ngrok.com/download
```

### 2. Environment Variables (.env)
```
OPENAI_API_KEY=your_openai_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

### 3. Run Server
```bash
# Terminal 1: Run Django with Channels
python manage.py runserver

# Terminal 2: Expose with ngrok
ngrok http 8000
```

### 4. Configure Twilio
1. Copy your ngrok URL (e.g., `https://abc123.ngrok.io`)
2. Go to Twilio Console → Phone Numbers → Your Number
3. Set webhook URL: `https://abc123.ngrok.io/assistant/incoming-call/?org_id=1`
4. Replace `org_id=1` with your organization ID

## API Endpoints

### GET /assistant/incoming-call/?org_id=<id>
Handles incoming Twilio calls

### WebSocket /assistant/media-stream
Handles real-time audio streaming

### GET /assistant/get-prompt/?org_id=<id>
Get generated system prompt for organization

### POST /assistant/send-sms/
Send SMS via Twilio
```json
{
  "to": "+1234567890",
  "message": "Your message"
}
```

### POST /assistant/transfer-call/
Transfer call to fallback number
```json
{
  "organization_id": 1,
  "call_sid": "CA123..."
}
```

## How It Works

1. Customer calls Twilio number
2. Twilio sends webhook to `/incoming-call/?org_id=X`
3. Django returns TwiML with WebSocket URL
4. WebSocket connects: `/media-stream`
5. Assistant connects to OpenAI Realtime API
6. System prompt is built dynamically from database
7. Audio streams between Twilio ↔ Django ↔ OpenAI
8. Functions handle: booking, update, cancel, notify, transfer

## Dynamic Prompt Building

The system prompt is built from:
- Organization details
- Assistant name and voice
- Business hours
- Services and add-ons
- FAQs
- Booking rules
- Communication templates

See `prompt_builder.py` for full implementation.

## Functions Available

- `book_service`: Send booking SMS
- `update_booking`: Send reschedule SMS
- `cancel_booking`: Send cancel SMS
- `notify_owner`: Notify business owner
- `transfer_call`: Transfer to human

## Testing

1. Call your Twilio number
2. Voice assistant responds with greeting
3. Say "I want to book an appointment"
4. Receive booking SMS
5. Check logs for transcript
