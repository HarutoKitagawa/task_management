from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta, timezone
from src.backend.main import app

client = TestClient(app)

@pytest.fixture
def user1_token():
    # Create a test user
    signup_data = {
        "username": "taskuser1",
        "password": "securepassword123"
    }
    client.post("/signup", json=signup_data)
    
    # Login to get token
    login_data = {
        "username": "taskuser1",
        "password": "securepassword123"
    }
    response = client.post("/login", data=login_data)
    return response.json()["access_token"]

@pytest.fixture
def user2_token():
    # Create another test user
    signup_data = {
        "username": "taskuser2",
        "password": "securepassword123"
    }
    client.post("/signup", json=signup_data)
    
    # Login to get token
    login_data = {
        "username": "taskuser2",
        "password": "securepassword123"
    }
    response = client.post("/login", data=login_data)
    return response.json()["access_token"]

@pytest.fixture
def create_task(user1_token):
    """Fixture to create a task and return its ID"""
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.post("/tasks", json=task_data, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    return data["id"]

def test_create_task(user1_token):
    # Test creating a task
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.post("/tasks", json=task_data, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert "id" in data
    assert "owner" in data

def test_get_tasks(user1_token, create_task):
    # Test getting all tasks
    task_id = create_task
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.get("/tasks", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if our created task is in the list
    task_ids = [task["id"] for task in data]
    assert task_id in task_ids

def test_get_task_detail(user1_token, create_task):
    # Test getting a specific task
    task_id = create_task
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.get(f"/tasks/{task_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert "assignees" in data
    assert isinstance(data["assignees"], list)

def test_update_task(user1_token, create_task):
    # Test updating the task
    task_id = create_task
    
    update_data = {
        "title": "Updated Task Title",
        "description": "Updated task description"
    }
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.put(f"/tasks/{task_id}", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]

def test_delete_task(user1_token, create_task):
    # Test deleting the task
    task_id = create_task
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.delete(f"/tasks/{task_id}", headers=headers)
    
    assert response.status_code == 204
    
    # Verify task is no longer accessible
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 404

def test_assign_users_to_task(user1_token, user2_token, create_task):
    # Get the task ID
    task_id = create_task
    
    # Get user2's ID
    headers = {"Authorization": f"Bearer {user2_token}"}
    response = client.get("/users/me", headers=headers)
    user2_id = response.json()["id"]
    
    # Assign user2 to the task
    assign_data = {
        "user_ids": [user2_id]
    }
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    
    # Check if user2 is in the assignees list
    assignee_ids = [assignee["id"] for assignee in data["assignees"]]
    assert user2_id in assignee_ids

    headers = {"Authorization": f"Bearer {user2_token}"}

    # Test that task list of user2 includes the task
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    task_ids = [task["id"] for task in data]
    assert task_id in task_ids
    
    # Test that user2 can now access the task
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200

def test_remove_assignee_from_task(user1_token, user2_token, create_task):
    # Get the task ID
    task_id = create_task
    
    # Get user2's ID
    headers = {"Authorization": f"Bearer {user2_token}"}
    response = client.get("/users/me", headers=headers)
    user2_id = response.json()["id"]
    
    # Assign user2 to the task
    assign_data = {
        "user_ids": [user2_id]
    }
    
    headers = {"Authorization": f"Bearer {user1_token}"}
    client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers)
    
    # Remove user2 from the task
    response = client.delete(f"/tasks/{task_id}/assignees/{user2_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify user2 can no longer access the task
    headers = {"Authorization": f"Bearer {user2_token}"}
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 403

def test_authorization_restrictions(user1_token, user2_token, create_task):
    # Get the task ID
    task_id = create_task
    
    # Try to access with user2 (should fail)
    headers = {"Authorization": f"Bearer {user2_token}"}
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 403
    
    # Try to update with user2 (should fail)
    update_data = {"title": "Unauthorized Update"}
    response = client.put(f"/tasks/{task_id}", json=update_data, headers=headers)
    assert response.status_code == 403
    
    # Try to delete with user2 (should fail)
    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 403
    
    # Try to assign users with user2 (should fail)
    assign_data = {"user_ids": [1]}
    response = client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers)
    assert response.status_code == 403
