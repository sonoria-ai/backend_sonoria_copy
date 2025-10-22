# 🚀 Voice Assistant Quick Start Guide

## ⚡ 3-Step Setup

### Step 1: Add Twilio Credentials (2 minutes)

1. Go to https://www.twilio.com/try-twilio and sign up
2. Get your credentials from the console
3. Edit `.env` file:

```bash
# Replace these with your actual Twilio credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_actual_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
```

### Step 2: Start Server (30 seconds)

**Terminal 1 - Django**:
```bash
cd sonoria_backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - ngrok**:
```bash
ngrok http 8000
```

Copy the ngrok URL (looks like: `https://abc123.ngrok.io`)

### Step 3: Configure Twilio (1 minute)

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click your phone number
3. Under "Voice Configuration":
   - Webhook: `https://abc123.ngrok.io/assistant/incoming-call/?org_id=1`
   - Method: `POST`
4. Click Save

---

## ✅ Test It!

### Make a Call

Call your Twilio number from your phone and try:

1. **"I want to book an appointment"**
   - ✅ Should send you booking SMS

2. **"What are your hours?"**
   - ✅ Should answer from database

3. **"I want to speak to a manager"**
   - ✅ Should transfer call

### Check Logs

In Terminal 1 (Django server), you'll see:
```
INFO: Incoming call from +15551234567 for organization 1
INFO: User: I want to book an appointment
INFO: Function called: book_service
INFO: Booking SMS sent successfully
```

---

## 📊 View Generated Prompt

See what the AI is using:
```bash
curl http://localhost:8000/assistant/get-prompt/?org_id=1
```

Or visit in browser: http://localhost:8000/assistant/get-prompt/?org_id=1

---

## 🔧 Troubleshooting

### "No organization found"
- Make sure you have an organization in database with ID=1
- Or change `org_id=1` to your actual organization ID in webhook URL

### "Twilio not configured"
- Check `.env` has correct Twilio credentials
- Restart Django server after updating `.env`

### "OpenAI API error"
- Verify OPENAI_API_KEY in `.env` is correct
- Check OpenAI account has credits

### Call doesn't connect
- Verify ngrok is running
- Check Twilio webhook URL is correct
- Ensure webhook method is POST

### No SMS received
- Check Twilio phone number is verified
- View Django logs for errors
- Verify TWILIO_PHONE_NUMBER format: `+15551234567`

---

## 📱 What's Working

✅ Dynamic prompts from database
✅ Real-time voice conversations
✅ SMS for booking/update/cancel
✅ Call transfers to fallback
✅ Owner notifications
✅ Full transcript logging
✅ 8 voice options
✅ Organization-specific configuration

---

## 🎯 Test Scenarios

| Say This | What Happens |
|----------|--------------|
| "I want to book an appointment" | Sends booking SMS |
| "I need to reschedule" | Sends update SMS |
| "Cancel my appointment" | Sends cancel SMS |
| "What are your hours?" | Answers from database |
| "How much does X cost?" | Answers from services |
| "I have a question" | Takes message for owner |
| "Transfer me to manager" | Transfers call |
| "I'm running 10 minutes late" | Notifies owner |

---

## 📚 Full Documentation

- `VOICE_ASSISTANT_COMPLETE.md` - Complete implementation guide
- `SETUP_VERIFICATION.md` - Setup checklist
- `assistant/README.md` - Technical details
- `ASSISTANT_IMPLEMENTATION.md` - Architecture overview

---

## 🎉 That's It!

Your voice assistant is ready to handle calls. Each call will:
1. Greet with your custom message from database
2. Answer questions using your business data
3. Send SMS links for booking/updates
4. Transfer to human when needed
5. Log full conversation transcript

**Enjoy your AI receptionist! 🤖📞**
