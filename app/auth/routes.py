from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from datetime import timedelta, timezone
from flask import current_app

from app import db
from app.models import ClassSession, User, utcnow


auth_bp = Blueprint("auth", __name__)


def _as_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "teacher":
            return redirect(url_for("teacher.dashboard"))
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        if role not in {"student", "teacher"}:
            role = "student"

        if not all([full_name, email, password]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("auth/register.html")

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        flash("Login successful.", "success")
        if user.role == "teacher":
            return redirect(url_for("teacher.dashboard"))
        return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/scan/<int:session_id>")
@login_required
def scan_session(session_id: int):
    if current_user.role != "student":
        flash("Only students can mark attendance from scan link.", "danger")
        return redirect(url_for("teacher.dashboard"))
    session = ClassSession.query.get_or_404(session_id)
    if not session.is_active:
        flash("This class session is closed.", "warning")
        return redirect(url_for("student.dashboard"))
    window_minutes = current_app.config.get("QR_SCAN_ENTRY_WINDOW_MINUTES", 10)
    started_at = _as_utc(session.started_at)
    now_utc = _as_utc(utcnow())
    expires_at = started_at + timedelta(minutes=window_minutes)
    is_expired = now_utc > expires_at
    return render_template(
        "student/scan_session.html",
        session=session,
        entry_window_minutes=window_minutes,
        scan_window_expired=is_expired,
    )
