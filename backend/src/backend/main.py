from fastapi import FastAPI
from .auth import routes as auth_routes
from .user import routes as user_routes
from .task import routes as task_routes

app = FastAPI()

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(task_routes.router)
