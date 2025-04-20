from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

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

def test_get_notifications(user1, user2):
    # Create a task as user1
    task_data = {
        "title": "Test Task for Notifications",
        "description": "This is a test task to generate notifications",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    }
    
    headers_user1 = {"Authorization": f"Bearer {user1[1]}"}
    response = client.post("/tasks", json=task_data, headers=headers_user1)
    
    assert response.status_code == 201
    task_data = response.json()
    task_id = task_data["id"]
    
    # Assign user2 to the task (generates notification for user2)
    assign_data = {
        "user_ids": [user2[0]]
    }
    
    response = client.post(f"/tasks/{task_id}/assignees", json=assign_data, headers=headers_user1)
    assert response.status_code == 200
    
    # Update task status (generates another notification for user2)
    update_data = {
        "status": "IN_PROGRESS"
    }
    
    response = client.patch(f"/tasks/{task_id}/status", json=update_data, headers=headers_user1)
    assert response.status_code == 200
    
    # Get notifications as user2
    headers_user2 = {"Authorization": f"Bearer {user2[1]}"}
    response = client.get("/users/notifications", headers=headers_user2)
    
    assert response.status_code == 200
    notifications = response.json()
    
    # Verify notifications content
    assert isinstance(notifications, list)
    assert len(notifications) == 2  # Should have 2 notifications (assignment and status update)
    
    # Check if notifications contain expected text
    assignment_notification = False
    status_notification = False
    
    for notification in notifications:
        if "assigned to" in notification:
            assignment_notification = True
        if "status changed" in notification:
            status_notification = True
    
    assert assignment_notification, "Assignment notification not found"
    assert status_notification, "Status update notification not found"
    
    # Get notifications again to verify they're marked as read
    response = client.get("/users/notifications", headers=headers_user2)
    
    assert response.status_code == 200
    notifications = response.json()
    
    # Should be empty now as all notifications were marked as read
    assert isinstance(notifications, list)
    assert len(notifications) == 0, "Notifications were not marked as read"
