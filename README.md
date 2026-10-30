# PrismLive — merged website + AI assistant + UPI intent page

This folder combines the uploaded Flask/SQLite/Flask-SocketIO PrismLive project with the Prism AI chatbot integration and requested UI/backend updates.

## What was changed
- Integrated the Prism AI Gemini endpoint into the existing Flask app (no second Flask app).
- Added the Prism AI widget to the existing member live-chat page. Member-to-member Socket.IO messaging remains separate.
- Added a right-side, icon-only Live Chat shortcut on the home page for signed-in users; removed the text Live Chat link from the top navbar.
- Rebuilt registration fields as first name, last name, email, interest, password, confirm password, and one Terms checkbox. Server validates matching passwords and stores interest.
- Added a login-protected Payment page that creates a UPI intent using `UPI_ID` and `UPI_PAYEE_NAME`.
- Added environment examples and `.gitignore` protections.

## Run in VS Code (Windows)
1. Extract this ZIP.
2. Open the `PrismLive_ones` folder in VS Code (File → Open Folder).
3. Open Terminal → New Terminal.
4. Run:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.
5. Copy `.env.example` to `.env` and set a long random `SECRET_KEY`.
6. For AI, set `GEMINI_API_KEY` from Google AI Studio. Optional `GEMINI_MODEL` defaults to `gemini-2.5-flash`.
7. For UPI intent generation, set your real merchant `UPI_ID` and `UPI_PAYEE_NAME`. Do not use a personal UPI ID for a public business without confirming the account is authorized to receive payments.
8. Start:
   ```powershell
   python app.py
   ```
9. Open http://127.0.0.1:10000/

You can also double-click `run_local.bat` to create the virtual environment, install dependencies, and start the app.

## Important payment limitation
The payment page generates a UPI deep link only. A successful app launch, screenshot, or user click is NOT proof that funds were received. It does not automatically update payment status. For real commerce, integrate a payment gateway (for example Razorpay) with server-created orders, signature validation, and verified webhooks before marking any payment as paid. Never collect a UPI PIN or OTP.

## Gemini setup
Create an API key at https://aistudio.google.com/ and store it only in server environment / `.env`. Never expose it in HTML or JavaScript and never commit `.env`. The backend endpoint is `/api/ai-chat`.

## GitHub
The distributable intentionally excludes `.git`, `.venv`, Python cache files, and the local SQLite database. To publish:
```bash
git init
git add .
git commit -m "Merge PrismLive AI, registration and UPI page"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```
Create an empty GitHub repository first and replace the URL with its real URL. Do not upload `.env`, database files, or API keys.

## Files to know
- `app.py`: Flask routes, auth, Socket.IO, Gemini endpoint, payment page
- `db.py`: SQLite schema and safe migration for `interest`
- `templates/prismlive_register_page.html`: updated registration form
- `templates/prismlive_chat_page.html`: existing real-time chat + AI widget include
- `templates/partials/prism_ai_widget.html`: AI panel markup
- `static/css/prism-ai.css`: scoped AI styles
- `static/js/prism-ai.js`: frontend AI chat
- `templates/prismlive_payment_page.html`: UPI intent page

## Testing checklist
- Register with matching passwords and selected interest.
- Confirm a mismatched password is rejected.
- Log in and open Live Chat from the side icon.
- Test member-to-member messaging in two browser sessions.
- Open Prism AI and test it with a valid Gemini key.
- Open Payment and test with a valid configured UPI ID on a device with a UPI app.
- Confirm payment is not shown as verified unless a payment gateway webhook is implemented.
