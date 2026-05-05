"""Root and health endpoints."""


def test_root_returns_running_status(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Sportsona API", "status": "running"}


def test_health_returns_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
