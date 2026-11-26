# Spec 03 — Login and logout

## Goal
Let a registered user sign in from `/login` and sign out from `/logout`. A signed-in
user is remembered with Flask's cookie-based `session`, and the navbar shows whether
someone is signed in.

## Scope
- In scope: a `SECRET_KEY` so sessions work, POST handling on `/login`, checking the
  password hash, storing the user in `session`, the real `/logout` route, keeping the
  submitted email after a failed login, and a navbar that changes when signed in.
- Out of scope: protecting pages behind login (a `login_required` helper comes with the
  profile page in Step 4), "remember me", password reset, rate limiting or lockout,
  CSRF tokens, and signing the user in automatically after registration.

## Files touched
- `app.py`: app config (`SECRET_KEY`), the `login()` and `logout()` routes
- `templates/login.html`: keep the submitted `email` value after an error
- `templates/base.html`: navbar links depend on whether someone is signed in
- No schema changes. `users(id, name, email, password_hash)` already exists.

## Behaviour

### Configuration
- Set `app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")`
  right after `app = Flask(__name__)`. The fallback is only for local development.

### Session contents
- A signed-in user has `session["user_id"]` (the `users.id`) and `session["user_name"]`
  (the `users.name`). Nothing else about the user goes in the session, and the password
  or hash never does.

### `GET /login`
1. If `session` already has `user_id`, `redirect(url_for("profile"))`.
2. Otherwise render `login.html` as it does now.

### `POST /login`
1. Read `email` and `password` from `request.form`.
2. Normalize: `email = email.strip().lower()`, the same as registration. The password
   is not changed.
3. Validate, in this order, and stop at the first failure:
   | Check                                         | Error message                        | Status |
   |-----------------------------------------------|--------------------------------------|--------|
   | email or password empty                       | "Email and password are required."   | 400    |
   | no user with that email                       | "Invalid email or password."         | 401    |
   | `check_password_hash` fails                   | "Invalid email or password."         | 401    |
4. On failure, re-render `login.html` with `error=<message>` and `email` so the form
   keeps it. Never send the password back. The two "invalid" cases must use the exact
   same message so the page doesn't reveal which emails are registered.
5. On success:
   - `session.clear()` first, so no data from an earlier session carries over
   - set `session["user_id"]` and `session["user_name"]`
   - `redirect(url_for("profile"))` (still the Step 4 placeholder, which is fine)

### `GET /logout`
1. `session.clear()`.
2. `redirect(url_for("landing"))`.
3. Works even if nobody is signed in (it just redirects).

### Navbar (`base.html`)
- Signed out (no `session.user_id`): the current "Sign in" and "Get started" links.
- Signed in: a "Hi, {{ session.user_name }}" link to `url_for('profile')` and a
  "Log out" link to `url_for('logout')`. Reuse the existing `.nav-links` styles; the
  log-out link must not use the `nav-cta` style.

## Implementation notes
- Import `session` from `flask` and `check_password_hash` from `werkzeug.security`.
- Look up the user with parameterized SQL:
  `SELECT id, name, password_hash FROM users WHERE email = ?`.
- Close the connection in a `try/finally`, as `register()` does.
- Add a small `_login_error(message, email, status)` helper, matching
  `_register_error`.
- Template input: add `value="{{ email or '' }}"` to the email field. Leave the
  password field empty.
- The seeded demo user is `demo@spendly.com` / `demo123`. Its password is shorter than
  the 8-character registration minimum, so login must not check password length.

## Acceptance criteria
- [ ] Signing in as `demo@spendly.com` / `demo123` redirects to `/profile` and sets
      `user_id` and `user_name` in the session.
- [ ] `DEMO@spendly.com` with surrounding spaces also signs in.
- [ ] A wrong password and an unknown email both show "Invalid email or password." with 401.
- [ ] An empty field shows "Email and password are required." with 400.
- [ ] After a failed login the email field keeps its value and the password field is empty.
- [ ] Visiting `/login` while signed in redirects to `/profile`.
- [ ] `/logout` clears the session and redirects to `/`, and works when signed out.
- [ ] The navbar shows "Hi, <name>" and "Log out" when signed in, and "Sign in" and
      "Get started" when signed out.
- [ ] All existing tests in `tests/` still pass.

## Tests (`tests/test_login.py`, pytest + pytest-flask)
- `conftest.py` already points `DB_PATH` at a fresh temp DB for each test. Create a
  user in each test (or a fixture) by inserting a row with `generate_password_hash`.
- Happy path: 302 to `/profile`, and `session["user_id"]` matches (check with
  `with client.session_transaction() as sess:`).
- Email normalization: mixed case with spaces still signs in.
- Wrong password and unknown email: 401, the same message, no `user_id` in session.
- Empty fields: 400 and the required message.
- Signed-in `GET /login` redirects to `/profile`.
- Logout: after signing in, `GET /logout` redirects to `/` and the session is empty.
- Navbar: after signing in, `GET /` contains "Log out" and the user's name; signed out
  it contains "Sign in".
