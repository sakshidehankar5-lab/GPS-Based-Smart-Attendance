# Smart Attendance System (Flask)

Full-stack smart attendance platform with role-based dashboards for Students and Teachers/Admins, QR-based entry, location-based continuous verification, auto-exit, and attendance duration calculation.

## Tech Stack
- Backend: Flask, Flask-SQLAlchemy, Flask-Login
- DB: PostgreSQL / MySQL (SQLite default for local run)
- Frontend: HTML, Bootstrap 5, JavaScript
- Charts: Chart.js
- QR: `qrcode` Python library

## Features Implemented

### Student
- Register / login authentication
- QR token based attendance entry
- Duplicate entry prevention for same session
- Continuous GPS presence pings
- Auto exit when outside classroom radius
- Attendance history and date filter
- Mobile-friendly dashboard with chart

### Teacher/Admin
- Start class session with geofence center and radius
- Generate QR token/QR image at class start
- Live student monitoring table
- Trigger random presence checks
- End session and close active entries
- Date/student filtered attendance reports
- CSV export for attendance records
- Dashboard statistics and charts

## Project Structure
```text
att_ai/
  app/
    __init__.py
    models.py
    api/routes.py
    auth/routes.py
    student/routes.py
    teacher/routes.py
    utils/geo.py
    static/css/style.css
    static/js/main.js
    templates/
      base.html
      auth/*.html
      student/*.html
      teacher/*.html
  config.py
  run.py
  requirements.txt
  .env.example
```
🚀 Built a Smart Attendance System using GPS + QR + Real-Time Validation

Tired of proxy attendance & manual tracking?
So I built something smarter 👇

🔗 GitHub: https://github.com/sakshidehankar5-lab/GPS-Based-Smart-Attendance
🌐 Live Demo: https://gps-based-smart-attendance-8umg.onrender.com

💡 **The Idea**
Traditional attendance systems are slow, error-prone, and easy to manipulate.
This project solves that using **location + time + authentication**.

⚙️ **Key Features**
📍 GPS-based verification (student must be physically present)
📱 QR-based quick attendance
⏱️ Time-restricted entry (no late marking)
👨‍🏫 Admin approval system
📊 Dashboard for tracking & analytics

📌 **How it Works**
1️⃣ Teacher creates session
2️⃣ QR generated (time-limited)
3️⃣ Student scans QR
4️⃣ System verifies GPS + time → marks attendance

👉 This ensures **zero proxy & real-time accuracy**

🧠 **Tech Stack**
Frontend: HTML, CSS, JS
Backend: (Your stack)
Deployment: Render

💥 **Why this matters?**
Smart attendance systems using GPS & real-time validation can **eliminate manual errors and fake entries completely** ()

🎯 **Use Cases**
✔️ Colleges & Schools
✔️ Coaching Institutes
✔️ Offices / Field Teams
✔️ Events & Workshops

🚧 **What’s next?**

* Face recognition integration
* Mobile app version
* AI-based anomaly detection

---

💬 I’d love your feedback!
⭐ Star the repo if you like it
🤝 Open to collaboration

#AI #Startup #WebDevelopment #India #OpenSource #StudentProject #GPS #TechInnovation #BuildInPublic

- Enforce HTTPS to protect location/session traffic.
