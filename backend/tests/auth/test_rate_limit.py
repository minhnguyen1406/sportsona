"""Tests that auth endpoints enforce rate limits."""


class TestRateLimitLogin:
    def test_returns_429_after_11_attempts(self, client):
        # Default limit is 10/minute. The 11th request must be rejected.
        for _ in range(10):
            r = client.post(
                "/api/v1/auth/login",
                data={"username": "nope@example.com", "password": "wrong-pw"},
            )
            # Each is 401 (unknown user) but the limiter still counts the call.
            assert r.status_code == 401

        rejected = client.post(
            "/api/v1/auth/login",
            data={"username": "nope@example.com", "password": "wrong-pw"},
        )
        assert rejected.status_code == 429


class TestRateLimitRegister:
    def test_returns_429_after_11_attempts(self, client):
        for i in range(10):
            r = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"u{i}@example.com",
                    "username": f"user_{i}",
                    "password": "supersecret1",
                },
            )
            assert r.status_code in (201, 422)

        rejected = client.post(
            "/api/v1/auth/register",
            json={
                "email": "u11@example.com",
                "username": "user_11",
                "password": "supersecret1",
            },
        )
        assert rejected.status_code == 429
