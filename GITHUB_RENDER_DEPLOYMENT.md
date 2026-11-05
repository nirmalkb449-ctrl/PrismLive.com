# PrismLive: GitHub and Render deployment

See `README.md` for the full run, GitHub push, Render Blueprint, database persistence, and production checklist. This file is a quick reference.

## GitHub push (PowerShell or VS Code terminal)

Run from the extracted folder containing `app.py`:

```bash
git init
git add .
git status
git commit -m "Deploy responsive PrismLive"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the GitHub placeholders. Do not commit `.env`, `.venv`, `*.db`, API keys, or passwords. `.gitignore` excludes these.

## Render

1. Push the code to GitHub.
2. In Render, choose **New + → Blueprint**.
3. Connect the repository and confirm `render.yaml`.
4. The blueprint creates a paid Starter web service and a 1 GB persistent disk for the SQLite database. A Free web service has ephemeral storage and is not appropriate for retaining this SQLite user database.
5. Deploy and open the service's generated `onrender.com` URL.
6. Optionally add `GEMINI_API_KEY`, `UPI_ID`, and `UPI_PAYEE_NAME` in Render Environment settings.
7. Create the Super Admin using Render Shell: `python create_superadmin.py`.

The service is configured to use `/var/data/prismlive.db`; only data under the attached `/var/data` disk persists. This SQLite setup is single-instance only. For horizontal scaling, migrate to managed PostgreSQL and shared Socket.IO infrastructure.
