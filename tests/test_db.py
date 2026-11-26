import sqlite3

import pytest
from werkzeug.security import check_password_hash

from database import db


def test_init_creates_tables(temp_db):
    conn = temp_db.get_db()
    names = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"users", "expenses"} <= names


def test_get_db_row_factory_and_foreign_keys(temp_db):
    conn = temp_db.get_db()
    assert conn.row_factory is sqlite3.Row
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


def test_seed_is_idempotent_and_hashes_password(temp_db):
    temp_db.seed_db()
    temp_db.seed_db()
    conn = temp_db.get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    expense_count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    assert len(users) == 1
    assert expense_count > 0
    assert check_password_hash(users[0]["password_hash"], "demo123")


def test_expense_requires_existing_user(temp_db):
    conn = temp_db.get_db()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (999, 10, 'Food', '2026-01-01')"
        )
    conn.close()
