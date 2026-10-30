import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db, init_db

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_url_path='/images', static_folder='images')
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me-before-deploying-7c2b9e5f"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)
socketio = SocketIO(app, cors_allowed_origins=None, async_mode="threading", logger=False, engineio_logger=False)

# Socket.IO presence is in-memory (one server process). Messages themselves are stored in SQLite.
online_users = set()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.get("is_active"):
            session.clear()
            flash("Please log in with an active account.", "error")
            return redirect(url_for("login"))
        if user.get("role") not in ("admin", "superadmin"):
            flash("Administrator access is required.", "error")
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped


def superadmin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.get("is_active"):
            session.clear()
            flash("Please log in with an active account.", "error")
            return redirect(url_for("login"))
        if user.get("role") != "superadmin":
            flash("Only the Super Admin can perform that action.", "error")
            return redirect(url_for("admin_dashboard"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as db:
        row = db.execute("SELECT id, first_name, last_name, email, role, is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


@app.context_processor
def inject_template_context():
    return {"current_user": current_user(), "logged_in": "user_id" in session}


@app.route("/")
def index():
    return redirect(url_for("home"))


@app.route("/home")
def home():
    return render_template("prismlive_home_page.html")


@app.route("/about")
def about():
    return render_template("prismlive_about_page.html")


@app.route("/media")
def media():
    return render_template("prismlive_media_page.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()[:80]
        last_name = request.form.get("last_name", "").strip()[:80]
        email = request.form.get("email", "").strip().lower()[:254]
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        interest = request.form.get("interest", "").strip()[:100]
        terms = request.form.get("terms")
        if not all([first_name, last_name, email, password]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        if not interest:
            flash("Please select your interest.", "error")
            return redirect(url_for("register"))
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))
        if not terms:
            flash("Please accept the terms to register.", "error")
            return redirect(url_for("register"))
        try:
            with get_db() as db:
                db.execute("INSERT INTO users (first_name, last_name, email, interest, password_hash) VALUES (?, ?, ?, ?, ?)",
                           (first_name, last_name, email, interest, generate_password_hash(password)))
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("register"))
    return render_template("prismlive_register_page.html")



@app.post("/api/ai-chat")
def ai_chat_api():
    """Gemini-powered public assistant. API key stays on the server."""
    import requests
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "AI assistant is not configured. Add GEMINI_API_KEY to server environment."}), 503
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])
    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 4000:
        return jsonify({"error": "Message is too long."}), 413
    contents = []
    if isinstance(history, list):
        for item in history[-10:]:
            if isinstance(item, dict) and item.get("role") in ("user", "model") and isinstance(item.get("text"), str):
                contents.append({"role": item["role"], "parts": [{"text": item["text"][:4000]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": api_key},
            json={
                "systemInstruction": {"parts": [{"text":
                    "You are Prism AI, a friendly assistant on PrismLive. Give useful concise answers. "
                    "Do not claim to access private user data or complete website actions. Never request passwords, OTPs or payment secrets."}]},
                "contents": contents,
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 900},
            }, timeout=35)
        resp.raise_for_status()
        data = resp.json()
        answer = "".join(p.get("text", "") for p in data.get("candidates", [{}])[0].get("content", {}).get("parts", [])).strip()
        if not answer:
            return jsonify({"error": "The AI returned an empty response."}), 502
        return jsonify({"reply": answer})
    except requests.Timeout:
        return jsonify({"error": "AI request timed out. Please try again."}), 504
    except requests.RequestException:
        app.logger.exception("Gemini API request failed")
        return jsonify({"error": "Could not connect to AI. Check the server API key and model configuration."}), 502


@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    upi_id = os.environ.get("UPI_ID", "").strip()
    payee = os.environ.get("UPI_PAYEE_NAME", "PrismLive").strip()
    amount = ""
    upi_link = ""
    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        try:
            value = float(amount)
            if not (1 <= value <= 100000):
                raise ValueError()
            if not upi_id or "@" not in upi_id:
                flash("UPI payment is not configured yet. Contact the website administrator.", "error")
            else:
                from urllib.parse import urlencode
                upi_link = "upi://pay?" + urlencode({
                    "pa": upi_id, "pn": payee, "am": f"{value:.2f}",
                    "cu": "INR", "tn": "PrismLive payment"
                })
        except ValueError:
            flash("Enter a valid amount between ₹1 and ₹100,000.", "error")
    return render_template("prismlive_payment_page.html",
                           upi_id=upi_id, payee=payee, amount=amount, upi_link=upi_link)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password) and user["is_active"]:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["first_name"]
            if user["role"] in ("admin", "superadmin"):
                return redirect(url_for("admin_dashboard"))
            target = request.args.get("next", "")
            # Avoid open redirects; only allow local paths.
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("home"))
        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))
    return render_template("prismlive_login_page.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:120]
        email = request.form.get("email", "").strip().lower()[:254]
        subject = request.form.get("subject", "").strip()[:200]
        message = request.form.get("message", "").strip()[:5000]
        if not all([name, email, subject, message]):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("contact"))
        with get_db() as db:
            db.execute("INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)",
                       (name, email, subject, message))
        flash("Your message has been submitted.", "success")
        return redirect(url_for("contact"))
    return render_template("prismlive_contact_page.html")


@app.route("/chat")
@login_required
def chat():
    user_id = session["user_id"]
    with get_db() as db:
        users = db.execute("SELECT id, first_name, last_name, email FROM users WHERE id != ? ORDER BY first_name, last_name", (user_id,)).fetchall()
    return render_template("prismlive_chat_page.html", users=[dict(u) for u in users], my_user_id=user_id)


@app.get("/api/users")
@login_required
def api_users():
    user_id = session["user_id"]
    with get_db() as db:
        users = db.execute("SELECT id, first_name, last_name, email FROM users WHERE id != ? ORDER BY first_name, last_name", (user_id,)).fetchall()
    return jsonify([dict(u, online=(u["id"] in online_users)) for u in users])


@app.get("/api/messages/<int:recipient_id>")
@login_required
def api_messages(recipient_id):
    user_id = session["user_id"]
    with get_db() as db:
        recipient = db.execute("SELECT id FROM users WHERE id = ?", (recipient_id,)).fetchone()
        if not recipient or recipient_id == user_id:
            return jsonify({"error": "User not found"}), 404
        rows = db.execute("""SELECT m.id, m.sender_id, m.recipient_id, m.message, m.created_at,
                                  u.first_name || ' ' || u.last_name AS sender_name
                           FROM chat_messages m JOIN users u ON u.id=m.sender_id
                           WHERE (m.sender_id=? AND m.recipient_id=?) OR (m.sender_id=? AND m.recipient_id=?)
                           ORDER BY m.id ASC LIMIT 500""", (user_id, recipient_id, recipient_id, user_id)).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/admin")
@admin_required
def admin_dashboard():
    user = current_user()
    with get_db() as db:
        stats = {
            "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "admins": db.execute("SELECT COUNT(*) FROM users WHERE role IN ('admin','superadmin')").fetchone()[0],
            "messages": db.execute("SELECT COUNT(*) FROM contact_messages").fetchone()[0],
            "pending": db.execute("SELECT COUNT(*) FROM admin_change_requests WHERE status='pending'").fetchone()[0],
        }
        requests_rows = db.execute("""SELECT r.*, u.first_name || ' ' || u.last_name AS requester_name,
                                          reviewer.first_name || ' ' || reviewer.last_name AS reviewer_name
                                   FROM admin_change_requests r
                                   JOIN users u ON u.id=r.requested_by
                                   LEFT JOIN users reviewer ON reviewer.id=r.reviewed_by
                                   ORDER BY CASE r.status WHEN 'pending' THEN 0 ELSE 1 END, r.id DESC LIMIT 100""").fetchall()
        users_rows = db.execute("SELECT id, first_name, last_name, email, role, is_active, created_at FROM users ORDER BY id DESC LIMIT 200").fetchall() if user["role"] == "superadmin" else []
        contact_rows = db.execute("SELECT id, name, email, subject, message, created_at FROM contact_messages ORDER BY id DESC LIMIT 100").fetchall() if user["role"] == "superadmin" else []
    return render_template("admin_dashboard.html", user=user, stats=stats,
                           change_requests=[dict(r) for r in requests_rows],
                           users=[dict(u) for u in users_rows], contacts=[dict(c) for c in contact_rows])


@app.post("/admin/request-change")
@admin_required
def admin_request_change():
    title = request.form.get("title", "").strip()[:160]
    details = request.form.get("details", "").strip()[:5000]
    if not title or not details:
        flash("Enter a title and details for your request.", "error")
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        db.execute("INSERT INTO admin_change_requests (requested_by, title, details) VALUES (?, ?, ?)",
                   (session["user_id"], title, details))
    flash("Change request submitted for Super Admin review. It has not changed the live website.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/requests/<int:request_id>/decision")
@superadmin_required
def admin_decide_request(request_id):
    decision = request.form.get("decision", "").strip().lower()
    note = request.form.get("reviewer_note", "").strip()[:1000]
    if decision not in ("approved", "rejected"):
        flash("Invalid decision.", "error")
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        row = db.execute("SELECT id, status FROM admin_change_requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            flash("Request not found.", "error")
        elif row["status"] != "pending":
            flash("This request has already been reviewed.", "info")
        else:
            db.execute("UPDATE admin_change_requests SET status=?, reviewed_by=?, reviewer_note=?, reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
                       (decision, session["user_id"], note, request_id))
            flash(f"Request marked {decision}. Apply the approved change to the relevant website feature before it goes live.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/users/<int:target_id>/role")
@superadmin_required
def admin_set_user_role(target_id):
    role = request.form.get("role", "user").strip().lower()
    if role not in ("user", "admin"):
        flash("You cannot assign the Super Admin role from this form.", "error")
        return redirect(url_for("admin_dashboard"))
    if target_id == session.get("user_id"):
        flash("You cannot change your own role here.", "error")
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        target = db.execute("SELECT id, role FROM users WHERE id=?", (target_id,)).fetchone()
        if not target:
            flash("User not found.", "error")
        elif target["role"] == "superadmin":
            flash("The Super Admin account cannot be changed here.", "error")
        else:
            db.execute("UPDATE users SET role=? WHERE id=?", (role, target_id))
            flash("User role updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/users/<int:target_id>/active")
@superadmin_required
def admin_set_user_active(target_id):
    active = 1 if request.form.get("active") == "1" else 0
    if target_id == session.get("user_id"):
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        target = db.execute("SELECT id, role FROM users WHERE id=?", (target_id,)).fetchone()
        if not target:
            flash("User not found.", "error")
        elif target["role"] == "superadmin":
            flash("The Super Admin account cannot be deactivated here.", "error")
        else:
            db.execute("UPDATE users SET is_active=? WHERE id=?", (active, target_id))
            flash("Account status updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.get("/images/<path:filename>")
def legacy_images(filename):
    # Existing HTML uses relative images/ URLs. Keep those paths working without changing its design.
    return send_from_directory(BASE_DIR / "static" / "images", filename)


# Keep the original .html navigation links working, while routing auth/chat through their real handlers.
PAGE_MAP = {
    "index.html": "home", "prismlive_home_page.html": "home",
    "prismlive_login_page.html": "login", "prismlive_register_page.html": "register",
    "prismlive_chat_page.html": "chat", "prismlive_contact_page.html": "contact", "prismlive_payment_page.html": "payment",
}
@app.get("/<path:page>.html")
def legacy_page(page):
    filename = page + ".html"
    endpoint = PAGE_MAP.get(filename)
    if endpoint:
        return redirect(url_for(endpoint))
    candidate = BASE_DIR / "templates" / filename
    if candidate.is_file() and filename.startswith("prismlive_"):
        return render_template(filename)
    return render_template("404.html"), 404


@socketio.on("connect")
def socket_connect(auth=None):
    user_id = session.get("user_id")
    if not user_id:
        return False
    join_room(f"user_{user_id}")
    online_users.add(user_id)
    emit("presence_update", {"user_id": user_id, "online": True}, broadcast=True)


@socketio.on("disconnect")
def socket_disconnect(reason=None):
    user_id = session.get("user_id")
    if user_id:
        online_users.discard(user_id)
        socketio.emit("presence_update", {"user_id": user_id, "online": False})


@socketio.on("send_message")
def socket_send_message(data):
    user_id = session.get("user_id")
    if not user_id:
        emit("chat_error", {"message": "Please log in again to send messages."})
        return
    if not isinstance(data, dict):
        emit("chat_error", {"message": "Invalid message."})
        return
    try:
        recipient_id = int(data.get("recipient_id", 0))
    except (TypeError, ValueError):
        recipient_id = 0
    message = str(data.get("message", "")).strip()
    if not message or len(message) > 2000 or recipient_id == user_id:
        emit("chat_error", {"message": "Choose a user and enter a message under 2,000 characters."})
        return
    with get_db() as db:
        recipient = db.execute("SELECT id FROM users WHERE id = ?", (recipient_id,)).fetchone()
        if not recipient:
            emit("chat_error", {"message": "Recipient not found."})
            return
        cursor = db.execute("INSERT INTO chat_messages (sender_id, recipient_id, message) VALUES (?, ?, ?)",
                            (user_id, recipient_id, message))
        message_id = cursor.lastrowid
        row = db.execute("SELECT first_name, last_name FROM users WHERE id = ?", (user_id,)).fetchone()
        sender_name = f"{row['first_name']} {row['last_name']}"
        saved = db.execute("SELECT created_at FROM chat_messages WHERE id = ?", (message_id,)).fetchone()
    payload = {"id": message_id, "sender_id": user_id, "recipient_id": recipient_id,
               "message": message, "created_at": saved["created_at"], "sender_name": sender_name}
    socketio.emit("new_message", payload, room=f"user_{recipient_id}")
    emit("new_message", payload)


# Initialize schema when imported by Flask/Gunicorn as well as when run locally.
init_db()

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)