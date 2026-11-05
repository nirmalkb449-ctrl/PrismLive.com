# PrismLive — responsive Flask website

This package keeps the supplied PrismLive pages, branding, images, and features, and adds a responsive/touch-friendly stylesheet plus corrected deployment configuration.

## Included

- Original PrismLive templates, images, CSS and JavaScript
- Flask application with registration, login/logout, admin dashboard, contact form, chat and optional Gemini AI endpoint
- SQLite schema initialization (`db.py`)
- Mobile/tablet responsive layer (`static/css/mobile-responsive.css`)
- Render Blueprint (`render.yaml`), Procfile, environment example and deployment guide

## Important fixes made

1. Corrected Flask static-file configuration. The supplied app pointed Flask's static endpoint at an `images` folder, but its CSS and JavaScript are stored in `static/`; this could break CSS/JS loading.
2. Added a responsive/touch stylesheet to every page and ensured each page has a viewport meta tag. Original design assets and page templates are retained.
3. Added `/healthz` for Render health checks.
4. Corrected Render YAML indentation and configured a Gunicorn threaded start command suitable for the current Flask-SocketIO setup.
5. Removed `.git`, `.venv`, bytecode, and the local SQLite database from the distributable archive. Never deploy a local development database or secrets from a ZIP.
6. Made production startup require a configured secret key; Render Blueprint generates one automatically.

## Run locally on Windows

Open this folder in VS Code (the folder containing `app.py`) and run in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python db.py
python app.py
```

Open `http://127.0.0.1:10000`. Edit `.env` and set a private `SECRET_KEY` before using the app beyond local testing. For example, generate one with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Create the owner/admin account from the project folder with:

```powershell
python create_superadmin.py
```

Use a unique email and a strong password of at least 12 characters. Do not share the password.

## Push to GitHub

1. Extract this ZIP.
2. Open the extracted `PrismLive` folder in VS Code.
3. Create an empty GitHub repository (for example, `PrismLive`).
4. In the VS Code terminal, make sure the current directory contains `app.py`, then run:

```bash
git init
git add .
git status
git commit -m "Prepare PrismLive responsive website for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the placeholders with your own GitHub username and repository. Check `git status` before committing: `.env`, `.venv`, `*.db` and secrets must not be included. If `origin` already exists, use `git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git` instead of adding it again.

## Deploy on Render

The included `render.yaml` is a Render Blueprint for a Flask web service. It configures Python, dependencies, Gunicorn, `/healthz`, a generated `SECRET_KEY`, HTTPS-only session cookies, and a persistent disk mounted at `/var/data` for SQLite.

1. Push the project to GitHub as above.
2. Sign in at https://render.com and connect your GitHub account.
3. In Render, choose **New + → Blueprint** (or create a Web Service and connect the repository).
4. Select the repository and confirm the `render.yaml` settings.
5. The Blueprint requests a **Starter paid web service** because the SQLite database needs a persistent disk. Render persistent disks are available on paid web services; the disk is not available on the Free plan.
6. Deploy. Render will install dependencies and start the app. Open the generated `https://prismlive.onrender.com` URL (the exact hostname may differ if already taken).
7. In the service's Environment page, optionally add `GEMINI_API_KEY`, `GEMINI_MODEL`, `UPI_ID`, and `UPI_PAYEE_NAME` if you use those features. Keep all keys private.
8. Create the first Super Admin account using Render Shell: run `python create_superadmin.py`, then follow the prompts. If Shell is not available on your plan, use a secure one-off local/admin provisioning process before opening admin functions publicly; do not put admin credentials in source code.

### Render database warning

Render's default filesystem is ephemeral. This configuration attaches a persistent disk and points `DATABASE_PATH` to `/var/data/prismlive.db`, so user registrations and messages persist across restarts/deploys. Persistent disks are paid, attach to one service instance, and prevent zero-downtime deploys. For a scalable multi-instance production deployment, migrate from SQLite to Render Postgres and configure a shared Socket.IO message queue/presence store. Do not scale this SQLite+disk setup horizontally.

### Socket.IO / chat note

The current application stores chat messages in SQLite and tracks online users in process memory. It is designed for a single running web-service instance. Multi-instance scaling requires shared presence and a Socket.IO message queue.

## Environment variables

See `.env.example`. On Render, use the service's Environment page. Never commit `.env`, passwords, database files, or API keys.

## Before public launch

- Test registration, login, logout, forms, chat, admin permissions, and AI/payment options.
- Configure a private `SECRET_KEY` (the Blueprint generates one).
- Create the Super Admin account securely.
- Add the Gemini API key only if you want the AI chat enabled.
- Configure actual merchant UPI details only if you accept payments. The UPI link only launches a payment app; it does not verify or reconcile payment. Do not treat a redirect as proof of payment.
- Review all content, external image/font/CDN dependencies, privacy notice, terms, and contact details.
