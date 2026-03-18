# Hera — Logistics SMS System

Django app to manage driver assignments and send SMS via Twilio.

---

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

---

## Required `.env`

```
DJANGO_SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_MESSAGING_SERVICE_SID=

SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=
```

---

## Optional

```
REDIS_URL=redis://localhost:6379/0
DB_ENGINE=mysql
```

---

## Flow

```
Signup → Verify → Upload Excel → Assignments created → Send SMS → Status updates
```

---

## Key APIs

```
/signup/
/login/

/api/drivers/
/api/vehicles/
/api/assignments/

/api/roster/upload/
/api/roster/send-sms/

/api/sms/status/
```

---

## Excel Columns

```
Driver Name, Phone, Vehicle Code, Vehicle Plate,
Route, Staging, Pad, Wave Time, Date
```

---

## Status

```
pending → queued → sent → delivered / failed
```

---

## Deploy

```
DEBUG=False
Use MySQL
python manage.py collectstatic
```