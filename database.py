"""
Database layer — every SQL statement in the app lives here.
Nothing here needs editing; credentials come from config.py.
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from datetime import date
from config import DB_CONFIG


class DatabaseError(Exception):
    pass


@contextmanager
def get_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"], port=DB_CONFIG["port"],
            dbname=DB_CONFIG["database"], user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        yield conn
    except psycopg2.OperationalError as e:
        raise DatabaseError(
            "Could not connect to PostgreSQL. Check config.py (host, port, "
            f"database, user, password) and make sure Postgres is running.\nDetails: {e}"
        )
    finally:
        if conn is not None:
            conn.close()


def init_db():
    """Creates the users and expenses tables if they don't already exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(150) NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    expense_date DATE NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);")
            conn.commit()


# ------------------------------------------------------------------- users
def create_user(username, email, password_hash):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (username, email, password_hash)
                   VALUES (%s, %s, %s) RETURNING id;""",
                (username, email, password_hash),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id


def get_user_by_login(login):
    """Looks a user up by username OR email (whichever the person typed)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE username = %s OR email = %s;",
                (login, login),
            )
            return cur.fetchone()


def get_user_by_id(user_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
            return cur.fetchone()


# ---------------------------------------------------------------- expenses
def add_expense(user_id, title, amount, category, expense_date, note=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO expenses (user_id, title, amount, category, expense_date, note)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;""",
                (user_id, title, amount, category, expense_date, note),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id


def update_expense(user_id, expense_id, title, amount, category, expense_date, note=""):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE expenses SET title=%s, amount=%s, category=%s,
                   expense_date=%s, note=%s WHERE id=%s AND user_id=%s;""",
                (title, amount, category, expense_date, note, expense_id, user_id),
            )
            conn.commit()
            return cur.rowcount


def delete_expense(user_id, expense_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s;",
                        (expense_id, user_id))
            conn.commit()
            return cur.rowcount


def get_expenses(user_id, search="", category="All", date_from=None, date_to=None):
    query = "SELECT * FROM expenses WHERE user_id = %s"
    params = [user_id]

    if search:
        query += " AND (title ILIKE %s OR note ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category and category != "All":
        query += " AND category = %s"
        params.append(category)
    if date_from:
        query += " AND expense_date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND expense_date <= %s"
        params.append(date_to)

    query += " ORDER BY expense_date DESC, id DESC"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_expense(user_id, expense_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM expenses WHERE id=%s AND user_id=%s;",
                        (expense_id, user_id))
            return cur.fetchone()


def get_summary(user_id):
    today = date.today()
    month_start = today.replace(day=1)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s;",
                        (user_id,))
            total_all = cur.fetchone()[0]
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s AND expense_date>=%s;",
                (user_id, month_start))
            total_month = cur.fetchone()[0]
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=%s AND expense_date=%s;",
                (user_id, today))
            total_today = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id=%s;", (user_id,))
            count_all = cur.fetchone()[0]
    return {
        "total_all": float(total_all), "total_month": float(total_month),
        "total_today": float(total_today), "count_all": int(count_all),
    }


def get_category_breakdown(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, SUM(amount) FROM expenses
                WHERE user_id=%s GROUP BY category ORDER BY SUM(amount) DESC;
            """, (user_id,))
            return cur.fetchall()


def get_monthly_trend(user_id, months=6):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT TO_CHAR(expense_date, 'Mon YYYY') AS label,
                       DATE_TRUNC('month', expense_date) AS month_start,
                       SUM(amount)
                FROM expenses WHERE user_id=%s
                GROUP BY label, month_start
                ORDER BY month_start DESC LIMIT %s;
            """, (user_id, months))
            rows = cur.fetchall()
            return list(reversed(rows))
