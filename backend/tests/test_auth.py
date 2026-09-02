import pytest
from backend.app.config import settings


def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "username": settings.INITIAL_ADMIN_USERNAME,
        "password": settings.INITIAL_ADMIN_PASSWORD
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == settings.INITIAL_ADMIN_USERNAME
    assert data["user"]["role"] in ("admin", "super_admin")


def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "username": settings.INITIAL_ADMIN_USERNAME,
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_get_me(client, admin_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == settings.INITIAL_ADMIN_USERNAME
    assert data["role"] in ("admin", "super_admin")


def test_rbac_admin_endpoint_forbidden_for_user(client, operator_token):
    # Standard operator tries to call admin user list without users.read
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 403
    assert "users.read" in res.json()["detail"]


def test_rbac_admin_endpoint_allowed_for_admin(client, admin_token):
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 2
