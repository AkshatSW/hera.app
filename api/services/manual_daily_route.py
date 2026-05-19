"""
Create DailyRoute rows outside of Excel import (manual entry).
Uses a dedicated per-user ImportBatch so linking/review URLs stay consistent.
"""
from django.db import transaction

from api.models import ImportBatch, DailyRoute
from api.services.sms_eligibility import evaluate_sms_status

MANUAL_BATCH_FILE_NAME = '__hera_manual_routes__'


def _get_or_create_manual_batch(user):
    batch, _ = ImportBatch.objects.get_or_create(
        user=user,
        file_name=MANUAL_BATCH_FILE_NAME,
        defaults={
            'total_rows': 0,
            'matched_rows': 0,
            'unmatched_rows': 0,
            'ambiguous_rows': 0,
            'ready_for_sms_rows': 0,
        },
    )
    return batch


def refresh_import_batch_summary(batch):
    """Recompute aggregate fields from child routes (for manual batch)."""
    qs = DailyRoute.objects.filter(batch=batch)
    batch.total_rows = qs.count()
    batch.matched_rows = qs.filter(match_status='matched').count()
    batch.unmatched_rows = qs.filter(match_status='unmatched').count()
    batch.ambiguous_rows = qs.filter(match_status='ambiguous').count()
    batch.ready_for_sms_rows = qs.filter(sms_status='ready').count()
    batch.save(
        update_fields=[
            'total_rows',
            'matched_rows',
            'unmatched_rows',
            'ambiguous_rows',
            'ready_for_sms_rows',
            'updated_at',
        ]
    )


@transaction.atomic
def create_manual_daily_route(user, *, data: dict) -> DailyRoute:
    """
    data keys: route_code, driver (Driver instance), dsp, transporter_id, route_date,
    route_progress, delivery_service_type, route_duration,
    all_stops, stops_completed, not_started_stops
    """
    batch = _get_or_create_manual_batch(user)

    driver = data['driver']
    raw_dsp = data.get('dsp')
    dsp = raw_dsp.strip() if isinstance(raw_dsp, str) else None
    dsp = dsp or None
    raw_tid = data.get('transporter_id')
    transporter_id = raw_tid.strip() if isinstance(raw_tid, str) else None
    transporter_id = transporter_id or None
    driver_name_raw = driver.name.strip()

    route = DailyRoute(
        user=user,
        batch=batch,
        route_code=data['route_code'].strip(),
        dsp=dsp,
        transporter_id=transporter_id,
        driver_name_raw=driver_name_raw,
        route_progress=data.get('route_progress') or 'not_started',
        delivery_service_type=data.get('delivery_service_type') or 'DSP',
        route_duration=(data.get('route_duration') or '').strip() or None,
        all_stops=int(data.get('all_stops') or 0),
        stops_completed=int(data.get('stops_completed') or 0),
        not_started_stops=int(data.get('not_started_stops') or 0),
        driver=driver,
        match_status='matched',
        match_notes='Manual route entry: linked to saved associate.',
        route_date=data.get('route_date'),
    )
    route.sms_status = evaluate_sms_status(route)
    route.save()

    refresh_import_batch_summary(batch)
    return route
