"""
Daily route import service.

Handles parsing Excel files and creating DailyRoute records with driver matching.
"""
import logging
import pandas as pd
from datetime import datetime
from api.models import ImportBatch, DailyRoute
from api.services.driver_matching import match_driver
from api.services.sms_eligibility import evaluate_sms_status

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'Route code',
    'DSP',
    'Transporter Id',
    'Driver name',
    'Route progress',
    'Delivery service type',
    'Route duration',
    'All stops',
    'Stops completed',
    'Not started stops',
]


def parse_daily_routes_from_excel(file, user, file_name=None):
    """
    Parse Excel file and create DailyRoute records with driver matching.

    Returns a dict with:
    - success: bool
    - batch: ImportBatch instance (if successful)
    - error: str (if failed)
    - summary: import summary dict
    """
    try:
        df = pd.read_excel(file)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        return {
            "success": False,
            "error": f"Failed to read Excel file: {str(e)}",
        }

    # Validate columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return {
            "success": False,
            "error": f"Missing required columns: {', '.join(missing_cols)}",
        }

    # Create import batch
    batch = ImportBatch.objects.create(
        user=user,
        file_name=file_name or "uploaded_routes.xlsx",
        total_rows=len(df),
    )

    # Track statistics
    matched_count = 0
    unmatched_count = 0
    ambiguous_count = 0
    ready_for_sms_count = 0
    errors = []

    def _cell_text(value):
        """Normalize Excel cell values to trimmed text, treating NaN as empty."""
        if pd.isna(value):
            return ""
        return str(value).strip()

    # Process each row
    for index, row in df.iterrows():
        row_num = index + 2  # Excel rows are 1-indexed, +1 for header row
        try:
            # Parse row values
            route_code = _cell_text(row.get('Route code', ''))
            driver_name_raw = _cell_text(row.get('Driver name', ''))
            dsp = _cell_text(row.get('DSP', '')) or None
            transporter_id = _cell_text(row.get('Transporter Id', '')) or None

            if not route_code:
                errors.append(f"Row {row_num}: Route code is empty")
                continue

            if not driver_name_raw:
                errors.append(f"Row {row_num}: Driver name is empty")
                continue

            # Parse stop numbers safely
            try:
                all_stops = int(row.get('All stops', 0)) if pd.notna(row.get('All stops')) else 0
            except (ValueError, TypeError):
                all_stops = 0

            try:
                stops_completed = int(row.get('Stops completed', 0)) if pd.notna(row.get('Stops completed')) else 0
            except (ValueError, TypeError):
                stops_completed = 0

            try:
                not_started_stops = int(row.get('Not started stops', 0)) if pd.notna(row.get('Not started stops')) else 0
            except (ValueError, TypeError):
                not_started_stops = 0

            # Parse route progress
            route_progress = str(row.get('Route progress', 'not_started')).strip().lower()
            if route_progress not in ['not_started', 'in_progress', 'completed']:
                route_progress = 'not_started'

            # Parse delivery service type
            delivery_service_type = str(row.get('Delivery service type', 'DSP')).strip().upper()
            if delivery_service_type not in ['AMZL', 'DSP', 'LINEHAUL']:
                delivery_service_type = 'DSP'

            # Attempt to match driver
            match_result = match_driver(
                user=user,
                driver_name=driver_name_raw,
                transporter_id=transporter_id,
                dsp=dsp,
            )

            # Create DailyRoute and evaluate sms_status before save.
            daily_route = DailyRoute(
                user=user,
                batch=batch,
                route_code=route_code,
                dsp=dsp,
                transporter_id=transporter_id,
                driver_name_raw=driver_name_raw,
                route_progress=route_progress,
                delivery_service_type=delivery_service_type,
                route_duration=_cell_text(row.get('Route duration', '')) or None,
                all_stops=all_stops,
                stops_completed=stops_completed,
                not_started_stops=not_started_stops,
                driver=match_result["driver"],
                match_status=match_result["match_status"],
                match_notes=match_result["match_notes"],
            )
            daily_route.sms_status = evaluate_sms_status(daily_route)
            daily_route.save()

            # Update counters
            if match_result["match_status"] == "matched":
                matched_count += 1
            elif match_result["match_status"] == "unmatched":
                unmatched_count += 1
            elif match_result["match_status"] == "ambiguous":
                ambiguous_count += 1

            if daily_route.sms_status == "ready":
                ready_for_sms_count += 1

        except Exception as e:
            logger.error(f"Error processing row {row_num}: {e}")
            errors.append(f"Row {row_num}: {str(e)}")

    # Update batch summary
    batch.matched_rows = matched_count
    batch.unmatched_rows = unmatched_count
    batch.ambiguous_rows = ambiguous_count
    batch.ready_for_sms_rows = ready_for_sms_count
    batch.save()

    return {
        "success": True,
        "batch_id": batch.id,
        "batch": batch,
        "summary": {
            "total_rows": batch.total_rows,
            "matched_rows": matched_count,
            "unmatched_rows": unmatched_count,
            "ambiguous_rows": ambiguous_count,
            "ready_for_sms_rows": ready_for_sms_count,
            "errors": errors,
        },
    }
