
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "EventSphere" in response.text



def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_docs():
    response = client.get("/docs")
    assert response.status_code == 200


def test_register_invalid_email():
    response = client.post(
        "/users/register",
        json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "SecurePass123"
        }
    )
    assert response.status_code == 422


def test_register_short_password():
    response = client.post(
        "/users/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "123"
        }
    )
    assert response.status_code == 422

