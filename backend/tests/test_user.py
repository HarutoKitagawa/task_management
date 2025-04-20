from fastapi.testclient import TestClient

from src.backend.main import app

client = TestClient(app)

def test_list_users(user1, user2):
    headers = {"Authorization": f"Bearer {user1[1]}"}
    # Test listing all users with no keyword
    response = client.get("/users", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Test listing users with a keyword
    response = client.get("/users?keyword=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == user1[0]
    assert data[0]["username"] == "taskuser1"

    # Test listing users with a non-existing keyword
    response = client.get("/users?keyword=nonexistent", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0