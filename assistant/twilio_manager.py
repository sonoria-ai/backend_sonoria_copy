import os
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

def get_twilio_client():
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return None
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def buy_phone_number(organization_id, webhook_url):
    """
    Buy a new phone number from Twilio and configure it
    Returns: (phone_number, phone_sid) or (None, None) if failed
    """
    try:
        client = get_twilio_client()
        if not client:
            logger.error("Twilio client not configured")
            return None, None

        # Search for available phone numbers (US)
        available_numbers = client.available_phone_numbers('US').local.list(limit=1)

        if not available_numbers:
            logger.error("No available phone numbers")
            return None, None

        phone_number = available_numbers[0].phone_number

        # Purchase the phone number
        incoming_phone = client.incoming_phone_numbers.create(
            phone_number=phone_number,
            voice_url=webhook_url,
            voice_method='POST'
        )

        logger.info(f"Purchased phone number: {phone_number} with SID: {incoming_phone.sid}")
        return phone_number, incoming_phone.sid

    except Exception as e:
        logger.error(f"Error buying phone number: {str(e)}")
        return None, None


def update_phone_webhook(phone_sid, webhook_url):
    """
    Update the webhook URL for an existing phone number
    """
    try:
        client = get_twilio_client()
        if not client:
            logger.error("Twilio client not configured")
            return False

        client.incoming_phone_numbers(phone_sid).update(
            voice_url=webhook_url,
            voice_method='POST'
        )

        logger.info(f"Updated webhook for {phone_sid} to {webhook_url}")
        return True

    except Exception as e:
        logger.error(f"Error updating webhook: {str(e)}")
        return False


def release_phone_number(phone_sid):
    """
    Release a phone number back to Twilio
    """
    try:
        client = get_twilio_client()
        if not client:
            logger.error("Twilio client not configured")
            return False

        client.incoming_phone_numbers(phone_sid).delete()
        logger.info(f"Released phone number: {phone_sid}")
        return True

    except Exception as e:
        logger.error(f"Error releasing phone number: {str(e)}")
        return False
