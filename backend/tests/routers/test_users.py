"""Tests for /api/v1/users/me/* endpoints (PATCH, follow, dashboard)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.auth.security import create_access_token, verify_password
from app.models import User
from tests._seed import (
    make_circuit,
    make_constructor,
    make_constructor_standing,
    make_driver,
    make_driver_standing,
    make_race,
    make_race_result,
    make_season,
    make_user,
)


@pytest.fixture
def authed_user(db_session):
    """Create a user and yield (user, auth_headers).

    Uses ``create_access_token`` directly rather than going through
    /login so tests for these endpoints don't depend on the login flow.
    """
    user = make_user(db_session, email="me@example.com", username="myname", password="rightpw1")
    db_session.commit()
    token = create_access_token(subject=user.id)
    return user, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me
# ---------------------------------------------------------------------------


class TestPatchMe:
    def test_requires_auth(self, client):
        response = client.patch("/api/v1/users/me", json={"username": "new"})
        assert response.status_code == 401

    def test_updates_username(self, client, authed_user, db_session):
        _, headers = authed_user
        response = client.patch("/api/v1/users/me", headers=headers, json={"username": "newname"})

        assert response.status_code == 200
        assert response.json()["username"] == "newname"
        # Verify persisted in DB (separate session — confirms commit, not just session state)
        assert db_session.query(User).filter_by(username="newname").count() == 1

    def test_username_taken_returns_409(self, client, authed_user, db_session):
        make_user(db_session, email="other@example.com", username="taken")
        db_session.commit()
        _, headers = authed_user

        response = client.patch("/api/v1/users/me", headers=headers, json={"username": "taken"})
        assert response.status_code == 409

    def test_changes_password_with_correct_current(self, client, authed_user, db_session):
        user, headers = authed_user
        response = client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"current_password": "rightpw1", "new_password": "brandnewpw"},
        )

        assert response.status_code == 200
        db_session.refresh(user)
        assert verify_password("brandnewpw", user.hashed_password)

    def test_password_change_without_current_returns_400(self, client, authed_user):
        _, headers = authed_user
        response = client.patch(
            "/api/v1/users/me", headers=headers, json={"new_password": "brandnewpw"}
        )
        assert response.status_code == 400
        assert "current_password" in response.json()["detail"]

    def test_password_change_with_wrong_current_returns_400(self, client, authed_user):
        _, headers = authed_user
        response = client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"current_password": "WRONG_NOPE", "new_password": "brandnewpw"},
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]

    def test_can_set_username_to_current_value(self, client, authed_user):
        # Setting username to the same value should not 409 against itself
        user, headers = authed_user
        response = client.patch(
            "/api/v1/users/me", headers=headers, json={"username": user.username}
        )
        assert response.status_code == 200

    def test_empty_payload_is_noop(self, client, authed_user):
        _, headers = authed_user
        response = client.patch("/api/v1/users/me", headers=headers, json={})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Followed drivers
# ---------------------------------------------------------------------------


class TestFollowDrivers:
    def test_requires_auth(self, client):
        assert client.post("/api/v1/users/me/followed-drivers/x").status_code == 401
        assert client.delete("/api/v1/users/me/followed-drivers/x").status_code == 401
        assert client.get("/api/v1/users/me/followed-drivers").status_code == 401

    def test_follow_unknown_driver_returns_404(self, client, authed_user):
        _, headers = authed_user
        response = client.post(
            "/api/v1/users/me/followed-drivers/nope", headers=headers
        )
        assert response.status_code == 404

    def test_follow_then_list(self, client, authed_user, db_session):
        make_driver(db_session, "max_v", "Max", "Verstappen")
        db_session.commit()
        _, headers = authed_user

        post = client.post("/api/v1/users/me/followed-drivers/max_v", headers=headers)
        assert post.status_code == 204

        listing = client.get("/api/v1/users/me/followed-drivers", headers=headers)
        assert listing.status_code == 200
        ids = [d["driver_id"] for d in listing.json()]
        assert ids == ["max_v"]

    def test_follow_is_idempotent(self, client, authed_user, db_session):
        make_driver(db_session, "max_v", "Max", "Verstappen")
        db_session.commit()
        _, headers = authed_user

        client.post("/api/v1/users/me/followed-drivers/max_v", headers=headers)
        # Second follow must not error and must not duplicate
        second = client.post("/api/v1/users/me/followed-drivers/max_v", headers=headers)
        assert second.status_code == 204

        listing = client.get("/api/v1/users/me/followed-drivers", headers=headers)
        assert len(listing.json()) == 1

    def test_max_three_drivers(self, client, authed_user, db_session):
        for i in range(4):
            make_driver(db_session, f"d{i}", f"First{i}", f"Last{i}")
        db_session.commit()
        _, headers = authed_user

        for i in range(3):
            assert client.post(f"/api/v1/users/me/followed-drivers/d{i}", headers=headers).status_code == 204

        fourth = client.post("/api/v1/users/me/followed-drivers/d3", headers=headers)
        assert fourth.status_code == 400
        assert "3" in fourth.json()["detail"]

    def test_unfollow(self, client, authed_user, db_session):
        make_driver(db_session, "max_v", "Max", "Verstappen")
        db_session.commit()
        _, headers = authed_user
        client.post("/api/v1/users/me/followed-drivers/max_v", headers=headers)

        delete = client.delete("/api/v1/users/me/followed-drivers/max_v", headers=headers)
        assert delete.status_code == 204
        assert client.get("/api/v1/users/me/followed-drivers", headers=headers).json() == []

    def test_unfollow_unfollowed_is_idempotent(self, client, authed_user, db_session):
        make_driver(db_session, "max_v", "Max", "Verstappen")
        db_session.commit()
        _, headers = authed_user

        # Never followed; DELETE should still 204
        response = client.delete("/api/v1/users/me/followed-drivers/max_v", headers=headers)
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# Followed constructors
# ---------------------------------------------------------------------------


class TestFollowConstructors:
    def test_max_two_constructors(self, client, authed_user, db_session):
        for i in range(3):
            make_constructor(db_session, f"c{i}", f"Team {i}")
        db_session.commit()
        _, headers = authed_user

        for i in range(2):
            assert (
                client.post(
                    f"/api/v1/users/me/followed-constructors/c{i}", headers=headers
                ).status_code
                == 204
            )

        third = client.post("/api/v1/users/me/followed-constructors/c2", headers=headers)
        assert third.status_code == 400
        assert "2" in third.json()["detail"]

    def test_unknown_constructor_returns_404(self, client, authed_user):
        _, headers = authed_user
        response = client.post(
            "/api/v1/users/me/followed-constructors/nope", headers=headers
        )
        assert response.status_code == 404

    def test_follow_constructor_is_idempotent(self, client, authed_user, db_session):
        make_constructor(db_session, "rb", "Red Bull")
        db_session.commit()
        _, headers = authed_user

        first = client.post("/api/v1/users/me/followed-constructors/rb", headers=headers)
        second = client.post("/api/v1/users/me/followed-constructors/rb", headers=headers)
        assert first.status_code == 204
        assert second.status_code == 204
        listing = client.get("/api/v1/users/me/followed-constructors", headers=headers).json()
        assert len(listing) == 1

    def test_unfollow_unfollowed_constructor_is_idempotent(self, client, authed_user, db_session):
        make_constructor(db_session, "rb", "Red Bull")
        db_session.commit()
        _, headers = authed_user

        # Never followed; DELETE should still 204
        response = client.delete("/api/v1/users/me/followed-constructors/rb", headers=headers)
        assert response.status_code == 204

    def test_follow_unfollow_round_trip(self, client, authed_user, db_session):
        make_constructor(db_session, "rb", "Red Bull")
        db_session.commit()
        _, headers = authed_user

        client.post("/api/v1/users/me/followed-constructors/rb", headers=headers)
        listing = client.get("/api/v1/users/me/followed-constructors", headers=headers).json()
        assert [c["constructor_id"] for c in listing] == ["rb"]

        client.delete("/api/v1/users/me/followed-constructors/rb", headers=headers)
        assert client.get("/api/v1/users/me/followed-constructors", headers=headers).json() == []


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_requires_auth(self, client):
        assert client.get("/api/v1/users/me/dashboard").status_code == 401

    def test_empty_dashboard_when_no_follows_or_races(self, client, authed_user):
        _, headers = authed_user
        response = client.get("/api/v1/users/me/dashboard", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["followed_drivers"] == []
        assert body["followed_constructors"] == []
        assert body["next_race"] is None
        assert body["user"]["username"] == "myname"

    def test_includes_followed_driver_with_standing_and_results(
        self, client, authed_user, db_session
    ):
        # Seed driver, season, two races with results
        make_driver(db_session, "max_v", "Max", "Verstappen")
        make_constructor(db_session, "rb", "Red Bull")
        make_season(db_session, 2024)
        make_circuit(db_session)
        r1 = make_race(db_session, season=2024, round_number=1, race_date=date(2024, 3, 1))
        r2 = make_race(db_session, season=2024, round_number=2, race_date=date(2024, 3, 15))
        make_race_result(db_session, race_id=r1.id, driver_id="max_v", constructor_id="rb", position=1, points=25)
        make_race_result(db_session, race_id=r2.id, driver_id="max_v", constructor_id="rb", position=2, points=18)
        make_driver_standing(
            db_session, season=2024, round_number=1, driver_id="max_v",
            position=1, points=25, wins=1,
        )
        make_driver_standing(
            db_session, season=2024, round_number=2, driver_id="max_v",
            position=1, points=43, wins=1,
        )
        db_session.commit()
        _, headers = authed_user

        client.post("/api/v1/users/me/followed-drivers/max_v", headers=headers)

        response = client.get("/api/v1/users/me/dashboard", headers=headers)
        body = response.json()

        assert response.status_code == 200
        assert len(body["followed_drivers"]) == 1
        d = body["followed_drivers"][0]
        assert d["driver"]["driver_id"] == "max_v"
        # Latest standing is round 2 of 2024
        assert d["current_standing"]["round"] == 2
        assert d["current_standing"]["points"] == 43
        # Recent results ordered by race date desc
        assert [r["round"] for r in d["recent_results"]] == [2, 1]

    def test_recent_results_capped_to_three(self, client, authed_user, db_session):
        make_driver(db_session, "max_v", "Max", "Verstappen")
        make_constructor(db_session, "rb", "Red Bull")
        make_season(db_session, 2024)
        make_circuit(db_session)
        for i in range(5):
            race = make_race(
                db_session, season=2024, round_number=i + 1,
                race_date=date(2024, 3, i + 1),
            )
            make_race_result(
                db_session, race_id=race.id, driver_id="max_v",
                constructor_id="rb", position=1, points=25,
            )
        db_session.commit()
        _, headers = authed_user
        client.post("/api/v1/users/me/followed-drivers/max_v", headers=headers)

        body = client.get("/api/v1/users/me/dashboard", headers=headers).json()
        assert len(body["followed_drivers"][0]["recent_results"]) == 3

    def test_includes_followed_constructor_standing(self, client, authed_user, db_session):
        make_constructor(db_session, "rb", "Red Bull")
        make_season(db_session, 2024)
        make_constructor_standing(
            db_session, season=2024, round_number=22, constructor_id="rb",
            position=1, points=860, wins=21,
        )
        db_session.commit()
        _, headers = authed_user

        client.post("/api/v1/users/me/followed-constructors/rb", headers=headers)
        body = client.get("/api/v1/users/me/dashboard", headers=headers).json()

        assert len(body["followed_constructors"]) == 1
        c = body["followed_constructors"][0]
        assert c["constructor"]["constructor_id"] == "rb"
        assert c["current_standing"]["points"] == 860

    def test_next_race_is_soonest_future_race(self, client, authed_user, db_session):
        make_season(db_session, 2024)
        make_circuit(db_session, "monza", "Monza", country="Italy")
        # Past race — must NOT be picked
        make_race(
            db_session, season=2024, round_number=1, name="Past",
            circuit_id="monza", race_date=date.today() - timedelta(days=5),
        )
        # Two future races; the closer one must be picked
        make_race(
            db_session, season=2024, round_number=2, name="Far",
            circuit_id="monza", race_date=date.today() + timedelta(days=30),
        )
        soonest = make_race(
            db_session, season=2024, round_number=3, name="Soon",
            circuit_id="monza", race_date=date.today() + timedelta(days=2),
        )
        db_session.commit()
        _, headers = authed_user

        body = client.get("/api/v1/users/me/dashboard", headers=headers).json()
        assert body["next_race"]["id"] == soonest.id
        assert body["next_race"]["name"] == "Soon"

    def test_no_standings_returns_null_standing(self, client, authed_user, db_session):
        # Followed driver with no standing rows → current_standing is None
        make_driver(db_session, "rookie", "Brand", "New")
        db_session.commit()
        _, headers = authed_user
        client.post("/api/v1/users/me/followed-drivers/rookie", headers=headers)

        body = client.get("/api/v1/users/me/dashboard", headers=headers).json()
        assert body["followed_drivers"][0]["current_standing"] is None
        assert body["followed_drivers"][0]["recent_results"] == []
