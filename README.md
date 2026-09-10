# ExpenseFlow — Web 💰

A personal expense tracker: Flask (Python) backend, PostgreSQL database,
and a hand-designed HTML/CSS/JS frontend — with accounts, so everyone's
expenses stay private and are exactly where they left them next time they sign in.

## What you need to do (only this)

1. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Create a local PostgreSQL database:**
   ```sql
   CREATE DATABASE expense_tracker;
   ```

3. **Open `config.py`** and fill in the three marked fields:
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "port": "5432",
       "database": "expense_tracker",   # <- your db name
       "user": "postgres",              # <- your username
       "password": "your_password",     # <- your password
   }
   ```

4. **Run it**
   ```
   python app.py
   ```
   Then open **http://127.0.0.1:5000** in your browser.

That's it — the `users` and `expenses` tables are created automatically on first run.

## How accounts work

- **Register** creates an account (username, email, password — passwords are
  hashed, never stored in plain text).
- **Log in** starts a session that lasts up to 7 days (configurable in
  `config.py` as `SESSION_LIFETIME_DAYS`) if "Keep me signed in" is checked.
- Every expense is tied to the account that created it in the database, so
  when a user logs back in — a minute later or a week later — their full
  history loads straight from Postgres, exactly as they left it.
- Two people using the same app on the same computer never see each other's
  data; each account only ever queries its own rows.

## What you get

- **Split-screen login & register pages** — clean, distinct from a generic template
- **Dashboard** — today / this-month / all-time / entry-count stats (with a
  gentle count-up animation), plus a recent-expenses ledger
- **Add / Edit Expense** — one form handles both
- **All Expenses** — search, filter by category and date range, edit, delete
- **Reports** — a category doughnut chart and a 6-month bar chart (Chart.js)

## Project files

| File / folder            | Purpose                                                |
|---------------------------|---------------------------------------------------------|
| `config.py`                | Your database credentials + app constants (only file you edit) |
| `database.py`               | All PostgreSQL queries — users and expenses            |
| `app.py`                    | Flask routes: auth pages + JSON API — run this          |
| `templates/login.html`      | Sign-in page                                             |
| `templates/register.html`   | Account creation page                                     |
| `templates/dashboard.html`  | The app shell (all four views live here)                 |
| `templates/db_error.html`   | Shown if Postgres isn't reachable yet                     |
| `static/css/style.css`      | Design tokens + shared form/button styles                |
| `static/css/auth.css`       | Login/register split-screen layout                        |
| `static/css/dashboard.css`  | Sidebar, stat cards, table, charts layout                 |
| `static/js/dashboard.js`    | All frontend behavior — fetches `/api/...`, renders views |

## Troubleshooting

- **"Database isn't connected yet" page** → check `config.py`, make sure
  Postgres is running locally and the database already exists.
- Passwords must be 6+ characters; usernames 3+ characters.
- If port 5000 is taken, run `python app.py` after changing
  `app.run(debug=True)` in `app.py` to `app.run(debug=True, port=5050)` (or any free port).
