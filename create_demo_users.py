"""
Demo Users Creation Script
Run this after deployment to create test accounts
"""

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Create Teacher Account
    teacher = User.query.filter_by(email="teacher@demo.com").first()
    if not teacher:
        teacher = User(
            full_name="Demo Teacher",
            email="teacher@demo.com",
            role="teacher"
        )
        teacher.set_password("teacher123")
        db.session.add(teacher)
        print("✅ Teacher account created: teacher@demo.com / teacher123")
    else:
        print("⚠️ Teacher account already exists")

    # Create Student Accounts
    students = [
        {"name": "Rahul Kumar", "email": "rahul@demo.com"},
        {"name": "Priya Sharma", "email": "priya@demo.com"},
        {"name": "Amit Patel", "email": "amit@demo.com"},
        {"name": "Sneha Singh", "email": "sneha@demo.com"},
        {"name": "Rohan Verma", "email": "rohan@demo.com"},
    ]

    for student_data in students:
        student = User.query.filter_by(email=student_data["email"]).first()
        if not student:
            student = User(
                full_name=student_data["name"],
                email=student_data["email"],
                role="student"
            )
            student.set_password("student123")
            db.session.add(student)
            print(f"✅ Student account created: {student_data['email']} / student123")
        else:
            print(f"⚠️ Student {student_data['email']} already exists")

    db.session.commit()
    print("\n🎉 All demo accounts created successfully!")
    print("\n📋 Demo Credentials:")
    print("\nTeacher:")
    print("  Email: teacher@demo.com")
    print("  Password: teacher123")
    print("\nStudents (all use password: student123):")
    for s in students:
        print(f"  - {s['email']}")
