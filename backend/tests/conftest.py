"""Shared test fixtures.

We use SQLAlchemy's "external transaction" pattern so each test runs inside
a connection-scoped transaction that is rolled back at the end. The test's
session and any sessions opened by request handlers share the same
connection but are otherwise independent — this surfaces real session
lifecycle bugs (stale references, detached instances) that a single shared
session would mask.

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


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the in-memory rate limiter between tests so counts don't bleed."""
    from app.auth.rate_limit import limiter
    yield
    limiter.reset()


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
def db_connection(db_engine):
    """One connection scoped to the test, with an outer transaction that we
    roll back on teardown. All sessions in the test bind to this connection
    so they share an isolated view of the database.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(db_connection) -> Session:
    """Test-side session bound to ``db_connection``.

    Inner ``commit()`` calls (in tests or in the SUT) close a SAVEPOINT but
    do not end the outer transaction; we re-enter another savepoint via the
    ``after_transaction_end`` listener so the next commit has somewhere to
    land. This is the canonical SQLAlchemy pattern from the docs.
    """
    nested = db_connection.begin_nested()  # noqa: F841 — held by SQLAlchemy
    SessionLocal = sessionmaker(bind=db_connection, autoflush=False, autocommit=False)
    session = SessionLocal()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            db_connection.begin_nested()

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
def client(db_connection, db_session):
    """FastAPI TestClient where each request gets its *own* session bound to
    the same connection as ``db_session``.

    Depending on ``db_session`` is intentional: it makes the test fixture's
    nested-savepoint listener active before any request is handled, so
    request-side commits land safely inside the outer transaction.
    """
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.main import app

    RequestSession = sessionmaker(bind=db_connection, autoflush=False, autocommit=False)

    def _override_get_db():
        s = RequestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
