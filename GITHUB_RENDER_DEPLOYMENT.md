# Prism Live — GitHub + Live Deployment Guide

This guide uploads the Flask project to GitHub and deploys it to Render so users can access it through a public URL.

## 1. What is included

- Original Prism Live HTML/CSS templates and images
- Flask registration/login and session handling
- Flask-SocketIO private chat
- SQLite schema and Super Admin setup script
- Render configuration and environment example

The local virtual environment and local SQLite database are intentionally excluded. Never upload `.env`, passwords, secret keys, or a live user database to GitHub.

## 2. Run locally first (Windows / VS Code)

Open this folder in VS Code: the folder containing `app.py`.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python db.py
python app.py
```

Open `http://127.0.0.1:10000` (or the port printed in the terminal). Create two test users using different email addresses. Open the chat as each user in separate browsers or one normal and one incognito window.

To create the owner account locally:

```powershell
python create_superadmin.py
```

Use a strong password (12+ characters). Sign in at `/login`; the Super Admin dashboard is at `/admin`.

## 3. Create a GitHub repository

1. Sign in to GitHub.
2. Click **+ → New repository**.
3. Choose a repository name such as `PrismLive`.
4. Choose **Private** if the source should not be public.
5. Create the repository empty. Do not add a README if this project already contains one.
6. Copy the repository HTTPS URL.

## 4. Push the project from VS Code

Open a terminal in the folder containing `app.py`. Run:

```powershell
git init
git add .
git status
git commit -m "Prepare Prism Live for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPOSITORY` with your own values.

Before `git commit`, inspect `git status`. It must not show `.venv`, `.env`, or `prismlive.db`. The included `.gitignore` excludes them. If a remote already exists, use:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

If Git asks who you are, set your commit identity:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

For later updates:

```powershell
git add .
git commit -m "Describe your update"
git push
```

## 5. Deploy the live website with Render

1. Sign in to Render and choose **New + → Web Service**.
2. Connect your GitHub account and select the PrismLive repository.
3. Use these settings:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --worker-class gthread --threads 100 app:app`
   - Health check path: `/home`
4. Set `SECRET_KEY` to a long, random, private value. Do not commit it to GitHub.
5. Set `COOKIE_SECURE` to `1` when using the HTTPS public URL.
6. Deploy and open the public `https://...onrender.com` URL.
7. Test registration/login in two separate browsers and send a chat message between accounts.

The repository includes `render.yaml`; if Render offers a Blueprint deployment, review its service and environment settings before creating it.

## 6. Important: make user accounts and chat persistent

The current application uses SQLite by default. On many hosted services, files on the app filesystem can be replaced or lost during redeploy/restart unless a persistent disk is configured. Do not assume that the local SQLite database is automatically available online.

For a real public site, use a managed PostgreSQL database and update the app's database layer to PostgreSQL, or configure a persistent disk for SQLite if the host and service plan support it. Back up data before migrations. Do not upload the local database to GitHub.

For a single Render service, the current Socket.IO threading setup can support real-time chat, subject to host configuration. If you scale to multiple app instances, configure a shared Socket.IO message queue and shared presence storage; in-memory online-user status is only per process.

## 7. How the real-time chat works

1. User A registers and logs in.
2. User B registers and logs in from another device/browser.
3. Both open **Chat**.
4. Socket.IO authenticates the connection using the Flask session.
5. A message is stored in the database and emitted to the recipient's private room.
6. The recipient's open chat receives the `new_message` event without refreshing.

The current application has real-time chat code already. GitHub alone does not make a local server public; deploying the application is required.

## 8. Admin roles

- `user`: normal account and chat access
- `admin`: admin dashboard and change-request submission
- `superadmin`: owner-level account and role controls

Create the Super Admin account on the environment/database that will be used by the deployed site. Running `create_superadmin.py` on your own computer only creates the account in your local database, not automatically in the hosted database.

## 9. Production security checklist

- Use HTTPS and a strong private `SECRET_KEY`.
- Never commit `.env`, passwords, database files, or credentials.
- Enable CSRF protection for form submissions before public production use.
- Add login rate limits and email verification if appropriate.
- Back up persistent database data.
- Test user isolation: one user must not be able to read another user's private conversations.
- Keep source-code changes under trusted repository/developer control.
