# Prism Live — Admin Approval Upgrade

This upgrade keeps the existing Flask website/templates and adds role-based admin pages.

## Roles
- `user`: regular registered account.
- `admin`: can view the admin dashboard and submit change requests.
- `superadmin`: owner account; can review requests, manage user/admin roles, activate/deactivate accounts, and view the contact inbox.

## Run locally (Windows / VS Code)
1. Make a backup of your current project folder and database.
2. Extract this ZIP to a new folder. Do not copy your old `.venv` or `.git` folders.
3. Open the extracted folder in VS Code.
4. In the terminal, create a virtual environment if needed: `py -m venv .venv`
5. Activate it: PowerShell `.venv\Scripts\Activate.ps1` (or Command Prompt `.venv\Scripts\activate.bat`).
6. Install dependencies: `pip install -r requirements.txt`
7. Create the owner account: `python create_superadmin.py`. Use a strong password of at least 12 characters. This script creates `prismlive.db` if it does not exist.
8. Start the site: `python app.py`
9. Open `http://127.0.0.1:10000/login` and sign in using the Super Admin credentials.
10. Admin dashboard URL: `http://127.0.0.1:10000/admin`.

## Existing database
`db.py` adds `role` and `is_active` columns safely when an older database is present. Back up `prismlive.db` before running. Existing accounts default to `user`; run `python create_superadmin.py` to promote the owner account. Do not delete an existing production database.

## Approval workflow limitation
An admin's request is stored as pending; the Super Admin can approve or reject it. Approval is an audit/decision record and does not automatically rewrite arbitrary website code. For production, connect specific approved request types to a controlled content-management action (for example, updating a workshop title/description in a database table). Do not expose arbitrary Python/code execution through the web dashboard.

## Production checklist
- Set a long random `SECRET_KEY` in Render environment variables; never use a development fallback in production.
- Set `COOKIE_SECURE=1` when HTTPS is enabled.
- Use persistent storage or a managed production database; ephemeral SQLite files may be lost on redeploy.
- Use a persistent Socket.IO-compatible deployment strategy for real-time chat; in-memory online presence only works reliably in a single process.
- Add CSRF protection and rate limiting before public production use.
- Keep the source code in a private Git repository and restrict deployment permissions to trusted maintainers.
