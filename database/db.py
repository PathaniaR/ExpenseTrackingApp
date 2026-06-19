import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

# Resolve the DB path from this file's location so it always points at the
# project root, regardless of the current working directory.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))  # .../expense-tracker/database
PROJECT_ROOT = os.path.dirname(_THIS_DIR)               # .../expense-tracker
DB_PATH = os.path.join(PROJECT_ROOT, "spendly.db")


def get_db():
    """Open a SQLite connection with dict-like rows and foreign keys enforced.

    PRAGMA foreign_keys must run on every connection — SQLite defaults it off
    and never persists it. The caller is responsible for closing the connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create both tables if they do not already exist. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert one demo user and 8 sample expenses. Idempotent — skips if seeded."""
    conn = get_db()
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        if row["n"] > 0:
            return  # already seeded — avoid duplicates

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid

        today = date.today()

        def d(day):
            return date(today.year, today.month, day).isoformat()  # YYYY-MM-DD

        expenses = [
            (user_id, 42.50, "Food", d(2), "Groceries"),
            (user_id, 12.00, "Food", d(9), "Lunch with team"),
            (user_id, 30.00, "Transport", d(4), "Monthly metro top-up"),
            (user_id, 120.00, "Bills", d(6), "Electricity bill"),
            (user_id, 65.00, "Health", d(8), "Pharmacy"),
            (user_id, 25.00, "Entertainment", d(11), "Movie tickets"),
            (user_id, 89.99, "Shopping", d(13), "New headphones"),
            (user_id, 15.00, "Other", d(15), "Misc"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            expenses,
        )
        conn.commit()
    finally:
        conn.close()
