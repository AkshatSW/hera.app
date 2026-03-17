import logging
from api.services.sms_service import send_sms

logger = logging.getLogger(__name__)


def send_otp_sms(phone, otp_code, purpose='verification'):
    """Send a 6-digit OTP code via SMS."""
    if purpose == 'verification':
        message = f"Hera: Your verification code is {otp_code}. It expires in 10 minutes."
    else:
        message = f"Hera: Your password reset code is {otp_code}. It expires in 10 minutes."

    try:
        send_sms(phone, message)
        logger.info(f"OTP SMS sent to {phone}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone}: {e}")
        raise
