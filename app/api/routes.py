from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from datetime import timedelta, timezone
from sqlalchemy import func

from app import db
from app.models import AttendanceRecord, ClassSession, PresencePing, utcnow
from app.utils.geo import haversine_distance_meters


api_bp = Blueprint("api", __name__)


def _as_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _validate_student():
    if current_user.role != "student":
        return jsonify({"error": "Student access required"}), 403
    return None


def _scan_window_expired(session: ClassSession) -> bool:
    window_minutes = current_app.config.get("QR_SCAN_ENTRY_WINDOW_MINUTES", 10)
    started_at = _as_utc(session.started_at)
    now_utc = _as_utc(utcnow())
    expires_at = started_at + timedelta(minutes=window_minutes)
    return now_utc > expires_at


@api_bp.route("/scan-entry", methods=["POST"])
@login_required
def scan_entry():
    role_error = _validate_student()
    if role_error:
        return role_error

    data = request.get_json(silent=True) or {}
    qr_token = data.get("qr_token", "").strip()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not qr_token or latitude is None or longitude is None:
        return jsonify({"error": "qr_token, latitude and longitude are required"}), 400

    session = ClassSession.query.filter_by(qr_token=qr_token, is_active=True).first()
    if not session:
        return jsonify({"error": "Invalid or expired QR token"}), 404
    if _scan_window_expired(session):
        return jsonify(
            {
                "error": "QR entry time window expired for this class session.",
                "allowed_entry_window_minutes": current_app.config.get(
                    "QR_SCAN_ENTRY_WINDOW_MINUTES", 10
                ),
            }
        ), 400

    existing = AttendanceRecord.query.filter_by(
        session_id=session.id, student_id=current_user.id
    ).first()
    if existing:
        return jsonify({"error": "Attendance already marked for this session"}), 409

    distance = haversine_distance_meters(
        float(latitude), float(longitude), session.latitude, session.longitude
    )
    inside = distance <= session.radius_meters
    if not inside:
        return jsonify(
            {
                "error": "You are outside classroom radius",
                "distance_meters": round(distance, 2),
                "allowed_radius_meters": session.radius_meters,
            }
        ), 400

    record = AttendanceRecord(
        session_id=session.id,
        student_id=current_user.id,
        entry_time=utcnow(),
        entry_latitude=float(latitude),
        entry_longitude=float(longitude),
        last_seen_at=utcnow(),
        status="in_class",
    )
    db.session.add(record)
    db.session.flush()
    ping = PresencePing(
        attendance_record_id=record.id,
        latitude=float(latitude),
        longitude=float(longitude),
        distance_meters=distance,
        is_inside=True,
    )
    db.session.add(ping)
    db.session.commit()
    return jsonify({"message": "Entry attendance marked", "session_id": session.id})


@api_bp.route("/scan-session/<int:session_id>", methods=["POST"])
@login_required
def scan_session_entry(session_id: int):
    role_error = _validate_student()
    if role_error:
        return role_error

    data = request.get_json(silent=True) or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if latitude is None or longitude is None:
        return jsonify({"error": "latitude and longitude are required"}), 400

    session = ClassSession.query.get_or_404(session_id)
    if not session.is_active:
        return jsonify({"error": "Session is not active"}), 400
    if _scan_window_expired(session):
        return jsonify(
            {
                "error": "QR entry time window expired for this class session.",
                "allowed_entry_window_minutes": current_app.config.get(
                    "QR_SCAN_ENTRY_WINDOW_MINUTES", 10
                ),
            }
        ), 400

    existing = AttendanceRecord.query.filter_by(
        session_id=session.id, student_id=current_user.id
    ).first()
    if existing:
        return jsonify({"error": "Attendance already marked for this session"}), 409

    distance = haversine_distance_meters(
        float(latitude), float(longitude), session.latitude, session.longitude
    )
    inside = distance <= session.radius_meters
    if not inside:
        return jsonify(
            {
                "error": "Attendance rejected. You are outside classroom radius.",
                "distance_meters": round(distance, 2),
                "allowed_radius_meters": session.radius_meters,
            }
        ), 400

    record = AttendanceRecord(
        session_id=session.id,
        student_id=current_user.id,
        entry_time=utcnow(),
        entry_latitude=float(latitude),
        entry_longitude=float(longitude),
        last_seen_at=utcnow(),
        status="in_class",
    )
    db.session.add(record)
    db.session.flush()
    ping = PresencePing(
        attendance_record_id=record.id,
        latitude=float(latitude),
        longitude=float(longitude),
        distance_meters=distance,
        is_inside=True,
    )
    db.session.add(ping)
    db.session.commit()
    return jsonify(
        {
            "message": "Attendance marked successfully.",
            "session_id": session.id,
            "entry_time": record.entry_time.isoformat(),
        }
    )


@api_bp.route("/presence/<int:session_id>", methods=["POST"])
@login_required
def presence_ping(session_id: int):
    role_error = _validate_student()
    if role_error:
        return role_error

    data = request.get_json(silent=True) or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if latitude is None or longitude is None:
        return jsonify({"error": "latitude and longitude are required"}), 400

    session = ClassSession.query.get_or_404(session_id)
    record = AttendanceRecord.query.filter_by(
        session_id=session.id, student_id=current_user.id
    ).first()
    if not record:
        return jsonify({"error": "No active attendance entry found"}), 404
    if record.exit_time:
        return jsonify({"message": "Already exited", "status": record.status}), 200

    distance = haversine_distance_meters(
        float(latitude), float(longitude), session.latitude, session.longitude
    )
    inside = distance <= session.radius_meters

    record.last_seen_at = utcnow()
    ping = PresencePing(
        attendance_record_id=record.id,
        latitude=float(latitude),
        longitude=float(longitude),
        distance_meters=distance,
        is_inside=inside,
    )
    db.session.add(ping)

    if not inside:
        record.close("exit_out_of_radius")
        db.session.commit()
        return jsonify(
            {
                "message": "Exit marked due to leaving class area",
                "status": record.status,
                "distance_meters": round(distance, 2),
                "total_minutes": round(record.total_minutes, 2),
            }
        )

    db.session.commit()
    return jsonify(
        {
            "message": "Presence verified",
            "status": "in_class",
            "distance_meters": round(distance, 2),
        }
    )


@api_bp.route("/my-active-session")
@login_required
def my_active_session():
    role_error = _validate_student()
    if role_error:
        return role_error
    record = (
        AttendanceRecord.query.join(ClassSession)
        .filter(
            AttendanceRecord.student_id == current_user.id,
            AttendanceRecord.status == "in_class",
            ClassSession.is_active.is_(True),
        )
        .order_by(AttendanceRecord.entry_time.desc())
        .first()
    )
    if not record:
        return jsonify({"active": False})
    return jsonify(
        {
            "active": True,
            "session_id": record.session_id,
            "presence_check_nonce": record.session.presence_check_nonce,
            "session_title": record.session.title,
        }
    )


@api_bp.route("/session/<int:session_id>/live")
@login_required
def live_session_data(session_id: int):
    if current_user.role != "teacher":
        return jsonify({"error": "Teacher access required"}), 403

    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    students = []
    for rec in session.attendance_records:
        students.append(
            {
                "name": rec.student.full_name,
                "email": rec.student.email,
                "entry_time": rec.entry_time.isoformat() if rec.entry_time else "",
                "last_seen_at": rec.last_seen_at.isoformat() if rec.last_seen_at else "",
                "status": rec.status,
                "total_minutes": round(rec.total_minutes, 2),
            }
        )
    return jsonify({"session": session.title, "students": students})


@api_bp.route("/config")
@login_required
def config_payload():
    return jsonify(
        {
            "presence_interval_ms": 45000,
            "classroom_radius_meters": current_app.config["CLASSROOM_RADIUS_METERS"],
        }
    )


@api_bp.route("/teacher/summary")
@login_required
def teacher_summary():
    if current_user.role != "teacher":
        return jsonify({"error": "Teacher access required"}), 403

    totals = (
        db.session.query(
            func.count(AttendanceRecord.id),
            func.sum(AttendanceRecord.total_minutes),
        )
        .join(ClassSession, AttendanceRecord.session_id == ClassSession.id)
        .filter(ClassSession.teacher_id == current_user.id)
        .first()
    )
    total_entries = int(totals[0] or 0)
    total_minutes = float(totals[1] or 0)

    active = (
        ClassSession.query.filter_by(teacher_id=current_user.id, is_active=True)
        .order_by(ClassSession.started_at.desc())
        .first()
    )
    active_count = 0
    active_id = None
    active_title = None
    active_room = None
    if active:
        active_id = active.id
        active_title = active.title
        active_room = active.room
        active_count = AttendanceRecord.query.filter_by(session_id=active.id).count()

    return jsonify(
        {
            "total_entries": total_entries,
            "total_minutes": round(total_minutes, 2),
            "active_session": {
                "id": active_id,
                "title": active_title,
                "room": active_room,
                "count": active_count,
            },
        }
    )
