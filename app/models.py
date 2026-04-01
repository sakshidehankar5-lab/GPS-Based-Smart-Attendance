from datetime import datetime, timezone
import secrets

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    attendance_records = db.relationship("AttendanceRecord", back_populates="student")
    sessions_taught = db.relationship("ClassSession", back_populates="teacher")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    room = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius_meters = db.Column(db.Integer, nullable=False, default=80)
    qr_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    presence_check_nonce = db.Column(db.Integer, default=0, nullable=False)
    presence_check_issued_at = db.Column(db.DateTime(timezone=True), nullable=True)

    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    teacher = db.relationship("User", back_populates="sessions_taught")

    attendance_records = db.relationship(
        "AttendanceRecord", back_populates="session", cascade="all, delete-orphan"
    )

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)


class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_time = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    entry_latitude = db.Column(db.Float, nullable=True)
    entry_longitude = db.Column(db.Float, nullable=True)
    exit_time = db.Column(db.DateTime(timezone=True), nullable=True)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="in_class")
    total_minutes = db.Column(db.Float, nullable=False, default=0.0)

    session_id = db.Column(db.Integer, db.ForeignKey("class_session.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    session = db.relationship("ClassSession", back_populates="attendance_records")
    student = db.relationship("User", back_populates="attendance_records")
    pings = db.relationship(
        "PresencePing", back_populates="attendance_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("session_id", "student_id", name="uq_session_student_attendance"),
    )

    def close(self, reason: str) -> None:
        if self.exit_time:
            return
        self.exit_time = utcnow()
        self.status = reason
        self.total_minutes = max(
            0.0, (self.exit_time - self.entry_time).total_seconds() / 60.0
        )


class PresencePing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    distance_meters = db.Column(db.Float, nullable=False)
    is_inside = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    attendance_record_id = db.Column(
        db.Integer, db.ForeignKey("attendance_record.id"), nullable=False
    )
    attendance_record = db.relationship("AttendanceRecord", back_populates="pings")
