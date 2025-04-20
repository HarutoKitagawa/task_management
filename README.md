# Task Managent

## About
Simple task management app built with FastAPI. This app includes the following features:
- User registration and authentication
- Task creation and management
- Task assignment to users

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
- To check the API specification in detail, please visit http://localhost:8000/docs after starting the server.
