# Spec 04 — Profile page

## Goal
Give a signed-in user a real `/profile` page: a header with their name and when they
joined, their account details, three spending figures in rupees, and their five most
recent expenses. Signed-out visitors who open it are sent to the login page, and
logging in now lands on `/profile` instead of the landing page.

## Scope
- In scope: a `login_required` decorator, the `/profile` route, `templates/profile.html`
  and `static/css/profile.css`, an initials avatar, account details (name, email,
  member since), three summary tiles (total spent, this month, expenses recorded), a
  read-only table of the five most recent expenses with category pills, an empty state,
  an `inr` template filter for rupee amounts, a "Log out" button on the page, and
  changing the login redirects to `/profile`.
- Out of scope: editing the name, email or password, deleting the account, profile
  photos, a `?next=` return URL after login, charts or category breakdowns,  editing or deleting expenses
  (Steps 7, 8 and 9). Expense rows have no edit or delete links yet.

## Files touched
- `app.py`: a `login_required` decorator, `format_inr` registered as the `inr`
  template filter, a `_initials(name)` helper, the real `profile()` route (moved into
  the implemented routes section), and both login redirects changed to `profile`.
- `templates/profile.html` (new): extends `base.html`, loads `profile.css` in the
  `head` block.
- `static/css/profile.css` (new): page styles, every class prefixed `pf-`.
- `tests/test_profile.py` (new).
- `tests/test_login.py`: the two tests that expect `Location == "/"` after a login now
  expect `/profile`. The logout tests are unchanged.
- No schema changes. `users(id, name, email, created_at)` and
  `expenses(id, user_id, amount, category, date, description)` already exist.
- `.claude/specs/03-login-and-logout.md` is not edited; this spec supersedes its
  redirect target.

## Behaviour

### `login_required` decorator
1. If `session.get("user_id")` is falsy, `redirect(url_for("login"))`.
2. Otherwise call the wrapped view with its arguments.
3. Wrap with `functools.wraps` so the endpoint name stays `profile`.
4. Only `/profile` uses it in this step. Steps 7–9 will reuse it on the expense routes.

### `GET /profile` (decorated with `@login_required`)
1. Open one connection with `get_db()` and run all queries inside a single
   `try/finally`.
2. Load the user: `SELECT name, email, created_at FROM users WHERE id = ?` with
   `session["user_id"]`.
3. If there is no row (the account was deleted while the cookie was still valid),
   `session.clear()` and `redirect(url_for("login"))`.
4. Load the totals for this user only:
   - `SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?`
   - `SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND date LIKE ?`
     with `date.today().strftime("%Y-%m") + "-%"`.
5. Load recent expenses:
   `SELECT date, category, description, amount FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5`.
6. Render `profile.html` with status 200 and these variables:
   | Variable          | Value                                                        |
   |-------------------|--------------------------------------------------------------|
   | `user`            | the `users` row (`name`, `email`)                            |
   | `initials`        | `_initials(user["name"])`                                    |
   | `member_since`    | e.g. `"November 2026"`, from `created_at`                    |
   | `total_spent`     | float, all-time sum                                          |
   | `month_spent`     | float, sum for the current calendar month                    |
   | `expense_count`   | int                                                          |
   | `recent_expenses` | list of dicts: `display_date`, `category`, `description`, `amount` |

There are no form submissions on this page, so there is no validation table. The only
error paths are the two redirects to `/login` (signed out, or stale session), both 302.

### Page layout (`profile.html`)
`{% block title %}Profile · Spendly{% endblock %}`. All content sits in
`<section class="pf-section"><div class="pf-inner">…</div></section>`, top to bottom:

1. **Header (`.pf-header`)**
   - `.pf-avatar`: a 64px circle with `initials`, `--accent-light` background,
     `--accent` text, `--font-display`.
   - `.pf-title` (`<h1>`, `--font-display`, about 2.25rem): the user's name.
   - `.pf-subtitle` (`--ink-muted`): "Member since November 2026".
2. **Account card (`.pf-card .pf-account`)**
   - Heading "Account" (`.pf-card-title`).
   - A `<dl>` with two rows: "Name" / name and "Email" / email. Labels in
     `--ink-muted`, small caps-style uppercase at about 0.75rem.
   - A "Log out" link styled `btn-ghost`, pointing to `url_for('logout')`. This is the
     only way to log out on screens under 600px, where `style.css` hides the navbar's
     non-CTA links.
3. **Summary tiles (`.pf-stats`)**: three `.pf-stat` cards in a row:
   | Label (`.pf-stat-label`) | Value (`.pf-stat-value`)        |
   |--------------------------|---------------------------------|
   | Total spent              | `total_spent \| inr`            |
   | This month               | `month_spent \| inr`            |
   | Expenses recorded        | `expense_count` (plain integer) |
   Values in `--font-display` at about 1.75rem. The "This month" tile has a
   `--accent-2` top border (3px) to set it apart; the others use `--border`.
4. **Recent expenses (`.pf-card .pf-recent`)**
   - `.pf-recent-header`: heading "Recent expenses" on the left and, when
     `expense_count > 0`, an "Add expense" link styled `btn-primary` pointing to
     `url_for('add_expense')` on the right. It leads to the Step 7 placeholder for now.
   - With expenses: `<table class="pf-table">` with columns Date, Category,
     Description, Amount.
     - Date: `display_date`, e.g. `05 Nov 2026`.
     - Category: `<span class="pf-pill">` with `--accent-light` background,
       `--accent` text, `--radius-sm`.
     - Description: the text, or `—` when empty or `NULL`.
     - Amount: `amount | inr`, right-aligned, `font-variant-numeric: tabular-nums`.
     - Header row in `--ink-muted` uppercase small text; rows separated by
       `--border-soft`.
   - Empty state (`expense_count == 0`): instead of the table and the header button,
     `.pf-empty` shows "No expenses yet." and a `btn-primary` link "Add your first
     expense" to `url_for('add_expense')`. The tiles still show `₹0.00`, `₹0.00` and `0`.

### Visual rules (`profile.css`)
- Only `:root` variables from `style.css` for colours, radii and fonts. No new hex
  values.
- `.pf-section`: `padding: 3rem 1.5rem 5rem`. `.pf-inner`: `max-width: 960px;
  margin: 0 auto`, children spaced with `display: grid; gap: 1.5rem`.
- Cards (`.pf-card`, `.pf-stat`): `--paper-card` background, 1px `--border`,
  `--radius-md`, `padding: 1.5rem`.
- `.pf-stats`: `grid-template-columns: repeat(3, 1fr)`.
- At `max-width: 700px`: `.pf-stats` becomes one column, `.pf-header` stacks the avatar
  above the text, `.pf-table` is wrapped in `.pf-table-wrap { overflow-x: auto; }` so
  it scrolls instead of overflowing, and `.pf-recent-header` wraps.
- No JavaScript on this page; leave the `scripts` block empty.

### Rupee formatting (`inr` filter)
`format_inr(amount)` returns `₹` plus the amount with two decimals and Indian digit
grouping (last three digits, then groups of two):
| Input       | Output            |
|-------------|-------------------|
| `0`         | `₹0.00`           |
| `450`       | `₹450.00`         |
| `1899`      | `₹1,899.00`       |
| `123456.5`  | `₹1,23,456.50`    |
| `10000000`  | `₹1,00,00,000.00` |
Register with `app.add_template_filter(format_inr, "inr")` so later steps can reuse it.
Amounts are always positive (the schema has `CHECK (amount > 0)`), so negatives need
no handling.

### Initials (`_initials`)
- Split the stripped name on whitespace and take the first letter of the first two
  words, upper-cased: `"Asha Rao"` → `"AR"`, `"demo user"` → `"DU"`, `"Madonna"` → `"M"`.
- If the name is empty, return `"?"`.

### Login redirects (changes Step 03 behaviour)
- A successful `POST /login` redirects to `url_for("profile")`.
- `GET /login` while signed in redirects to `url_for("profile")`.
- `/logout` still redirects to `url_for("landing")`.

## Implementation notes
- Imports: `from functools import wraps` and `from datetime import date, datetime`.
- Every query filters by `user_id = ?` with the id from the session, so one user never
  sees another's data. Use `?` placeholders only.
- Do the date formatting in the route, not the template:
  - `member_since = datetime.strptime(user["created_at"][:10], "%Y-%m-%d").strftime("%B %Y")`.
    `created_at` is SQLite `CURRENT_TIMESTAMP` (`YYYY-MM-DD HH:MM:SS`, UTC).
  - `display_date = datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y")`.
    Keep the leading zero (`05 Nov 2026`); `%-d` doesn't work on Windows.
- `format_inr`: format with `f"{float(amount):.2f}"` first, split into integer and
  decimal parts, then group the integer part (last three digits, then pairs from the
  right). Formatting first stops floating-point noise from showing.
- Jinja autoescapes names, emails and descriptions. Don't use `|safe` anywhere.
- The navbar's "Hi, <name>" comes from `session["user_name"]`, but the page itself
  uses the fresh `users` row.
- Remove the `"Profile page — coming in Step 4"` placeholder and the old undecorated
  `profile()`; Flask raises an error if two views share an endpoint name.
- Seed data trap: `seed_db()` dates every demo expense on days 01–12 of the current
  month, so on the demo account "This month" equals "Total spent" (₹6,247.00, 8
  expenses). That's expected. Tests don't rely on seed data: `conftest.py` gives each
  test an empty DB, and the tests insert rows with explicit dates, including one in an
  earlier month.
- Test trap: the "this month" test must build its dates from `date.today()`, not
  hard-coded strings, or it breaks when the month changes. Use a fixed date in an
  earlier year (e.g. `2020-01-15`) for the "not this month" row.

## Acceptance criteria
- [ ] Signed out, `GET /profile` returns 302 to `/login`.
- [ ] Signed in, `GET /profile` returns 200 and shows the user's name, email, initials
      and "Member since <Month YYYY>".
- [ ] Total spent, this month and expenses recorded match the user's own rows; another
      user's expenses are never included.
- [ ] Amounts use ₹ with two decimals and Indian grouping, e.g. `₹1,23,456.50`.
- [ ] Recent expenses shows at most five rows, newest date first, with dates like
      `05 Nov 2026` and `—` for an empty description.
- [ ] A user with no expenses sees "No expenses yet.", an "Add your first expense"
      link, and `₹0.00` totals.
- [ ] A session whose user no longer exists is cleared and redirected to `/login`.
- [ ] Logging in redirects to `/profile`, and visiting `/login` while signed in does too.
- [ ] The page has a "Log out" link to `/logout`.
- [ ] `profile.css` uses only `:root` variables, and the tiles stack into one column
      under 700px.
- [ ] All existing tests in `tests/` still pass.

## Tests (`tests/test_profile.py`, pytest + pytest-flask)
- Fixtures: `conftest.py` provides `temp_db` (autouse, fresh empty DB) and `client`.
  Add a `user` fixture inserting "Asha Rao" / `asha@example.com` with
  `generate_password_hash` (as in `test_login.py`), an `other_user` fixture, and an
  `add_expense(user_id, amount, date, category="Food", description="")` helper that
  inserts through `temp_db.get_db()`. Sign in by setting `sess["user_id"]` and
  `sess["user_name"]` inside `client.session_transaction()`.
- Signed out: `GET /profile` → 302, `Location` ends with `/login`.
- Signed in: 200; body contains `Asha Rao`, `asha@example.com`, `AR` and
  `Member since`.
- Totals: two expenses this month (100 and 250.5) and one on `2020-01-15` (1000);
  `other_user` has 5000 this month. Body contains `₹1,350.50` (total), `₹350.50`
  (this month) and the count `3`, and does not contain `₹5,000.00`.
- Recent list: insert seven expenses on consecutive days with descriptions
  `exp-1` … `exp-7`. Only `exp-3` … `exp-7` appear, and `exp-7` comes before `exp-3`
  in the body.
- Description fallback: an expense with an empty description renders `—`.
- Empty state: body contains `No expenses yet.` and `₹0.00`, and no `pf-table`.
- Stale session: set `user_id` to an id with no row → 302 to `/login`, and the session
  is empty afterwards.
- Login redirect: `POST /login` with valid credentials → `Location` ends with
  `/profile`.
- `format_inr`: parametrized over the five table values, calling the function directly.
- `_initials`: `"Asha Rao"` → `"AR"`, `"Madonna"` → `"M"`, `""` → `"?"`.
- In `tests/test_login.py`, update `test_valid_login_sets_session_and_redirects` and
  `test_signed_in_user_is_redirected_from_login` to expect `/profile`.
