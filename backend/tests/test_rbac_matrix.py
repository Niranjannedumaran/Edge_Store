import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.user import User
from backend.app.models.session import UserSession
from backend.app.models.role import Role
from backend.app.core.security import hash_password, create_access_token


@pytest.fixture
def guest_token(client, db_session):
    guest_user = db_session.query(User).filter(User.username == "guest").first()
    if not guest_user:
        guest_role = db_session.query(Role).filter(Role.name == "guest").first()
        guest_user = User(
            username="guest",
            display_name="Test Guest",
            hashed_password=hash_password("GuestEdgeStore2026!"),
            role="guest",
            role_id=guest_role.id if guest_role else None,
            is_active=True
        )
        db_session.add(guest_user)
        db_session.commit()

    res = client.post("/api/auth/login", json={
        "username": "guest",
        "password": "GuestEdgeStore2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def security_admin_token(client, db_session):
    sec_user = db_session.query(User).filter(User.username == "sec_admin").first()
    if not sec_user:
        sec_role = db_session.query(Role).filter(Role.name == "security_admin").first()
        sec_user = User(
            username="sec_admin",
            display_name="Security Admin",
            hashed_password=hash_password("SecurityAdmin2026!"),
            role="security_admin",
            role_id=sec_role.id if sec_role else None,
            is_active=True
        )
        db_session.add(sec_user)
        db_session.commit()

    res = client.post("/api/auth/login", json={
        "username": "sec_admin",
        "password": "SecurityAdmin2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


def test_guest_read_only_permissions(client, guest_token):
    headers = {"Authorization": f"Bearer {guest_token}"}

    # 1. Reading file list is ALLOWED
    res_list = client.get("/api/files", headers=headers)
    assert res_list.status_code == 200

    # 2. Upload is DENIED with 403 Forbidden
    res_upload = client.post(
        "/api/files/upload",
        headers=headers,
        files={"file": ("unauthorized.txt", b"malicious content", "text/plain")}
    )
    assert res_upload.status_code == 403
    assert "files.upload" in res_upload.json()["detail"]

    # 3. Rename is DENIED with 403 Forbidden
    res_rename = client.put(
        "/api/files/dummy-id/rename",
        headers=headers,
        json={"new_filename": "renamed.txt"}
    )
    assert res_rename.status_code == 403
    assert "files.rename" in res_rename.json()["detail"]

    # 4. Delete is DENIED with 403 Forbidden
    res_delete = client.delete("/api/files/dummy-id", headers=headers)
    assert res_delete.status_code == 403
    assert "files.delete" in res_delete.json()["detail"]

    # 5. User management is DENIED with 403 Forbidden
    res_users = client.get("/api/admin/users", headers=headers)
    assert res_users.status_code == 403

    # 6. Storage vault unlock is DENIED with 403 Forbidden
    res_vault = client.post("/api/storage/vault/unlock", headers=headers)
    assert res_vault.status_code == 403

    # 7. Replication rebuild is DENIED with 403 Forbidden
    res_rebuild = client.post("/api/replication/rebuild", headers=headers)
    assert res_rebuild.status_code == 403

    # 8. Hardware simulation is DENIED with 403 Forbidden
    res_sim = client.post("/api/simulation/drive", headers=headers, json={"drive": "primary", "action": "fail"})
    assert res_sim.status_code == 403


def test_storage_admin_vs_security_admin_separation(client, operator_token, security_admin_token):
    # operator_token has storage_admin role
    storage_headers = {"Authorization": f"Bearer {operator_token}"}
    sec_headers = {"Authorization": f"Bearer {security_admin_token}"}

    # Storage Admin can view storage & trigger replication retry
    res_storage = client.get("/api/storage/status", headers=storage_headers)
    assert res_storage.status_code == 200

    # Storage Admin CANNOT create users -> 403 Forbidden
    res_user_create = client.post("/api/admin/users", headers=storage_headers, json={
        "username": "illegal_user",
        "password": "Password123!"
    })
    assert res_user_create.status_code == 403
    assert "users.create" in res_user_create.json()["detail"]

    # Security Admin CAN view users
    res_sec_users = client.get("/api/admin/users", headers=sec_headers)
    assert res_sec_users.status_code == 200

    # Security Admin CANNOT rebuild replica -> 403 Forbidden
    res_sec_rebuild = client.post("/api/replication/rebuild", headers=sec_headers)
    assert res_sec_rebuild.status_code == 403
    assert "replication.rebuild" in res_sec_rebuild.json()["detail"]


def test_temporary_guest_expiration(client, db_session):
    # Create an expired guest account
    guest_role = db_session.query(Role).filter(Role.name == "guest").first()
    expired_user = User(
        username="expired_guest",
        display_name="Expired Reviewer",
        hashed_password=hash_password("ExpiredPass2026!"),
        role="guest",
        role_id=guest_role.id if guest_role else None,
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(expired_user)
    db_session.commit()

    # Login should be rejected
    res = client.post("/api/auth/login", json={
        "username": "expired_guest",
        "password": "ExpiredPass2026!"
    })
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_session_revocation(client, guest_token, db_session):
    headers = {"Authorization": f"Bearer {guest_token}"}

    # Request works before revocation
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200

    # Revoke all sessions for guest user
    guest_user = db_session.query(User).filter(User.username == "guest").first()
    db_session.query(UserSession).filter(UserSession.user_id == guest_user.id).update({"is_revoked": True})
    db_session.commit()

    # Next request with revoked token MUST be rejected
    res_after = client.get("/api/auth/me", headers=headers)
    assert res_after.status_code == 401
    assert "revoked" in res_after.json()["detail"].lower()
