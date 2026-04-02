# Hera

Logistics and route-assignment app built with Django. The current workflow centers on importing daily route spreadsheets, matching or creating drivers, reviewing batch imports, and sending SMS for ready routes.

## What the app does

- Manage drivers and delivery associates.
- Upload route spreadsheets and review the import batch before sending SMS.
- Link imported routes to existing drivers or create a new driver when one is missing.
- View daily routes, filter them, send SMS, and delete a route when it is no longer needed.
- Track assignment and route status fields used by the updated Excel format.

## Setup

```bash
cd hera.app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser_if_none --email admin@example.com --password yourpassword
python manage.py runserver
```

## Environment

Required:

```bash
DJANGO_SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_MESSAGING_SERVICE_SID=
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=
```

Optional:

```bash
REDIS_URL=redis://localhost:6379/0
DB_ENGINE=mysql
```

## Main Pages

- Route Assignments: upload spreadsheets, review imported rows, and manage daily routes.
- Import Review: resolve unmatched or ambiguous routes by linking an existing driver or adding a new one.
- Associates: create, update, and delete driver records.
- Vehicles: manage delivery vehicles.
- SMS Center: inspect and send message activity.

## Updated route workflow

1. Upload the updated route spreadsheet.
2. Review matched, unmatched, and ambiguous rows in Import Review.
3. For unmatched rows, either link an existing driver or add a new driver and link them immediately.
4. Return to Route Assignments to manage active daily routes, including deleting a route when required.
5. Send SMS only for routes that are marked ready.

## Updated Excel format

The app now expects the newer route-assignment spreadsheet structure that includes the route metadata used by the updated UI and backend matching flow. The assignment data model supports these fields:

- Driver Name
- Phone
- Vehicle Code
- Vehicle Plate
- Route
- Staging
- Pad
- Wave Time
- Date
- DSP Name
- Transporter ID
- Route Progress
- Delivery Service Type
- Route Duration
- All Stops
- Not Started Stops

## API areas

- `/api/drivers/`
- `/api/vehicles/`
- `/api/assignments/`
- `/api/routes/`
- `/api/routes/import/<batch_id>/`
- `/api/routes/import/<batch_id>/routes/`
- `/api/routes/<route_id>/link-driver/`
- `/api/routes/<route_id>/create-driver/`
- `/api/routes/<route_id>/send-sms/`
- `/api/routes/<batch_id>/send-sms/`
- `/api/sms/history/`
- `/api/sms/send/`
- `/api/sms/status/`

## Status values

- Match status: matched, unmatched, ambiguous
- SMS status: pending, ready, sent, failed, blocked

## Deployment notes

For production, set `DEBUG=False`, use a production database, and run `python manage.py collectstatic` before deploying static assets.