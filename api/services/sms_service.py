import logging
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


def send_sms(phone, message):
    """Send an SMS message via Twilio using Messaging Service.

    Returns the Twilio message SID on success.
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    messaging_service_sid = settings.TWILIO_MESSAGING_SERVICE_SID

    if not all([account_sid, auth_token, messaging_service_sid]):
        logger.error("Twilio credentials not configured")
        raise ValueError("Twilio credentials not configured")

    client = Client(account_sid, auth_token)

    try:
        tw_message = client.messages.create(
            body=message,
            messaging_service_sid=messaging_service_sid,
            to=phone,
        )
        logger.info(f"SMS sent to {phone}, SID: {tw_message.sid}")
        return tw_message.sid
    except TwilioRestException as e:
        logger.error(f"Twilio error sending SMS to {phone}: {e}")
        raise
