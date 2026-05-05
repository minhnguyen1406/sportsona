"""Tests for /api/v1/f1/seasons/* endpoints."""

from __future__ import annotations

from datetime import date

from tests._seed import (
    make_circuit,
    make_constructor,
    make_constructor_standing,
    make_driver,
    make_driver_standing,
    make_race,
    make_season,
)


# ---------------------------------------------------------------------------
# GET /seasons
# ---------------------------------------------------------------------------


class TestListSeasons:
    def test_returns_empty_list_when_no_seasons(self, client):
        response = client.get("/api/v1/f1/seasons")
        assert response.status_code == 200
        assert response.json() == []

    def test_orders_by_year_descending(self, client, db_session):
        for year in (2022, 2024, 2023):
            make_season(db_session, year)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons")

        assert response.status_code == 200
        years = [s["year"] for s in response.json()]
        assert years == [2024, 2023, 2022]


# ---------------------------------------------------------------------------
# GET /seasons/{year}/races
# ---------------------------------------------------------------------------


class TestListRacesBySeason:
    def test_404_when_no_races(self, client):
        response = client.get("/api/v1/f1/seasons/2024/races")
        assert response.status_code == 404
        assert "2024" in response.json()["detail"]

    def test_orders_by_round_and_includes_circuit(self, client, db_session):
        make_season(db_session, 2024)
        make_circuit(db_session, "monza", "Monza", "Italy")
        make_circuit(db_session, "spa", "Spa", "Belgium")
        # Insert out of order to verify ordering
        make_race(db_session, season=2024, round_number=2, name="Spa GP", circuit_id="spa")
        make_race(db_session, season=2024, round_number=1, name="Monza GP", circuit_id="monza")
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/races")

        assert response.status_code == 200
        body = response.json()
        assert [r["round"] for r in body] == [1, 2]
        assert body[0]["circuit"]["circuit_id"] == "monza"
        assert body[0]["circuit"]["country"] == "Italy"

    def test_only_returns_races_for_given_year(self, client, db_session):
        make_season(db_session, 2023)
        make_season(db_session, 2024)
        make_circuit(db_session)
        make_race(db_session, season=2023, round_number=1)
        make_race(db_session, season=2024, round_number=1)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/races")

        assert response.status_code == 200
        seasons = {r["season"] for r in response.json()}
        assert seasons == {2024}


# ---------------------------------------------------------------------------
# GET /seasons/{year}/standings/drivers
# ---------------------------------------------------------------------------


class TestDriverStandings:
    def test_404_when_no_standings(self, client):
        response = client.get("/api/v1/f1/seasons/2024/standings/drivers")
        assert response.status_code == 404

    def test_defaults_to_latest_round(self, client, db_session):
        make_season(db_session, 2024)
        make_driver(db_session, "max_verstappen", "Max", "Verstappen")
        make_driver_standing(db_session, season=2024, round_number=5, driver_id="max_verstappen", points=100)
        make_driver_standing(db_session, season=2024, round_number=10, driver_id="max_verstappen", points=250)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/standings/drivers")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["round"] == 10
        assert body[0]["points"] == 250

    def test_explicit_round_query_param(self, client, db_session):
        make_season(db_session, 2024)
        make_driver(db_session, "max_verstappen", "Max", "Verstappen")
        make_driver_standing(db_session, season=2024, round_number=5, driver_id="max_verstappen", points=100)
        make_driver_standing(db_session, season=2024, round_number=10, driver_id="max_verstappen", points=250)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/standings/drivers?round=5")

        assert response.status_code == 200
        assert response.json()[0]["points"] == 100

    def test_orders_by_position_and_includes_driver(self, client, db_session):
        make_season(db_session, 2024)
        make_driver(db_session, "norris", "Lando", "Norris")
        make_driver(db_session, "max", "Max", "Verstappen")
        make_driver_standing(db_session, season=2024, round_number=22, driver_id="norris", position=2, points=374)
        make_driver_standing(db_session, season=2024, round_number=22, driver_id="max", position=1, points=575)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/standings/drivers")

        body = response.json()
        assert [s["position"] for s in body] == [1, 2]
        assert body[0]["driver"]["driver_id"] == "max"
        assert body[0]["driver"]["given_name"] == "Max"


# ---------------------------------------------------------------------------
# GET /seasons/{year}/standings/constructors
# ---------------------------------------------------------------------------


class TestConstructorStandings:
    def test_404_when_no_standings(self, client):
        response = client.get("/api/v1/f1/seasons/2024/standings/constructors")
        assert response.status_code == 404

    def test_defaults_to_latest_round(self, client, db_session):
        make_season(db_session, 2024)
        make_constructor(db_session, "red_bull", "Red Bull")
        make_constructor_standing(db_session, season=2024, round_number=5, constructor_id="red_bull", points=200)
        make_constructor_standing(db_session, season=2024, round_number=10, constructor_id="red_bull", points=500)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/standings/constructors")

        body = response.json()
        assert len(body) == 1
        assert body[0]["round"] == 10
        assert body[0]["points"] == 500

    def test_explicit_round_query_param(self, client, db_session):
        make_season(db_session, 2024)
        make_constructor(db_session, "red_bull", "Red Bull")
        make_constructor_standing(db_session, season=2024, round_number=5, constructor_id="red_bull", points=200)
        make_constructor_standing(db_session, season=2024, round_number=10, constructor_id="red_bull", points=500)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/standings/constructors?round=5")

        assert response.json()[0]["points"] == 200

    def test_orders_by_position_and_includes_constructor(self, client, db_session):
        make_season(db_session, 2024)
        make_constructor(db_session, "ferrari", "Ferrari")
        make_constructor(db_session, "red_bull", "Red Bull")
        make_constructor_standing(db_session, season=2024, round_number=22, constructor_id="ferrari", position=2, points=652)
        make_constructor_standing(db_session, season=2024, round_number=22, constructor_id="red_bull", position=1, points=860)
        db_session.commit()

        response = client.get("/api/v1/f1/seasons/2024/standings/constructors")
        body = response.json()
        assert [s["position"] for s in body] == [1, 2]
        assert body[0]["constructor"]["constructor_id"] == "red_bull"
