"""
Views for daily route import and SMS management.

Handles uploading route Excel files, reviewing matches, and sending SMS.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction

from api.models import ImportBatch, DailyRoute, Driver, SMSLog
from api.serializers.serializers import (
    ImportBatchSerializer,
    DailyRouteSerializer,
    DailyRouteLinkDriverSerializer,
    DriverSerializer,
)
from api.services.daily_route_import import parse_daily_routes_from_excel
from api.services.sms_eligibility import is_route_sms_eligible, evaluate_sms_status
from api.services.sms_builder import build_route_sms
from api.services.sms_service import send_sms
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class RoutesUploadView(APIView):
    """Upload and parse route Excel file."""
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

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

        # Parse routes
        result = parse_daily_routes_from_excel(file, request.user, file.name)

        if not result.get('success'):
            return Response(
                {'error': result.get('error', 'Unknown error')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch = result['batch']
        summary = result['summary']

        return Response({
            'batch_id': batch.id,
            'file_name': batch.file_name,
            'summary': summary,
        }, status=status.HTTP_201_CREATED)


class ImportBatchDetailView(APIView):
    """Get import batch details and summary."""
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        batch = get_object_or_404(ImportBatch, id=batch_id, user=request.user)

        serializer = ImportBatchSerializer(batch)
        return Response(serializer.data)


class DailyRouteListView(APIView):
    """List all DailyRoute records for the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = DailyRoute.objects.filter(user=request.user).select_related('driver', 'batch').order_by('-created_at')

        route_date = request.query_params.get('route_date')
        if route_date:
            qs = qs.filter(route_date=route_date)

        match_status = request.query_params.get('match_status')
        if match_status:
            qs = qs.filter(match_status=match_status)

        sms_status = request.query_params.get('sms_status')
        if sms_status:
            qs = qs.filter(sms_status=sms_status)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(route_code__icontains=search) |
                Q(driver_name_raw__icontains=search) |
                Q(transporter_id__icontains=search) |
                Q(dsp__icontains=search) |
                Q(driver__name__icontains=search)
            )

        raw_page_size = request.query_params.get('page_size', request.query_params.get('limit', 50))
        raw_offset = request.query_params.get('offset', 0)

        try:
            page_size = int(raw_page_size)
            offset = int(raw_offset)
        except (TypeError, ValueError):
            return Response(
                {'error': 'Query params page_size/limit and offset must be integers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page_size <= 0:
            return Response(
                {'error': 'Query param page_size/limit must be greater than 0.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if offset < 0:
            return Response(
                {'error': 'Query param offset cannot be negative.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        page_size = min(page_size, 500)
        qs = qs[offset : offset + page_size]

        serializer = DailyRouteSerializer(qs, many=True)
        return Response({
            'count': DailyRoute.objects.filter(user=request.user).count(),
            'results': serializer.data,
        })


class DailyRouteDetailView(APIView):
    """Delete a DailyRoute record."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, route_id):
        daily_route = get_object_or_404(DailyRoute, id=route_id, user=request.user)
        daily_route.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ImportBatchRoutesView(APIView):
    """List routes in an import batch with filtering."""
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        batch = get_object_or_404(ImportBatch, id=batch_id, user=request.user)

        # Build query
        qs = DailyRoute.objects.filter(batch=batch, user=request.user)

        # Filter by match status
        match_status = request.query_params.get('match_status')
        if match_status:
            qs = qs.filter(match_status=match_status)

        # Filter by SMS status
        sms_status = request.query_params.get('sms_status')
        if sms_status:
            qs = qs.filter(sms_status=sms_status)

        # Search by driver name or route code
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(driver_name_raw__icontains=search) |
                Q(route_code__icontains=search)
            )

        # Pagination with validation to avoid 500s on bad query params.
        raw_limit = request.query_params.get('limit', 50)
        raw_offset = request.query_params.get('offset', 0)

        try:
            limit = int(raw_limit)
            offset = int(raw_offset)
        except (TypeError, ValueError):
            return Response(
                {'error': 'Query params limit and offset must be integers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if limit <= 0:
            return Response(
                {'error': 'Query param limit must be greater than 0.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if offset < 0:
            return Response(
                {'error': 'Query param offset cannot be negative.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cap page size to protect the endpoint from unbounded requests.
        limit = min(limit, 500)
        qs = qs[offset : offset + limit]

        serializer = DailyRouteSerializer(qs, many=True)
        return Response({
            'count': DailyRoute.objects.filter(batch=batch, user=request.user).count(),
            'results': serializer.data,
        })


class DailyRouteLinkDriverView(APIView):
    """Manually link a driver to a DailyRoute."""
    permission_classes = [IsAuthenticated]

    def post(self, request, route_id):
        daily_route = get_object_or_404(DailyRoute, id=route_id, user=request.user)

        serializer = DailyRouteLinkDriverSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        driver_id = serializer.validated_data['driver_id']
        driver = get_object_or_404(Driver, id=driver_id, user=request.user)

        # Link driver
        daily_route.driver = driver
        daily_route.match_status = 'matched'
        daily_route.match_notes = f"Manually linked to {driver.name}"

        # Re-evaluate SMS status
        daily_route.sms_status = evaluate_sms_status(daily_route)

        daily_route.save()

        serializer = DailyRouteSerializer(daily_route)
        return Response(serializer.data)


class DailyRouteCreateDriverView(APIView):
    """Create a new driver and link it to a DailyRoute."""
    permission_classes = [IsAuthenticated]

    def post(self, request, route_id):
        daily_route = get_object_or_404(DailyRoute, id=route_id, user=request.user)

        serializer = DriverSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            driver = serializer.save(user=request.user)

            daily_route.driver = driver
            daily_route.match_status = 'matched'
            daily_route.match_notes = f"Created new driver and linked to {driver.name}"
            daily_route.sms_status = evaluate_sms_status(daily_route)
            daily_route.save()

        return Response(DailyRouteSerializer(daily_route).data, status=status.HTTP_201_CREATED)


class BatchSendSMSView(APIView):
    """Send SMS for all eligible routes in a batch."""
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        batch = get_object_or_404(ImportBatch, id=batch_id, user=request.user)

        # Get all routes with sms_status='ready'
        routes = DailyRoute.objects.filter(
            batch=batch,
            user=request.user,
            sms_status='ready',
        )

        sent_count = 0
        failed_count = 0
        errors = []

        for route in routes:
            try:
                eligibility = is_route_sms_eligible(route)
                if not eligibility['eligible']:
                    errors.append(f"Route {route.route_code}: {eligibility['reason']}")
                    continue

                # Build message
                message = build_route_sms(route)
                if not message:
                    errors.append(f"Route {route.route_code}: Could not build SMS")
                    failed_count += 1
                    continue

                # Send SMS
                driver = route.driver
                phone = driver.phone

                # Send via Twilio (or use mock if not configured)
                try:
                    message_id = send_sms(phone, message)

                    # Log SMS
                    SMSLog.objects.create(
                        driver=driver,
                        daily_route=route,
                        phone=phone,
                        message=message,
                        provider_message_id=message_id,
                        status='sent',
                        sent_at=datetime.now(),
                    )

                    # Update route status
                    route.sms_status = 'sent'
                    route.save(update_fields=['sms_status'])

                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending SMS for route {route.route_code}: {e}")
                    route.sms_status = 'failed'
                    route.save(update_fields=['sms_status'])
                    failed_count += 1
                    errors.append(f"Route {route.route_code}: {str(e)}")

            except Exception as e:
                logger.error(f"Error processing route {route.route_code}: {e}")
                errors.append(f"Route {route.route_code}: {str(e)}")
                failed_count += 1

        return Response({
            'sent': sent_count,
            'failed': failed_count,
            'total_attempted': len(routes),
            'errors': errors,
        })


class SingleRouteSendSMSView(APIView):
    """Send SMS for a single route."""
    permission_classes = [IsAuthenticated]

    def post(self, request, route_id):
        daily_route = get_object_or_404(DailyRoute, id=route_id, user=request.user)

        # Check eligibility
        eligibility = is_route_sms_eligible(daily_route)
        if not eligibility['eligible']:
            return Response(
                {'error': eligibility['reason']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build message
        message = build_route_sms(daily_route)
        if not message:
            return Response(
                {'error': 'Could not build SMS message'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send SMS
        try:
            driver = daily_route.driver
            phone = driver.phone

            message_id = send_sms(phone, message)

            # Log SMS
            SMSLog.objects.create(
                driver=driver,
                daily_route=daily_route,
                phone=phone,
                message=message,
                provider_message_id=message_id,
                status='sent',
                sent_at=datetime.now(),
            )

            # Update route status
            daily_route.sms_status = 'sent'
            daily_route.save(update_fields=['sms_status'])

            return Response({
                'success': True,
                'message': 'SMS sent successfully',
            })
        except Exception as e:
            logger.error(f"Error sending SMS for route {daily_route.route_code}: {e}")
            daily_route.sms_status = 'failed'
            daily_route.save(update_fields=['sms_status'])
            return Response(
                {'error': f'Failed to send SMS: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
