import pytest

from database import db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every test at a fresh, empty SQLite file instead of the dev database."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    return db


@pytest.fixture
def app():
    from app import app as flask_app

    flask_app.config.update(TESTING=True)
    return flask_app
