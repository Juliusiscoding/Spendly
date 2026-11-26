from werkzeug.security import check_password_hash

VALID = {"name": "Asha Rao", "email": "asha@example.com", "password": "supersecret"}


def post(client, **overrides):
    return client.post("/register", data={**VALID, **overrides})


def get_user(temp_db, email):
    conn = temp_db.get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()


def test_get_renders_form(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b"Create your account" in resp.data


def test_valid_registration_creates_user_and_redirects(client, temp_db):
    resp = post(client, name="  Asha Rao ", email="  Asha@Example.COM ")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")

    user = get_user(temp_db, "asha@example.com")
    assert user is not None
    assert user["name"] == "Asha Rao"
    assert user["password_hash"] != VALID["password"]
    assert check_password_hash(user["password_hash"], VALID["password"])


def test_missing_field(client):
    resp = post(client, name="   ")
    assert resp.status_code == 400
    assert b"All fields are required." in resp.data


def test_invalid_email(client):
    resp = post(client, email="not-an-email")
    assert resp.status_code == 400
    assert b"Please enter a valid email address." in resp.data


def test_short_password(client):
    resp = post(client, password="short")
    assert resp.status_code == 400
    assert b"Password must be at least 8 characters." in resp.data


def test_duplicate_email_is_case_insensitive(client, temp_db):
    temp_db.seed_db()
    resp = post(client, email="DEMO@spendly.com")
    assert resp.status_code == 400
    assert b"An account with that email already exists." in resp.data


def test_error_keeps_name_and_email_but_not_password(client):
    resp = post(client, password="tiny123")
    assert b'value="Asha Rao"' in resp.data
    assert b'value="asha@example.com"' in resp.data
    assert b"tiny123" not in resp.data
