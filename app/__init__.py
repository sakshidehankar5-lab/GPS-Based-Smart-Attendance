from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.student.routes import student_bp
    from app.teacher.routes import teacher_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    @app.cli.command("create-admin")
    def create_admin():
        from app.models import User

        email = "admin@school.com"
        existing = User.query.filter_by(email=email).first()
        if existing:
            print("Admin already exists: admin@school.com / admin123")
            return
        admin = User(full_name="System Admin", email=email, role="teacher")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Created admin: admin@school.com / admin123")

    @app.cli.command("create-student")
    def create_student():
        from app.models import User

        email = "student@school.com"
        existing = User.query.filter_by(email=email).first()
        if existing:
            print("Student already exists: student@school.com / student123")
            return
        student = User(full_name="Demo Student", email=email, role="student")
        student.set_password("student123")
        db.session.add(student)
        db.session.commit()
        print("Created student: student@school.com / student123")

    return app
