from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta, timezone
from src.backend.main import app

client = TestClient(app)

@pytest.fixture
def create_task(user1):
    """Fixture to create a task and return its ID"""
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.post("/tasks", json=task_data, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    return data["id"]

def test_create_task(user1):
    # Test creating a task
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.post("/tasks", json=task_data, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert "id" in data
    assert data["owner"]["id"] == user1[0]

def test_get_tasks(user1, create_task):
    # Test getting all tasks
    task_id = create_task
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.get("/tasks", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # Check if our created task is in the list
    task_ids = [task["id"] for task in data['owned_tasks']]
    assert task_id in task_ids

def test_get_task_detail(user1, create_task):
    # Test getting a specific task
    task_id = create_task
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.get(f"/tasks/{task_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert "assignees" in data
    assert isinstance(data["assignees"], list)

def test_update_task(user1, create_task):
    # Test updating the task
    task_id = create_task
    
    update_data = {
        "title": "Updated Task Title",
        "description": "Updated task description",
        "status": "IN_PROGRESS",
    }
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.put(f"/tasks/{task_id}", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]
    assert data["status"] == update_data["status"]

def test_update_task_status(user1, create_task):
    # Test updating the task status
    task_id = create_task

    update_data = {
        "status": "COMPLETED"
    }

    header = {"Authorization": f"Bearer {user1[1]}"}
    response = client.patch(f"/tasks/{task_id}/status", json=update_data, headers=header)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["status"] == update_data["status"]

def test_delete_task(user1, create_task):
    # Test deleting the task
    task_id = create_task
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.delete(f"/tasks/{task_id}", headers=headers)
    
    assert response.status_code == 204
    
    # Verify task is no longer accessible
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 404

def test_assign_users_to_task(user1, user2, create_task):
    # Get the task ID
    task_id = create_task
    
    # Get user2's ID
    headers = {"Authorization": f"Bearer {user2[1]}"}
    user2_id = user2[0]
    
    # Assign user2 to the task
    assign_data = {
        "user_ids": [user2_id]
    }
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    response = client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    
    # Check if user2 is in the assignees list
    assignee_ids = [assignee["id"] for assignee in data["assignees"]]
    assert user2_id in assignee_ids

    headers = {"Authorization": f"Bearer {user2[1]}"}

    # Test that task list of user2 includes the task
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    task_ids = [task["id"] for task in data['assigned_tasks']]
    assert task_id in task_ids
    
    # Test that user2 can now access the task
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200

def test_remove_assignee_from_task(user1, user2, create_task):
    # Get the task ID
    task_id = create_task
    
    # Get user2's ID
    headers = {"Authorization": f"Bearer {user2[1]}"}
    user2_id = user2[0]
    
    # Assign user2 to the task
    assign_data = {
        "user_ids": [user2_id]
    }
    
    headers = {"Authorization": f"Bearer {user1[1]}"}
    client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers)
    
    # Remove user2 from the task
    response = client.delete(f"/tasks/{task_id}/assignees/{user2_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify user2 can no longer access the task
    headers = {"Authorization": f"Bearer {user2[1]}"}
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 403

def test_authorization_restrictions(user1, user2, create_task):
    # Get the task ID
    task_id = create_task
    
    # Try to access with user2 (should fail)
    headers = {"Authorization": f"Bearer {user2[1]}"}
    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 403
    
    # Try to update with user2 (should fail)
    update_data = {"title": "Unauthorized Update"}
    response = client.put(f"/tasks/{task_id}", json=update_data, headers=headers)
    assert response.status_code == 403

    # Try to update status with user2 (should fail)
    update_data = {"status": "COMPLETED"}
    response = client.patch(f"/tasks/{task_id}/status", json=update_data, headers=headers)
    assert response.status_code == 403
    
    # Try to delete with user2 (should fail)
    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 403
    
    # Try to assign users with user2 (should fail)
    assign_data = {"user_ids": [1]}
    response = client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers)
    assert response.status_code == 403

def test_assignee_can_update_task_status(user1, user2, create_task):
    task_id = create_task

    # Assign user2 to the task
    headers_user2 = {"Authorization": f"Bearer {user2[1]}"}
    user2_id = user2[0]

    # Assign user2 to the task
    headers_user1 = {"Authorization": f"Bearer {user1[1]}"}
    assign_data = {"user_ids": [user2_id]}
    response = client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers_user1)
    assert response.status_code == 200

    # User2 should be able to update the task status
    update_data = {"status": "IN_PROGRESS"}
    response = client.patch(f"/tasks/{task_id}/status", json=update_data, headers=headers_user2)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["status"] == "IN_PROGRESS"