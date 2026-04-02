"""
Quick test of the new route import and SMS workflow.
Run with: python manage.py shell < test_workflow.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.models import Driver, ImportBatch, DailyRoute
from api.services.driver_matching import match_driver, normalize_driver_name
from api.services.sms_eligibility import is_route_sms_eligible, evaluate_sms_status
from api.services.sms_builder import build_route_sms
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*60)
print("HERA ROUTE IMPORT WORKFLOW TEST")
print("="*60)

# Create test user
user, _ = User.objects.get_or_create(
    email='test@example.com',
    defaults={'first_name': 'Test', 'last_name': 'User', 'is_active': True}
)
print(f"✓ User: {user.email}")

# Create test drivers
driver1, _ = Driver.objects.get_or_create(
    user=user,
    name='Alice Smith',
    defaults={
        'phone': '+16175551234',
        'transporter_id': 'TRANS-001',
        'dsp': 'DSP-East',
        'status': 'active',
    }
)
print(f"✓ Driver 1: {driver1.name} ({driver1.phone})")

driver2, _ = Driver.objects.get_or_create(
    user=user,
    name='Bob Johnson',
    defaults={
        'phone': '+16175555678',
        'transporter_id': 'TRANS-002',
        'dsp': 'DSP-West',
        'status': 'active',
    }
)
print(f"✓ Driver 2: {driver2.name} ({driver2.phone})")

print("\n" + "-"*60)
print("TEST 1: Driver Matching")
print("-"*60)

# Test exact match
result = match_driver(user, 'Alice Smith', 'TRANS-001', 'DSP-East')
print(f"Match 'Alice Smith' + TRANS-001: {result['match_status']} ✓")
assert result['match_status'] == 'matched'
assert result['driver'].id == driver1.id

# Test fuzzy match
result = match_driver(user, 'alice smith', 'TRANS-001', 'DSP-East')
print(f"Match 'alice smith' (fuzzy): {result['match_status']} ✓")
assert result['match_status'] == 'matched'

# Test unmatched
result = match_driver(user, 'Fake Driver', None, None)
print(f"Match 'Fake Driver': {result['match_status']} ✓")
assert result['match_status'] == 'unmatched'

print("\n" + "-"*60)
print("TEST 2: Import Batch Creation")
print("-"*60)

# Create a test batch
batch = ImportBatch.objects.create(
    user=user,
    file_name='test_routes.xlsx',
    total_rows=3,
    matched_rows=2,
    unmatched_rows=1,
    ambiguous_rows=0,
    ready_for_sms_rows=2,
)
print(f"✓ Created batch {batch.id}: {batch.file_name}")

print("\n" + "-"*60)
print("TEST 3: Daily Route Creation & SMS Eligibility")
print("-"*60)

# Create a matched route
route1 = DailyRoute.objects.create(
    user=user,
    batch=batch,
    route_code='ROUTE-001',
    dsp='DSP-East',
    transporter_id='TRANS-001',
    driver_name_raw='Alice Smith',
    driver=driver1,
    match_status='matched',
    route_progress='not_started',
    delivery_service_type='DSP',
    route_duration='2h',
    all_stops=10,
    stops_completed=0,
    not_started_stops=10,
)
route1.sms_status = evaluate_sms_status(route1)
route1.save()
print(f"✓ Route 1 (matched): {route1.route_code}")

eligibility = is_route_sms_eligible(route1)
print(f"  SMS eligible: {eligibility['eligible']} ✓")
assert eligibility['eligible'] == True

# Create an unmatched route
route2 = DailyRoute.objects.create(
    user=user,
    batch=batch,
    route_code='ROUTE-002',
    dsp='DSP-West',
    transporter_id='TRANS-999',
    driver_name_raw='Unknown Driver',
    driver=None,
    match_status='unmatched',
    route_progress='not_started',
    delivery_service_type='DSP',
    route_duration='3h',
    all_stops=15,
    stops_completed=0,
    not_started_stops=15,
)
route2.sms_status = evaluate_sms_status(route2)
route2.save()
print(f"✓ Route 2 (unmatched): {route2.route_code}")

eligibility = is_route_sms_eligible(route2)
print(f"  SMS eligible: {eligibility['eligible']} ✓")
assert eligibility['eligible'] == False
assert route2.sms_status == 'blocked'

print("\n" + "-"*60)
print("TEST 4: SMS Message Building")
print("-"*60)

message = build_route_sms(route1)
print(f"✓ SMS for ROUTE-001:\n{message}\n")
assert 'Alice Smith' in message
assert 'ROUTE-001' in message
assert '10 total' in message

print("\n" + "-"*60)
print("TEST 5: Database Queries")
print("-"*60)

# Query routes by match status
matched = DailyRoute.objects.filter(user=user, match_status='matched').count()
unmatched = DailyRoute.objects.filter(user=user, match_status='unmatched').count()
ready = DailyRoute.objects.filter(user=user, sms_status='ready').count()
blocked = DailyRoute.objects.filter(user=user, sms_status='blocked').count()

print(f"✓ Matched routes: {matched}")
print(f"✓ Unmatched routes: {unmatched}")
print(f"✓ Ready for SMS: {ready}")
print(f"✓ Blocked (no SMS): {blocked}")

assert matched == 1
assert unmatched == 1
assert ready == 1
assert blocked == 1

print("\n" + "="*60)
print("ALL TESTS PASSED ✓")
print("="*60)
