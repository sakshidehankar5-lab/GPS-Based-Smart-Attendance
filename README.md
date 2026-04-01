# Smart Attendance System (Flask)

Full-stack smart attendance platform with role-based dashboards for Students and Teachers/Admins, QR-based entry, location-based continuous verification, auto-exit, and attendance duration calculation.

## Tech Stack
- Backend: Flask, Flask-SQLAlchemy, Flask-Login
- DB: PostgreSQL / MySQL (SQLite default for local run)
- Frontend: HTML, Bootstrap 5, JavaScript
- Charts: Chart.js
- QR: `qrcode` Python library

## Features Implemented

### Student
- Register / login authentication
- QR token based attendance entry
- Duplicate entry prevention for same session
- Continuous GPS presence pings
- Auto exit when outside classroom radius
- Attendance history and date filter
- Mobile-friendly dashboard with chart

### Teacher/Admin
- Start class session with geofence center and radius
- Generate QR token/QR image at class start
- Live student monitoring table
- Trigger random presence checks
- End session and close active entries
- Date/student filtered attendance reports
- CSV export for attendance records
- Dashboard statistics and charts

## Project Structure
```text
att_ai/
  app/
    __init__.py
    models.py
    api/routes.py
    auth/routes.py
    student/routes.py
    teacher/routes.py
    utils/geo.py
    static/css/style.css
    static/js/main.js
    templates/
      base.html
      auth/*.html
      student/*.html
      teacher/*.html
  config.py
  run.py
  requirements.txt
  .env.example
```

## Setup

1. Create virtual environment and install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
copy .env.example .env
```
Update `.env` with a secure `SECRET_KEY` and your `DATABASE_URL`.

3. Initialize DB (Flask-Migrate):
```bash
flask --app run.py db init
flask --app run.py db migrate -m "init"
flask --app run.py db upgrade
```

4. Run app:
```bash
python run.py
```

## Database URL Examples
- PostgreSQL: `postgresql+psycopg2://user:password@localhost:5432/attendance_db`
- MySQL: `mysql+pymysql://user:password@localhost:3306/attendance_db`
- SQLite (default): `sqlite:///attendance.db`

## Important API Endpoints
- `POST /api/scan-entry` - student marks entry with QR token + location
- `POST /api/presence/<session_id>` - periodic GPS presence verification
- `GET /api/my-active-session` - currently active session for logged-in student
- `GET /api/session/<session_id>/live` - teacher live attendance feed

## Deployment Notes
- Use production WSGI server (`gunicorn`/`waitress`) behind reverse proxy.
- Set strong `SECRET_KEY`.
- Use PostgreSQL/MySQL in production.
- Enforce HTTPS to protect location/session traffic.
