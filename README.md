# Hera - Logistics & Route Assignment Platform

A comprehensive Django-based logistics and route-assignment application for managing drivers, routes, and SMS communication. The app streamlines the workflow of importing daily route spreadsheets, intelligently matching drivers, reviewing batch imports, and sending SMS notifications.

## Table of Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [Settings & Configuration](#settings--configuration)
- [Main Features & Pages](#main-features--pages)
- [Route Import Workflow](#route-import-workflow)
- [Excel File Format](#excel-file-format)
- [API Documentation](#api-documentation)
- [SMS & Email Services](#sms--email-services)
- [Authentication & Permissions](#authentication--permissions)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

## Overview

Hera is a production-ready logistics platform designed to:

- **Manage drivers and delivery associates** with status tracking (active/inactive).
- **Upload and import route spreadsheets** with intelligent driver matching using fuzzy string similarity.
- **Review import batches** before committing to the system, with granular control over matched/unmatched/ambiguous assignments.
- **Link routes to existing drivers** or quickly create new drivers in-context.
- **Track route and assignment status** (match_status, sms_status, progress) for operational oversight.
- **Send SMS notifications** with Twilio integration, safeguarded by eligibility checks.
- **Manage vehicle records** and associate them with routes.
- **Query SMS history** and monitor delivery communications.

## Technology Stack

### Backend
- **Django 5.2.12** - Web framework
- **Django REST Framework 3.14+** - API layer
- **Python 3.9+** - Runtime
- **pandas** - Excel file parsing and data manipulation
- **Twilio SDK** - SMS service integration
- **SendGrid** - Email notifications
- **MySQL / PostgreSQL / SQLite** - Database (configurable)

### Frontend
- **HTML5 with Jinja2 templating** - Dynamic page rendering
- **Vanilla JavaScript (ES6+)** - Client-side interactivity, async/await for API calls
- **Custom CSS** - Responsive design with CSS variables for theming
- **Bootstrap-based component styling** - Forms, modals, tables, badges

### Services
- **Twilio** - SMS delivery (requires account and auth token)
- **SendGrid** - Email notifications (requires API key)
- **Redis** (optional) - Caching and Celery task queue for async operations

### Development & DevOps
- **Git** - Version control
- **Python venv** - Virtual environment management
- **pytest** (if added) - Testing framework
- **Gunicorn** - Production WSGI server
- **Nginx** - Reverse proxy (recommended for production)

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip and venv (built into Python 3.3+)
- Git
- MySQL, PostgreSQL, or use SQLite (default for development)
- Twilio account (for SMS functionality)
- SendGrid account (for email)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hera.app
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (admin account)**
   ```bash
   # Interactive prompt:
   python manage.py createsuperuser
   
   # Or non-interactive (creates if none exists):
   python manage.py createsuperuser_if_none --email admin@example.com --password yourpassword
   ```

7. **Collect static files** (for production; development uses runserver static serving)
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Start development server**
   ```bash
   python manage.py runserver
   ```
   Visit http://localhost:8000/

---

## Project Structure

```
hera.app/
├── manage.py                          # Django management CLI
├── requirements.txt                   # Python dependencies
├── runtime.txt                        # Python version (for Heroku/PaaS)
├── .env.example                       # Environment variables template
├── test_workflow.py                   # Manual workflow test script
│
├── api/                               # Main Django app: models, views, serializers
│   ├── models/
│   │   ├── models.py                  # Core models: Route, ImportBatch, Assignment
│   │   ├── user.py                    # User-scoped model mixins
│   │   └── otp.py                     # OTP for email verification
│   │
│   ├── serializers/
│   │   └── serializers.py             # DRF serializers for all models
│   │
│   ├── views/                         # API views organized by concern
│   │   ├── assignment_views.py        # Assignment CRUD and actions
│   │   ├── auth_views.py              # Login, logout, password reset
│   │   ├── dashboard_views.py         # Stats and overview
│   │   ├── driver_views.py            # Driver/Associate CRUD
│   │   ├── roster_views.py            # Roster/batch operations
│   │   ├── routes_views.py            # Route CRUD, SMS, linking, matching
│   │   ├── sms_views.py               # SMS history, status, sending
│   │   └── vehicle_views.py           # Vehicle CRUD
│   │
│   ├── services/                      # Business logic layer
│   │   ├── daily_route_import.py      # Excel parsing, driver matching
│   │   ├── driver_matching.py         # Fuzzy matching algorithm
│   │   ├── email_service.py           # SendGrid integration
│   │   ├── sms_service.py             # Twilio integration
│   │   ├── sms_eligibility.py         # SMS safeguard rules
│   │   └── roster_service.py          # Batch operations
│   │
│   ├── tasks/
│   │   └── sms_tasks.py               # Celery async tasks for SMS
│   │
│   ├── migrations/                    # Database schema migrations
│   ├── management/commands/           # Custom management commands
│   ├── admin.py                       # Django admin interface config
│   ├── urls.py                        # API route definitions
│   ├── apps.py                        # App config
│   └── tests.py                       # Unit tests
│
├── config/                            # Django project settings
│   ├── settings.py                    # Configuration (database, logging, middleware, etc.)
│   ├── urls.py                        # Main URL dispatcher
│   ├── wsgi.py                        # WSGI entry point for production servers
│   ├── asgi.py                        # ASGI entry point (for async support)
│   └── celery.py                      # Celery async task configuration
│
├── templates/dashboard/               # Jinja2 HTML templates
│   ├── base.html                      # Base layout (navigation, CSS, JS)
│   ├── home.html                      # Route Assignments main page
│   ├── import_review.html             # Import batch review & driver linking
│   ├── associates.html                # Driver/Associate management
│   ├── vehicles.html                  # Vehicle management
│   ├── sms_center.html                # SMS history and sending
│   ├── login.html                     # Authentication
│   ├── signup.html                    # User registration
│   ├── forgot_password.html           # Password recovery
│   ├── verify_email.html              # Email verification flow
│   └── rate_limited.html              # Rate limit error page
│
├── static/
│   ├── css/hera.css                   # Custom component and utility styles
│   ├── js/                            # JavaScript files (embedded in templates)
│   └── img/                           # Images and icons
│
├── staticfiles/                       # Collected static assets (generated)
│   ├── admin/                         # Django admin UI files
│   └── rest_framework/                # DRF UI files
│
└── media/                             # User-uploaded files (if applicable)
```

---

## Database Models

### Core Models

**User** (Django built-in)
- Email-based authentication
- Staff/superuser flags for admin access
- User-scoped query filtering on all models

**Driver** (aka Associate)
```
- name: CharField
- phone: CharField (unique, E.164 format)
- status: CharField (choices: active, inactive) → used for SMS eligibility
- created_at: DateTimeField
- user: ForeignKey to User (for scoping)
```

**Vehicle**
```
- vehicle_code: CharField (unique)
- vehicle_plate: CharField (unique)
- vehicle_type: CharField
- status: CharField (active/inactive)
- user: ForeignKey to User
```

**ImportBatch**
```
- batch_id: UUIDField (primary key)
- file: FileField (uploaded Excel)
- status: CharField (processing, completed, failed)
- matched_rows: IntegerField
- unmatched_rows: IntegerField
- ambiguous_rows: IntegerField
- created_at: DateTimeField
- user: ForeignKey to User
```

**Route** (formerly Assignment)
```
- route_code: CharField
- dsp_name: CharField
- transporter_id: CharField
- driver: ForeignKey to Driver (nullable; set during linking)
- vehicle: ForeignKey to Vehicle (nullable)
- phone: CharField (driver phone; copied at import time)
- match_status: CharField (matched, unmatched, ambiguous)
- sms_status: CharField (pending, ready, sent, failed, blocked)
- route_progress: CharField (Not Started, In Progress, Completed)
- wave_time: TimeField
- staging: CharField
- pad: CharField
- date: DateField
- all_stops: IntegerField
- not_started_stops: IntegerField
- import_batch: ForeignKey to ImportBatch
- created_at: DateTimeField
- user: ForeignKey to User
```

**SMS** (Message log)
```
- to_number: CharField (recipient phone)
- message_body: TextField
- status: CharField (pending, sent, failed)
- twilio_sid: CharField (Twilio message ID)
- route: ForeignKey to Route
- sent_at: DateTimeField
- user: ForeignKey to User
```

**OTP** (One-Time Password)
```
- user: ForeignKey to User
- code: CharField (6-digit code)
- created_at: DateTimeField
- expires_at: DateTimeField
```

---

## Settings & Configuration

### settings.py Overview

**Database Configuration**
```python
# Supports MySQL, PostgreSQL, SQLite (see environment variables)
# Default: SQLite (db.sqlite3) for development
# For production: use MySQL or PostgreSQL with connection pooling
```

**Authentication**
- Django's TokenAuthentication (DRF)
- Email login (custom backend)
- Permission classes: `IsAuthenticated` on all sensitive endpoints

**Installed Apps**
- `api` - Main application
- `rest_framework` - REST API
- `corsheaders` - CORS handling (if frontend is separate)
- `django.contrib.admin`, `auth`, `sessions`, `messages`, `staticfiles`

**Middleware**
- StandardMiddleware, SessionMiddleware, AuthenticationMiddleware
- MessageMiddleware, CsrfViewMiddleware

**Logging** (configured for development; adjust for production)
- Logs to console (DEBUG=True)
- Include API requests, migrations, SQL queries

**Static Files**
- STATIC_URL: `/static/`
- STATIC_ROOT: `<project>/staticfiles/` (collect before deploy)
- MEDIA_URL, MEDIA_ROOT: For user uploads

---

## Main Features & Pages

### 1. **Route Assignments** (Dashboard / Home)
- **URL**: `/` or `/dashboard/`
- **Features**:
  - Upload new route spreadsheets via form
  - View all routes in paginated, searchable table
  - Filter by match_status, sms_status, driver name
  - Send SMS for routes with sms_status=ready
  - Delete routes
  - Bulk operations (future)
- **Backend**: `home.html` + `/api/routes/`, `/api/routes/<route_id>/send-sms/`, `/api/routes/<route_id>/delete`

### 2. **Import Review**
- **URL**: `/import-review/?batch_id=<batch_id>`
- **Features**:
  - Batch summary showing matched/unmatched/ambiguous counts
  - List of all routes in batch with match_status badges
  - For unmatched/ambiguous rows:
    - Link Existing Driver: modal shows all drivers with search/filter
    - Add Driver: inline form to create new driver and link immediately
  - Auto-retry on transient network errors (3 retries, 1-second backoff)
  - Non-blocking driver list loading
- **Backend**: `import_review.html` + `/api/routes/import/<batch_id>/`, `/api/routes/import/<batch_id>/routes/`, `/api/routes/<route_id>/link-driver/`, `/api/drivers/`

### 3. **Associates** (Driver Management)
- **URL**: `/associates/`
- **Features**:
  - Add/Edit/Delete driver records
  - Search by name or phone
  - View status (active/inactive) and creation date
  - Stats card showing total, active, inactive counts
- **Backend**: `associates.html` + `/api/drivers/`

### 4. **Vehicles**
- **URL**: `/vehicles/`
- **Features**:
  - Manage vehicle fleet
  - Assign vehicles to routes (future bulk linking)
  - Track vehicle status
- **Backend**: `vehicles.html` + `/api/vehicles/`

### 5. **SMS Center**
- **URL**: `/sms-center/`
- **Features**:
  - View SMS history filtered by status, route, date range
  - Monitor Twilio delivery status
  - Manual SMS sending (future: bulk send with templating)
- **Backend**: `sms_center.html` + `/api/sms/history/`, `/api/sms/status/`

### 6. **Authentication**
- **Login**: `/login/` — Email + password (no social login)
- **Signup**: `/signup/` — Email verification with OTP
- **Password Recovery**: `/forgot-password/` → `/reset-password/`

---

## Route Import Workflow

### Step-by-Step Process

1. **Upload Phase** (Route Assignments page)
   - User selects Excel file via form
   - POST to `/api/routes/upload/`
   - Backend:
     - Parses spreadsheet with pandas
     - Creates ImportBatch record
     - For each row, attempts driver matching:
       - First: `transporter_id + driver_name` (75%+ fuzzy match)
       - Second: `dsp_name + driver_name` (75%+ fuzzy match)
       - Third: exact `driver_name` match
       - Fallback: `fuzzy driver_name` (75%+ threshold)
     - Sets initial match_status for each Route (matched/unmatched/ambiguous)
     - Redirects to `/import-review/?batch_id=<uuid>`

2. **Review Phase** (Import Review page)
   - Page loads batch summary (counts by match_status)
   - Loads all routes in batch
   - Uses auto-retry (3 attempts, 1-second backoff) if transient failures occur
   - User can filter by match_status or scroll through list

3. **Linking Phase** (still on Import Review)
   - For unmatched/ambiguous routes:
     - **Link Existing Driver**: Opens modal with all drivers (searchable)
       - POST `/api/routes/<route_id>/link-driver/` with driver_id
     - **Add Driver**: Opens inline form to create new driver
       - POST `/api/drivers/` with name + phone
       - After creation, immediately POST `/api/routes/<route_id>/link-driver/` with new driver_id
   - Updates route.match_status to "matched" after linking
   - Updates route.sms_status based on eligibility check:
     - If driver.status=active AND phone number is valid → sms_status=ready
     - Otherwise → sms_status=blocked

4. **Management Phase** (Route Assignments page)
   - View all routes from batch
   - Filter by match_status, sms_status
   - Manually update sms_status (mark ready/blocked) [future feature]
   - Delete routes no longer needed

5. **Send Phase** (Route Assignments page)
   - User selects routes with sms_status=ready
   - POST `/api/routes/send-sms/` (single) or `/api/routes/<batch_id>/send-sms/` (batch)
   - Backend:
     - Checks SMS eligibility (driver active, phone valid, status=ready)
     - Sends via Twilio (async task via Celery, if configured)
     - Logs SMS record with Twilio message ID
     - Updates route.sms_status = sent

### Driver Matching Algorithm

**File**: `api/services/driver_matching.py`

Uses fuzzy string similarity (python-fuzzywuzzy or similar) with priority order:

```python
1. Try: f"{transporter_id} + driver_name" → min 75% similarity
2. Try: f"{dsp_name} + driver_name" → min 75% similarity
3. Try: exact driver_name match (case-insensitive)
4. Try: fuzzy driver_name match → min 75% similarity
5. Fallback: No match found (mark as unmatched)
```

If multiple drivers match at same priority, mark as "ambiguous" (user must choose).

---

## Excel File Format

### Supported Columns

The app expects Excel files with the following columns (case-insensitive, can be in any order):

| Column | Type | Required | Example | Notes |
|--------|------|----------|---------|-------|
| Route | String | ✓ | RT001 | Unique route identifier |
| Driver Name | String | ✓ | John Smith | Used for fuzzy matching |
| Phone | String | | +447700000001 | E.164 format (starts with +) |
| DSP Name | String | | Fast Delivery Co | Delivery Service Partner |
| Transporter ID | String | | TRX123 | Carrier/transporter code |
| Vehicle Code | String | | VH001 | Vehicle identifier |
| Vehicle Plate | String | | ABC123 | License plate |
| Staging | String | | 5A | Distribution hub/area |
| Pad | String | | P1 | Load bay identifier |
| Wave Time | Time | | 08:30 | Departure time (HH:MM format) |
| Date | Date | | 2025-04-02 | Delivery date (YYYY-MM-DD) |
| Route Progress | String | | Not Started | One of: Not Started, In Progress, Completed |
| Delivery Service Type | String | | Standard | Service level (Standard, Express, etc.) |
| Route Duration | Number | | 45 | Estimated minutes |
| All Stops | Integer | | 12 | Total delivery stops |
| Not Started Stops | Integer | | 12 | Remaining stops |

### Example File Structure

```
Route | Driver Name    | Phone           | DSP Name       | Vehicle Code | Wave Time | Date
------|----------------|-----------------|----------------|--------------|-----------|----------
RT001 | John Smith     | +447700000001   | Fast Delivery  | VH001        | 08:30     | 2025-04-02
RT002 | Jane Doe       | +447700000002   | Quick Services | VH002        | 09:00     | 2025-04-02
RT003 | Bob Johnson    |                 | Express Routes | VH003        | 09:30     | 2025-04-02
```

### Upload Constraints

- File format: `.xlsx` (Excel 2007+) or `.csv`
- Max file size: 10 MB (configurable in settings)
- Max rows: 5000 per batch (recommended; no hard limit)
- Empty rows are skipped
- Duplicate routes (same Route code) in the same batch: last one wins
- Duplicate drivers (same name + phone): creates single Route per driver, one per row

---

## API Documentation

### Authentication

All endpoints (except `/api/auth/login/` and `/api/auth/signup/`) require:

```
Authorization: Token <token>
```

Obtain token via login:
```bash
POST /api/auth/login/
Body: { "email": "user@example.com", "password": "..." }
Response: { "token": "abc123...", "user": {...} }
```

### REST Endpoints

#### Routes

**List Routes**  
```
GET /api/routes/?page=1&page_size=50&match_status=unmatched&sms_status=ready
Response: { count: 100, results: [...] }
```

**Upload Routes**  
```
POST /api/routes/upload/
Body: multipart/form-data with 'file' field
Response: { batch_id: "uuid", matched_rows: 50, unmatched_rows: 10 }
```

**Get Import Batch Summary**  
```
GET /api/routes/import/<batch_id>/
Response: { 
  batch_id: "uuid",
  file: "path/to/file.xlsx",
  status: "completed",
  matched_rows: 50,
  unmatched_rows: 10,
  ambiguous_rows: 2,
  created_at: "2025-04-02T10:00:00Z"
}
```

**Get Routes in Batch**  
```
GET /api/routes/import/<batch_id>/routes/?limit=500
Response: [
  {
    id: 1,
    route_code: "RT001",
    driver: { id: 1, name: "John Smith", ... },
    match_status: "matched",
    sms_status: "ready",
    ...
  },
  ...
]
```

**Link Route to Driver**  
```
POST /api/routes/<route_id>/link-driver/
Body: { "driver_id": 5 }
Response: { 
  id: 1,
  route_code: "RT001",
  driver: { id: 5, name: "Jane Doe", ... },
  match_status: "matched",
  sms_status: "ready"
}
```

**Create Driver (from Import Review)**  
```
POST /api/drivers/
Body: { "name": "New Driver", "phone": "+447700000099", "status": "active" }
Response: { id: 99, name: "New Driver", phone: "+447700000099", status: "active" }
```

**Send SMS for Route**  
```
POST /api/routes/<route_id>/send-sms/
Body: {}
Response: { 
  route_id: 1,
  sms_status: "sent",
  sms_id: "twilio-msg-id-123",
  sent_at: "2025-04-02T10:05:00Z"
}
```

**Send SMS for Batch**  
```
POST /api/routes/<batch_id>/send-sms/
Body: {}
Response: {
  batch_id: "uuid",
  sent_count: 48,
  blocked_count: 2,
  failed_count: 0
}
```

**Delete Route**  
```
DELETE /api/routes/<route_id>/
Response: { id: 1, deleted: true }
```

#### Drivers

**List Drivers**  
```
GET /api/drivers/?page=1&page_size=100&status=active
Response: { count: 245, results: [...] }
```

**Create Driver**  
```
POST /api/drivers/
Body: { "name": "John Smith", "phone": "+447700000001", "status": "active" }
Response: { id: 1, name: "John Smith", phone: "+447700000001", status: "active", created_at: "..." }
```

**Update Driver**  
```
PUT /api/drivers/<driver_id>/
Body: { "name": "John Smith", "phone": "+447700000001", "status": "inactive" }
Response: { id: 1, ... }
```

**Delete Driver**  
```
DELETE /api/drivers/<driver_id>/
Response: { id: 1, deleted: true }
```

#### Vehicles

**List Vehicles**  
```
GET /api/vehicles/?page=1&page_size=50
Response: { count: 30, results: [...] }
```

**Create Vehicle**  
```
POST /api/vehicles/
Body: { 
  "vehicle_code": "VH001",
  "vehicle_plate": "ABC123",
  "vehicle_type": "Van",
  "status": "active"
}
Response: { id: 1, vehicle_code: "VH001", ... }
```

#### SMS

**SMS History**  
```
GET /api/sms/history/?route_id=1&status=sent&limit=100
Response: [
  {
    id: 1,
    to_number: "+447700000001",
    message_body: "Your delivery...",
    status: "sent",
    twilio_sid: "...",
    sent_at: "2025-04-02T10:05:00Z"
  },
  ...
]
```

**Check SMS Status**  
```
GET /api/sms/status/<twilio_sid>/
Response: { 
  twilio_sid: "...", 
  status: "delivered",
  failure_code: null,
  updated_at: "2025-04-02T10:10:00Z"
}
```

---

## SMS & Email Services

### SMS (Twilio)

**Configuration** (in `.env`):
```
TWILIO_ACCOUNT_SID=AC1234567890abcdef
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_MESSAGING_SERVICE_SID=MG1234567890abcdef
```

**File**: `api/services/sms_service.py`

**How it works**:
1. User clicks "Send SMS" on Route Assignments or via API
2. SMS eligibility check runs:
   - Is driver.status = "active"?
   - Is phone number valid (not empty, matches E.164)?
   - Is route.sms_status = "ready"?
3. If eligible, POST to Twilio Messaging Service
4. SMS record created with Twilio message ID
5. Twilio webhook (optional) updates SMS status to "delivered" or "failed"

**Eligibility Rules** (`api/services/sms_eligibility.py`):
- Driver must be active
- Phone must be valid (not blocked, no invalid characters)
- Route must be marked "ready"
- Optional: daily/hourly rate limits per driver

### Email (SendGrid)

**Configuration** (in `.env`):
```
SENDGRID_API_KEY=SG.1234567890abcdefg
SENDGRID_FROM_EMAIL=noreply@example.com
```

**File**: `api/services/email_service.py`

**Used for**:
- Account verification (signup)
- Password reset links
- Delivery confirmations (optional feature)

**Workflow**:
1. User signs up or requests password reset
2. OTP generated and stored in database
3. Email sent with OTP code or reset link
4. User clicks link or enters OTP to verify/reset

---

## Authentication & Permissions

### User Model

- Email-based (no username)
- Superuser flag for admin access
- All queries are user-scoped (drivers, routes, vehicles only visible to their creator)

### Permissions

- `IsAuthenticated` on all API endpoints except `/api/auth/login/` and `/api/auth/signup/`
- No role-based permissions (yet); all authenticated users have same access within their scope
- Admin users can access Django admin panel at `/admin/`

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

Response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_staff": false
  }
}
```

### Token Usage

All subsequent requests:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

## Development

### Tools & Best Practices

**Code Style**:
- PEP 8 for Python (use `black` for formatting)
- Vanilla JavaScript (no frameworks for templates; use async/await)
- CSS variables for theming (`--hera-green`, `--hera-red`, etc.)

**Git Workflow**:
1. Create feature branch: `git checkout -b feature/add-bulk-operations`
2. Make changes and commit: `git add . && git commit -m "Add bulk operations to routes"`
3. Push: `git push origin feature/add-bulk-operations`
4. Create pull request for code review

**Logging**:
- Django logger configured in settings
- Use `python manage.py runserver` to see all requests/errors
- Production: logs to file or external service (Sentry, etc.)

### Running the Development Server

```bash
python manage.py runserver
# or with custom host/port:
python manage.py runserver 0.0.0.0:8001
```

### Creating a New API Endpoint

1. **Define model** (if needed) in `api/models/models.py`
2. **Write serializer** in `api/serializers/serializers.py`
3. **Create view** in appropriate file under `api/views/` (e.g., `routes_views.py`)
4. **Add URL** to `api/urls.py`
5. **Test** with curl or Postman
6. **Update frontend** (template) if needed

### Working with the Frontend

- All templates inherit from `templates/dashboard/base.html`
- JavaScript embedded in `{% block extra_js %}`
- Fetch API calls with `Authorization: Token <token>` header
- Modals use custom CSS (class names: `.modal-overlay`, `.modal`, `.modal-header`, etc.)
- Use `getRouteById(routeId)` for safe route lookups (don't pass raw JSON in onclick)
- Use `routeMap` for client-side caching to avoid extra API calls

### Database Management

**Create new migration**:
```bash
python manage.py makemigrations
python manage.py migrate
```

**Rollback migration**:
```bash
python manage.py migrate api <migration_number>
```

**View migration status**:
```bash
python manage.py showmigrations
```

**Reset database** (development only):
```bash
python manage.py sqlflush | python manage.py dbshell
python manage.py migrate
```

---

## Testing

### Manual Testing (Current)

Use `test_workflow.py` to run end-to-end scenario:
```bash
python test_workflow.py
```

### Unit Tests (Future)

Create tests in `api/tests.py`:
```python
from django.test import TestCase

class DriverTestCase(TestCase):
    def setUp(self):
        self.driver = Driver.objects.create(name="John", phone="+447700000001")
    
    def test_driver_creation(self):
        self.assertEqual(self.driver.name, "John")
        self.assertTrue(self.driver.status == "active")
```

Run tests:
```bash
python manage.py test
# Run specific test:
python manage.py test api.tests.DriverTestCase.test_driver_creation
```

### Integration Tests (Future)

Test full workflows using `client.post()`, `client.get()`, etc.

---

## Deployment

### Pre-Deployment Checklist

- [ ] `DEBUG=False` in `.env`
- [ ] `SECRET_KEY` is secure and unique
- [ ] Database is MySQL/PostgreSQL (not SQLite)
- [ ] `ALLOWED_HOSTS` includes production domain
- [ ] `TWILIO_*` and `SENDGRID_*` credentials configured
- [ ] Static files collected: `python manage.py collectstatic --noinput`
- [ ] Email backend configured (SMTP or SendGrid)
- [ ] Logs configured to file or external service

### Production Server Setup (Example: Ubuntu + Gunicorn + Nginx)

1. **Install dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-venv nginx mysql-server redis-server
   ```

2. **Create app user** (separate from root):
   ```bash
   sudo useradd -m hera_app
   sudo su - hera_app
   ```

3. **Clone and setup**:
   ```bash
   git clone <repo>
   cd hera.app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   nano .env
   # Set all production values
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

6. **Create Gunicorn service** (`/etc/systemd/system/hera.service`):
   ```ini
   [Unit]
   Description=Hera Django App
   After=network.target
   
   [Service]
   User=hera_app
   WorkingDirectory=/home/hera_app/hera.app
   ExecStart=/home/hera_app/hera.app/venv/bin/gunicorn \
     --workers 4 \
     --bind 127.0.0.1:8000 \
     config.wsgi:application
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

7. **Create Nginx config** (`/etc/nginx/sites-available/hera`):
   ```nginx
   server {
       listen 80;
       server_name example.com;
       client_max_body_size 10M;

       location /static/ {
           alias /home/hera_app/hera.app/staticfiles/;
       }

       location /media/ {
           alias /home/hera_app/hera.app/media/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

8. **Enable and start services**:
   ```bash
   sudo systemctl enable hera
   sudo systemctl start hera
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

9. **Setup SSL** (Let's Encrypt):
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d example.com
   ```

### Docker Deployment (Alternative)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y default-libmysqlclient-dev build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
```

Build and run:
```bash
docker build -t hera:latest .
docker run -d -p 8000:8000 --env-file .env hera:latest
```

### Environment Variables (Production)

```bash
# Django
DEBUG=False
SECRET_KEY=<generate-secure-key>
ALLOWED_HOSTS=example.com,www.example.com

# Database (MySQL example)
DB_ENGINE=django.db.backends.mysql
DB_NAME=hera_db
DB_USER=hera_user
DB_PASSWORD=<secure-password>
DB_HOST=localhost
DB_PORT=3306

# Twilio
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_MESSAGING_SERVICE_SID=<sid>

# SendGrid
SENDGRID_API_KEY=<api-key>
SENDGRID_FROM_EMAIL=noreply@example.com

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<app-password>

# Logging
LOG_FILE=/var/log/hera/app.log
```

### Monitoring & Maintenance

- **Logs**: Monitor `/var/log/hera/app.log` and Nginx logs
- **Database**: Regular backups with `mysqldump` or automated service
- **Celery**: Monitor async tasks with flower (optional)
- **Uptime**: Use monitoring service (Uptime Robot, New Relic, etc.)

---

## Troubleshooting

### Common Issues

**1. Database migration errors**
```
python manage.py makemigrations --no-header --no-input
python manage.py migrate
```

**2. "No module named 'api'" after cloning**
- Ensure you're in the correct directory: `cd hera.app`
- Activate venv: `source venv/bin/activate`

**3. Static files not loading (development)**
- Run: `python manage.py collectstatic --clear --noinput`
- Restart server: `python manage.py runserver`

**4. CSRF token errors**
- Ensure `CSRF_TRUSTED_ORIGINS` includes your domain in `settings.py`
- Clear browser cookies and try again

**5. SMS not sending**
- Check Twilio credentials in `.env`
- Verify phone numbers are in E.164 format (e.g., +447700000001)
- Check SMS eligibility: driver active, sms_status=ready
- View logs: `python manage.py runserver` and look for Twilio errors

**6. Email verification not working**
- Check SendGrid API key and from email in `.env`
- Verify email backend in `settings.py`
- Check logs for Send Grid errors

**7. Import getting stuck on loading**
- Check network tab in browser Dev Tools
- Verify backend is responding: `curl http://localhost:8000/api/routes/import/<batch_id>/`
- Page uses automatic retry (3 attempts, 1-second backoff); if still fails, manual "Retry Load" button available
- Check database: are import batch and routes being created?

**8. Driver matching not working as expected**
- Verify Excel file has "Driver Name" column (case-insensitive)
- Check fuzzy similarity threshold in `driver_matching.py` (default 75%)
- Test matching directly: `python manage.py shell` then import and test

### Debug Mode

Enable verbose logging:
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Getting Help

- Check Django docs: https://docs.djangoproject.com/
- Check DRF docs: https://www.django-rest-framework.org/
- Check Twilio docs: https://www.twilio.com/docs/
- Check SendGrid docs: https://docs.sendgrid.com/

---

## Future Enhancements

### Short Term (Next Sprint)

- [ ] **Toast notifications** — UI confirmation on successful delete/SMS send
- [ ] **Bulk operations** — Select multiple routes, delete/send SMS in batch
- [ ] **Email templates** — Custom templates for password reset, verification
- [ ] **Advanced filtering** — Filter by date range, vehicle, DSP, etc.
- [ ] **Export to CSV** — Download routes or SMS history as CSV

### Medium Term (1-2 Months)

- [ ] **Driver performance metrics** — Track delivery completion per driver
- [ ] **Route scheduling** — Assign routes by capacity, availability
- [ ] **Webhook support** — Receive real-time updates from Twilio
- [ ] **Multi-tenant support** — Separate workspaces per organization
- [ ] **Historical analytics** — Charts and reports on delivery trends
- [ ] **API rate limiting** — Prevent abuse of public endpoints

### Long Term (3-6 Months)

- [ ] **Mobile app** — React Native for drivers to accept/complete routes
- [ ] **Real-time tracking** — GPS integration with driver location
- [ ] **AI-powered matching** — ML model to predict driver from route details
- [ ] **Payment integration** — Invoice drivers, track financials
- [ ] **Integration with logistics APIs** — Real-time carrier tracking (FedEx, UPS, etc.)
- [ ] **White-label support** — Customizable branding for different clients
- [ ] **Advanced scheduling** — Route optimization for fuel efficiency
- [ ] **Driver roster management** — Availability calendar, shift planning

### Technical Debt

- [ ] Write comprehensive unit and integration tests
- [ ] Add comprehensive API documentation (OpenAPI/Swagger)
- [ ] Refactor views into class-based views (CBV) for consistency
- [ ] Add request/response validation with Pydantic or similar
- [ ] Implement caching strategy (Redis) for frequently accessed data
- [ ] Setup CI/CD pipeline (GitHub Actions, Jenkins, etc.)
- [ ] Add performance monitoring and alerting
- [ ] Improve error handling and validation messages
- [ ] Document edge cases and known limitations

---

## Support & Contributing

For issues, feature requests, or contributions:

1. Check existing issues/discussions
2. Create a new issue with detailed description
3. Fork the repository and create a feature branch
4. Submit a pull request with clear description of changes
5. Ensure code passes tests and follows PEP 8

---

## License

[Add your license here if applicable]

---

## Contact

[Add contact info or support email]