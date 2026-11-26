import pytest
from werkzeug.security import generate_password_hash

VALID = {"email": "asha@example.com", "password": "supersecret"}
INVALID = b"Invalid email or password."
REQUIRED = b"Email and password are required."


@pytest.fixture
def user(temp_db):
    conn = temp_db.get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Asha Rao", VALID["email"], generate_password_hash(VALID["password"])),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def login(client, **overrides):
    return client.post("/login", data={**VALID, **overrides})


def session_data(client):
    with client.session_transaction() as sess:
        return dict(sess)


def test_get_renders_form(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data


def test_valid_login_sets_session_and_redirects(client, user):
    resp = login(client)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"

    sess = session_data(client)
    assert sess["user_id"] == user
    assert sess["user_name"] == "Asha Rao"


def test_email_is_normalized(client, user):
    resp = login(client, email="  ASHA@Example.com ")
    assert resp.status_code == 302
    assert session_data(client)["user_id"] == user


def test_wrong_password(client, user):
    resp = login(client, password="wrongpassword")
    assert resp.status_code == 401
    assert INVALID in resp.data
    assert "user_id" not in session_data(client)


def test_unknown_email(client, user):
    resp = login(client, email="nobody@example.com")
    assert resp.status_code == 401
    assert INVALID in resp.data
    assert "user_id" not in session_data(client)


@pytest.mark.parametrize("field", ["email", "password"])
def test_missing_field(client, user, field):
    resp = login(client, **{field: "   " if field == "email" else ""})
    assert resp.status_code == 400
    assert REQUIRED in resp.data


def test_failed_login_keeps_email_but_not_password(client, user):
    resp = login(client, password="wrongpassword")
    assert b'value="asha@example.com"' in resp.data
    assert b"wrongpassword" not in resp.data


def test_signed_in_user_is_redirected_from_login(client, user):
    login(client)
    resp = client.get("/login")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"


def test_logout_clears_session(client, user):
    login(client)
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    assert session_data(client) == {}


def test_logout_when_signed_out(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_navbar_when_signed_in(client, user):
    login(client)
    resp = client.get("/")
    assert b"Log out" in resp.data
    assert b"Hi, Asha Rao" in resp.data
    assert b"Sign in" not in resp.data


def test_navbar_when_signed_out(client):
    resp = client.get("/")
    assert b"Sign in" in resp.data
    assert b"Log out" not in resp.data
