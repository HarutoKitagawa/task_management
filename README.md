# Table of Contents
- [About](#about)
- [Requirements](#requirements)
- [Setup](#setup)
- [How to use](#how-to-use)
- [API Spec](#api-spec)
  - [Sign up and Login](#sign-up-and-login)
  - [Users](#users)
  - [Tasks](#tasks)
  - [Notifications](#notifications)
- [Testing](#testing)

# About
Simple task management app built with FastAPI. This app includes the following features:
- User registration and authentication
- Task creation and management
- Task assignment to users
- Task status management
- Notification system based on task events (e.g., assignment, status changes)

# Requirements
- Docker/Docker Compose
- GNU Make

# Setup
- Clone the repository
```bash
git clone git@github.com:HarutoKitagawa/task_management.git
```
- Start docker container
```bash
docker-compose up -d
```
- Migrate database
```bash
make migrate-up
```

# How to use
The Swagger UI is available at http://localhost:8000/docs — you can use it to view and test the API after starting the server.
- To create a new user, you can use the `/signup` endpoint.
- To login, please click on the "Authorize" button in the top right corner of the Swagger UI and enter your username and password. This will allow you to access the endpoints that require authentication.

## Recommended API usage flows for implementing frontend features
You can follow the sequences below when implementing each feature on the frontend:

### Sign up and Login
- **Sign up**: `POST /signup`
- **Login**: `POST /login`

### Create and manage tasks
- **Create task**: `POST /tasks`
- **Get all tasks**: `GET /tasks`
- **Get task by ID**: `GET /tasks/{task_id}`
- **Update task**: `PUT /tasks/{task_id}`

### Assign users to a task
- **Get all tasks**: `GET /tasks`
- (**Get task by ID**: `GET /tasks/{task_id}`)
- **List users**: `GET /users`
- **Assign users to a task**: `POST /tasks/{task_id}/assignees`

### Assignee update task status
- **Get all tasks**: `GET /tasks`
- (**Get task by ID**: `GET /tasks/{task_id}`)
- **Update task status**: `PATCH /tasks/{task_id}/status`

# API Spec
### Sign up and Login
- Sign up: `POST /signup`
Request body:
```json
{
  "username": "string",
  "password": "string"
}
```
- Login: `POST /login`
Request body:
```json
{
  "username": "string",
  "password": "string"
}
```

### Users
- **List users**: `GET /users`  
**Access**: Authenticated users  
Query parameters:  
    - `keyword` (optional): Filter users by username containing this keyword  

### Tasks
- **Create task**: `POST /tasks`  
**Access**: Authenticated users  
Request body:
```json
{
    "title": "string",
    "description": "string",
    "due_date": "string (optional, ISO 8601 format)"
}
```
- **Get all tasks**: `GET /tasks`  
**Access**: Authenticated users (returns tasks created by or assigned to the user)  
- **Get task by ID**: `GET /tasks/{task_id}`  
**Access**: Task creator or assignee  
- **Update task**: `PUT /tasks/{task_id}`  
**Access**: Only the task creator  
Request body:
```json
{
    "title": "string (optional)",
    "description": "string (optional)",
    "due_date": "string (optional, ISO 8601 format)"
}
```
- **Update task status**: `PATCH /tasks/{task_id}/status`  
**Access**: Only the task creator or assignee  
Request body:
```json
{
    "status": "string (optional, one of: 'PENDING', 'IN_PROGRESS', 'COMPLETED')"
}
```
- **Delete task**: `DELETE /tasks/{task_id}`  
**Access**: Only the task creator  
- **Assign users to a task**: `POST /tasks/{task_id}/assignees`  
**Access**: Only the task creator  
Request body:
```json
{
    "user_ids": [1, 2, 3]
}
```
- **Remove a user from a task**: `DELETE /tasks/{task_id}/assignees/{user_id}`  
**Access**: Only the task creator

### Notifications
- **Get unread notifications**: `GET /users/notifications`  
**Access**: Authenticated users  
**Description**:  
This endpoint returns a list of unread notifications for the authenticated user.  
Notifications are generated automatically based on specific task-related events.

Currently, the application supports two types of notification-triggering events:

1. **Task Assignment**  
   When a user assigns one or more users to a task using `POST /tasks/{task_id}/assignees`, each assigned user will receive a notification.  
   The notification includes a message such as:  
   _"You have been assigned to the task 'Design review' by UserA."_

2. **Task Status Change**  
   When the status of a task is changed via `PUT /tasks/{task_id}` or `PATCH /tasks/{task_id}/status`, notifications are sent to all participants in the task — including the task owner and all assignees.  

These notifications are based on structured **task events**, which are also stored separately.  
This allows not only notification delivery but also richer activity logs (e.g., task history on detail pages).

Each notification includes a human-readable message and an unread flag. 

## Testing
- To run the backend tests, use the following command:
```bash
make pytest
```

## DB Structure
![taskdb](https://github.com/user-attachments/assets/3abf208b-1e7b-4190-bca6-5c97750557a0)
