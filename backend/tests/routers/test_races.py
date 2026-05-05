"""Tests for /api/v1/f1/races/* endpoints."""

from __future__ import annotations

from tests._seed import (
    make_circuit,
    make_constructor,
    make_driver,
    make_qualifying_result,
    make_race,
    make_race_result,
    make_season,
)


def _seed_race_with_metadata(db_session, *, season=2024, round_number=1):
    make_season(db_session, season)
    make_circuit(db_session, "monza", "Monza", "Italy")
    return make_race(db_session, season=season, round_number=round_number, circuit_id="monza")


# ---------------------------------------------------------------------------
# GET /races/{race_id}
# ---------------------------------------------------------------------------


class TestGetRace:
    def test_404_when_race_missing(self, client):
        response = client.get("/api/v1/f1/races/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Race not found"

    def test_returns_race_with_circuit(self, client, db_session):
        race = _seed_race_with_metadata(db_session)
        db_session.commit()

        response = client.get(f"/api/v1/f1/races/{race.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == race.id
        assert body["circuit"]["circuit_id"] == "monza"


# ---------------------------------------------------------------------------
# GET /races/{race_id}/results
# ---------------------------------------------------------------------------


class TestGetRaceResults:
    def test_404_when_race_missing(self, client):
        response = client.get("/api/v1/f1/races/999/results")
        assert response.status_code == 404

    def test_orders_by_position_with_nulls_last(self, client, db_session):
        race = _seed_race_with_metadata(db_session)
        make_driver(db_session, "winner", "Win", "Ner")
        make_driver(db_session, "second", "Sec", "Ond")
        make_driver(db_session, "dnf", "DNF", "Driver")
        make_constructor(db_session, "team_a", "Team A")
        # Insert in non-finishing order; the API must order them
        make_race_result(
            db_session, race_id=race.id, driver_id="dnf", constructor_id="team_a",
            position=None, points=0,
        )
        make_race_result(
            db_session, race_id=race.id, driver_id="second", constructor_id="team_a",
            position=2, points=18,
        )
        make_race_result(
            db_session, race_id=race.id, driver_id="winner", constructor_id="team_a",
            position=1, points=25,
        )
        db_session.commit()

        response = client.get(f"/api/v1/f1/races/{race.id}/results")

        assert response.status_code == 200
        body = response.json()
        # Positions ascending, NULL position last
        assert [r["driver"]["driver_id"] for r in body] == ["winner", "second", "dnf"]
        assert body[-1]["position"] is None

    def test_returns_empty_list_when_no_results(self, client, db_session):
        race = _seed_race_with_metadata(db_session)
        db_session.commit()

        response = client.get(f"/api/v1/f1/races/{race.id}/results")

        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# GET /races/{race_id}/qualifying
# ---------------------------------------------------------------------------


class TestGetQualifyingResults:
    def test_404_when_race_missing(self, client):
        response = client.get("/api/v1/f1/races/999/qualifying")
        assert response.status_code == 404

    def test_orders_by_position(self, client, db_session):
        race = _seed_race_with_metadata(db_session)
        make_driver(db_session, "pole", "Pole", "Sitter")
        make_driver(db_session, "p2", "Front", "Row")
        make_constructor(db_session, "team_a", "Team A")
        make_qualifying_result(db_session, race_id=race.id, driver_id="p2", constructor_id="team_a", position=2)
        make_qualifying_result(db_session, race_id=race.id, driver_id="pole", constructor_id="team_a", position=1)
        db_session.commit()

        response = client.get(f"/api/v1/f1/races/{race.id}/qualifying")

        assert response.status_code == 200
        positions = [q["position"] for q in response.json()]
        assert positions == [1, 2]

    def test_returns_empty_list_when_no_results(self, client, db_session):
        race = _seed_race_with_metadata(db_session)
        db_session.commit()

        response = client.get(f"/api/v1/f1/races/{race.id}/qualifying")
        assert response.status_code == 200
        assert response.json() == []
