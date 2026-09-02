import pytest
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.database import Base, get_db
from backend.app.config import settings
from backend.app.db.init_db import init_database
from backend.app.hal import hal

TEST_DB_URL = "sqlite:///./test_edgestore.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Ensure test directories exist
    Path(settings.SIMULATION_PRIMARY_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.SIMULATION_REPLICA_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.SIMULATION_KEY_SD_PATH).mkdir(parents=True, exist_ok=True)

    # Re-initialize clean test database
    Base.metadata.drop_all(bind=test_engine)
    init_database(target_engine=test_engine)

    yield

    # Teardown test db
    test_db_path = Path("./test_edgestore.db")
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    res = client.post("/api/auth/login", json={
        "username": settings.INITIAL_ADMIN_USERNAME,
        "password": settings.INITIAL_ADMIN_PASSWORD
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def operator_token(client):
    res = client.post("/api/auth/login", json={
        "username": "operator",
        "password": "OperatorEdgeStore2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]
