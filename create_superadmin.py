"""Create or promote the single owner account. Run from the project folder."""
import getpass
import sqlite3
from werkzeug.security import generate_password_hash
from db import init_db, get_db


def main():
    init_db()
    print("Create the Prism Live Super Admin account")
    first = input("First name: ").strip()[:80]
    last = input("Last name: ").strip()[:80]
    email = input("Owner email: ").strip().lower()[:254]
    password = getpass.getpass("Password (minimum 12 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if not first or not last or "@" not in email:
        raise SystemExit("Enter a name and valid email address.")
    if len(password) < 12 or password != confirm:
        raise SystemExit("Passwords must match and contain at least 12 characters.")
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            db.execute("UPDATE users SET first_name=?, last_name=?, password_hash=?, role='superadmin', is_active=1 WHERE id=?",
                       (first, last, generate_password_hash(password), existing["id"]))
            print("Existing account promoted to Super Admin and password updated.")
        else:
            db.execute("INSERT INTO users(first_name,last_name,email,password_hash,role,is_active) VALUES(?,?,?,?, 'superadmin',1)",
                       (first, last, email, generate_password_hash(password)))
            print("Super Admin account created.")
    print("Go to /login and sign in. Keep this account's password private.")

if __name__ == "__main__":
    main()
