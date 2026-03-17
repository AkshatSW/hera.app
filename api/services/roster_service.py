import re
import pandas as pd
import logging
from datetime import datetime
from api.models import Driver, Vehicle, Assignment

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'Driver Name',
    'Phone',
    'Vehicle Code',
    'Vehicle Plate',
    'Route',
    'Staging',
    'Pad',
    'Wave Time',
    'Date',
]


def validate_phone(phone):
    """Validate phone number format: +countrycode number."""
    phone = str(phone).strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    pattern = r'^\+\d{7,15}$'
    if not re.match(pattern, phone):
        return None
    return phone


def parse_roster(file, user):
    """Parse an Excel roster file and create drivers, vehicles, and assignments.

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
            # Validate phone
            phone = validate_phone(row['Phone'])
            if not phone:
                results['errors'].append(f"Row {row_num}: Invalid phone number '{row['Phone']}'")
                continue

            # Get or create driver (scoped to user)
            driver, created = Driver.objects.get_or_create(
                user=user,
                phone=phone,
                defaults={'name': str(row['Driver Name']).strip()},
            )
            if created:
                results['drivers_created'] += 1

            # Get or create vehicle (scoped to user)
            vehicle_code = str(row['Vehicle Code']).strip()
            plate_number = str(row['Vehicle Plate']).strip()
            vehicle, created = Vehicle.objects.get_or_create(
                user=user,
                vehicle_code=vehicle_code,
                defaults={'plate_number': plate_number},
            )
            if created:
                results['vehicles_created'] += 1

            # Parse wave time
            wave_time_raw = row['Wave Time']
            if isinstance(wave_time_raw, datetime):
                wave_time = wave_time_raw.time()
            elif isinstance(wave_time_raw, str):
                for fmt in ('%I:%M %p', '%H:%M', '%I:%M%p'):
                    try:
                        wave_time = datetime.strptime(wave_time_raw.strip(), fmt).time()
                        break
                    except ValueError:
                        continue
                else:
                    results['errors'].append(f"Row {row_num}: Invalid wave time '{wave_time_raw}'")
                    continue
            else:
                wave_time = wave_time_raw

            # Parse date
            route_date_raw = row['Date']
            if isinstance(route_date_raw, str):
                for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y'):
                    try:
                        route_date = datetime.strptime(route_date_raw.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    results['errors'].append(f"Row {row_num}: Invalid date '{route_date_raw}'")
                    continue
            elif isinstance(route_date_raw, datetime):
                route_date = route_date_raw.date()
            else:
                route_date = route_date_raw

            # Check for duplicate assignment (scoped to user)
            existing = Assignment.objects.filter(
                user=user,
                driver=driver,
                route_date=route_date,
                route_code=str(row['Route']).strip(),
            ).exists()
            if existing:
                results['errors'].append(
                    f"Row {row_num}: Duplicate assignment for {driver.name} on {route_date}"
                )
                continue

            # Create assignment (scoped to user)
            assignment = Assignment.objects.create(
                user=user,
                driver=driver,
                vehicle=vehicle,
                route_code=str(row['Route']).strip(),
                staging=str(row['Staging']).strip(),
                pad=str(row['Pad']).strip(),
                wave_time=wave_time,
                route_date=route_date,
                sms_status='pending',
            )
            results['assignments_created'] += 1
            results['assignment_ids'].append(assignment.id)

        except Exception as e:
            logger.error(f"Error processing row {row_num}: {e}")
            results['errors'].append(f"Row {row_num}: {str(e)}")

    return results
