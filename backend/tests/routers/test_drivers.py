"""Tests for /api/v1/f1/drivers/* endpoints."""

from __future__ import annotations

from datetime import date

from tests._seed import make_driver


# ---------------------------------------------------------------------------
# GET /drivers
# ---------------------------------------------------------------------------


class TestListDrivers:
    def test_returns_empty_list(self, client):
        response = client.get("/api/v1/f1/drivers")
        assert response.status_code == 200
        assert response.json() == []

    def test_orders_by_family_then_given_name(self, client, db_session):
        make_driver(db_session, "alonso", "Fernando", "Alonso")
        make_driver(db_session, "max", "Max", "Verstappen")
        make_driver(db_session, "jos", "Jos", "Verstappen")
        db_session.commit()

        response = client.get("/api/v1/f1/drivers")

        ids = [d["driver_id"] for d in response.json()]
        # Alonso < Verstappen alphabetically; within Verstappen, Jos < Max
        assert ids == ["alonso", "jos", "max"]

    def test_search_matches_given_name_case_insensitive(self, client, db_session):
        make_driver(db_session, "alonso", "Fernando", "Alonso")
        make_driver(db_session, "max", "Max", "Verstappen")
        db_session.commit()

        response = client.get("/api/v1/f1/drivers?search=fernando")

        body = response.json()
        assert len(body) == 1
        assert body[0]["driver_id"] == "alonso"

    def test_search_matches_family_name(self, client, db_session):
        make_driver(db_session, "alonso", "Fernando", "Alonso")
        make_driver(db_session, "max", "Max", "Verstappen")
        db_session.commit()

        response = client.get("/api/v1/f1/drivers?search=verstap")

        ids = [d["driver_id"] for d in response.json()]
        assert ids == ["max"]

    def test_search_matches_driver_id(self, client, db_session):
        make_driver(db_session, "max_verstappen", "Max", "Verstappen")
        make_driver(db_session, "alonso", "Fernando", "Alonso")
        db_session.commit()

        response = client.get("/api/v1/f1/drivers?search=verstap")

        ids = [d["driver_id"] for d in response.json()]
        assert "max_verstappen" in ids

    def test_pagination(self, client, db_session):
        for i in range(5):
            make_driver(db_session, f"d{i}", f"First{i}", f"Family{i}")
        db_session.commit()

        first = client.get("/api/v1/f1/drivers?limit=2&offset=0").json()
        second = client.get("/api/v1/f1/drivers?limit=2&offset=2").json()

        assert len(first) == 2
        assert len(second) == 2
        # No overlap
        first_ids = {d["driver_id"] for d in first}
        second_ids = {d["driver_id"] for d in second}
        assert first_ids.isdisjoint(second_ids)

    def test_limit_below_minimum_is_rejected(self, client):
        response = client.get("/api/v1/f1/drivers?limit=0")
        assert response.status_code == 422

    def test_limit_above_maximum_is_rejected(self, client):
        response = client.get("/api/v1/f1/drivers?limit=300")
        assert response.status_code == 422

    def test_negative_offset_is_rejected(self, client):
        response = client.get("/api/v1/f1/drivers?offset=-1")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /drivers/{driver_id}
# ---------------------------------------------------------------------------


class TestGetDriver:
    def test_404_when_missing(self, client):
        response = client.get("/api/v1/f1/drivers/nope")
        assert response.status_code == 404

    def test_returns_full_driver(self, client, db_session):
        make_driver(
            db_session, "max_verstappen", "Max", "Verstappen",
            nationality="NED", dob=date(1997, 9, 30),
        )
        db_session.commit()

        response = client.get("/api/v1/f1/drivers/max_verstappen")

        assert response.status_code == 200
        body = response.json()
        assert body["driver_id"] == "max_verstappen"
        assert body["nationality"] == "NED"
        assert body["date_of_birth"] == "1997-09-30"
