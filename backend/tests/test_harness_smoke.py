"""Smoke test: confirms the SQLite + attached f1-schema harness works."""

from app.models import Driver, Season


def test_db_session_can_create_f1_models(db_session):
    db_session.add(Season(year=2024))
    db_session.add(Driver(driver_id="max_verstappen", given_name="Max", family_name="Verstappen"))
    db_session.commit()

    assert db_session.query(Season).count() == 1
    assert db_session.query(Driver).filter_by(driver_id="max_verstappen").one().given_name == "Max"


def test_service_constructs_without_real_fastf1(service):
    assert service.db is not None
    assert service.ergast is not None
