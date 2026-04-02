# 🚀 Render Deployment Guide - Smart Attendance System

## Quick Deploy Steps

### 1️⃣ Push to GitHub (Already Done ✅)
Your code is already on GitHub:
```
https://github.com/sakshidehankar5-lab/GPS-Based-Smart-Attendance
```

### 2️⃣ Create Render Account
- Go to: https://render.com
- Sign up with GitHub account
- Authorize Render to access your repositories

### 3️⃣ Deploy Web Service

#### Option A: Using render.yaml (Recommended)
1. Go to Render Dashboard
2. Click "New" → "Blueprint"
3. Connect your GitHub repository: `GPS-Based-Smart-Attendance`
4. Render will automatically detect `render.yaml`
5. Click "Apply" - It will create both web service and database!

#### Option B: Manual Setup
1. Go to Render Dashboard: https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `GPS-Based-Smart-Attendance`
4. Configure:
   - **Name:** smart-attendance-system
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
   - **Instance Type:** Free

### 4️⃣ Add Environment Variables
In Render dashboard, add these environment variables:

```
SECRET_KEY = (auto-generate or use random string)
DATABASE_URL = (will be auto-set if using PostgreSQL)
CLASSROOM_RADIUS_METERS = 200
DISABLE_LOCATION_CHECK = true
QR_SCAN_ENTRY_WINDOW_MINUTES = 10
PRESENCE_TIMEOUT_MINUTES = 5
```

### 5️⃣ Add PostgreSQL Database (Optional but Recommended)
1. In Render Dashboard → "New +" → "PostgreSQL"
2. Name: `attendance-db`
3. Database: `attendance`
4. User: `attendance_user`
5. Copy the "Internal Database URL"
6. Add it as `DATABASE_URL` in your web service environment variables

### 6️⃣ Deploy!
- Click "Create Web Service"
- Wait 5-10 minutes for deployment
- Your app will be live at: `https://your-app-name.onrender.com`

## 🔧 Important Notes

### Database Migrations
After first deployment, run migrations:
1. Go to Render Dashboard → Your Service → Shell
2. Run:
```bash
flask db upgrade
```

### Free Tier Limitations
- App sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- 750 hours/month free

### Custom Domain (Optional)
- Go to Settings → Custom Domain
- Add your domain
- Update DNS records as shown

## 🎯 Post-Deployment

### Test Your App
1. Visit: `https://your-app-name.onrender.com`
2. Register a teacher account
3. Create a session
4. Test QR scanning

### Update APP_BASE_URL
After deployment, update environment variable:
```
APP_BASE_URL = https://your-app-name.onrender.com
```

## 🐛 Troubleshooting

### Build Fails
- Check `requirements.txt` is correct
- Verify Python version in `runtime.txt`
- Check logs in Render dashboard

### Database Connection Error
- Verify `DATABASE_URL` is set correctly
- Run migrations: `flask db upgrade`
- Check PostgreSQL is running

### App Not Loading
- Check logs in Render dashboard
- Verify `gunicorn run:app` command
- Ensure port binding is correct (Render auto-assigns)

## 📱 Share Your App
Once deployed, share the URL:
```
https://your-app-name.onrender.com
```

Students can scan QR codes from anywhere in India! 🇮🇳

## 🔄 Auto-Deploy
Every time you push to GitHub main branch, Render will automatically redeploy!

```bash
git add .
git commit -m "Update"
git push origin main
```

---

**Need Help?** Check Render docs: https://render.com/docs
