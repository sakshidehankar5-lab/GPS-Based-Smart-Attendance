import base64
import io
from datetime import timedelta
from urllib.parse import urljoin

import qrcode
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import AttendanceRecord, ClassSession, User, utcnow


teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


def teacher_required():
    if current_user.role != "teacher":
        flash("Teacher access required.", "danger")
        return False
    return True


def close_stale_records():
    timeout = current_app.config["PRESENCE_TIMEOUT_MINUTES"]
    threshold = utcnow() - timedelta(minutes=timeout)
    stale = AttendanceRecord.query.filter(
        AttendanceRecord.status == "in_class",
        AttendanceRecord.last_seen_at.isnot(None),
        AttendanceRecord.last_seen_at < threshold,
    ).all()
    for record in stale:
        record.close("exit_inactive")
    if stale:
        db.session.commit()


def qr_base64_for_payload(payload: str) -> str:
    image = qrcode.make(payload)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@teacher_bp.route("/dashboard")
@login_required
def dashboard():
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    close_stale_records()

    sessions = (
        ClassSession.query.filter_by(teacher_id=current_user.id)
        .order_by(ClassSession.started_at.desc())
        .all()
    )
    active_session = next((s for s in sessions if s.is_active), None)

    totals = (
        db.session.query(
            func.count(AttendanceRecord.id),
            func.sum(AttendanceRecord.total_minutes),
        )
        .join(ClassSession, AttendanceRecord.session_id == ClassSession.id)
        .filter(ClassSession.teacher_id == current_user.id)
        .first()
    )
    total_entries = totals[0] or 0
    total_minutes = float(totals[1] or 0)

    chart_labels = [s.title for s in sessions[:7]][::-1]
    chart_values = [len(s.attendance_records) for s in sessions[:7]][::-1]

    return render_template(
        "teacher/dashboard.html",
        sessions=sessions[:10],
        active_session=active_session,
        total_entries=total_entries,
        total_minutes=round(total_minutes, 2),
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@teacher_bp.route("/start-session", methods=["POST"])
@login_required
def start_session():
    if not teacher_required():
        return redirect(url_for("student.dashboard"))

    title = request.form.get("title", "").strip()
    room = request.form.get("room", "").strip()
    latitude = request.form.get("latitude", type=float)
    longitude = request.form.get("longitude", type=float)
    radius = request.form.get("radius_meters", type=int) or current_app.config[
        "CLASSROOM_RADIUS_METERS"
    ]

    if not all([title, room]) or latitude is None or longitude is None:
        flash("Please provide class title, room, and valid location.", "danger")
        return redirect(url_for("teacher.dashboard"))

    active = ClassSession.query.filter_by(teacher_id=current_user.id, is_active=True).first()
    if active:
        active.is_active = False
        active.ended_at = utcnow()

    session = ClassSession(
        title=title,
        room=room,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius,
        qr_token=ClassSession.generate_token(),
        teacher_id=current_user.id,
    )
    db.session.add(session)
    db.session.commit()
    flash("Session started and QR generated.", "success")
    return redirect(url_for("teacher.session_qr", session_id=session.id))


@teacher_bp.route("/session/<int:session_id>/qr")
@login_required
def session_qr(session_id: int):
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher.dashboard"))
    
    scan_path = url_for("auth.scan_session", session_id=session.id)
    
    # Get base URL from config or auto-detect from request
    app_base_url = current_app.config.get("APP_BASE_URL", "").strip()
    
    if app_base_url:
        # Use configured base URL (for production deployment)
        if not app_base_url.endswith("/"):
            app_base_url = f"{app_base_url}/"
        scan_url = urljoin(app_base_url, scan_path.lstrip("/"))
    else:
        # Auto-detect from current request (works for Render/Railway)
        from flask import request
        # Get the scheme (http/https) and host from the request
        scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
        host = request.headers.get('X-Forwarded-Host', request.host)
        scan_url = f"{scheme}://{host}{scan_path}"
    
    qr_data = qr_base64_for_payload(scan_url)
    return render_template(
        "teacher/session_qr.html",
        session=session,
        qr_data=qr_data,
        scan_url=scan_url,
    )


@teacher_bp.route("/session/<int:session_id>/update-location", methods=["POST"])
@login_required
def update_session_location(session_id: int):
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher.dashboard"))
    
    latitude = request.form.get("latitude", type=float)
    longitude = request.form.get("longitude", type=float)
    radius = request.form.get("radius_meters", type=int)
    
    if latitude is None or longitude is None:
        flash("Invalid location data.", "danger")
        return redirect(url_for("teacher.session_qr", session_id=session.id))
    
    session.latitude = latitude
    session.longitude = longitude
    if radius is not None:
        session.radius_meters = radius
    
    db.session.commit()
    flash("Session location updated successfully.", "success")
    return redirect(url_for("teacher.session_qr", session_id=session.id))


@teacher_bp.route("/session/<int:session_id>/end", methods=["POST"])
@login_required
def end_session(session_id: int):
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher.dashboard"))
    if session.is_active:
        session.is_active = False
        session.ended_at = utcnow()
        for rec in session.attendance_records:
            if rec.status == "in_class":
                rec.close("exit_session_end")
        db.session.commit()
    flash("Session ended.", "info")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/session/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_session(session_id: int):
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher.dashboard"))
    db.session.delete(session)
    db.session.commit()
    flash("Session deleted successfully.", "success")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/session/<int:session_id>/live")
@login_required
def live_students(session_id: int):
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    close_stale_records()
    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher.dashboard"))
    return render_template("teacher/live_students.html", session=session)


@teacher_bp.route("/session/<int:session_id>/presence-check", methods=["POST"])
@login_required
def issue_presence_check(session_id: int):
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    session = ClassSession.query.get_or_404(session_id)
    if session.teacher_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("teacher.dashboard"))
    session.presence_check_nonce += 1
    session.presence_check_issued_at = utcnow()
    db.session.commit()
    flash("Random presence check issued.", "success")
    return redirect(url_for("teacher.live_students", session_id=session.id))


@teacher_bp.route("/report")
@login_required
def report():
    if not teacher_required():
        return redirect(url_for("student.dashboard"))

    selected_date = request.args.get("date")
    selected_student = request.args.get("student_id", type=int)

    q = (
        db.session.query(AttendanceRecord, ClassSession, User)
        .join(ClassSession, AttendanceRecord.session_id == ClassSession.id)
        .join(User, AttendanceRecord.student_id == User.id)
        .filter(ClassSession.teacher_id == current_user.id)
    )
    if selected_date:
        q = q.filter(func.date(ClassSession.started_at) == selected_date)
    if selected_student:
        q = q.filter(User.id == selected_student)
    rows = q.order_by(ClassSession.started_at.desc()).all()

    students = (
        User.query.filter_by(role="student").order_by(User.full_name.asc()).all()
    )
    return render_template(
        "teacher/report.html",
        rows=rows,
        students=students,
        selected_date=selected_date,
        selected_student=selected_student,
    )


@teacher_bp.route("/report/export")
@login_required
def export_report():
    if not teacher_required():
        return redirect(url_for("student.dashboard"))
    rows = (
        db.session.query(AttendanceRecord, ClassSession, User)
        .join(ClassSession, AttendanceRecord.session_id == ClassSession.id)
        .join(User, AttendanceRecord.student_id == User.id)
        .filter(ClassSession.teacher_id == current_user.id)
        .order_by(ClassSession.started_at.desc())
        .all()
    )
    csv_lines = [
        "student_name,student_email,session_title,room,date,entry_time,exit_time,total_minutes,status"
    ]
    for rec, session, student in rows:
        csv_lines.append(
            ",".join(
                [
                    student.full_name,
                    student.email,
                    session.title,
                    session.room,
                    session.started_at.date().isoformat(),
                    rec.entry_time.isoformat() if rec.entry_time else "",
                    rec.exit_time.isoformat() if rec.exit_time else "",
                    str(round(rec.total_minutes, 2)),
                    rec.status,
                ]
            )
        )

    return Response(
        "\n".join(csv_lines),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance_report.csv"},
    )
