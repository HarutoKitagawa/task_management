# Task Managent

## Table of Contents
- [About](#about)
- [Requirements](#requirements)
- [Setup](#setup)
- [How to use](#how-to-use)
- [API Spec](#api-spec)
  - [Sign up and Login](#sign-up-and-login)
  - [Users](#users)
  - [Tasks](#tasks)
- [Testing](#testing)

## About
Simple task management app built with FastAPI. This app includes the following features:
- User registration and authentication
- Task creation and management
- Task assignment to users
- Task status management

## Requirements
- Docker/Docker Compose
- GNU Make

## Setup
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

## How to use
The Swagger UI is available at http://localhost:8000/docs — you can use it to view and test the API after starting the server.
- To create a new user, you can use the `/signup` endpoint.
- To login, please click on the "Authorize" button in the top right corner of the Swagger UI and enter your username and password. This will allow you to access the endpoints that require authentication.

## API Spec
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

## Testing
- To run the backend tests, use the following command:
```bash
make pytest
```
