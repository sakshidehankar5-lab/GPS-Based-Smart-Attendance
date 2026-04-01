import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///attendance.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_BASE_URL = os.getenv("APP_BASE_URL", "").strip()

    # Classroom radius in meters for location validation.
    CLASSROOM_RADIUS_METERS = int(os.getenv("CLASSROOM_RADIUS_METERS", "50"))
    # QR entry is only valid for this many minutes after class start.
    QR_SCAN_ENTRY_WINDOW_MINUTES = int(os.getenv("QR_SCAN_ENTRY_WINDOW_MINUTES", "10"))
    # If no ping is received for this many minutes, auto exit.
    PRESENCE_TIMEOUT_MINUTES = int(os.getenv("PRESENCE_TIMEOUT_MINUTES", "5"))
