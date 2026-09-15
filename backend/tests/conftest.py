import os

os.environ["DATABASE_URL"] = "sqlite:///./test_kbs_toolbox.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["SEED_DEMO_DATA"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_kbs_toolbox.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    return TestClient(app)


def register_and_login(client, email="admin@test.local", password="StrongPass123!", role="ADMINISTRATOR", full_name="Test Admin"):
    client.post(
        "/api/auth/register",
        json={"full_name": full_name, "email": email, "password": password, "role": role},
    )
    resp = client.post("/api/auth/login-json", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
