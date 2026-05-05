"""Shared test fixtures.

The F1 models live in a Postgres ``f1`` schema. We emulate that on SQLite by
ATTACHing a second database file as ``f1`` so cross-schema FKs in the metadata
resolve. SQLite does not enforce cross-database FK constraints, but that is
fine for service-level tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


@pytest.fixture
def db_engine(tmp_path):
    main_db = tmp_path / "main.db"
    f1_db = tmp_path / "f1.db"
    engine = create_engine(f"sqlite:///{main_db}", future=True)

    @event.listens_for(engine, "connect")
    def _attach_f1(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute(f"ATTACH DATABASE '{f1_db}' AS f1")
        cur.close()

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_fastf1(mocker):
    """Replace the ``fastf1`` module reference inside sync_service.

    Covers ``fastf1.Cache.enable_cache`` (called in __init__) and the
    ``get_event_schedule`` / ``get_session`` functions used during sync.
    """
    return mocker.patch("app.services.f1.sync_service.fastf1")


@pytest.fixture
def mock_ergast(mocker):
    """Replace the ``Ergast`` class so ``service.ergast`` is a MagicMock."""
    fake = MagicMock()
    mocker.patch("app.services.f1.sync_service.Ergast", return_value=fake)
    return fake


@pytest.fixture
def service(db_session, mock_fastf1, mock_ergast):
    from app.services.f1.sync_service import F1DataService

    return F1DataService(db_session)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with ``get_db`` overridden to use the test session.

    The override yields the same session the test holds, so tests can seed
    data with ``db_session`` and then call the API and see it.
    """
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
