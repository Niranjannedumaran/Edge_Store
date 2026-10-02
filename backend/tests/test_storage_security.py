import io
import hashlib
import pytest
from fastapi.testclient import TestClient
from backend.app.hal import hal
from backend.app.config import DriveState
from backend.app.core.exceptions import StorageUnavailableException


def get_token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_idor_download_blocked_between_users(client: TestClient, admin_token: str):
    """Verify that User A cannot download User B's file directly by guessing or passing its ID (IDOR Defense)."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create User Alpha
    client.post("/api/admin/users", headers=admin_headers, json={
        "username": "user_alpha", "password": "UserAlphaPassword2026!", "role": "file_manager"
    })
    alpha_token = get_token(client, "user_alpha", "UserAlphaPassword2026!")
    alpha_headers = {"Authorization": f"Bearer {alpha_token}"}

    # Create User Beta
    client.post("/api/admin/users", headers=admin_headers, json={
        "username": "user_beta", "password": "UserBetaPassword2026!", "role": "file_manager"
    })
    beta_token = get_token(client, "user_beta", "UserBetaPassword2026!")
    beta_headers = {"Authorization": f"Bearer {beta_token}"}

    # User Alpha uploads a sensitive file
    secret_payload = b"Top Secret Financial Records of Alpha"
    up_res = client.post("/api/files/upload", headers=alpha_headers, files={
        "file": ("alpha_financials.txt", io.BytesIO(secret_payload), "text/plain")
    })
    assert up_res.status_code == 201
    file_id = up_res.json()["file"]["id"]

    # User Beta attempts to download Alpha's file -> Expect 403 Forbidden (IDOR Blocked)
    down_res = client.get(f"/api/files/{file_id}/download", headers=beta_headers)
    assert down_res.status_code == 403
    assert "ownership required" in down_res.json().get("message", "").lower()

    # User Beta attempts to get details of Alpha's file -> Expect 403 Forbidden
    detail_res = client.get(f"/api/files/{file_id}", headers=beta_headers)
    assert detail_res.status_code == 403

    # User Alpha can download their own file cleanly -> Expect 200 OK
    alpha_down = client.get(f"/api/files/{file_id}/download", headers=alpha_headers)
    assert alpha_down.status_code == 200
    assert alpha_down.content == secret_payload


def test_safe_internal_uuid_paths(client: TestClient, admin_token: str):
    """Verify that stored file paths use safe internal UUID identifiers and never reflect arbitrary user paths."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    up_res = client.post("/api/files/upload", headers=admin_headers, files={
        "file": ("audit_report_2026.pdf", io.BytesIO(b"PDF File Content Dummy"), "application/pdf")
    })
    assert up_res.status_code == 201
    file_data = up_res.json()["file"]

    # Storage path must follow pattern: files/{owner_id}/{uuid}
    storage_path = file_data["storage_path"]
    parts = storage_path.split("/")
    assert len(parts) == 3
    assert parts[0] == "files"
    assert parts[1] == str(file_data["owner_id"])
    assert len(parts[2]) == 36  # UUID length
    assert "audit_report" not in storage_path  # Original name kept only in metadata


def test_dangerous_executable_upload_blocked(client: TestClient, admin_token: str):
    """Verify that executable extensions (.exe, .bat, .cmd, .ps1, .vbs) are rejected."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    blocked_names = [
        "malware.exe",
        "script.bat",
        "exploit.cmd",
        "payload.ps1",
        "trojan.vbs"
    ]
    for b_name in blocked_names:
        res = client.post("/api/files/upload", headers=admin_headers, files={
            "file": (b_name, io.BytesIO(b"malicious script binary"), "application/octet-stream")
        })
        assert res.status_code == 400
        assert "executable" in res.json().get("message", "").lower()


def test_temporary_guest_share_workflow(client: TestClient, admin_token: str):
    """Verify temporary guest share creation, anonymous access, download permissions, and revocation."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    content = b"Shared Project Proposal for External Reviewers"
    up_res = client.post("/api/files/upload", headers=admin_headers, files={
        "file": ("proposal.txt", io.BytesIO(content), "text/plain")
    })
    assert up_res.status_code == 201
    file_id = up_res.json()["file"]["id"]

    # 1. Create temporary share with allow_download=True
    share_res = client.post(f"/api/files/{file_id}/share", headers=admin_headers, json={
        "expires_in_hours": 2,
        "allow_download": True,
        "max_uses": 5
    })
    assert share_res.status_code == 201
    share_data = share_res.json()["share"]
    share_token = share_data["id"]

    # 2. Anonymous client accesses public share info endpoint
    info_res = client.get(f"/api/files/shared/{share_token}")
    assert info_res.status_code == 200
    assert info_res.json()["file"]["filename"] == "proposal.txt"
    assert info_res.json()["allow_download"] is True

    # 3. Anonymous client downloads file using share token query parameter
    down_res = client.get(f"/api/files/{file_id}/download?share_token={share_token}")
    assert down_res.status_code == 200
    assert down_res.content == content

    # 4. List active shares for the file
    list_shares_res = client.get(f"/api/files/{file_id}/shares", headers=admin_headers)
    assert list_shares_res.status_code == 200
    assert len(list_shares_res.json()) >= 1

    # 5. Revoke the share
    revoke_res = client.delete(f"/api/files/shares/{share_token}", headers=admin_headers)
    assert revoke_res.status_code == 200

    # 6. Attempted download with revoked token must be rejected with 403 Forbidden
    down_after = client.get(f"/api/files/{file_id}/download?share_token={share_token}")
    assert down_after.status_code == 403
    assert "invalid, expired, or has reached its usage limit" in down_after.json().get("message", "").lower()


def test_preview_only_share_blocks_binary_download(client: TestClient, admin_token: str):
    """Verify that a share created with allow_download=False rejects download attempts."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    up_res = client.post("/api/files/upload", headers=admin_headers, files={
        "file": ("view_only.txt", io.BytesIO(b"View only confidential memo"), "text/plain")
    })
    file_id = up_res.json()["file"]["id"]

    # Create share with allow_download=False
    share_res = client.post(f"/api/files/{file_id}/share", headers=admin_headers, json={
        "expires_in_hours": 1,
        "allow_download": False
    })
    share_token = share_res.json()["share"]["id"]

    # Anonymous download attempt should fail
    down_res = client.get(f"/api/files/{file_id}/download?share_token={share_token}")
    assert down_res.status_code == 403
    assert "preview" in down_res.json().get("message", "").lower()


def test_replication_failure_preserves_primary(client: TestClient, admin_token: str):
    """Verify that when the replica is faulted, the primary upload still succeeds and file remains available."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Inject replication fault
    client.post("/api/simulation/replication-fault", headers=admin_headers, json={"simulate_failure": True})

    try:
        content = b"Data uploaded during degraded replica failure"
        up_res = client.post("/api/files/upload", headers=admin_headers, files={
            "file": ("degraded_mode_doc.txt", io.BytesIO(content), "text/plain")
        })
        assert up_res.status_code == 201
        data = up_res.json()
        assert data["primary_write"] is True
        assert data["replica_synced"] is False
        assert data["is_degraded"] is True
        assert data["replica_status"] == "failed"
        file_id = data["file"]["id"]

        # Primary file must still be accessible and downloadable despite replica failure
        dl_res = client.get(f"/api/files/{file_id}/download", headers=admin_headers)
        assert dl_res.status_code == 200
        assert dl_res.content == content
    finally:
        # Restore replication engine
        client.post("/api/simulation/replication-fault", headers=admin_headers, json={"simulate_failure": False})


def test_truthful_storage_status_telemetry(client: TestClient, operator_token: str):
    """Verify that storage telemetry reports truthful values and never fabricates LUKS encryption in simulation/Docker."""
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    res = client.get("/api/storage/status", headers=operator_headers)
    assert res.status_code == 200
    status_data = res.json()

    storage = status_data["storage"]
    primary = storage["primary"]
    assert "capacity_bytes" in primary
    assert "used_bytes" in primary
    assert "free_bytes" in primary

    # Verify no fake LUKS claim
    encryption = status_data.get("vault", {}).get("encryption", {})
    assert encryption.get("is_simulated", False) is True or encryption.get("cipher") != "LUKS2 512-bit physical"
