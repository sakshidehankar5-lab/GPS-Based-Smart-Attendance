import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    
    # Database configuration - Render uses DATABASE_URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///attendance.db")
    
    # Fix for Render PostgreSQL URL (postgres:// -> postgresql://)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_BASE_URL = os.getenv("APP_BASE_URL", "").strip()

    # Classroom radius in meters for location validation.
    CLASSROOM_RADIUS_METERS = int(os.getenv("CLASSROOM_RADIUS_METERS", "200"))
    # QR entry is only valid for this many minutes after class start.
    QR_SCAN_ENTRY_WINDOW_MINUTES = int(os.getenv("QR_SCAN_ENTRY_WINDOW_MINUTES", "10"))
    # If no ping is received for this many minutes, auto exit.
    PRESENCE_TIMEOUT_MINUTES = int(os.getenv("PRESENCE_TIMEOUT_MINUTES", "5"))
    # Disable location validation for testing (set to "true" to bypass location checks)
    DISABLE_LOCATION_CHECK = os.getenv("DISABLE_LOCATION_CHECK", "false").lower() == "true"
