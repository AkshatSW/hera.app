import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from twilio.request_validator import RequestValidator
from api.models import Driver, SMSLog
from api.serializers import SMSLogSerializer, ManualSMSSerializer
from api.tasks import send_manual_sms_task

logger = logging.getLogger(__name__)


class SMSHistoryView(APIView):
    def get(self, request):
        driver_id = request.query_params.get('driver_id')
        if not driver_id:
            return Response(
                {'error': 'driver_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sms_logs = SMSLog.objects.filter(
            driver_id=driver_id,
            driver__user=request.user,
        ).order_by('sent_at')
        serializer = SMSLogSerializer(sms_logs, many=True)
        return Response(serializer.data)


class SendManualSMSView(APIView):
    def post(self, request):
        serializer = ManualSMSSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        driver_id = serializer.validated_data['driver_id']
        message = serializer.validated_data['message']

        try:
            driver = Driver.objects.get(id=driver_id, user=request.user)
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        send_manual_sms_task.delay(driver.phone, message, driver.id)

        return Response(
            {'status': 'queued', 'message': 'SMS queued for delivery'},
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_exempt, name='dispatch')
class SMSWebhookView(APIView):
    """Handle Twilio delivery status webhooks with signature validation."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Validate Twilio signature
        if not self._validate_twilio_signature(request):
            logger.warning("Invalid Twilio webhook signature")
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_403_FORBIDDEN,
            )

        message_sid = request.data.get('MessageSid')
        message_status = request.data.get('MessageStatus')

        if not message_sid or not message_status:
            return Response(
                {'error': 'Missing MessageSid or MessageStatus'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sms_log = SMSLog.objects.get(provider_message_id=message_sid)
        except SMSLog.DoesNotExist:
            return Response(
                {'error': 'SMS log not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        sms_log.status = message_status
        if message_status == 'delivered':
            from django.utils import timezone
            sms_log.delivered_at = timezone.now()
        elif message_status == 'failed':
            sms_log.error_message = request.data.get('ErrorMessage', '')

        sms_log.save()

        # Update assignment SMS status if linked
        if sms_log.assignment_id:
            from api.models import Assignment
            Assignment.objects.filter(id=sms_log.assignment_id).update(
                sms_status=message_status
            )

        return Response({'status': 'updated'})

    def _validate_twilio_signature(self, request):
        """Validate that the request came from Twilio."""
        auth_token = settings.TWILIO_AUTH_TOKEN
        if not auth_token:
            # Skip validation if auth token not configured (development)
            logger.warning("Twilio auth token not configured, skipping signature validation")
            return True

        validator = RequestValidator(auth_token)

        # Get the full URL including scheme
        url = request.build_absolute_uri()

        # Get the signature from headers
        signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')

        # Get POST parameters
        params = request.POST.dict()

        return validator.validate(url, params, signature)
