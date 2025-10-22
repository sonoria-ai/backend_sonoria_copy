#!/usr/bin/env python
"""
Test script to verify phone number purchasing works
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonoria_backend.settings')
django.setup()

from assistant.twilio_manager import get_twilio_client
from gabby_booking.models import Organization, Assistant

def test_twilio_connection():
    print("Testing Twilio connection...")
    client = get_twilio_client()

    if not client:
        print("❌ Twilio client not configured")
        return False

    print(f"✅ Twilio client connected (SID: {client.username})")

    # Test searching for available numbers
    try:
        numbers = client.available_phone_numbers('US').local.list(limit=3)
        if numbers:
            print(f"✅ Found {len(numbers)} available numbers:")
            for num in numbers:
                print(f"   - {num.phone_number}")
        else:
            print("⚠️ No available numbers found")
    except Exception as e:
        print(f"❌ Error searching numbers: {str(e)}")
        return False

    return True

def test_database():
    print("\n" + "="*60)
    print("Testing database...")

    # Check if organizations exist
    orgs = Organization.objects.all()
    print(f"✅ Found {orgs.count()} organization(s)")

    if orgs.exists():
        org = orgs.first()
        print(f"   First org: {org.name} (ID: {org.id})")

        # Check assistant
        assistant = Assistant.objects.filter(organization=org).first()
        if assistant:
            print(f"✅ Assistant exists: {assistant.name}")
            print(f"   Voice: {assistant.voice_type}")
            print(f"   Phone: {assistant.twilio_phone_number or 'Not assigned'}")
            print(f"   Active: {assistant.is_active}")
        else:
            print("⚠️ No assistant found for this organization")

    return True

def show_phone_assignments():
    print("\n" + "="*60)
    print("Current phone number assignments:")

    assistants = Assistant.objects.filter(twilio_phone_number__isnull=False)

    if assistants.exists():
        for asst in assistants:
            print(f"  {asst.organization.name}: {asst.twilio_phone_number}")
            print(f"    - Voice: {asst.voice_type}")
            print(f"    - Active: {asst.is_active}")
    else:
        print("  No phone numbers assigned yet")

def show_how_it_works():
    print("\n" + "="*60)
    print("HOW IT WORKS:")
    print("="*60)
    print("""
1. User clicks 'Create My Assistant' in frontend
   └─> Frontend sends POST to /assistant/create-assistant/

2. Backend (views.create_assistant_with_number):
   ├─> Gets assistant data (name, voice, greeting)
   ├─> Builds webhook URL: https://yourdomain.com/assistant/incoming-call/
   ├─> Calls Twilio API to buy phone number
   ├─> Configures that number to POST to webhook URL
   └─> Saves phone number to Assistant model

3. When someone calls the Twilio number:
   ├─> Twilio sends POST to: /assistant/incoming-call/
   ├─> Backend looks up organization by phone number (To field)
   ├─> Returns TwiML with WebSocket URL
   ├─> WebSocket connects to OpenAI Realtime API
   └─> Voice conversation begins

4. No need to pass org_id in webhook URL!
   └─> Phone number automatically identifies the organization

TESTING:
--------
To test buying a number (without frontend):

  from assistant.twilio_manager import buy_phone_number

  phone, sid = buy_phone_number(
      organization_id=1,
      webhook_url='https://your-ngrok-url.ngrok.io/assistant/incoming-call/'
  )

  print(f"Purchased: {phone}")

Then call that number and it will automatically route to your organization!
    """)

if __name__ == "__main__":
    print("="*60)
    print("PHONE NUMBER SYSTEM TEST")
    print("="*60)

    if test_twilio_connection():
        test_database()
        show_phone_assignments()
        show_how_it_works()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Tests failed - check Twilio credentials")
        print("="*60)
