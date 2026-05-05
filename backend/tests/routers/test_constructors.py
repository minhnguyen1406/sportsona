"""Tests for /api/v1/f1/constructors/* endpoints."""

from __future__ import annotations

from tests._seed import make_constructor


class TestListConstructors:
    def test_returns_empty_list(self, client):
        response = client.get("/api/v1/f1/constructors")
        assert response.status_code == 200
        assert response.json() == []

    def test_orders_by_name(self, client, db_session):
        make_constructor(db_session, "red_bull", "Red Bull Racing")
        make_constructor(db_session, "ferrari", "Ferrari")
        make_constructor(db_session, "mclaren", "McLaren")
        db_session.commit()

        response = client.get("/api/v1/f1/constructors")
        names = [c["name"] for c in response.json()]
        assert names == ["Ferrari", "McLaren", "Red Bull Racing"]

    def test_pagination(self, client, db_session):
        for i in range(5):
            make_constructor(db_session, f"team_{i}", f"Team {i}")
        db_session.commit()

        first = client.get("/api/v1/f1/constructors?limit=2&offset=0").json()
        second = client.get("/api/v1/f1/constructors?limit=2&offset=2").json()

        assert len(first) == 2
        assert len(second) == 2
        first_ids = {c["constructor_id"] for c in first}
        second_ids = {c["constructor_id"] for c in second}
        assert first_ids.isdisjoint(second_ids)

    def test_limit_validation(self, client):
        assert client.get("/api/v1/f1/constructors?limit=0").status_code == 422
        assert client.get("/api/v1/f1/constructors?limit=300").status_code == 422


class TestGetConstructor:
    def test_404_when_missing(self, client):
        response = client.get("/api/v1/f1/constructors/nope")
        assert response.status_code == 404

    def test_returns_constructor(self, client, db_session):
        make_constructor(db_session, "red_bull", "Red Bull Racing", nationality="Austrian")
        db_session.commit()

        response = client.get("/api/v1/f1/constructors/red_bull")

        assert response.status_code == 200
        body = response.json()
        assert body["constructor_id"] == "red_bull"
        assert body["name"] == "Red Bull Racing"
        assert body["nationality"] == "Austrian"
