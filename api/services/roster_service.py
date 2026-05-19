import pandas as pd
import logging
from datetime import datetime
from api.models import Driver, Vehicle, Assignment

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


def parse_roster(file, user):
    """Parse an Excel roster file and create drivers and assignments.

    Returns a dict with counts and any errors encountered.
    """
    try:
        df = pd.read_excel(file)
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        return {'success': False, 'error': f'Failed to read Excel file: {e}'}

    # Validate columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return {
            'success': False,
            'error': f'Missing required columns: {", ".join(missing_cols)}',
        }

    results = {
        'success': True,
        'drivers_created': 0,
        'vehicles_created': 0,
        'assignments_created': 0,
        'assignment_ids': [],
        'errors': [],
    }

    for index, row in df.iterrows():
        row_num = index + 2  # Excel rows start at 1, header is row 1
        try:
            driver_name = str(row['Driver name']).strip()
            route_code = str(row['Route code']).strip()

            # Create a unique phone by hashing driver name + route code
            # (since phone is not provided in the new format)
            phone = f"+1{hash(driver_name + route_code) % 9000000000 + 1000000000}"

            # Get or create driver (scoped to user)
            driver, created = Driver.objects.get_or_create(
                user=user,
                phone=phone,
                defaults={'name': driver_name},
            )
            if created:
                results['drivers_created'] += 1

            if driver.status != 'active':
                results['errors'].append(
                    f"Row {row_num}: Associate '{driver_name}' is inactive; cannot create route assignment."
                )
                continue

            # Create a simple vehicle (scoped to user)
            vehicle_code = f"{route_code}_VEH"
            vehicle, created = Vehicle.objects.get_or_create(
                user=user,
                vehicle_code=vehicle_code,
                defaults={'plate_number': ''},
            )
            if created:
                results['vehicles_created'] += 1

            if vehicle.status != 'active':
                results['errors'].append(
                    f"Row {row_num}: Vehicle '{vehicle_code}' is grounded (inactive); cannot assign route."
                )
                continue

            # Use default wave time and route date
            wave_time = datetime.now().time()
            route_date = datetime.now().date()

            # Check for duplicate assignment (scoped to user)
            existing = Assignment.objects.filter(
                user=user,
                driver=driver,
                route_date=route_date,
                route_code=route_code,
            ).exists()
            if existing:
                results['errors'].append(
                    f"Row {row_num}: Duplicate assignment for {driver_name} on {route_date}"
                )
                continue

            # Parse delivery service type
            delivery_service_type = str(row['Delivery service type']).strip().upper()
            if delivery_service_type not in ['AMZL', 'DSP', 'LINEHAUL']:
                delivery_service_type = 'DSP'

            # Parse route progress
            route_progress = str(row['Route progress']).strip().lower()
            if route_progress not in ['not_started', 'in_progress', 'completed']:
                route_progress = 'not_started'

            # Create assignment (scoped to user)
            assignment = Assignment.objects.create(
                user=user,
                driver=driver,
                vehicle=vehicle,
                route_code=route_code,
                staging='',
                pad='',
                wave_time=wave_time,
                route_date=route_date,
                sms_status='pending',
                dsp_name=str(row['DSP']).strip(),
                transporter_id=str(row['Transporter Id']).strip(),
                route_progress=route_progress,
                delivery_service_type=delivery_service_type,
                route_duration=str(row['Route duration']).strip(),
                all_stops=int(row['All stops']) if pd.notna(row['All stops']) else 0,
                not_started_stops=int(row['Not started stops']) if pd.notna(row['Not started stops']) else 0,
            )
            results['assignments_created'] += 1
            results['assignment_ids'].append(assignment.id)

        except Exception as e:
            logger.error(f"Error processing row {row_num}: {e}")
            results['errors'].append(f"Row {row_num}: {str(e)}")

    return results
