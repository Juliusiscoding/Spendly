from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import _initials, format_inr

TODAY = date.today().isoformat()


def _insert_user(temp_db, name, email):
    conn = temp_db.get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash("supersecret")),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


@pytest.fixture
def user(temp_db):
    return _insert_user(temp_db, "Asha Rao", "asha@example.com")


@pytest.fixture
def other_user(temp_db):
    return _insert_user(temp_db, "Ravi Kumar", "ravi@example.com")


def add_expense(temp_db, user_id, amount, day, category="Food", description=""):
    conn = temp_db.get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, day, description),
        )
        conn.commit()
    finally:
        conn.close()


def sign_in(client, user_id, name="Asha Rao"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = name


def session_data(client):
    with client.session_transaction() as sess:
        return dict(sess)


def test_signed_out_redirects_to_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_signed_in_shows_account_details(client, user):
    sign_in(client, user)
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"Asha Rao" in resp.data
    assert b"asha@example.com" in resp.data
    assert b">AR<" in resp.data
    assert b"Member since" in resp.data


def test_totals_only_include_own_expenses(client, temp_db, user, other_user):
    add_expense(temp_db, user, 100, TODAY)
    add_expense(temp_db, user, 250.5, TODAY)
    add_expense(temp_db, user, 1000, "2020-01-15")
    add_expense(temp_db, other_user, 5000, TODAY)

    sign_in(client, user)
    data = client.get("/profile").data
    assert "₹1,350.50".encode() in data
    assert "₹350.50".encode() in data
    assert b'class="pf-stat-value">3<' in data
    assert "₹5,000.00".encode() not in data


def test_recent_list_shows_five_newest(client, temp_db, user):
    for i in range(1, 8):
        add_expense(temp_db, user, 10 * i, f"2020-01-0{i}", description=f"exp-{i}")

    sign_in(client, user)
    data = client.get("/profile").data
    assert b"exp-1" not in data
    assert b"exp-2" not in data
    for i in range(3, 8):
        assert f"exp-{i}".encode() in data
    assert data.index(b"exp-7") < data.index(b"exp-3")
    assert b"07 Jan 2020" in data


def test_empty_description_renders_dash(client, temp_db, user):
    add_expense(temp_db, user, 99, TODAY, description="")
    sign_in(client, user)
    data = client.get("/profile").data
    assert "<td>—</td>".encode() in data


def test_empty_state(client, user):
    sign_in(client, user)
    data = client.get("/profile").data
    assert b"No expenses yet." in data
    assert b"Add your first expense" in data
    assert "₹0.00".encode() in data
    assert b"pf-table" not in data


def test_stale_session_is_cleared(client, user):
    sign_in(client, 999, name="Ghost")
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    assert session_data(client) == {}


def test_login_redirects_to_profile(client, user):
    resp = client.post("/login", data={"email": "asha@example.com", "password": "supersecret"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


@pytest.mark.parametrize(
    "amount, expected",
    [
        (0, "₹0.00"),
        (450, "₹450.00"),
        (1899, "₹1,899.00"),
        (123456.5, "₹1,23,456.50"),
        (10000000, "₹1,00,00,000.00"),
    ],
)
def test_format_inr(amount, expected):
    assert format_inr(amount) == expected


@pytest.mark.parametrize(
    "name, expected",
    [("Asha Rao", "AR"), ("demo user", "DU"), ("Madonna", "M"), ("", "?"), ("   ", "?")],
)
def test_initials(name, expected):
    assert _initials(name) == expected
