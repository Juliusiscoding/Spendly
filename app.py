import os
import re
import sqlite3
from datetime import date, datetime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

init_db()
seed_db()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DUPLICATE_EMAIL_ERROR = "An account with that email already exists."
INVALID_LOGIN_ERROR = "Invalid email or password."


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def login_required(view):
    """Redirect to the login page unless someone is signed in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def format_inr(amount):
    """Format an amount as rupees with Indian digit grouping, e.g. 1,23,456.50."""
    integer, decimals = f"{float(amount):.2f}".split(".")
    if len(integer) > 3:
        head, tail = integer[:-3], integer[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        integer = ",".join(groups + [tail])
    return f"₹{integer}.{decimals}"


app.add_template_filter(format_inr, "inr")


def _initials(name):
    parts = name.split()
    if not parts:
        return "?"
    return "".join(part[0] for part in parts[:2]).upper()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


def _register_error(message, name, email):
    return render_template("register.html", error=message, name=name, email=email), 400


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return _register_error("All fields are required.", name, email)
    if not EMAIL_RE.match(email):
        return _register_error("Please enter a valid email address.", name, email)
    if len(password) < 8:
        return _register_error("Password must be at least 8 characters.", name, email)

    conn = get_db()
    try:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            return _register_error(DUPLICATE_EMAIL_ERROR, name, email)
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return _register_error(DUPLICATE_EMAIL_ERROR, name, email)
    finally:
        conn.close()

    return redirect(url_for("login"))


def _login_error(message, email, status):
    return render_template("login.html", error=message, email=email), status


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return _login_error("Email and password are required.", email, 400)

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return _login_error(INVALID_LOGIN_ERROR, email, 401)

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            session.clear()
            return redirect(url_for("login"))

        totals = conn.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total "
            "FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        month = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
            "WHERE user_id = ? AND date LIKE ?",
            (user_id, date.today().strftime("%Y-%m") + "-%"),
        ).fetchone()
        rows = conn.execute(
            "SELECT date, category, description, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    recent_expenses = [
        {
            "display_date": datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y"),
            "category": row["category"],
            "description": row["description"],
            "amount": row["amount"],
        }
        for row in rows
    ]
    member_since = datetime.strptime(user["created_at"][:10], "%Y-%m-%d").strftime("%B %Y")

    return render_template(
        "profile.html",
        user=user,
        initials=_initials(user["name"]),
        member_since=member_since,
        total_spent=totals["total"],
        month_spent=month["total"],
        expense_count=totals["count"],
        recent_expenses=recent_expenses,
    )


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
