"""
Notification utilities for sending SMS messages for bookings
"""
import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None


def send_booking_sms(customer_phone, message_body):
    """
    Send SMS notification using Twilio

    Args:
        customer_phone: Customer's phone number
        message_body: SMS message content

    Returns:
        tuple: (success: bool, message_sid: str or None)
    """
    try:
        if not twilio_client:
            logger.warning('Twilio client not configured - skipping SMS')
            return False, None

        if not customer_phone:
            logger.warning('No customer phone number provided - skipping SMS')
            return False, None

        # Clean phone number (remove spaces, dashes, etc.)
        cleaned_phone = ''.join(filter(str.isdigit, customer_phone))

        # Add country code if not present (assuming US/Canada +1)
        if not cleaned_phone.startswith('+'):
            if len(cleaned_phone) == 10:
                cleaned_phone = f'+1{cleaned_phone}'
            elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
                cleaned_phone = f'+{cleaned_phone}'
            else:
                cleaned_phone = f'+{cleaned_phone}'

        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=cleaned_phone
        )

        logger.info(f"SMS sent successfully. SID: {message.sid}")
        return True, message.sid

    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return False, None


def format_booking_confirmation_message(appointment, organization):
    """
    Format booking confirmation SMS message

    Args:
        appointment: Appointment object
        organization: Organization object

    Returns:
        str: Formatted SMS message
    """
    # Get assistant name
    from .models import Assistant

    try:
        assistant = Assistant.objects.filter(organization=organization).first()
        assistant_name = assistant.name if assistant else "Clara"
    except Exception:
        assistant_name = "Clara"

    # Build booking portal link with org_id
    base_url = os.getenv('FRONTEND_URL', 'https://sonoria-frontend-9cay.vercel.app')
    booking_link = f"{base_url}/booking-portal?org={organization.id}"

    # Format message exactly as specified
    message = f"""Hi this is {assistant_name} from {organization.name}. Here's the link to book your appointment easily:
{booking_link}
Let me know if you need anything, I'm happy to help."""

    return message


def format_reschedule_message(appointment, organization, old_date=None, old_time=None):
    """
    Format reschedule confirmation SMS message

    Args:
        appointment: Updated appointment object
        organization: Organization object
        old_date: Previous date (not used, kept for compatibility)
        old_time: Previous time (not used, kept for compatibility)

    Returns:
        str: Formatted SMS message
    """
    # Get assistant name
    from .models import Assistant

    try:
        assistant = Assistant.objects.filter(organization=organization).first()
        assistant_name = assistant.name if assistant else "Clara"
    except Exception:
        assistant_name = "Clara"

    # Build customer portal link with org_id
    base_url = os.getenv('FRONTEND_URL', 'https://sonoria-frontend-9cay.vercel.app')
    customer_portal_link = f"{base_url}/customer-portal?org={organization.id}"

    # Format message exactly as specified
    message = f"""Hi this is {assistant_name} from {organization.name}. Here's the link to reschedule your appointment easily:
{customer_portal_link}
Let me know if you need anything, I'm happy to help."""

    return message


def format_cancellation_message(appointment, organization):
    """
    Format cancellation confirmation SMS message

    Args:
        appointment: Cancelled appointment object (not used, kept for compatibility)
        organization: Organization object

    Returns:
        str: Formatted SMS message
    """
    # Get assistant name
    from .models import Assistant

    try:
        assistant = Assistant.objects.filter(organization=organization).first()
        assistant_name = assistant.name if assistant else "Clara"
    except Exception:
        assistant_name = "Clara"

    # Build customer portal link with org_id
    base_url = os.getenv('FRONTEND_URL', 'https://sonoria-frontend-9cay.vercel.app')
    customer_portal_link = f"{base_url}/customer-portal?org={organization.id}"

    # Format message exactly as specified
    message = f"""Hi this is {assistant_name} from {organization.name}. Here's the link to cancel your appointment:
{customer_portal_link}
You can easily manage your booking there. Let me know if you need any help!"""

    return message


def send_booking_notification(appointment, notification_type='created', old_date=None, old_time=None):
    """
    Send SMS notification for booking events

    Args:
        appointment: Appointment object
        notification_type: 'created', 'rescheduled', or 'cancelled'
        old_date: Previous date (for reschedule)
        old_time: Previous time (for reschedule)

    Returns:
        tuple: (success: bool, message_sid: str or None)
    """
    try:
        organization = appointment.organization
        customer = appointment.customer

        # Check if customer has phone number
        if not customer.phone:
            logger.info(f"No phone number for customer {customer.email} - skipping SMS")
            return False, None

        # Format message based on notification type
        if notification_type == 'created':
            message_body = format_booking_confirmation_message(appointment, organization)
        elif notification_type == 'rescheduled':
            message_body = format_reschedule_message(appointment, organization, old_date, old_time)
        elif notification_type == 'cancelled':
            message_body = format_cancellation_message(appointment, organization)
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False, None

        # Send SMS
        return send_booking_sms(customer.phone, message_body)

    except Exception as e:
        logger.error(f"Error in send_booking_notification: {str(e)}")
        return False, None
