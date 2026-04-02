# 🎭 Demo Accounts for Presentation

## 📋 Pre-Created Demo Accounts

### 👨‍🏫 Teacher Account
```
Email: teacher@demo.com
Password: teacher123
```

### 👨‍🎓 Student Accounts (All use password: student123)

1. **Rahul Kumar**
   - Email: `rahul@demo.com`
   - Password: `student123`

2. **Priya Sharma**
   - Email: `priya@demo.com`
   - Password: `student123`

3. **Amit Patel**
   - Email: `amit@demo.com`
   - Password: `student123`

4. **Sneha Singh**
   - Email: `sneha@demo.com`
   - Password: `student123`

5. **Rohan Verma**
   - Email: `rohan@demo.com`
   - Password: `student123`

---

## 🚀 How to Create Demo Accounts

### After Deployment:

**Option 1: Run Script Locally**
```bash
python create_demo_users.py
```

**Option 2: Manual Registration**
1. Go to: `https://your-app-url/auth/register`
2. Fill details:
   - Full Name: Student Name
   - Email: student@example.com
   - Password: student123
   - Role: Student
3. Click Register

---

## 🎯 For Presentation Demo:

### Teacher Flow:
1. Login as: `teacher@demo.com` / `teacher123`
2. Create a new session
3. Generate QR code
4. Show QR to students

### Student Flow:
1. Students login with their credentials
2. Scan QR code
3. Attendance marked automatically

---

## 📱 Quick Test Accounts

**For quick testing, use:**

**Teacher:**
- Email: `teacher@demo.com`
- Password: `teacher123`

**Student:**
- Email: `rahul@demo.com`
- Password: `student123`

---

## ⚠️ Important Notes:

1. **First Time Setup:**
   - After deployment, run `create_demo_users.py` to create accounts
   - Or manually register accounts

2. **Database:**
   - SQLite: Accounts stored locally
   - PostgreSQL: Accounts stored in cloud database

3. **Reset:**
   - Delete database file to reset all accounts
   - Or use admin panel (if available)

---

## 🔐 Security Note:

**These are DEMO accounts only!**
- Don't use in production
- Change passwords for real deployment
- Use strong passwords for actual users

---

## 📞 Need More Accounts?

Edit `create_demo_users.py` and add more students to the list!
