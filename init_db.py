"""
Database initialization script for Render deployment
Run this to ensure all tables are created
"""

from app import create_app, db
from app.models import User, ClassSession, AttendanceRecord, PresencePing

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ All database tables created successfully!")
    
    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Created tables: {', '.join(tables)}")
    
    # Create demo admin if doesn't exist
    admin = User.query.filter_by(email="admin@demo.com").first()
    if not admin:
        admin = User(
            full_name="Admin User",
            email="admin@demo.com",
            role="teacher"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("\n✅ Demo admin created: admin@demo.com / admin123")
    else:
        print("\n⚠️ Admin already exists")
    
    print("\n🎉 Database initialization complete!")
