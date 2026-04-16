# Heroku Deployment Guide for Siinqee Bank KMS

## Prerequisites
✅ Heroku account with student credits
✅ Heroku CLI installed
✅ Git installed
✅ App already created on Heroku dashboard

## Deployment Steps

### 1. Initialize Git (if not already done)
```bash
git init
git add .
git commit -m "Initial commit - Siinqee Bank KMS"
```

### 2. Connect to your Heroku app
Replace `your-app-name` with your actual Heroku app name:
```bash
heroku git:remote -a your-app-name
```

### 3. Set environment variable (CRITICAL!)
```bash
heroku config:set GROQ_API_KEY=your_actual_groq_api_key_here
```

### 4. Deploy to Heroku
```bash
git push heroku main
```
OR if your branch is named `master`:
```bash
git push heroku master
```

### 5. Open your app
```bash
heroku open
```

## Verify Deployment
```bash
heroku logs --tail
```

## Your app will be live at:
https://your-app-name.herokuapp.com

## Files Created for Deployment:
✅ Procfile - Tells Heroku how to run the app
✅ runtime.txt - Specifies Python version
✅ .gitignore - Excludes sensitive files
✅ main.py - Updated to read PORT from environment

## Troubleshooting
- If deployment fails, check logs: `heroku logs --tail`
- Verify GROQ_API_KEY is set: `heroku config`
- Ensure all files are committed: `git status`

## Team Access
Share the Heroku app URL with your team members!
