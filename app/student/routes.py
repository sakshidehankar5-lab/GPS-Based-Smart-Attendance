from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.models import AttendanceRecord, ClassSession


student_bp = Blueprint("student", __name__, url_prefix="/student")


def student_required():
    if current_user.role != "student":
        flash("Student access required.", "danger")
        return False
    return True


@student_bp.route("/dashboard")
@login_required
def dashboard():
    if not student_required():
        return redirect(url_for("teacher.dashboard"))

    active_sessions = ClassSession.query.filter_by(is_active=True).all()
    my_records = (
        AttendanceRecord.query.filter_by(student_id=current_user.id)
        .order_by(AttendanceRecord.entry_time.desc())
        .all()
    )
    by_date = (
        AttendanceRecord.query.with_entities(
            func.date(AttendanceRecord.entry_time), func.sum(AttendanceRecord.total_minutes)
        )
        .filter(AttendanceRecord.student_id == current_user.id)
        .group_by(func.date(AttendanceRecord.entry_time))
        .all()
    )
    labels = [str(row[0]) for row in by_date][::-1]
    values = [float(row[1] or 0) for row in by_date][::-1]

    return render_template(
        "student/dashboard.html",
        active_sessions=active_sessions,
        my_records=my_records[:10],
        chart_labels=labels,
        chart_values=values,
    )


@student_bp.route("/history")
@login_required
def history():
    if not student_required():
        return redirect(url_for("teacher.dashboard"))
    selected_date = request.args.get("date")
    q = (
        AttendanceRecord.query.join(ClassSession)
        .filter(AttendanceRecord.student_id == current_user.id)
    )
    if selected_date:
        q = q.filter(func.date(AttendanceRecord.entry_time) == selected_date)
    records = q.order_by(AttendanceRecord.entry_time.desc()).all()
    return render_template(
        "student/history.html",
        records=records,
        selected_date=selected_date,
    )


@student_bp.route("/scan")
@login_required
def scan():
    if not student_required():
        return redirect(url_for("teacher.dashboard"))
    return render_template("student/scan.html")
