from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)

def test_signup_and_login():
    signup_data = {
        "username": "testuser",
        "password": "securepassword123"
    }
    response = client.post("/signup", json=signup_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["username"] == "testuser"

    login_data = {
        "username": "testuser",
        "password": "securepassword123"
    }
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    json_data = response.json()
    assert "id" in json_data
    assert "token" in json_data
    token = json_data["token"]
    assert "access_token" in token
    assert token["token_type"] == "bearer"
