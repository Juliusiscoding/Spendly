# Spec 02 — Registration

## Goal
Let a new visitor create a Spendly account from `/register`. The account is stored
in the `users` table created in Step 1.

## Scope
- In scope: POST handling on `/register`, server-side validation, password hashing,
  inserting the user, error display, and redirecting on success.
- Out of scope: logging the user in or using sessions (that comes with login/logout in
  Step 3), email verification, password strength meters, and rate limiting.

## Files touched
- `app.py`: the `register()` route
- `templates/register.html`: keep the submitted `name`/`email` values after an error
  (the template already renders `{{ error }}`)
- No schema changes. `database/db.py` already has `users(name, email UNIQUE, password_hash)`.

## Behaviour

### `GET /register`
Renders `register.html` the same way it does now.

### `POST /register`
1. Read `name`, `email` and `password` from `request.form`.
2. Normalize: `name = name.strip()` and `email = email.strip().lower()`. The password
   is not changed.
3. Validate, in this order, and stop at the first failure:
   | Check                                      | Error message                                  |
   |--------------------------------------------|------------------------------------------------|
   | any field empty                            | "All fields are required."                     |
   | email doesn't look like `x@y.z`            | "Please enter a valid email address."          |
   | `len(password) < 8`                        | "Password must be at least 8 characters."      |
   | email already in `users`                   | "An account with that email already exists."   |
4. On failure, re-render `register.html` with `error=<message>` plus `name` and `email`
   so the form keeps them, and return HTTP **400**. Never send the password back.
5. On success, insert `(name, email, generate_password_hash(password))` using
   `get_db()`, commit, close the connection, and `redirect(url_for("login"))`.
6. The duplicate-email check must also handle a race: catch `sqlite3.IntegrityError`
   from the INSERT and show the same "already exists" error.

## Implementation notes
- Use `werkzeug.security.generate_password_hash`, which `seed_db()` already uses.
- Always use parameterized SQL (`?` placeholders) and never string formatting.
- Close the connection in a `try/finally`, as `db.py` does.
- Template inputs: add `value="{{ name or '' }}"` and `value="{{ email or '' }}"`.
  Leave the password field empty.

## Acceptance criteria
- [ ] Submitting valid details creates a row in `users` with a hashed (not plaintext)
      password and redirects to `/login`.
- [ ] The stored email is lowercased and trimmed.
- [ ] Each validation failure shows its message, returns 400, and keeps name/email filled in.
- [ ] Registering `demo@spendly.com` (or `DEMO@spendly.com`) fails with the duplicate error.
- [ ] `GET /register` is unchanged.

## Tests (`tests/test_register.py`, pytest + pytest-flask)
- Use a temporary DB: monkeypatch `database.db.DB_PATH` to a `tmp_path` file and run `init_db()`.
- Test the happy path (302 to `/login`, row exists, `check_password_hash` passes).
- Test each of the four error cases (400 and the message in the response body).
- Test that email normalization lets a mixed-case duplicate be caught.
