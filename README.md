# Hera — Logistics SMS System

Hera is a web application for managing driver route assignments and sending automated SMS notifications via Twilio. Built by **PacTrack, Inc**.

Administrators sign up with their DSP (Delivery Service Partner) name, verify their email via a 6-digit OTP, then upload Excel roster files. The system parses assignments, creates driver/vehicle records, and dispatches SMS messages through a background task queue.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Django, Django REST Framework |
| Database | MySQL (production), SQLite (development) |
| Task Queue | Celery + Redis |
| SMS Provider | Twilio (Messaging Service) |
| Email Provider | SendGrid (OTP delivery) |
| Frontend | Django Templates (vanilla HTML/CSS/JS) |
| Excel Parsing | pandas, openpyxl |
| Bot Protection | Google reCAPTCHA v2 |

## Architecture

```
Frontend Dashboard
        ↓
Django REST API
        ↓
MySQL / SQLite Database
        ↓
Celery Worker + Redis Queue
        ↓
Twilio SMS Provider
        ↓
SendGrid Email (OTP verification & password reset)
```

## Project Structure

```
hera.app/
├── config/
│   ├── __init__.py              # Celery app bootstrap
│   ├── celery.py                # Celery configuration
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Root URL routing (auth + dashboard pages)
│   ├── wsgi.py
│   └── asgi.py
├── api/
│   ├── models/
│   │   ├── __init__.py          # Re-exports all models
│   │   ├── user.py              # HeraUser custom user model + manager
│   │   ├── otp.py               # EmailOTP model (verification & password reset)
│   │   └── models.py            # Driver, Vehicle, Assignment, SMSLog
│   ├── views/
│   │   ├── __init__.py          # Re-exports all views
│   │   ├── auth_views.py        # Signup, login, logout, verify email, forgot/reset password
│   │   ├── dashboard_views.py   # Page views (home, associates, vehicles, sms)
│   │   ├── driver_views.py      # Driver CRUD API
│   │   ├── vehicle_views.py     # Vehicle CRUD API
│   │   ├── assignment_views.py  # Assignment CRUD API
│   │   ├── roster_views.py      # Excel upload endpoint
│   │   └── sms_views.py         # SMS history, send, webhook
│   ├── serializers/
│   │   └── serializers.py       # DRF serializers
│   ├── services/
│   │   ├── email_service.py     # SendGrid OTP email delivery
│   │   ├── sms_service.py       # Twilio SMS integration
│   │   └── roster_service.py    # Excel parsing and assignment creation
│   ├── tasks/
│   │   └── sms_tasks.py         # Celery background tasks
│   ├── management/commands/
│   │   └── createsuperuser_if_none.py  # Create superuser if none exists
│   ├── admin.py                 # Django admin (HeraUser, Driver, Vehicle, Assignment, SMSLog)
│   └── urls.py                  # API URL routing
├── templates/dashboard/
│   ├── base.html                # Base layout with sidebar, DSP name, and logout
│   ├── login.html               # Login page with links to signup and forgot password
│   ├── signup.html              # Sign-up form with reCAPTCHA
│   ├── verify_email.html        # OTP verification page
│   ├── forgot_password.html     # Email input for password reset
│   ├── reset_password.html      # OTP + new password form
│   ├── home.html                # Roster upload and assignments
│   ├── associates.html          # Associate (driver) management
│   ├── vehicles.html            # Vehicle management
│   └── sms_center.html          # SMS conversation interface
├── static/
│   ├── css/hera.css             # Application stylesheet
│   ├── img/heralogo.png         # Hera logo
│   ├── roster_format.xlsx       # Blank Excel format template (headers only)
│   └── roster_template.xlsx     # Downloadable Excel template with sample data
├── .env                         # Environment variables (not committed)
├── .env.example                 # Environment variable template
├── requirements.txt
└── manage.py
```

## Authentication Flow

Hera uses a custom user model (`HeraUser`) with email-based authentication — there is no username field.

### Sign Up

1. User fills in DSP name, first name, last name, phone, email, password, and reCAPTCHA
2. Account is created as **inactive** (`is_active=False`, `is_verified=False`)
3. A 6-digit OTP is generated and sent to the user's email via SendGrid
4. User is redirected to the email verification page

### Email Verification

1. User enters the 6-digit OTP received by email
2. On success, account is marked **verified and active**
3. User is automatically logged in and redirected to the dashboard
4. OTPs expire after 10 minutes; a "Resend Code" link is available

### Login

1. User enters email and password
2. Unverified accounts are shown a message to verify their email first
3. On success, user is redirected to the dashboard (or the `?next=` URL)

### Forgot / Reset Password

1. User enters their email on the forgot-password page
2. If the account exists, a 6-digit OTP is sent (non-revealing error for unknown emails)
3. User enters the OTP and a new password on the reset page
4. On success, user is redirected to login

## Pages

| URL | Page | Auth Required | Description |
|-----|------|:---:|-------------|
| `/signup/` | Sign Up | No | Create a new account with reCAPTCHA |
| `/verify-email/` | Verify Email | No | Enter 6-digit OTP to activate account |
| `/login/` | Login | No | Email/password sign-in |
| `/forgot-password/` | Forgot Password | No | Request a password reset OTP |
| `/reset-password/` | Reset Password | No | Enter OTP and new password |
| `/` | Roster | Yes | Upload rosters, view stats, browse assignments, send SMS |
| `/associates/` | Associate Management | Yes | Add, edit, delete, search drivers |
| `/vehicles/` | Vehicle Management | Yes | Add, edit, delete, search vehicles |
| `/sms/` | SMS Center | Yes | Chat-style conversation view with compose |
| `/admin/` | Django Admin | Staff | Admin panel for HeraUser, Driver, Vehicle, Assignment, SMSLog |

### Roster Page Features

- **Upload Roster** — Upload an Excel file to create assignments. SMS is **not** sent automatically.
- **Download Format** — Download a blank Excel template (`roster_format.xlsx`) with headers only to fill in.
- **Sample Template** — Download a pre-filled template (`roster_template.xlsx`) with example data.
- **SMS Confirmation** — After uploading, a confirmation modal asks whether to send SMS. Choose "Send SMS" to queue messages or "Not Now" to leave them in pending status.
- **Send / Retry** — Individual Send or Retry button on each `pending` or `failed` assignment row.
- **Resend** — Individual Resend button on each `sent` or `delivered` assignment row, in case the message needs to be sent again.
- **Send All Pending** — Bulk action button to send SMS for all pending/failed assignments at once.
- **Auto-refresh** — While any messages are in `queued` status, the table and stats automatically poll every 5 seconds until all messages transition to `sent`, `delivered`, or `failed`.

## Setup

You can run Hera in two ways:
1. **Docker** (Recommended — runs exactly the same on any system)
2. **Manual Installation** (Traditional Python virtual environment)

### Option 1: Docker Setup (Recommended)

Docker ensures the application runs exactly the same on your local system as it does on your clients' systems, eliminating "it works on my machine" issues.

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (recommended: Docker Desktop)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

#### Quick Start

```bash
# Clone the repository
cd hera.app

# Copy environment template
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# Start all services (database, Redis, web app)
docker-compose up -d

# View logs (optional)
docker-compose logs -f web

# Access the application
# Visit: http://localhost:8000
# Admin: http://localhost:8000/admin (admin/admin123)
```

The application will be available at `http://localhost:8000` with:
- **Automatic database setup** (PostgreSQL with sample data)
- **Redis** for caching and background tasks
- **Auto-created superuser**: `admin` / `admin123`
- **Hot-reload** for development (code changes refresh automatically)

#### Docker Commands

```bash
# Start services in development mode
docker-compose up -d

# View logs
docker-compose logs -f web
docker-compose logs -f celery-worker

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build web
docker-compose up -d

# Reset everything (remove volumes)
docker-compose down -v
docker-compose up -d

# Run Django commands
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Access shell inside container
docker-compose exec web bash
docker-compose exec web python manage.py shell

# Start with Celery workers (for background SMS tasks)
docker-compose --profile celery up -d
```

#### Production Deployment with Docker

For production environments:

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or build production image
docker build -t hera-app .
docker run -d -p 8000:8000 --env-file .env hera-app gunicorn
```

### Option 2: Manual Installation

#### Prerequisites

- Python 3.10+
- Redis (for Celery task queue)
- MySQL (optional — SQLite is used by default for development)

#### Installation

```bash
# Clone the repository
cd hera.app

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser_if_none --email admin@example.com --password yourpassword

# Start the development server
python manage.py runserver
```

#### Starting Celery Worker (Manual)

Redis must be running for Celery to function.

```bash
# Start Redis (if not already running)
redis-server

# Start Celery worker (in a separate terminal)
source venv/bin/activate
celery -A config worker -l info
```

### Environment Files

Both Docker and manual setups use the same `.env` file for configuration:

```bash
# Development (default in docker-compose.yml)
DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Production (use strong values)
DEBUG=False
DJANGO_SECRET_KEY=your-production-secret-key-minimum-50-characters-long
ALLOWED_HOSTS=your-domain.com
```

### Docker Troubleshooting

#### Common Issues

**Port already in use:**
```bash
# Check what's using port 8000
lsof -i :8000
# Kill the process or use different port
docker-compose -f docker-compose.yml up -d --scale web=1 -p 8001:8000
```

**Database connection errors:**
```bash
# Reset database volumes
docker-compose down -v
docker-compose up -d

# Check database status
docker-compose logs db
```

**Permission errors (Linux/Mac):**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x docker-entrypoint.sh
```

**Container won't start:**
```bash
# View detailed logs
docker-compose logs web
docker-compose logs db

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

**Static files not loading:**
```bash
# Collect static files manually
docker-compose exec web python manage.py collectstatic --noinput
```

#### Docker Desktop Settings

For optimal performance:
- **Memory**: Allocate at least 4GB RAM to Docker
- **CPU**: Allocate at least 2 CPU cores
- **Disk**: Ensure sufficient free space (at least 10GB)

#### Environment Variables

All services use environment variables for configuration. Key variables:

| Service | Variable | Purpose |
|---------|----------|---------|
| Web | `DEBUG` | Enable/disable debug mode |
| Web | `DATABASE_URL` | PostgreSQL connection string |
| Web | `REDIS_URL` | Redis connection string |
| Database | `POSTGRES_DB` | Database name |
| Database | `POSTGRES_USER` | Database user |
| Database | `POSTGRES_PASSWORD` | Database password |

## Configuration

All configuration is managed through environment variables in the `.env` file.

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | dev key (change in production) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DB_ENGINE` | Set to `mysql` for MySQL, otherwise SQLite | `sqlite3` |
| `DB_NAME` | Database name | `hera` |
| `DB_USER` | Database user | `root` |
| `DB_PASSWORD` | Database password | (empty) |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | (required for SMS) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | (required for SMS) |
| `TWILIO_MESSAGING_SERVICE_SID` | Twilio Messaging Service SID | (required for SMS) |
| `SENDGRID_API_KEY` | SendGrid API key for OTP emails | (required for auth) |
| `SENDGRID_FROM_EMAIL` | Sender email address for OTPs | `akshat@nizod.com` |
| `RECAPTCHA_SITE_KEY` | Google reCAPTCHA v2 site key | (optional — signup works without it) |
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA v2 secret key | (optional — verification skipped if empty) |

## Database Schema

### HeraUser (Custom User Model)

| Field | Type | Notes |
|-------|------|-------|
| id | BigInt | Primary key |
| email | VARCHAR(254) | Unique, used as USERNAME_FIELD |
| password | VARCHAR(128) | Hashed |
| first_name | VARCHAR(150) | |
| last_name | VARCHAR(150) | |
| phone | VARCHAR(30) | Optional |
| dsp_name | VARCHAR(255) | Delivery Service Partner name |
| is_active | Boolean | Default: `False` (activated after email verification) |
| is_verified | Boolean | Default: `False` (set to `True` after OTP verification) |
| is_staff | Boolean | Default: `False` |
| date_joined | Timestamp | Auto-set |

### EmailOTP

| Field | Type | Notes |
|-------|------|-------|
| id | BigInt | Primary key |
| user_id | FK → HeraUser | |
| code | VARCHAR(6) | 6-digit OTP |
| purpose | VARCHAR(20) | `verification` or `password_reset` |
| is_used | Boolean | Default: `False` |
| created_at | Timestamp | Auto-set; OTP expires after 10 minutes |

### Drivers

| Field | Type | Notes |
|-------|------|-------|
| id | BigInt | Primary key |
| user_id | FK → HeraUser | Owner |
| name | VARCHAR(255) | |
| phone | VARCHAR(30) | Unique |
| status | VARCHAR(20) | Default: `active` |
| created_at | Timestamp | Auto-set |

### Vehicles

| Field | Type | Notes |
|-------|------|-------|
| id | BigInt | Primary key |
| user_id | FK → HeraUser | Owner |
| vehicle_code | VARCHAR(50) | |
| plate_number | VARCHAR(50) | |
| status | VARCHAR(20) | Default: `active` |
| created_at | Timestamp | Auto-set |

### Assignments

| Field | Type | Notes |
|-------|------|-------|
| id | BigInt | Primary key |
| driver_id | FK → Drivers | |
| vehicle_id | FK → Vehicles | |
| route_code | VARCHAR(50) | |
| staging | VARCHAR(50) | |
| pad | VARCHAR(10) | |
| wave_time | Time | |
| route_date | Date | |
| sms_status | VARCHAR(20) | `pending` / `queued` / `sent` / `delivered` / `failed` |
| created_at | Timestamp | Auto-set |

### SMS Logs

| Field | Type | Notes |
|-------|------|-------|
| id | BigInt | Primary key |
| driver_id | FK → Drivers | |
| phone | VARCHAR(30) | |
| message | Text | |
| provider_message_id | VARCHAR(255) | Twilio SID |
| status | VARCHAR(20) | `queued` / `sent` / `delivered` / `failed` |
| sent_at | DateTime | |
| delivered_at | DateTime | |
| error_message | Text | |
| assignment_id | FK → Assignments | Nullable |

## API Endpoints

All API endpoints require authentication (session-based). Unauthenticated requests are redirected to `/login/`.

### Auth Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/signup/` | Sign-up form |
| GET/POST | `/verify-email/` | OTP email verification |
| GET | `/resend-otp/` | Resend verification OTP |
| GET/POST | `/login/` | Login form |
| POST | `/logout/` | Logout (POST only) |
| GET/POST | `/forgot-password/` | Request password reset |
| GET/POST | `/reset-password/` | Reset password with OTP |

### Drivers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/drivers/` | List all drivers |
| POST | `/api/drivers/` | Create a driver |
| GET | `/api/drivers/<id>/` | Get driver detail |
| PUT | `/api/drivers/<id>/` | Update a driver |
| DELETE | `/api/drivers/<id>/` | Delete a driver |

### Vehicles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles/` | List all vehicles |
| POST | `/api/vehicles/` | Create a vehicle |
| GET | `/api/vehicles/<id>/` | Get vehicle detail |
| PUT | `/api/vehicles/<id>/` | Update a vehicle |
| DELETE | `/api/vehicles/<id>/` | Delete a vehicle |

### Assignments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assignments/` | List all assignments |
| POST | `/api/assignments/` | Create an assignment |
| GET | `/api/assignments/<id>/` | Get assignment detail |
| PUT | `/api/assignments/<id>/` | Update an assignment |
| DELETE | `/api/assignments/<id>/` | Delete an assignment |

### Roster Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/roster/upload/` | Upload Excel roster file |
| POST | `/api/roster/send-sms/` | Send or resend SMS for assignment IDs |

**Upload — Request:** `multipart/form-data` with a `file` field containing an `.xlsx` file.

**Upload — Response:**
```json
{
  "success": true,
  "drivers_created": 3,
  "vehicles_created": 2,
  "assignments_created": 5,
  "assignment_ids": [1, 2, 3, 4, 5],
  "errors": []
}
```

Assignments are created with `sms_status: "pending"`. SMS is **not** sent automatically — use the send-sms endpoint to trigger it.

**Send SMS — Request:**
```json
{
  "assignment_ids": [1, 2, 3, 4, 5]
}
```

To resend SMS for assignments that were already sent or delivered, include `"resend": true`:
```json
{
  "assignment_ids": [3],
  "resend": true
}
```

Without `resend`, only assignments in `pending` or `failed` status are processed. With `resend: true`, assignments in any status (`pending`, `failed`, `queued`, `sent`, `delivered`) are re-queued.

**Send SMS — Response:**
```json
{
  "sms_queued": 5,
  "total_requested": 5
}
```

### SMS

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sms/history/?driver_id=<id>` | Get SMS conversation for a driver |
| POST | `/api/sms/send/` | Send a manual SMS to a driver |
| POST | `/api/sms/status/` | Twilio delivery status webhook |

**Send SMS request:**
```json
{
  "driver_id": 1,
  "message": "Your route has been updated."
}
```

## Excel Roster Format

The uploaded `.xlsx` file must contain these exact column headers in the first row:

| Column | Description | Example |
|--------|-------------|---------|
| Driver Name | Full name of the driver | Steven Parker |
| Phone | Phone with country code prefix | +447700100001 |
| Vehicle Code | Internal vehicle identifier | LMR11 |
| Vehicle Plate | License plate number | DZ66RY |
| Route | Route code for the assignment | CX305 |
| Staging | Staging area identifier | STG.H.10 |
| Pad | Loading pad letter or code | D |
| Wave Time | Dispatch time (12h or 24h) | 11:45 AM |
| Date | Route date (MM/DD/YYYY) | 03/07/2026 |

Each row represents one route assignment. Two downloadable templates are available from the Roster page:

- **Download Format** (`static/roster_format.xlsx`) — Blank template with headers only, ready to fill in.
- **Sample Template** (`static/roster_template.xlsx`) — Pre-filled template with 5 example rows.

### Sample rows

```
Driver Name      Phone            Vehicle Code  Vehicle Plate  Route  Staging     Pad  Wave Time   Date
Steven Parker    +447700100001    LMR11         DZ66RY         CX305  STG.H.10    D    11:45 AM    03/07/2026
David Chen       +447700100002    LMR12         AB12CD         CX210  STG.A.05    B    10:30 AM    03/07/2026
Sarah Mitchell   +447700100003    LMR15         EF34GH         CX118  STG.C.02    A    09:15 AM    03/07/2026
James Wilson     +447700100004    LMR18         IJ56KL         CX422  STG.D.08    C    12:00 PM    03/07/2026
Maria Garcia     +447700100005    LMR21         MN78OP         CX509  STG.F.12    A    01:15 PM    03/07/2026
```

### Phone number format

Phone numbers must include the `+` prefix with the country code:

- UK: `+447700100001`
- US: `+12025551234`
- AU: `+61400123456`

Numbers without a `+` prefix will have one prepended automatically. Numbers that are fewer than 7 digits or more than 15 digits (after removing the `+`) are rejected.

### Supported date formats

The parser accepts these date formats:

- `MM/DD/YYYY` (primary) — e.g., `03/07/2026`
- `YYYY-MM-DD` — e.g., `2026-03-07`
- `DD/MM/YYYY` — e.g., `07/03/2026`

### Supported time formats

- `HH:MM AM/PM` (primary) — e.g., `11:45 AM`
- `HH:MM` (24-hour) — e.g., `13:30`

## SMS Message Template

When SMS is confirmed by the admin after a roster upload (or when resending), drivers receive an SMS in this format:

```
You are rostered for: Saturday 03/07/2026

Wave Time: 11:45 AM
Vehicle: LMR11 DZ66RY
Route: CX305
Staging: STG.H.10 PAD D
```

## System Flow

```
New user signs up with DSP name, email, password
        ↓
6-digit OTP sent to email via SendGrid
        ↓
User verifies email → account activated
        ↓
User logs in → redirected to dashboard
        ↓
Admin uploads Excel roster
        ↓
System parses Excel file
        ↓
Drivers and vehicles created (or matched by phone / vehicle code)
        ↓
Assignments created with sms_status = "pending"
        ↓
Admin reviews assignments in Roster page
        ↓
Admin clicks "Send SMS" (confirmation modal)
        ↓
SMS jobs queued to Celery (sms_status → "queued")
        ↓
Dashboard auto-polls every 5 seconds while messages are queued
        ↓
Celery worker sends SMS via Twilio Messaging Service (sms_status → "sent")
        ↓
SMS logs stored in database
        ↓
Twilio sends delivery webhook (sms_status → "delivered" or "failed")
        ↓
Dashboard reflects final status; admin can Resend if needed
        ↓
SMS Center displays conversation
```

## SMS Status Lifecycle

Each assignment tracks its SMS status through these states:

| Status | Meaning |
|--------|---------|
| `pending` | Assignment created, SMS not yet requested |
| `queued` | SMS queued to Celery worker, waiting to be sent |
| `sent` | Twilio accepted the message |
| `delivered` | Twilio confirmed delivery to the recipient |
| `failed` | SMS sending failed (after up to 3 retries) |

The Roster page auto-refreshes every 5 seconds while any assignment is in `queued` status, so you can watch messages transition to `sent`/`delivered` in real time.

## Error Handling

- **Invalid phone numbers** — Rows with malformed phone numbers are skipped with an error report
- **Missing Excel columns** — Upload is rejected with a list of missing columns
- **Duplicate assignments** — Same driver + date + route combination is detected and skipped
- **SMS failures** — Failed messages are retried up to 3 times (60-second intervals); errors are logged to `sms_logs.error_message`

## Twilio Webhook Setup

To receive delivery status updates, configure your Twilio Messaging Service status callback URL:

```
https://your-domain.com/api/sms/status/
```

This endpoint accepts POST requests with `MessageSid` and `MessageStatus` fields.

## Deployment

### Vercel Deployment

You can deploy Hera to [Vercel](https://vercel.com/) for serverless hosting. The project is pre-configured for Vercel:

- `vercel.json` uses Django WSGI entrypoint (`config/wsgi.py`).
- Static files are handled via `STATIC_ROOT` and routed in `vercel.json`.
- All environment variables must be set in Vercel's dashboard.

#### Steps

1. **Fork or clone the repository**
2. **Create a `.env` file** (use `.env.example` as a template)
3. **Set production values:**
                - `DEBUG=False`
                - `DJANGO_SECRET_KEY` (use a strong, random value)
                - `ALLOWED_HOSTS=your-vercel-domain.vercel.app`
                - Use a managed MySQL database (do not use SQLite for production)
                - Set `REDIS_URL` to a production Redis instance
                - Set Twilio and SendGrid credentials
                - Set Celery worker to run externally (if using background tasks)
4. **Run static file collection locally:**
                ```bash
                python manage.py collectstatic
                ```
                This will create a `staticfiles/` directory for Vercel to serve.
5. **Push your code to GitHub**
6. **Connect your repo to Vercel**
7. **Configure environment variables in Vercel dashboard**
8. **Deploy**

#### Static Files

Static files are served from `/staticfiles/` via a custom route in `vercel.json`:

```json
{
        "routes": [
                { "src": "/static/(.*)", "dest": "/staticfiles/$1" },
                { "src": "/(.*)", "dest": "config/wsgi.py" }
        ]
}
```

#### Production Checklist

- [ ] `DEBUG=False`
- [ ] Strong `DJANGO_SECRET_KEY`
- [ ] `ALLOWED_HOSTS` includes your Vercel domain
- [ ] Managed MySQL database (update `.env` and `settings.py`)
- [ ] Production Redis URL
- [ ] All credentials/secrets set in Vercel dashboard
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Celery worker running externally (if used)

---

For traditional server hosting (AWS EC2, DigitalOcean, etc.), use Gunicorn + Nginx, and follow the same environment setup.
