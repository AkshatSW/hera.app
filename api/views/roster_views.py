from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.conf import settings
from api.services.roster_service import parse_roster
from api.models import Assignment
from api.tasks import send_sms_task

# Max file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


class RosterUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size
        if file.size > MAX_FILE_SIZE:
            return Response(
                {'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not file.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'File must be an Excel file (.xlsx or .xls)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = parse_roster(file, request.user)

        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_201_CREATED)


class RosterSendSMSView(APIView):
    """Send SMS for a batch of assignment IDs."""

    def post(self, request):
        assignment_ids = request.data.get('assignment_ids', [])
        if not assignment_ids:
            return Response(
                {'error': 'No assignment_ids provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resend = request.data.get('resend', False)
        allowed_statuses = ['pending', 'failed']
        if resend:
            allowed_statuses = ['pending', 'failed', 'queued', 'sent', 'delivered']

        assignments = Assignment.objects.filter(
            id__in=assignment_ids,
            user=request.user,
            sms_status__in=allowed_statuses,
        ).select_related('driver', 'vehicle')

        queued = 0
        for assignment in assignments:
            driver = assignment.driver
            vehicle = assignment.vehicle

            date_str = assignment.route_date.strftime('%A %m/%d/%Y')
            wave_time_str = assignment.wave_time.strftime('%I:%M %p')
            message = (
                f"You are rostered for: {date_str}\n\n"
                f"Wave Time: {wave_time_str}\n"
                f"Vehicle: {vehicle.vehicle_code} {vehicle.plate_number}\n"
                f"Route: {assignment.route_code}\n"
                f"Staging: {assignment.staging} PAD {assignment.pad}"
            )

            assignment.sms_status = 'queued'
            assignment.save(update_fields=['sms_status'])
            send_sms_task.delay(driver.phone, message, driver.id, assignment.id)
            queued += 1

        return Response({
            'sms_queued': queued,
            'total_requested': len(assignment_ids),
        })
