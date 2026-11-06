# PrismLive — consolidated project (four ZIP packages merged)

This is the single consolidated PrismLive project. Open the `PrismLive_Merged` folder in VS Code — the folder containing `app.py`.

## Included modules
- Original PrismLive Flask website pages, templates and supplied images.
- Responsive/mobile stylesheet (`static/css/mobile-responsive.css`).
- Registration/login with password hashing and SQLite storage.
- Member-to-member real-time chat using Flask-SocketIO.
- Prism AI Gemini assistant endpoint and widget (integrated into the existing Flask app).
- Login-protected UPI intent payment page.
- Admin dashboard with a Super Admin approval workflow for admin change requests.
- Render deployment files, health check, environment example and setup scripts.
- `docs/` contains the standalone chatbot blueprint from the separate chatbot ZIP for reference. It is not registered as a second Flask app; the live endpoint is already integrated in `app.py`.

## Run locally on Windows / VS Code

1. Install Python 3.11 and Git.
2. Extract the ZIP.
3. In VS Code, choose **File → Open Folder** and open `PrismLive_Merged`.
4. Open **Terminal → New Terminal** and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

5. Open `.env`. Set a long random `SECRET_KEY`. For the AI assistant, add your private `GEMINI_API_KEY`. For UPI intent, set your merchant `UPI_ID` and `UPI_PAYEE_NAME`.
6. Initialize the database and create the first Super Admin:

```powershell
python db.py
python create_superadmin.py
```

7. Start the website:

```powershell
python app.py
```

8. Visit `http://127.0.0.1:10000`.

If PowerShell blocks virtual-environment activation, run this once in that terminal, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Important configuration and safety notes

- Never upload `.env`, API keys, passwords, or `prismlive.db` to GitHub. `.gitignore` excludes local secrets/database files.
- `GEMINI_API_KEY` is a server-side secret. Never paste it into HTML or JavaScript.
- The payment page creates a UPI payment intent/link only. It does not verify that money was received. Do not mark orders paid based only on a redirect, screenshot, or user claim. For verified online payments, integrate a payment gateway with signed webhooks.
- The Render configuration uses a persistent disk path for SQLite. A persistent disk requires a Render service plan that supports disks. If deploying on a plan without a persistent disk, SQLite data may be lost on redeploy/restart; use a managed PostgreSQL database for durable production data.
- The Super Admin approval workflow records and approves/rejects requests. Approval does not automatically deploy arbitrary code or apply every requested website change; the corresponding approved change still needs to be implemented.
- The current Socket.IO online-presence set is in process memory. For multi-instance scaling, configure a shared message queue and compatible persistent database.

## Replace old GitHub project files with this consolidated project

**Recommended: keep the same GitHub repository and replace its tracked files from your local clone.** Do not delete the repository itself.

1. Download/clone your existing GitHub repository. In GitHub, open the repository, click **Code → HTTPS**, and copy its URL.
2. In VS Code terminal, run (replace the URL):

```powershell
cd $HOME\Desktop
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

3. Extract this new ZIP. Open the extracted `PrismLive_Merged` folder in File Explorer.
4. Open the cloned repository folder in another File Explorer window.
5. In the cloned repository folder, delete the old project files and folders **but keep the hidden `.git` folder**. Do not delete `.git`.
6. Copy everything inside `PrismLive_Merged` (including `app.py`, `db.py`, `templates`, `static`, `requirements.txt`, `Procfile`, `render.yaml`, `.gitignore`, and `docs`) into the cloned repository folder.
7. Open the cloned repository folder in VS Code. Confirm `app.py` is directly in the opened folder, not nested one extra level.
8. In Terminal run:

```powershell
git status
git add -A
git status
git commit -m "Replace old PrismLive project with consolidated version"
git push origin main
```

If your default branch is not `main`, replace `main` with the branch shown on GitHub. If Git says there is no remote named `origin`, add it:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

If `origin` already points to a different repository, update it:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

If GitHub rejects the push because the remote contains commits you do not have, first run:

```powershell
git pull --rebase origin main
```

Resolve any conflicts, then push again. Do not use `git push --force` unless you intentionally want to overwrite remote history.

## Alternative: replace through GitHub website

You can delete old files from the GitHub **Code** tab using the file's delete/trash option, but this is slow for a full project and can cause mistakes. The local clone method above is recommended because `git add -A` records both deleted old files and added new files in one commit.

## Deploy the updated repository on Render

1. Open Render Dashboard and select your existing PrismLive web service.
2. Confirm it is connected to the same GitHub repository and the correct branch.
3. Choose **Manual Deploy → Deploy latest commit** (or wait for automatic deploy).
4. Check the deploy logs for `Build successful` and a healthy service.
5. Set/verify environment variables in Render: `SECRET_KEY`, `COOKIE_SECURE=1`, `GEMINI_API_KEY` (optional), `GEMINI_MODEL`, `UPI_ID`, and `UPI_PAYEE_NAME`.
6. Ensure the SQLite `DATABASE_PATH` matches the mounted persistent disk. Keep a backup of any existing production database before changing database paths or replacing the app.


## Account registration, login and password reset

- Registration is handled by `POST /register`; passwords are stored as Werkzeug password hashes.
- Login is handled by `POST /login`. The registration/login cross-links now use Flask `url_for()` routes rather than static `.html` filenames.
- Forgot password: open `/forgot-password`, submit the registered email, then use the one-time link delivered by email. The link expires after 30 minutes and can only be used once.
- The reset token is stored as a SHA-256 hash in SQLite; the new password is hashed before it replaces the old hash. All outstanding reset links for that account are invalidated after a successful reset.
- Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` or `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD`, and `MAIL_DEFAULT_SENDER` in local `.env` and in Render Environment. For Gmail, enable 2-Step Verification and create an App Password; do not use your normal Gmail password.
- Email sending requires working SMTP credentials and an email provider that permits SMTP. Test the reset flow after deploying; do not publish SMTP credentials or commit `.env`.

## Before making the site public
- Test registration, login, logout, user-to-user chat, AI chat, payment intent, and admin approval.
- Create the Super Admin account securely; do not publish its credentials.
- Configure real UPI merchant details only if authorized. For automatic payment confirmation, add a gateway and webhook verification.

### Configure email on Render

1. Open Render Dashboard → your PrismLive web service → **Environment**.
2. Add `MAIL_SERVER` = `smtp.gmail.com`, `MAIL_PORT` = `587`, `MAIL_USE_TLS` = `1`, `MAIL_USE_SSL` = `0`.
3. Add `MAIL_USERNAME` = your full Gmail address.
4. Add `MAIL_PASSWORD` = the Google App Password (16 characters). Create it in your Google Account after enabling 2-Step Verification.
5. Add `MAIL_DEFAULT_SENDER` = `Prism Live <your-full-gmail-address>`.
6. Save changes and redeploy/restart the service.
7. Visit `/forgot-password`, submit a registered email, and confirm that the email arrives. Open the link, set a new password, and sign in with it.

Do not add quotation marks around environment values in Render. Never put SMTP passwords in HTML, JavaScript, GitHub, or this README.
