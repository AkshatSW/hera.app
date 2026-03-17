import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_task(self, phone, message, driver_id, assignment_id):
    """Celery task to send SMS and log the result."""
    from api.models import SMSLog, Assignment
    from api.services.sms_service import send_sms

    sms_log = SMSLog.objects.create(
        driver_id=driver_id,
        phone=phone,
        message=message,
        status='queued',
        assignment_id=assignment_id,
    )

    try:
        message_sid = send_sms(phone, message)
        sms_log.provider_message_id = message_sid
        sms_log.status = 'sent'
        sms_log.sent_at = timezone.now()
        sms_log.save()

        Assignment.objects.filter(id=assignment_id).update(sms_status='sent')

        logger.info(f"SMS sent to {phone}, SID: {message_sid}")
        return {'status': 'sent', 'message_sid': message_sid}

    except Exception as exc:
        sms_log.status = 'failed'
        sms_log.error_message = str(exc)
        sms_log.sent_at = timezone.now()
        sms_log.save()

        Assignment.objects.filter(id=assignment_id).update(sms_status='failed')

        logger.error(f"Failed to send SMS to {phone}: {exc}")

        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for SMS to {phone}")
            return {'status': 'failed', 'error': str(exc)}


@shared_task
def send_manual_sms_task(phone, message, driver_id):
    """Celery task to send a manual SMS (not tied to an assignment)."""
    from api.models import SMSLog
    from api.services.sms_service import send_sms

    sms_log = SMSLog.objects.create(
        driver_id=driver_id,
        phone=phone,
        message=message,
        status='queued',
    )

    try:
        message_sid = send_sms(phone, message)
        sms_log.provider_message_id = message_sid
        sms_log.status = 'sent'
        sms_log.sent_at = timezone.now()
        sms_log.save()
        return {'status': 'sent', 'message_sid': message_sid}
    except Exception as exc:
        sms_log.status = 'failed'
        sms_log.error_message = str(exc)
        sms_log.sent_at = timezone.now()
        sms_log.save()
        return {'status': 'failed', 'error': str(exc)}
