"""
ExpenseFlow (web) — Flask backend.

Setup (one-time):
    1. pip install -r requirements.txt
    2. Create a Postgres database (e.g. CREATE DATABASE expense_tracker;)
    3. Fill in config.py with your database name / user / password
    4. Run:  python app.py
    5. Open http://127.0.0.1:5000
"""

from functools import wraps
from datetime import timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

import database as db
from config import SECRET_KEY, SESSION_LIFETIME_DAYS, CATEGORIES

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=SESSION_LIFETIME_DAYS)

try:
    db.init_db()
    DB_READY = True
    DB_ERROR = None
except db.DatabaseError as e:
    DB_READY = False
    DB_ERROR = str(e)


# --------------------------------------------------------------- utilities
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def db_guard(view):
    """Shows a friendly setup page instead of crashing when Postgres isn't reachable."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not DB_READY:
            if request.path.startswith("/api/"):
                return jsonify({"error": DB_ERROR}), 500
            return render_template("db_error.html", error=DB_ERROR)
        return view(*args, **kwargs)
    return wrapped


def parse_date(text):
    text = (text or "").strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Date must look like YYYY-MM-DD")


def row_to_dict(r):
    return {
        "id": r["id"], "title": r["title"], "amount": float(r["amount"]),
        "category": r["category"], "date": r["expense_date"].isoformat(),
        "note": r["note"] or "",
    }


# ------------------------------------------------------------------- pages
@app.route("/register", methods=["GET", "POST"])
@db_guard
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = None
        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif "@" not in email or "." not in email:
            error = "Enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords don't match."
        else:
            existing = db.get_user_by_login(username) or db.get_user_by_login(email)
            if existing:
                error = "That username or email is already registered."

        if error:
            return render_template("register.html", error=error, username=username, email=email)

        user_id = db.create_user(username, email, generate_password_hash(password))
        session.permanent = True
        session["user_id"] = user_id
        session["username"] = username
        return redirect(url_for("dashboard"))

    return render_template("register.html", error=None, username="", email="")


@app.route("/login", methods=["GET", "POST"])
@db_guard
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = db.get_user_by_login(login_value)
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Incorrect username/email or password.",
                                    login_value=login_value)

        session.permanent = remember
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("dashboard"))

    return render_template("login.html", error=None, login_value="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
@db_guard
def dashboard():
    return render_template("dashboard.html", username=session.get("username"),
                            categories=CATEGORIES)


# --------------------------------------------------------------------- API
@app.route("/api/summary")
@login_required
@db_guard
def api_summary():
    return jsonify(db.get_summary(session["user_id"]))


@app.route("/api/expenses", methods=["GET"])
@login_required
@db_guard
def api_get_expenses():
    try:
        date_from = parse_date(request.args.get("date_from")) if request.args.get("date_from") else None
        date_to = parse_date(request.args.get("date_to")) if request.args.get("date_to") else None
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    rows = db.get_expenses(
        session["user_id"],
        search=request.args.get("search", ""),
        category=request.args.get("category", "All"),
        date_from=date_from, date_to=date_to,
    )
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/expenses", methods=["POST"])
@login_required
@db_guard
def api_add_expense():
    data = request.get_json(force=True)
    error = _validate_expense(data)
    if error:
        return jsonify({"error": error}), 400
    new_id = db.add_expense(
        session["user_id"], data["title"].strip(), float(data["amount"]),
        data["category"], parse_date(data["date"]), data.get("note", "").strip(),
    )
    return jsonify({"id": new_id}), 201


@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
@login_required
@db_guard
def api_update_expense(expense_id):
    data = request.get_json(force=True)
    error = _validate_expense(data)
    if error:
        return jsonify({"error": error}), 400
    updated = db.update_expense(
        session["user_id"], expense_id, data["title"].strip(), float(data["amount"]),
        data["category"], parse_date(data["date"]), data.get("note", "").strip(),
    )
    if not updated:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
@login_required
@db_guard
def api_delete_expense(expense_id):
    deleted = db.delete_expense(session["user_id"], expense_id)
    if not deleted:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/categories")
@login_required
@db_guard
def api_categories():
    rows = db.get_category_breakdown(session["user_id"])
    return jsonify([{"category": r[0], "total": float(r[1])} for r in rows])


@app.route("/api/trend")
@login_required
@db_guard
def api_trend():
    rows = db.get_monthly_trend(session["user_id"], months=6)
    return jsonify([{"label": r[0], "total": float(r[2])} for r in rows])


def _validate_expense(data):
    if not data or not data.get("title", "").strip():
        return "Title is required."
    try:
        amount = float(data.get("amount"))
        if amount <= 0:
            return "Amount must be a positive number."
    except (TypeError, ValueError):
        return "Amount must be a number."
    if data.get("category") not in CATEGORIES:
        return "Please choose a valid category."
    try:
        parse_date(data.get("date"))
    except ValueError as e:
        return str(e)
    return None


if __name__ == "__main__":
    app.run(debug=True)
