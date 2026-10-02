import pytest
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.database import Base, get_db
from backend.app.config import settings, EnvironmentMode
from backend.app.db.init_db import init_database
import backend.app.hal
from backend.app.hal import hal, HALContainer

import tempfile
TEST_DB_PATH = Path(tempfile.gettempdir()) / "test_edgestore.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Force simulation mode for unit/regression test runs
    original_mode = settings.ENVIRONMENT_MODE
    original_db_url = settings.DATABASE_URL
    settings.ENVIRONMENT_MODE = EnvironmentMode.SIMULATION
    settings.DATABASE_URL = TEST_DB_URL
    hal.reconfigure(EnvironmentMode.SIMULATION)

    # Ensure test directories exist
    Path(settings.SIMULATION_PRIMARY_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.SIMULATION_REPLICA_PATH).mkdir(parents=True, exist_ok=True)
    key_sd_path = Path(settings.SIMULATION_KEY_SD_PATH)
    key_sd_path.mkdir(parents=True, exist_ok=True)
    (key_sd_path / settings.LINUX_KEY_FILE_NAME).write_text("EDGESTORE-LUKS2-SIMULATED-KEY-TOKEN-2026\n")

    # Re-initialize clean test database
    Base.metadata.drop_all(bind=test_engine)
    init_database(target_engine=test_engine)

    yield

    settings.ENVIRONMENT_MODE = original_mode
    settings.DATABASE_URL = original_db_url
    hal.reconfigure(original_mode)


    # Teardown test db
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def reset_ddos_shield_per_test():
    from backend.app.core.anti_bot import AntiBotDDoSShield
    AntiBotDDoSShield.reset()
    yield
    AntiBotDDoSShield.reset()




@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

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
