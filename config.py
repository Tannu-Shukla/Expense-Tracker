"""
============================================================
 CONFIGURATION
============================================================
 LOCAL USE: fill in the DB_CONFIG values marked "FILL ME IN" below.
 HOSTED USE (Render + Neon etc.): don't edit this file at all —
 instead set DATABASE_URL and SECRET_KEY as environment variables
 on your hosting platform. If DATABASE_URL is set, it's used
 automatically instead of DB_CONFIG.
============================================================
"""

import os

# Set automatically by Neon/Render — a full connection string like
# postgres://user:password@host/dbname. Takes priority over DB_CONFIG below.
DATABASE_URL = os.environ.get("DATABASE_URL")

DB_CONFIG = {
    "host": "localhost",       # leave as-is for a local Postgres install
    "port": "5432",            # default Postgres port, change only if yours differs
    "database": "FILL_ME_IN",  # <-- FILL ME IN: your database name, e.g. "expense_tracker"
    "user": "FILL_ME_IN",      # <-- FILL ME IN: your Postgres username, e.g. "postgres"
    "password": "FILL_ME_IN",  # <-- FILL ME IN: your Postgres password
}

# Used to sign login session cookies. Set a real SECRET_KEY environment
# variable when hosting; this fallback is only fine for local use.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-please-change-this-secret-key")

# How many days a user stays logged in before needing to sign in again
SESSION_LIFETIME_DAYS = 7

CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills", "Entertainment",
    "Health", "Education", "Groceries", "Rent", "Other",
]
