
"""
app.py
-------------------------------------------------------
Campus Queue - Virtual Queue Management System
Flask + SQLite backend.

Run with:  python app.py
Opens at:  http://127.0.0.1:5000
-------------------------------------------------------
"""

import re
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

import database

app = Flask(__name__)
app.config["SECRET_KEY"] = "campus-queue-dev-secret-key-2026"

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[0-9]{10}$")
ACTIVE_TOKEN_STATUSES = ("WAITING", "CALLED", "IN_PROGRESS")
DEFAULT_SERVICE_TIME = 5  # minutes, used when a department has no services yet


# ---------------------------------------------------------------------------
# Database connection (scoped to the request)
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = database.get_db()
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Auth helpers / decorators
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                return render_template("access_denied.html"), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()


@app.context_processor
def inject_user():
    return {"logged_in_user": current_user()}


# ---------------------------------------------------------------------------
# Queue helper functions
# ---------------------------------------------------------------------------
def next_token_number(db, department_id, department_code):
    count = db.execute(
        "SELECT COUNT(*) AS c FROM tokens WHERE department_id = ?", (department_id,)
    ).fetchone()["c"]
    return f"{department_code}-{count + 1:03d}"


def department_avg_service_time(db, department_id):
    row = db.execute(
        "SELECT AVG(estimated_time) AS avg_time FROM services "
        "WHERE department_id = ? AND status = 'active'",
        (department_id,),
    ).fetchone()
    if row["avg_time"] is None:
        return DEFAULT_SERVICE_TIME
    return round(row["avg_time"])


def queue_position(db, token):
    """1-based position of a WAITING token among WAITING tokens in its department."""
    row = db.execute(
        "SELECT COUNT(*) AS pos FROM tokens "
        "WHERE department_id = ? AND status = 'WAITING' AND id <= ?",
        (token["department_id"], token["id"]),
    ).fetchone()
    return row["pos"]


def estimated_wait_minutes(db, token):
    position = queue_position(db, token)
    avg_time = department_avg_service_time(db, token["department_id"])
    return position * avg_time


def log_history(db, token_id, action, performed_by):
    db.execute(
        "INSERT INTO queue_history (token_id, action, performed_by, timestamp) "
        "VALUES (?, ?, ?, ?)",
        (token_id, action, performed_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def get_active_token_for_user(db, user_id):
    return db.execute(
        "SELECT t.*, d.name AS department_name, d.code AS department_code, "
        "s.name AS service_name, s.estimated_time "
        "FROM tokens t "
        "JOIN departments d ON d.id = t.department_id "
        "JOIN services s ON s.id = t.service_id "
        "WHERE t.user_id = ? AND t.status IN ('WAITING','CALLED','IN_PROGRESS') "
        "ORDER BY t.id DESC LIMIT 1",
        (user_id,),
    ).fetchone()


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Thanks for reaching out. Our team will get back to you shortly.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/access-denied")
def access_denied():
    return render_template("access_denied.html")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    errors = []
    if not name:
        errors.append("Name is required.")
    if not email:
        errors.append("Email is required.")
    elif not EMAIL_RE.match(email):
        errors.append("Enter a valid email address.")
    if not phone:
        errors.append("Phone number is required.")
    elif not PHONE_RE.match(phone):
        errors.append("Phone number must be exactly 10 digits.")
    if not password:
        errors.append("Password is required.")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if password != confirm_password:
        errors.append("Passwords do not match.")

    db = get_db()
    if not errors and email:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            errors.append("An account with this email already exists.")

    if errors:
        return render_template(
            "register.html",
            error=" ".join(errors),
            form={"name": name, "email": email, "phone": phone},
        ), 400

    db.execute(
        "INSERT INTO users (name, email, phone, password, role, status, created_at) "
        "VALUES (?, ?, ?, ?, 'student', 'active', ?)",
        (name, email, phone, generate_password_hash(password),
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    db.commit()
    flash("Registration successful. You can now log in.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "login.html", error="Email and password are required.", email=email
        ), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user or not check_password_hash(user["password"], password):
        return render_template(
            "login.html", error="Invalid email or password.", email=email
        ), 401

    if user["status"] != "active":
        return render_template(
            "login.html",
            error="Your account has been deactivated. Please contact the admin.",
            email=email,
        ), 403

    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["name"]

    if user["role"] == "student":
        return redirect(url_for("student_dashboard"))
    if user["role"] == "staff":
        return redirect(url_for("staff_dashboard"))
    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# STUDENT MODULE
# ---------------------------------------------------------------------------
@app.route("/student/dashboard")
@role_required("student")
def student_dashboard():
    db = get_db()
    token = get_active_token_for_user(db, session["user_id"])
    position = None
    wait_time = None
    if token and token["status"] == "WAITING":
        position = queue_position(db, token)
        wait_time = estimated_wait_minutes(db, token)
    elif token:
        position = 0

    total_history = db.execute(
        "SELECT COUNT(*) AS c FROM tokens WHERE user_id = ?", (session["user_id"],)
    ).fetchone()["c"]

    return render_template(
        "student/dashboard.html",
        token=token,
        position=position,
        wait_time=wait_time,
        total_history=total_history,
    )


@app.route("/student/generate-token", methods=["GET", "POST"])
@role_required("student")
def generate_token():
    db = get_db()
    departments = db.execute(
        "SELECT * FROM departments WHERE status = 'active' ORDER BY name"
    ).fetchall()

    if request.method == "GET":
        selected_dept = request.args.get("department_id")
        services = []
        if selected_dept:
            services = db.execute(
                "SELECT * FROM services WHERE department_id = ? AND status = 'active' ORDER BY name",
                (selected_dept,),
            ).fetchall()
        existing = get_active_token_for_user(db, session["user_id"])
        return render_template(
            "student/generate_token.html",
            departments=departments,
            services=services,
            selected_dept=selected_dept,
            existing_token=existing,
        )

    department_id = request.form.get("department_id", "")
    service_id = request.form.get("service_id", "")

    services = []
    if department_id:
        services = db.execute(
            "SELECT * FROM services WHERE department_id = ? AND status = 'active' ORDER BY name",
            (department_id,),
        ).fetchall()

    error = None
    if not department_id:
        error = "Please select a department."
    elif not service_id:
        error = "Please select a service."

    if not error:
        existing = get_active_token_for_user(db, session["user_id"])
        if existing:
            error = "You already have an active token."

    if error:
        return render_template(
            "student/generate_token.html",
            departments=departments,
            services=services,
            selected_dept=department_id,
            error=error,
            existing_token=get_active_token_for_user(db, session["user_id"]),
        ), 400

    dept = db.execute("SELECT * FROM departments WHERE id = ?", (department_id,)).fetchone()
    token_number = next_token_number(db, department_id, dept["code"])

    cur = db.execute(
        "INSERT INTO tokens (token_number, user_id, department_id, service_id, status, created_at) "
        "VALUES (?, ?, ?, ?, 'WAITING', ?)",
        (token_number, session["user_id"], department_id, service_id,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    log_history(db, cur.lastrowid, "GENERATED", session["user_id"])
    db.commit()

    flash(f"Token {token_number} generated successfully.", "success")
    return redirect(url_for("current_token"))


@app.route("/student/current-token")
@role_required("student")
def current_token():
    db = get_db()
    token = get_active_token_for_user(db, session["user_id"])
    position = None
    wait_time = None
    if token and token["status"] == "WAITING":
        position = queue_position(db, token)
        wait_time = estimated_wait_minutes(db, token)
    return render_template(
        "student/current_token.html", token=token, position=position, wait_time=wait_time
    )


@app.route("/student/cancel-token/<int:token_id>", methods=["POST"])
@role_required("student")
def cancel_token(token_id):
    db = get_db()
    token = db.execute(
        "SELECT * FROM tokens WHERE id = ? AND user_id = ?", (token_id, session["user_id"])
    ).fetchone()

    if not token:
        flash("Token not found.", "danger")
    elif token["status"] != "WAITING":
        flash("Only a token that is still waiting can be cancelled.", "danger")
    else:
        db.execute("UPDATE tokens SET status = 'CANCELLED' WHERE id = ?", (token_id,))
        log_history(db, token_id, "CANCELLED", session["user_id"])
        db.commit()
        flash("Token cancelled successfully.", "success")

    return redirect(url_for("student_dashboard"))


@app.route("/student/history")
@role_required("student")
def student_history():
    db = get_db()
    tokens = db.execute(
        "SELECT t.*, d.name AS department_name, s.name AS service_name "
        "FROM tokens t "
        "JOIN departments d ON d.id = t.department_id "
        "JOIN services s ON s.id = t.service_id "
        "WHERE t.user_id = ? ORDER BY t.id DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("student/history.html", tokens=tokens)


@app.route("/student/profile")
@role_required("student")
def student_profile():
    return render_template("student/profile.html", user=current_user())


# ---------------------------------------------------------------------------
# STAFF MODULE
# ---------------------------------------------------------------------------
def staff_department(db):
    user = current_user()
    if not user["department_id"]:
        return None
    return db.execute(
        "SELECT * FROM departments WHERE id = ?", (user["department_id"],)
    ).fetchone()


@app.route("/staff/dashboard")
@role_required("staff")
def staff_dashboard():
    db = get_db()
    dept = staff_department(db)

    current = None
    waiting_count = 0
    stats = {"completed": 0, "skipped": 0, "waiting": 0}

    if dept:
        current = db.execute(
            "SELECT t.*, u.name AS student_name, s.name AS service_name "
            "FROM tokens t "
            "JOIN users u ON u.id = t.user_id "
            "JOIN services s ON s.id = t.service_id "
            "WHERE t.department_id = ? AND t.status = 'CALLED' "
            "ORDER BY t.id ASC LIMIT 1",
            (dept["id"],),
        ).fetchone()

        waiting_count = db.execute(
            "SELECT COUNT(*) AS c FROM tokens WHERE department_id = ? AND status = 'WAITING'",
            (dept["id"],),
        ).fetchone()["c"]

        today = datetime.now().strftime("%Y-%m-%d")
        for status_key, status_val in (("completed", "COMPLETED"), ("skipped", "SKIPPED"), ("waiting", "WAITING")):
            stats[status_key] = db.execute(
                "SELECT COUNT(*) AS c FROM tokens "
                "WHERE department_id = ? AND status = ? AND created_at LIKE ?",
                (dept["id"], status_val, today + "%"),
            ).fetchone()["c"]

    return render_template(
        "staff/dashboard.html", dept=dept, current=current, waiting_count=waiting_count, stats=stats
    )


@app.route("/staff/queue")
@role_required("staff")
def staff_queue():
    db = get_db()
    dept = staff_department(db)
    waiting = []
    current = None
    if dept:
        current = db.execute(
            "SELECT t.*, u.name AS student_name, s.name AS service_name "
            "FROM tokens t "
            "JOIN users u ON u.id = t.user_id "
            "JOIN services s ON s.id = t.service_id "
            "WHERE t.department_id = ? AND t.status = 'CALLED' "
            "ORDER BY t.id ASC LIMIT 1",
            (dept["id"],),
        ).fetchone()
        waiting = db.execute(
            "SELECT t.*, u.name AS student_name, s.name AS service_name "
            "FROM tokens t "
            "JOIN users u ON u.id = t.user_id "
            "JOIN services s ON s.id = t.service_id "
            "WHERE t.department_id = ? AND t.status = 'WAITING' "
            "ORDER BY t.id ASC",
            (dept["id"],),
        ).fetchall()
    return render_template("staff/queue.html", dept=dept, current=current, waiting=waiting)


@app.route("/staff/call-next", methods=["POST"])
@role_required("staff")
def call_next():
    db = get_db()
    dept = staff_department(db)
    if not dept:
        flash("You are not assigned to a department.", "danger")
        return redirect(url_for("staff_dashboard"))

    already_current = db.execute(
        "SELECT id FROM tokens WHERE department_id = ? AND status = 'CALLED'", (dept["id"],)
    ).fetchone()
    if already_current:
        flash("Complete or skip the current token before calling the next one.", "warning")
        return redirect(url_for("staff_queue"))

    next_waiting = db.execute(
        "SELECT * FROM tokens WHERE department_id = ? AND status = 'WAITING' "
        "ORDER BY id ASC LIMIT 1",
        (dept["id"],),
    ).fetchone()

    if not next_waiting:
        flash("No students are currently waiting in the queue.", "info")
        return redirect(url_for("staff_queue"))

    db.execute(
        "UPDATE tokens SET status = 'CALLED', called_at = ? WHERE id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), next_waiting["id"]),
    )
    log_history(db, next_waiting["id"], "CALLED", session["user_id"])
    db.commit()
    flash(f"Token {next_waiting['token_number']} called.", "success")
    return redirect(url_for("staff_queue"))


@app.route("/staff/skip/<int:token_id>", methods=["POST"])
@role_required("staff")
def skip_token(token_id):
    db = get_db()
    dept = staff_department(db)
    token = db.execute(
        "SELECT * FROM tokens WHERE id = ? AND department_id = ?", (token_id, dept["id"] if dept else -1)
    ).fetchone()

    if not token or token["status"] != "CALLED":
        flash("Only the currently called token can be skipped.", "danger")
    else:
        db.execute("UPDATE tokens SET status = 'SKIPPED' WHERE id = ?", (token_id,))
        log_history(db, token_id, "SKIPPED", session["user_id"])
        db.commit()
        flash(f"Token {token['token_number']} skipped.", "info")

    return redirect(url_for("staff_queue"))


@app.route("/staff/complete/<int:token_id>", methods=["POST"])
@role_required("staff")
def complete_token(token_id):
    db = get_db()
    dept = staff_department(db)
    token = db.execute(
        "SELECT * FROM tokens WHERE id = ? AND department_id = ?", (token_id, dept["id"] if dept else -1)
    ).fetchone()

    if not token or token["status"] != "CALLED":
        flash("Only the currently called token can be marked as completed.", "danger")
    else:
        db.execute(
            "UPDATE tokens SET status = 'COMPLETED', completed_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), token_id),
        )
        log_history(db, token_id, "COMPLETED", session["user_id"])
        db.commit()
        flash(f"Token {token['token_number']} marked as completed.", "success")

    return redirect(url_for("staff_queue"))


@app.route("/staff/history")
@role_required("staff")
def staff_history():
    db = get_db()
    dept = staff_department(db)
    tokens = []
    if dept:
        tokens = db.execute(
            "SELECT t.*, u.name AS student_name, s.name AS service_name "
            "FROM tokens t "
            "JOIN users u ON u.id = t.user_id "
            "JOIN services s ON s.id = t.service_id "
            "WHERE t.department_id = ? "
            "ORDER BY t.id DESC LIMIT 100",
            (dept["id"],),
        ).fetchall()
    return render_template("staff/history.html", dept=dept, tokens=tokens)


# ---------------------------------------------------------------------------
# ADMIN MODULE
# ---------------------------------------------------------------------------
@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    db = get_db()
    stats = {
        "students": db.execute("SELECT COUNT(*) c FROM users WHERE role='student'").fetchone()["c"],
        "staff": db.execute("SELECT COUNT(*) c FROM users WHERE role='staff'").fetchone()["c"],
        "departments": db.execute("SELECT COUNT(*) c FROM departments").fetchone()["c"],
        "services": db.execute("SELECT COUNT(*) c FROM services").fetchone()["c"],
        "tokens_total": db.execute("SELECT COUNT(*) c FROM tokens").fetchone()["c"],
        "tokens_waiting": db.execute("SELECT COUNT(*) c FROM tokens WHERE status='WAITING'").fetchone()["c"],
        "tokens_completed": db.execute("SELECT COUNT(*) c FROM tokens WHERE status='COMPLETED'").fetchone()["c"],
    }
    recent_tokens = db.execute(
        "SELECT t.*, u.name AS student_name, d.name AS department_name "
        "FROM tokens t JOIN users u ON u.id = t.user_id JOIN departments d ON d.id = t.department_id "
        "ORDER BY t.id DESC LIMIT 8"
    ).fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent_tokens=recent_tokens)


@app.route("/admin/users")
@role_required("admin")
def admin_users():
    db = get_db()
    users = db.execute(
        "SELECT u.*, d.name AS department_name FROM users u "
        "LEFT JOIN departments d ON d.id = u.department_id "
        "ORDER BY u.role, u.name"
    ).fetchall()
    return render_template("admin/users.html", users=users)


@app.route("/admin/users/toggle/<int:user_id>", methods=["POST"])
@role_required("admin")
def toggle_user(user_id):
    db = get_db()
    if user_id == session["user_id"]:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin_users"))

    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin_users"))

    new_status = "inactive" if user["status"] == "active" else "active"
    db.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    flash(f"{user['name']} is now {new_status}.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/departments", methods=["GET", "POST"])
@role_required("admin")
def admin_departments():
    db = get_db()
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip().upper()
        if not name or not code:
            error = "Department name and code are required."
        elif db.execute("SELECT id FROM departments WHERE code = ?", (code,)).fetchone():
            error = "A department with this code already exists."
        else:
            db.execute(
                "INSERT INTO departments (name, code, status) VALUES (?, ?, 'active')", (name, code)
            )
            db.commit()
            flash(f"Department '{name}' added.", "success")
            return redirect(url_for("admin_departments"))

    departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
    return render_template("admin/departments.html", departments=departments, error=error)


@app.route("/admin/departments/toggle/<int:dept_id>", methods=["POST"])
@role_required("admin")
def toggle_department(dept_id):
    db = get_db()
    dept = db.execute("SELECT * FROM departments WHERE id = ?", (dept_id,)).fetchone()
    if dept:
        new_status = "inactive" if dept["status"] == "active" else "active"
        db.execute("UPDATE departments SET status = ? WHERE id = ?", (new_status, dept_id))
        db.commit()
        flash(f"Department '{dept['name']}' is now {new_status}.", "success")
    return redirect(url_for("admin_departments"))


@app.route("/admin/services", methods=["GET", "POST"])
@role_required("admin")
def admin_services():
    db = get_db()
    error = None
    if request.method == "POST":
        department_id = request.form.get("department_id", "")
        name = request.form.get("name", "").strip()
        estimated_time = request.form.get("estimated_time", "").strip()

        if not department_id or not name or not estimated_time:
            error = "All fields are required."
        elif not estimated_time.isdigit() or int(estimated_time) <= 0:
            error = "Estimated time must be a positive number of minutes."
        else:
            db.execute(
                "INSERT INTO services (department_id, name, estimated_time, status) "
                "VALUES (?, ?, ?, 'active')",
                (department_id, name, int(estimated_time)),
            )
            db.commit()
            flash(f"Service '{name}' added.", "success")
            return redirect(url_for("admin_services"))

    services = db.execute(
        "SELECT s.*, d.name AS department_name FROM services s "
        "JOIN departments d ON d.id = s.department_id ORDER BY d.name, s.name"
    ).fetchall()
    departments = db.execute("SELECT * FROM departments WHERE status='active' ORDER BY name").fetchall()
    return render_template(
        "admin/services.html", services=services, departments=departments, error=error
    )


@app.route("/admin/services/toggle/<int:service_id>", methods=["POST"])
@role_required("admin")
def toggle_service(service_id):
    db = get_db()
    service = db.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    if service:
        new_status = "inactive" if service["status"] == "active" else "active"
        db.execute("UPDATE services SET status = ? WHERE id = ?", (new_status, service_id))
        db.commit()
        flash(f"Service '{service['name']}' is now {new_status}.", "success")
    return redirect(url_for("admin_services"))


@app.route("/admin/tokens")
@role_required("admin")
def admin_tokens():
    db = get_db()
    status_filter = request.args.get("status", "")
    query = (
        "SELECT t.*, u.name AS student_name, d.name AS department_name, s.name AS service_name "
        "FROM tokens t "
        "JOIN users u ON u.id = t.user_id "
        "JOIN departments d ON d.id = t.department_id "
        "JOIN services s ON s.id = t.service_id "
    )
    params = ()
    if status_filter:
        query += "WHERE t.status = ? "
        params = (status_filter,)
    query += "ORDER BY t.id DESC LIMIT 200"

    tokens = db.execute(query, params).fetchall()
    return render_template("admin/tokens.html", tokens=tokens, status_filter=status_filter)


@app.route("/admin/reports")
@role_required("admin")
def admin_reports():
    db = get_db()
    by_status = db.execute(
        "SELECT status, COUNT(*) AS c FROM tokens GROUP BY status"
    ).fetchall()
    by_department = db.execute(
        "SELECT d.name AS department_name, COUNT(t.id) AS c "
        "FROM departments d LEFT JOIN tokens t ON t.department_id = d.id "
        "GROUP BY d.id ORDER BY d.name"
    ).fetchall()
    completed = db.execute(
        "SELECT department_id, created_at, completed_at FROM tokens WHERE status = 'COMPLETED'"
    ).fetchall()

    avg_wait_by_dept = {}
    totals = {}
    for row in completed:
        try:
            created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
            completed_dt = datetime.strptime(row["completed_at"], "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            continue
        minutes = (completed_dt - created).total_seconds() / 60
        totals.setdefault(row["department_id"], []).append(minutes)

    for dept_id, values in totals.items():
        avg_wait_by_dept[dept_id] = round(sum(values) / len(values), 1)

    departments = db.execute("SELECT * FROM departments ORDER BY name").fetchall()

    return render_template(
        "admin/reports.html",
        by_status=by_status,
        by_department=by_department,
        avg_wait_by_dept=avg_wait_by_dept,
        departments=departments,
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("access_denied.html", not_found=True), 404


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
