"""Tests for /api/v1/f1/circuits/* endpoints."""

from __future__ import annotations

from tests._seed import make_circuit


class TestListCircuits:
    def test_returns_empty_list(self, client):
        response = client.get("/api/v1/f1/circuits")
        assert response.status_code == 200
        assert response.json() == []

    def test_orders_by_name(self, client, db_session):
        make_circuit(db_session, "spa", "Spa-Francorchamps")
        make_circuit(db_session, "monza", "Autodromo Nazionale Monza")
        make_circuit(db_session, "silverstone", "Silverstone Circuit")
        db_session.commit()

        response = client.get("/api/v1/f1/circuits")
        names = [c["name"] for c in response.json()]
        assert names == ["Autodromo Nazionale Monza", "Silverstone Circuit", "Spa-Francorchamps"]

    def test_pagination(self, client, db_session):
        for i in range(5):
            make_circuit(db_session, f"track_{i}", f"Track {i}")
        db_session.commit()

        first = client.get("/api/v1/f1/circuits?limit=2&offset=0").json()
        second = client.get("/api/v1/f1/circuits?limit=2&offset=2").json()

        assert len(first) == 2
        assert len(second) == 2
        first_ids = {c["circuit_id"] for c in first}
        second_ids = {c["circuit_id"] for c in second}
        assert first_ids.isdisjoint(second_ids)

    def test_limit_validation(self, client):
        assert client.get("/api/v1/f1/circuits?limit=0").status_code == 422
        assert client.get("/api/v1/f1/circuits?limit=300").status_code == 422


class TestGetCircuit:
    def test_404_when_missing(self, client):
        response = client.get("/api/v1/f1/circuits/nope")
        assert response.status_code == 404

    def test_returns_circuit(self, client, db_session):
        make_circuit(db_session, "monza", "Autodromo Nazionale Monza", country="Italy")
        db_session.commit()

        response = client.get("/api/v1/f1/circuits/monza")

        assert response.status_code == 200
        body = response.json()
        assert body["circuit_id"] == "monza"
        assert body["country"] == "Italy"
