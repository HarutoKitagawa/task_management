# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.backend.models import Base
from src.backend.database import get_db
from src.backend.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def user1():
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
    json_data = response.json()
    return json_data['id'], json_data["token"]["access_token"]

@pytest.fixture
def user2():
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
    json_data = response.json()
    return json_data['id'], json_data["token"]["access_token"]