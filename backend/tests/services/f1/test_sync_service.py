"""Unit tests for ``F1DataService``.

Tests use a real SQLite session (with an attached ``f1`` schema) so SQLAlchemy
behavior is exercised end-to-end. External I/O — FastF1 sessions and the
Ergast API client — is mocked at the module-import boundary inside
``app.services.f1.sync_service``.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from app.models import (
    Circuit,
    Constructor,
    ConstructorStanding,
    Driver,
    DriverEntry,
    DriverStanding,
    Race,
    RaceResult,
    Season,
)

from tests.services.f1._factories import (
    NAN,
    ergast_constructor_standings,
    ergast_driver_standings,
    ergast_race_results,
    ergast_results_wrapper,
    ergast_schedule,
    fastf1_schedule,
    fastf1_session,
    fastf1_session_results,
)


# ---------------------------------------------------------------------------
# _ensure_* helpers
# ---------------------------------------------------------------------------


class TestEnsureSeason:
    def test_creates_when_missing(self, service, db_session):
        s = service._ensure_season(2024)
        assert s.year == 2024
        assert db_session.query(Season).count() == 1

    def test_returns_existing_without_inserting(self, service, db_session):
        db_session.add(Season(year=2024))
        db_session.commit()

        s = service._ensure_season(2024)
        assert s.year == 2024
        assert db_session.query(Season).count() == 1


class TestEnsureCircuit:
    def test_creates_with_all_fields(self, service, db_session):
        service._ensure_circuit_exists("monza", "Autodromo Nazionale Monza", country="Italy", locality="Monza")
        c = db_session.query(Circuit).filter_by(circuit_id="monza").one()
        assert c.country == "Italy"
        assert c.locality == "Monza"

    def test_existing_not_overwritten(self, service, db_session):
        db_session.add(Circuit(circuit_id="monza", name="Original"))
        db_session.commit()

        service._ensure_circuit_exists("monza", "Should Be Ignored", country="Italy")
        c = db_session.query(Circuit).filter_by(circuit_id="monza").one()
        assert c.name == "Original"  # existing record left untouched, not overwritten
        assert db_session.query(Circuit).count() == 1


class TestEnsureDriver:
    def test_creates_with_dob_and_nationality(self, service, db_session):
        service._ensure_driver_exists(
            "max_verstappen", "Max", "Verstappen", "NED", date(1997, 9, 30)
        )
        d = db_session.query(Driver).filter_by(driver_id="max_verstappen").one()
        assert d.date_of_birth == date(1997, 9, 30)
        assert d.nationality == "NED"

    def test_existing_not_overwritten(self, service, db_session):
        db_session.add(Driver(driver_id="max_verstappen", given_name="Max", family_name="Verstappen"))
        db_session.commit()

        service._ensure_driver_exists("max_verstappen", "Ignored", "Ignored")
        d = db_session.query(Driver).filter_by(driver_id="max_verstappen").one()
        assert d.given_name == "Max"
        assert db_session.query(Driver).count() == 1


class TestEnsureConstructor:
    def test_creates_with_nationality(self, service, db_session):
        service._ensure_constructor_exists("red_bull", "Red Bull Racing", "Austrian")
        c = db_session.query(Constructor).filter_by(constructor_id="red_bull").one()
        assert c.nationality == "Austrian"

    def test_existing_not_overwritten(self, service, db_session):
        db_session.add(Constructor(constructor_id="ferrari", name="Original"))
        db_session.commit()

        service._ensure_constructor_exists("ferrari", "Ignored")
        c = db_session.query(Constructor).filter_by(constructor_id="ferrari").one()
        assert c.name == "Original"
        assert db_session.query(Constructor).count() == 1


# ---------------------------------------------------------------------------
# sync_season — routing modern vs historical
# ---------------------------------------------------------------------------


class TestSyncSeasonRouting:
    def test_year_2018_uses_modern_path(self, service, mocker):
        modern = mocker.patch.object(service, "_sync_modern_season", return_value={"year": 2018})
        historical = mocker.patch.object(service, "_sync_historical_season")

        result = service.sync_season(2018)

        modern.assert_called_once_with(2018)
        historical.assert_not_called()
        assert result == {"year": 2018}

    def test_year_2017_uses_historical_path(self, service, mocker):
        modern = mocker.patch.object(service, "_sync_modern_season")
        historical = mocker.patch.object(service, "_sync_historical_season", return_value={"year": 2017})

        result = service.sync_season(2017)

        historical.assert_called_once_with(2017)
        modern.assert_not_called()
        assert result == {"year": 2017}

    def test_creates_season_row_before_routing(self, service, mocker, db_session):
        mocker.patch.object(service, "_sync_modern_season", return_value={})

        service.sync_season(2020)

        assert db_session.query(Season).filter_by(year=2020).count() == 1


# ---------------------------------------------------------------------------
# _sync_modern_season / _sync_historical_season — aggregate shape
# ---------------------------------------------------------------------------


class TestSyncSeasonAggregate:
    def test_modern_aggregates_counts(self, service, mocker):
        mocker.patch.object(service, "_sync_schedule_modern", return_value=[1, 2, 3])
        mocker.patch.object(
            service,
            "_sync_drivers_modern",
            return_value=(["d1", "d2"], ["c1"], ["e1", "e2", "e3", "e4"]),
        )

        result = service._sync_modern_season(2024)

        assert result == {
            "year": 2024,
            "races": 3,
            "drivers": 2,
            "constructors": 1,
            "driver_entries": 4,
        }

    def test_historical_aggregates_counts(self, service, mocker):
        mocker.patch.object(service, "_sync_schedule_ergast", return_value=[1, 2])
        mocker.patch.object(
            service, "_sync_drivers_ergast", return_value=(["d1"], ["c1"], ["e1"])
        )

        result = service._sync_historical_season(1990)

        assert result == {
            "year": 1990,
            "races": 2,
            "drivers": 1,
            "constructors": 1,
            "driver_entries": 1,
        }


# ---------------------------------------------------------------------------
# _sync_schedule_modern
# ---------------------------------------------------------------------------


class TestSyncScheduleModern:
    def test_creates_circuit_and_race_for_each_event(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"round": 1, "name": "Bahrain GP", "location": "Sakhir", "country": "Bahrain"},
            {"round": 2, "name": "Saudi GP", "location": "Jeddah", "country": "Saudi Arabia"},
        ])

        races = service._sync_schedule_modern(2024)

        assert len(races) == 2
        assert db_session.query(Circuit).count() == 2
        assert db_session.query(Race).count() == 2
        bahrain = db_session.query(Race).filter_by(round=1).one()
        assert bahrain.name == "Bahrain GP"
        assert bahrain.circuit_id == "sakhir"

    def test_skips_testing_events(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"round": 0, "name": "Pre-Season Test", "event_format": "testing"},
            {"round": 1, "name": "Bahrain GP", "location": "Sakhir"},
        ])

        races = service._sync_schedule_modern(2024)

        assert len(races) == 1
        assert races[0].round == 1

    def test_normalizes_circuit_id_from_location(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"round": 1, "location": "São Paulo"},
        ])

        service._sync_schedule_modern(2024)

        circuit = db_session.query(Circuit).one()
        # spaces lowercased; non-ASCII passes through unchanged
        assert circuit.circuit_id == "são_paulo"

    def test_handles_hyphenated_location(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"round": 1, "location": "Le-Castellet"},
        ])

        service._sync_schedule_modern(2024)

        assert db_session.query(Circuit).one().circuit_id == "le_castellet"

    def test_existing_race_is_not_duplicated(self, service, mock_fastf1, db_session):
        service._ensure_season(2024)
        service._ensure_circuit_exists("monza", "Monza Circuit")
        db_session.add(Race(season=2024, round=1, name="Existing", circuit_id="monza", date=date(2024, 9, 1)))
        db_session.commit()

        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"round": 1, "name": "New Name", "location": "Monza"},
        ])

        races = service._sync_schedule_modern(2024)

        assert len(races) == 1
        assert db_session.query(Race).count() == 1
        # Existing record returned, name NOT overwritten
        assert db_session.query(Race).one().name == "Existing"

    def test_converts_pandas_timestamp_to_date(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"round": 1, "event_date": pd.Timestamp("2024-09-15")},
        ])

        service._sync_schedule_modern(2024)

        assert db_session.query(Race).one().date == date(2024, 9, 15)

    def test_falls_back_to_event_name_when_official_name_missing(self, service, mock_fastf1, db_session):
        # Build a DataFrame with NO 'OfficialEventName' column to hit the fallback
        df = pd.DataFrame([{
            "RoundNumber": 1,
            "EventName": "Italian GP",
            "Location": "Monza",
            "Country": "Italy",
            "EventFormat": "conventional",
            "EventDate": pd.Timestamp("2024-09-01"),
        }])
        mock_fastf1.get_event_schedule.return_value = df

        service._sync_schedule_modern(2024)

        circuit = db_session.query(Circuit).one()
        assert circuit.name == "Italian GP"


# ---------------------------------------------------------------------------
# _sync_schedule_ergast
# ---------------------------------------------------------------------------


class TestSyncScheduleErgast:
    def test_empty_schedule_returns_empty_list(self, service, mock_ergast):
        mock_ergast.get_race_schedule.return_value = ergast_schedule([])

        races = service._sync_schedule_ergast(1950)

        assert races == []

    def test_creates_circuits_and_races(self, service, mock_ergast, db_session):
        mock_ergast.get_race_schedule.return_value = ergast_schedule([
            {"round": 1, "name": "British GP", "circuit_id": "silverstone",
             "circuit_name": "Silverstone Circuit", "country": "UK", "locality": "Silverstone",
             "race_date": "1950-05-13"},
        ])

        races = service._sync_schedule_ergast(1950)

        assert len(races) == 1
        circuit = db_session.query(Circuit).one()
        assert circuit.circuit_id == "silverstone"
        assert circuit.locality == "Silverstone"
        race = db_session.query(Race).one()
        assert race.date == date(1950, 5, 13)

    def test_handles_missing_race_date(self, service, mock_ergast, db_session):
        # raceDate as NaT/NaN triggers the None path
        df = pd.DataFrame([{
            "round": 1,
            "raceName": "Race",
            "circuitId": "monza",
            "circuitName": "Monza",
            "country": "Italy",
            "locality": "Monza",
            "raceDate": pd.NaT,
        }])
        mock_ergast.get_race_schedule.return_value = df

        # Race.date is NOT NULL in the schema, so the insert will fail at flush.
        # The test asserts the code path that yields a None date is exercised
        # before the integrity error — we check via raising at flush.
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            service._sync_schedule_ergast(1950)


# ---------------------------------------------------------------------------
# _sync_drivers_modern
# ---------------------------------------------------------------------------


class TestSyncDriversModern:
    def test_returns_empty_when_only_testing_events(self, service, mock_fastf1):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([
            {"event_format": "testing"},
            {"event_format": "testing"},
        ])

        drivers, constructors, entries = service._sync_drivers_modern(2024)

        assert (drivers, constructors, entries) == ([], [], [])

    def test_creates_driver_constructor_and_entry(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([{"round": 1}])
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "Max", "last_name": "Verstappen", "team": "Red Bull Racing",
             "driver_number": "1", "abbreviation": "VER"},
        ]))

        drivers, constructors, entries = service._sync_drivers_modern(2024)

        assert len(drivers) == 1
        assert len(constructors) == 1
        assert len(entries) == 1
        entry = db_session.query(DriverEntry).one()
        assert entry.driver_id == "max_verstappen"
        assert entry.constructor_id == "red_bull_racing"
        assert entry.driver_number == 1
        assert entry.driver_code == "VER"

    def test_dedupes_when_same_driver_appears_twice(self, service, mock_fastf1, db_session):
        # session.results sometimes lists drivers more than once across runs;
        # the seen_* sets must prevent duplicate inserts/list entries.
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([{"round": 1}])
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "Max", "last_name": "Verstappen", "team": "Red Bull Racing", "driver_number": "1"},
            {"first_name": "Max", "last_name": "Verstappen", "team": "Red Bull Racing", "driver_number": "1"},
        ]))

        drivers, constructors, entries = service._sync_drivers_modern(2024)

        assert len(drivers) == 1
        assert len(constructors) == 1
        assert len(entries) == 1
        assert db_session.query(Driver).count() == 1
        assert db_session.query(Constructor).count() == 1
        assert db_session.query(DriverEntry).count() == 1

    def test_handles_missing_driver_number(self, service, mock_fastf1, db_session):
        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([{"round": 1}])
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "Test", "last_name": "Driver", "team": "Backmarker", "driver_number": ""},
        ]))

        service._sync_drivers_modern(2024)

        assert db_session.query(DriverEntry).one().driver_number is None

    def test_existing_entry_is_not_duplicated(self, service, mock_fastf1, db_session):
        # Pre-seed a DriverEntry; second sync should not insert a second one
        service._ensure_season(2024)
        service._ensure_driver_exists("max_verstappen", "Max", "Verstappen")
        service._ensure_constructor_exists("red_bull_racing", "Red Bull Racing")
        db_session.add(DriverEntry(
            season=2024, driver_id="max_verstappen", constructor_id="red_bull_racing",
            driver_number=1, driver_code="VER",
        ))
        db_session.commit()

        mock_fastf1.get_event_schedule.return_value = fastf1_schedule([{"round": 1}])
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "Max", "last_name": "Verstappen", "team": "Red Bull Racing", "driver_number": "1"},
        ]))

        _, _, entries = service._sync_drivers_modern(2024)

        # Returned list contains only newly-inserted entries
        assert entries == []
        assert db_session.query(DriverEntry).count() == 1


# ---------------------------------------------------------------------------
# _sync_drivers_ergast
# ---------------------------------------------------------------------------


class TestSyncDriversErgast:
    def test_returns_empty_when_no_results(self, service, mock_ergast):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(None)

        result = service._sync_drivers_ergast(1990)

        assert result == ([], [], [])

    def test_returns_empty_when_content_dataframe_is_empty(self, service, mock_ergast):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(pd.DataFrame())

        assert service._sync_drivers_ergast(1990) == ([], [], [])

    def test_creates_driver_constructor_entry(self, service, mock_ergast, db_session):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "alain_prost", "given_name": "Alain", "family_name": "Prost",
             "constructor_id": "ferrari", "constructor_name": "Ferrari",
             "date_of_birth": "1955-02-24", "number": 1, "code": "PRO"},
        ]))

        drivers, constructors, entries = service._sync_drivers_ergast(1990)

        assert len(drivers) == 1
        driver = db_session.query(Driver).one()
        assert driver.date_of_birth == date(1955, 2, 24)
        entry = db_session.query(DriverEntry).one()
        assert entry.driver_number == 1

    def test_handles_missing_dob(self, service, mock_ergast, db_session):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "ghost_driver", "given_name": "Ghost", "family_name": "Driver",
             "date_of_birth": NAN},
        ]))

        service._sync_drivers_ergast(1955)

        assert db_session.query(Driver).one().date_of_birth is None

    def test_handles_missing_driver_number(self, service, mock_ergast, db_session):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "no_number", "given_name": "No", "family_name": "Number", "number": NAN},
        ]))

        service._sync_drivers_ergast(1960)

        assert db_session.query(DriverEntry).one().driver_number is None

    def test_existing_entry_is_not_duplicated(self, service, mock_ergast, db_session):
        service._ensure_season(1990)
        service._ensure_driver_exists("alain_prost", "Alain", "Prost")
        service._ensure_constructor_exists("ferrari", "Ferrari")
        db_session.add(DriverEntry(
            season=1990, driver_id="alain_prost", constructor_id="ferrari",
        ))
        db_session.commit()

        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "alain_prost", "constructor_id": "ferrari"},
        ]))

        _, _, entries = service._sync_drivers_ergast(1990)
        assert entries == []
        assert db_session.query(DriverEntry).count() == 1


# ---------------------------------------------------------------------------
# sync_race_results — routing
# ---------------------------------------------------------------------------


class TestSyncRaceResultsRouting:
    def test_modern_year_uses_fastf1(self, service, mocker):
        modern = mocker.patch.object(service, "_sync_race_results_modern", return_value=[])
        ergast = mocker.patch.object(service, "_sync_race_results_ergast")

        service.sync_race_results(2018, 1)

        modern.assert_called_once_with(2018, 1)
        ergast.assert_not_called()

    def test_historical_year_uses_ergast(self, service, mocker):
        modern = mocker.patch.object(service, "_sync_race_results_modern")
        ergast = mocker.patch.object(service, "_sync_race_results_ergast", return_value=[])

        service.sync_race_results(2017, 1)

        ergast.assert_called_once_with(2017, 1)
        modern.assert_not_called()


# ---------------------------------------------------------------------------
# _sync_race_results_modern
# ---------------------------------------------------------------------------


def _seed_race(db_session, service, *, year=2024, round_number=1):
    """Pre-create a Race so race-result tests have a target row."""
    service._ensure_season(year)
    service._ensure_circuit_exists("monza", "Monza")
    race = Race(season=year, round=round_number, name="Race", circuit_id="monza", date=date(year, 9, 1))
    db_session.add(race)
    db_session.commit()
    return race


class TestSyncRaceResultsModern:
    def test_raises_when_race_not_found(self, service, mock_fastf1):
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([{}]))

        with pytest.raises(ValueError, match="Race not found"):
            service._sync_race_results_modern(2024, 99)

    def test_creates_race_result(self, service, mock_fastf1, db_session):
        race = _seed_race(db_session, service)
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "Max", "last_name": "Verstappen", "team": "Red Bull Racing",
             "position": 1.0, "grid": 1.0, "points": 25.0, "laps": 50.0, "status": "Finished"},
        ]))

        results = service._sync_race_results_modern(2024, 1)

        assert len(results) == 1
        rr = db_session.query(RaceResult).one()
        assert rr.race_id == race.id
        assert rr.position == 1
        assert rr.position_text == "1"
        assert rr.points == 25.0
        assert rr.status == "Finished"

    def test_dnf_yields_status_R_and_null_position(self, service, mock_fastf1, db_session):
        _seed_race(db_session, service)
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "DNF", "last_name": "Driver", "position": NAN, "grid": 5.0, "points": 0.0,
             "status": "Collision"},
        ]))

        service._sync_race_results_modern(2024, 1)

        rr = db_session.query(RaceResult).one()
        assert rr.position is None
        assert rr.position_text == "R"
        assert rr.grid_position == 5

    def test_handles_missing_grid_column(self, service, mock_fastf1, db_session):
        _seed_race(db_session, service)
        df = pd.DataFrame([{
            "FirstName": "No", "LastName": "Grid",
            "TeamName": "Team", "CountryCode": "X", "DriverNumber": "1", "Abbreviation": "NOG",
            "Position": 1.0, "Points": 25.0, "NumberOfLaps": 50.0,
            "Time": "1:30", "Status": "Finished",
        }])
        mock_fastf1.get_session.return_value = fastf1_session(df)

        service._sync_race_results_modern(2024, 1)

        assert db_session.query(RaceResult).one().grid_position is None

    def test_handles_nan_time(self, service, mock_fastf1, db_session):
        _seed_race(db_session, service)
        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "X", "last_name": "Y", "time": NAN},
        ]))

        service._sync_race_results_modern(2024, 1)

        assert db_session.query(RaceResult).one().time is None

    def test_existing_result_not_duplicated(self, service, mock_fastf1, db_session):
        race = _seed_race(db_session, service)
        service._ensure_driver_exists("max_verstappen", "Max", "Verstappen")
        service._ensure_constructor_exists("red_bull_racing", "Red Bull Racing")
        db_session.add(RaceResult(
            race_id=race.id, driver_id="max_verstappen",
            constructor_id="red_bull_racing", position=1, position_text="1", points=25,
        ))
        db_session.commit()

        mock_fastf1.get_session.return_value = fastf1_session(fastf1_session_results([
            {"first_name": "Max", "last_name": "Verstappen", "team": "Red Bull Racing"},
        ]))

        service._sync_race_results_modern(2024, 1)

        assert db_session.query(RaceResult).count() == 1


# ---------------------------------------------------------------------------
# _sync_race_results_ergast
# ---------------------------------------------------------------------------


class TestSyncRaceResultsErgast:
    def test_empty_content_returns_empty_list(self, service, mock_ergast):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(None)
        assert service._sync_race_results_ergast(1990, 1) == []

    def test_empty_content_dataframe_returns_empty_list(self, service, mock_ergast):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(pd.DataFrame())
        assert service._sync_race_results_ergast(1990, 1) == []

    def test_raises_when_race_not_found(self, service, mock_ergast):
        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([{}]))

        with pytest.raises(ValueError, match="Race not found"):
            service._sync_race_results_ergast(1990, 1)

    def test_creates_drivers_and_constructors_implicitly(self, service, mock_ergast, db_session):
        # Pre-seed only the race; driver/constructor must be created by the sync
        service._ensure_season(1990)
        service._ensure_circuit_exists("monza", "Monza")
        race = Race(season=1990, round=1, name="Race", circuit_id="monza", date=date(1990, 9, 1))
        db_session.add(race)
        db_session.commit()

        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "alain_prost", "constructor_id": "ferrari", "position": 1, "points": 9.0},
        ]))

        results = service._sync_race_results_ergast(1990, 1)

        assert len(results) == 1
        assert db_session.query(Driver).filter_by(driver_id="alain_prost").count() == 1
        assert db_session.query(Constructor).filter_by(constructor_id="ferrari").count() == 1
        rr = db_session.query(RaceResult).one()
        assert rr.position == 1
        assert rr.points == 9.0

    def test_handles_nan_position(self, service, mock_ergast, db_session):
        service._ensure_season(1990)
        service._ensure_circuit_exists("monza", "Monza")
        db_session.add(Race(season=1990, round=1, name="R", circuit_id="monza", date=date(1990, 9, 1)))
        db_session.commit()

        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "ghost", "constructor_id": "ghost_team", "position": NAN,
             "position_text": "R", "grid": NAN, "points": NAN, "laps": NAN},
        ]))

        service._sync_race_results_ergast(1990, 1)

        rr = db_session.query(RaceResult).one()
        assert rr.position is None
        assert rr.position_text == "R"
        assert rr.grid_position is None
        assert rr.points == 0
        assert rr.laps is None

    def test_existing_result_not_duplicated(self, service, mock_ergast, db_session):
        service._ensure_season(1990)
        service._ensure_driver_exists("alain_prost", "Alain", "Prost")
        service._ensure_constructor_exists("ferrari", "Ferrari")
        service._ensure_circuit_exists("monza", "Monza")
        race = Race(season=1990, round=1, name="R", circuit_id="monza", date=date(1990, 9, 1))
        db_session.add(race)
        db_session.flush()
        db_session.add(RaceResult(
            race_id=race.id, driver_id="alain_prost", constructor_id="ferrari",
            position=1, position_text="1", points=9,
        ))
        db_session.commit()

        mock_ergast.get_race_results.return_value = ergast_results_wrapper(ergast_race_results([
            {"driver_id": "alain_prost", "constructor_id": "ferrari"},
        ]))

        service._sync_race_results_ergast(1990, 1)

        assert db_session.query(RaceResult).count() == 1


# ---------------------------------------------------------------------------
# sync_standings (orchestration)
# ---------------------------------------------------------------------------


class TestSyncStandings:
    def test_returns_zeros_when_no_past_races(self, service, mock_ergast, db_session):
        # No races at all
        result = service.sync_standings(2024)
        assert result == {"driver_standings": 0, "constructor_standings": 0}
        mock_ergast.get_driver_standings.assert_not_called()

    def test_uses_last_round_with_date_in_past(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        service._ensure_circuit_exists("monza", "Monza")
        today = date.today()
        # Round 5 is in the past; round 6 is in the future and must be ignored
        db_session.add_all([
            Race(season=2024, round=5, name="R5", circuit_id="monza", date=today - timedelta(days=7)),
            Race(season=2024, round=6, name="R6", circuit_id="monza", date=today + timedelta(days=7)),
        ])
        db_session.commit()

        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(
            ergast_driver_standings([{"position": 1}])
        )
        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(
            ergast_constructor_standings([{"position": 1}])
        )

        result = service.sync_standings(2024)

        assert result["round"] == 5
        assert result["driver_standings"] == 1
        assert result["constructor_standings"] == 1
        mock_ergast.get_driver_standings.assert_called_once_with(2024, round=5)


# ---------------------------------------------------------------------------
# _sync_driver_standings / _sync_constructor_standings
# ---------------------------------------------------------------------------


class TestSyncDriverStandings:
    def test_empty_content_returns_zero(self, service, mock_ergast):
        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(None)
        assert service._sync_driver_standings(2024, 5) == 0

    def test_empty_dataframe_returns_zero(self, service, mock_ergast):
        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(pd.DataFrame())
        assert service._sync_driver_standings(2024, 5) == 0

    def test_inserts_standings_and_creates_drivers(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(
            ergast_driver_standings([
                {"driver_id": "max_verstappen", "given_name": "Max", "family_name": "Verstappen",
                 "position": 1, "points": 575.0, "wins": 19},
                {"driver_id": "lando_norris", "given_name": "Lando", "family_name": "Norris",
                 "position": 2, "points": 374.0, "wins": 4},
            ])
        )

        count = service._sync_driver_standings(2024, 22)

        assert count == 2
        assert db_session.query(Driver).count() == 2
        top = db_session.query(DriverStanding).filter_by(position=1).one()
        assert top.driver_id == "max_verstappen"
        assert top.points == 575.0
        assert top.wins == 19

    def test_skips_rows_with_nan_position(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(
            ergast_driver_standings([
                {"driver_id": "valid", "position": 1},
                {"driver_id": "no_position", "position": NAN},
            ])
        )

        count = service._sync_driver_standings(2024, 22)

        assert count == 1
        assert db_session.query(DriverStanding).count() == 1

    def test_handles_nan_points_and_wins(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(
            ergast_driver_standings([
                {"driver_id": "ghost", "position": 1, "points": NAN, "wins": NAN},
            ])
        )

        service._sync_driver_standings(2024, 22)
        s = db_session.query(DriverStanding).one()
        assert s.points == 0
        assert s.wins == 0

    def test_existing_standing_not_duplicated(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        service._ensure_driver_exists("max_verstappen", "Max", "Verstappen")
        db_session.add(DriverStanding(
            season=2024, round=22, driver_id="max_verstappen",
            position=1, points=575.0, wins=19,
        ))
        db_session.commit()

        mock_ergast.get_driver_standings.return_value = ergast_results_wrapper(
            ergast_driver_standings([
                {"driver_id": "max_verstappen", "position": 1, "points": 999.0},
            ])
        )

        count = service._sync_driver_standings(2024, 22)

        assert count == 0
        assert db_session.query(DriverStanding).count() == 1
        # Existing row's points were not overwritten
        assert db_session.query(DriverStanding).one().points == 575.0


class TestSyncConstructorStandings:
    def test_empty_content_returns_zero(self, service, mock_ergast):
        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(None)
        assert service._sync_constructor_standings(2024, 5) == 0

    def test_empty_dataframe_returns_zero(self, service, mock_ergast):
        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(pd.DataFrame())
        assert service._sync_constructor_standings(2024, 5) == 0

    def test_inserts_standings_and_creates_constructors(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(
            ergast_constructor_standings([
                {"constructor_id": "red_bull", "constructor_name": "Red Bull",
                 "position": 1, "points": 860.0, "wins": 21},
            ])
        )

        count = service._sync_constructor_standings(2024, 22)

        assert count == 1
        assert db_session.query(Constructor).count() == 1
        s = db_session.query(ConstructorStanding).one()
        assert s.constructor_id == "red_bull"
        assert s.points == 860.0
        assert s.wins == 21

    def test_skips_rows_with_nan_position(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(
            ergast_constructor_standings([
                {"constructor_id": "valid", "position": 1},
                {"constructor_id": "no_position", "position": NAN},
            ])
        )

        assert service._sync_constructor_standings(2024, 22) == 1
        assert db_session.query(ConstructorStanding).count() == 1

    def test_handles_nan_points_and_wins(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(
            ergast_constructor_standings([
                {"constructor_id": "ghost", "position": 1, "points": NAN, "wins": NAN},
            ])
        )
        service._sync_constructor_standings(2024, 22)
        s = db_session.query(ConstructorStanding).one()
        assert s.points == 0
        assert s.wins == 0

    def test_existing_standing_not_duplicated(self, service, mock_ergast, db_session):
        service._ensure_season(2024)
        service._ensure_constructor_exists("red_bull", "Red Bull")
        db_session.add(ConstructorStanding(
            season=2024, round=22, constructor_id="red_bull",
            position=1, points=860.0, wins=21,
        ))
        db_session.commit()

        mock_ergast.get_constructor_standings.return_value = ergast_results_wrapper(
            ergast_constructor_standings([
                {"constructor_id": "red_bull", "position": 1, "points": 999.0},
            ])
        )

        assert service._sync_constructor_standings(2024, 22) == 0
        assert db_session.query(ConstructorStanding).one().points == 860.0
