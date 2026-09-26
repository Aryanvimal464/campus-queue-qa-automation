"""
database.py
-------------------------------------------------------
Handles all SQLite database setup for Campus Queue.

- Creates the database file and tables if they do not exist.
- Seeds demo accounts, departments and services on first run.
- Provides a get_db() helper that Flask routes use to get a
  connection scoped to the current request (via flask.g).

All queries elsewhere in the app use parameterized SQL (?) to
avoid SQL injection.
-------------------------------------------------------
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "campus_queue.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'staff', 'admin')),
    department_id INTEGER,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    estimated_time INTEGER NOT NULL DEFAULT 5,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_number TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'WAITING'
        CHECK(status IN ('WAITING','CALLED','IN_PROGRESS','COMPLETED','SKIPPED','CANCELLED')),
    created_at TEXT NOT NULL,
    called_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

CREATE TABLE IF NOT EXISTS queue_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    performed_by INTEGER,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (token_id) REFERENCES tokens(id),
    FOREIGN KEY (performed_by) REFERENCES users(id)
);
"""


def get_db():
    """Return a sqlite3 connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables (if needed) and seed demo data (if the DB is empty)."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()

    cur = conn.execute("SELECT COUNT(*) AS c FROM departments")
    if cur.fetchone()["c"] == 0:
        _seed(conn)

    conn.close()


def _seed(conn):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    departments = [
        ("Scholarship Office", "SCH"),
        ("Library", "LIB"),
        ("Examination Cell", "EXM"),
        ("Accounts Office", "ACC"),
        ("Placement Cell", "PLC"),
    ]
    dept_ids = {}
    for name, code in departments:
        cur = conn.execute(
            "INSERT INTO departments (name, code, status) VALUES (?, ?, 'active')",
            (name, code),
        )
        dept_ids[code] = cur.lastrowid

    services = [
        ("SCH", "Merit Scholarship Application", 6),
        ("SCH", "Scholarship Status Inquiry", 4),
        ("SCH", "Document Verification", 5),
        ("LIB", "Book Issue / Return", 3),
        ("LIB", "Library Card Renewal", 4),
        ("LIB", "No-Dues Clearance", 5),
        ("EXM", "Hall Ticket Collection", 4),
        ("EXM", "Revaluation Request", 7),
        ("EXM", "Migration Certificate", 6),
        ("ACC", "Fee Payment Receipt", 5),
        ("ACC", "Refund Request", 8),
        ("ACC", "Scholarship Disbursement Query", 5),
        ("PLC", "Resume Review", 10),
        ("PLC", "Placement Registration", 6),
        ("PLC", "Interview Slot Booking", 5),
    ]
    for code, name, est in services:
        conn.execute(
            "INSERT INTO services (department_id, name, estimated_time, status) "
            "VALUES (?, ?, ?, 'active')",
            (dept_ids[code], name, est),
        )

    demo_users = [
        ("Sam Student", "student@test.com", "9876500001", "Student@123", "student", None),
        ("Priya Staff", "staff@test.com", "9876500002", "Staff@123", "staff", dept_ids["SCH"]),
        ("Alex Admin", "admin@test.com", "9876500003", "Admin@123", "admin", None),
    ]
    for name, email, phone, pwd, role, dept in demo_users:
        conn.execute(
            "INSERT INTO users (name, email, phone, password, role, department_id, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
            (name, email, phone, generate_password_hash(pwd), role, dept, now),
        )

    conn.commit()
