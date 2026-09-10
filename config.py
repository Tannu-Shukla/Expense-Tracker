"""
============================================================
 CONFIGURATION
============================================================
 Fill in ONLY the values marked "FILL ME IN" below.
============================================================
"""

DB_CONFIG = {
    "host": "localhost",       # leave as-is for a local Postgres install
    "port": "5432",            # default Postgres port, change only if yours differs
    "database": "expense_tracker",  # <-- FILL ME IN: your database name, e.g. "expense_tracker"
    "user": "postgres",      # <-- FILL ME IN: your Postgres username, e.g. "postgres"
    "password": "Tannu",  # <-- FILL ME IN: your Postgres password
}

# Used to sign login session cookies. Works out of the box, but change this
# to any random string before you put the app anywhere other people can reach.
SECRET_KEY = "dev-please-change-this-secret-key"

# How many days a user stays logged in before needing to sign in again
SESSION_LIFETIME_DAYS = 7

CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills", "Entertainment",
    "Health", "Education", "Groceries", "Rent", "Other",
]
