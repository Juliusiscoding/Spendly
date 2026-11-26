from datetime import date, timedelta

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


def page(client):
    resp = client.get("/profile")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


# ------------------------------------------------------------------ #
# Access                                                              #
# ------------------------------------------------------------------ #

def test_signed_out_redirects_to_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_stale_session_is_cleared(client, user):
    sign_in(client, 999)
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    assert session_data(client) == {}


def test_signed_in_shows_identity_card(client, user):
    sign_in(client, user)
    html = page(client)
    assert "Profile · Spendly" in html
    assert "css/profile.css" in html
    assert "Asha Rao" in html
    assert "asha@example.com" in html
    assert ">AR<" in html
    assert "Member since" in html
    assert 'href="/logout"' in html


def test_lucide_loaded_only_on_profile(client, user):
    sign_in(client, user)
    html = page(client)
    assert "lucide@1.81.0" in html
    assert "createIcons" in html
    assert b"lucide" not in client.get("/").data


# ------------------------------------------------------------------ #
# Summary tiles                                                       #
# ------------------------------------------------------------------ #

def test_totals_only_include_own_expenses(client, temp_db, user, other_user):
    add_expense(temp_db, user, 100, TODAY)
    add_expense(temp_db, user, 250.5, TODAY)
    add_expense(temp_db, user, 1000, "2020-01-15")
    add_expense(temp_db, other_user, 5000, TODAY)

    sign_in(client, user)
    html = page(client)
    assert "₹350.50" in html
    assert "₹1,350.50" in html
    assert ">3<" in html
    assert "₹5,000.00" not in html


def test_tile_order(client, user):
    sign_in(client, user)
    html = page(client)
    assert html.index("This month") < html.index("Total spent") < html.index("Expenses recorded")


def test_indian_grouping_on_page(client, temp_db, user):
    add_expense(temp_db, user, 123456.5, TODAY)
    sign_in(client, user)
    assert "₹1,23,456.50" in page(client)


# ------------------------------------------------------------------ #
# Recent expenses                                                     #
# ------------------------------------------------------------------ #

def test_recent_shows_five_newest_first(client, temp_db, user):
    start = date.today() - timedelta(days=30)
    for i in range(1, 8):
        day = (start + timedelta(days=i)).isoformat()
        add_expense(temp_db, user, 10 * i, day, description=f"exp-{i}-row")

    sign_in(client, user)
    html = page(client)
    assert "exp-1-row" not in html
    assert "exp-2-row" not in html
    positions = [html.index(f"exp-{i}-row") for i in (7, 6, 5, 4, 3)]
    assert positions == sorted(positions)


def test_pill_tones(client, temp_db, user):
    for category in ("Food", "Bills", "Health", "Transport"):
        add_expense(temp_db, user, 50, TODAY, category=category)

    sign_in(client, user)
    html = page(client)
    for tone in ("green", "amber", "red", "neutral"):
        assert f"pf-pill--{tone}" in html


def test_empty_description_shows_dash(client, temp_db, user):
    add_expense(temp_db, user, 50, TODAY, description="")
    sign_in(client, user)
    assert "—" in page(client)


def test_description_is_escaped(client, temp_db, user):
    add_expense(temp_db, user, 50, TODAY, description="<script>alert(1)</script>")
    sign_in(client, user)
    html = page(client)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_empty_state(client, user):
    sign_in(client, user)
    html = page(client)
    assert "No expenses yet." in html
    assert "Add your first expense" in html
    assert 'href="/expenses/add"' in html
    assert "₹0.00" in html
    assert "<table" not in html


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

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
    [("Asha Rao", "AR"), ("madonna", "M"), ("Ana Maria Lopez", "AM"), ("", "?")],
)
def test_initials(name, expected):
    assert _initials(name) == expected
