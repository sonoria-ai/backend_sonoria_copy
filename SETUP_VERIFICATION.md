# Voice Assistant Setup Verification

## ✅ Completed Components

### 1. Django App: `assistant/`
- ✅ `prompt_builder.py` - Dynamic prompt generation from database
- ✅ `views.py` - HTTP endpoints (Twilio webhook, SMS, transfer)
- ✅ `websocket_handler.py` - Real-time audio streaming WebSocket consumer
- ✅ `routing.py` - WebSocket URL routing
- ✅ `urls.py` - HTTP URL patterns

### 2. Configuration Files
- ✅ `settings.py` - Added 'assistant' and 'channels' to INSTALLED_APPS
- ✅ `asgi.py` - ASGI configuration with WebSocket support
- ✅ Main `urls.py` - Included assistant URLs
- ✅ `.env` - Added TWILIO placeholders (needs actual credentials)

### 3. Dependencies Installed
```
✅ channels==4.3.1
✅ openai==2.4.0
✅ twilio==9.8.4
✅ websockets==15.0.1
```

### 4. Testing
- ✅ Django check passed: 0 issues
- ✅ Prompt builder tested successfully
- ✅ Generated 6,722 character prompt from database

## 🔧 Environment Setup Required

### Twilio Credentials (REQUIRED)
Update `.env` with your Twilio credentials:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

Get credentials from: https://console.twilio.com/

### OpenAI API Key (ALREADY CONFIGURED ✅)
```bash
OPENAI_API_KEY=sk-proj-... (already set)
```

## 🚀 Testing Instructions

### Step 1: Start Django Server
```bash
cd sonoria_backend
source venv/bin/activate
python manage.py runserver
```

### Step 2: Start ngrok (in new terminal)
```bash
# Install ngrok if not already installed
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Start tunnel
ngrok http 8000
```

### Step 3: Configure Twilio
1. Copy ngrok URL (e.g., `https://abc123.ngrok.io`)
2. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
3. Select your Twilio phone number
4. Under "Voice Configuration":
   - Webhook URL: `https://abc123.ngrok.io/assistant/incoming-call/?org_id=1`
   - Method: `POST`
5. Save configuration

### Step 4: Test Call Flow
1. Call your Twilio number from your phone
2. Expected flow:
   - ✅ Assistant greets with: "hi how are you" (from database)
   - ✅ Say: "I want to book an appointment"
   - ✅ Receive SMS with booking link
   - ✅ Check Django logs for full transcript

### Step 5: Test API Endpoints

```bash
# View generated prompt
curl http://localhost:8000/assistant/get-prompt/?org_id=1

# Test SMS (requires Twilio credentials)
curl -X POST http://localhost:8000/assistant/send-sms/ \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Test message"}'
```

## 📊 Database Integration

The prompt builder uses these models:
- ✅ Organization (name, industry, description)
- ✅ Assistant (name, voice_type, greeting_message)
- ✅ Service (name, duration, price, detail)
- ✅ Option (add-ons with duration, price, detail)
- ✅ BusinessHours (day, open_time, close_time, hours_type)
- ✅ ExceptionalClosing (open_date, close_date, reason)
- ✅ OrganizationFAQ (question, answer)
- ✅ BookingRule (all fields including cutoff, modifications, cancellations)
- ✅ CommunicationTemplate (SMS templates)
- ✅ ServiceLocation (main, multiple, or client location)
- ✅ Location (multiple locations)
- ✅ TeamMember (name, email, location)
- ✅ TeamMemberConfig (has_multiple_members, allow_client_choose_worker)
- ✅ FallbackNumber (phone number for transfers)

## 🎯 Function Capabilities

The AI assistant can execute these functions:

1. **book_service** - Send booking SMS with link
2. **update_booking** - Send reschedule SMS with link
3. **cancel_booking** - Send cancellation SMS with link
4. **notify_owner** - Forward message to business owner
5. **transfer_call** - Transfer to fallback number (human)

## 📝 Sample Test Prompts

Try these when you call:

1. **Booking**: "I want to book an appointment"
   - Expected: Receives booking SMS

2. **Rescheduling**: "I need to change my appointment"
   - Expected: Receives update link SMS

3. **Cancellation**: "Please cancel my appointment"
   - Expected: Receives cancellation link SMS

4. **Question**: "What are your hours?"
   - Expected: AI answers from business hours data

5. **Transfer**: "I want to speak to a manager"
   - Expected: Call transferred to fallback number

6. **Message**: "I'm running 10 minutes late"
   - Expected: Owner receives notification SMS

## 🔍 Monitoring & Logs

### View Logs
```bash
# Terminal running Django server will show:
- Incoming call details
- WebSocket connections
- OpenAI API interactions
- Function calls executed
- Full conversation transcript
```

### Sample Log Output
```
INFO: Incoming call from +1234567890 for organization 1
INFO: Call started: CA123..., Org: 1
INFO: User: I want to book an appointment
INFO: Function called: book_service with args: {'caller_number': '+1234567890'}
INFO: Booking SMS sent successfully
INFO: Agent: All of our classes are booked online — I've sent you the booking link by SMS. Anything else?
```

## ✨ Next Steps

1. **Get Twilio Credentials**: Sign up at https://www.twilio.com/try-twilio
2. **Update .env**: Add Twilio credentials
3. **Test Locally**: Use ngrok tunnel
4. **Production Deploy**: Use proper ASGI server (Daphne/Uvicorn) with WSS

## 🎤 Voice Options

Available voices (from Assistant model):
- alloy (Female)
- ash (Male)
- ballad (Female)
- coral (Female)
- sage (Male)
- echo (Male)
- shimmer (Female)
- verse (Male)

Current organization using: **ash** (from database)

## 🔐 Security Notes

- ✅ CORS configured for frontend
- ✅ CSRF exempt on Twilio webhooks (required)
- ✅ Environment variables for sensitive data
- ⚠️ Change Twilio credentials placeholders before deploying

## 📞 Production Deployment Checklist

For production (when ready):
- [ ] Deploy with Daphne or Uvicorn (ASGI server)
- [ ] Use WSS (secure WebSocket) with SSL certificate
- [ ] Update Twilio webhook to production domain
- [ ] Set environment variables on server
- [ ] Use Redis for channel layer (replace InMemoryChannelLayer)
- [ ] Enable logging and monitoring
- [ ] Set up backup fallback numbers
