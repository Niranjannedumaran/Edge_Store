import io
import hashlib
from backend.app.hal import hal


def test_drive_failure_and_failover_download(client, admin_token):
    # 1. Upload a file while both drives are healthy
    content = b"Data surviving single-drive failure on EdgeStore"
    expected_hash = hashlib.sha256(content).hexdigest()

    upload_res = client.post(
        "/api/files/upload",
        files={"file": ("failover_test.bin", io.BytesIO(content), "application/octet-stream")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file"]["id"]

    # 2. Simulate Primary Drive (Drive A) failure via simulation API
    fail_res = client.post(
        "/api/simulation/drive",
        json={"drive": "primary", "action": "fail"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert fail_res.status_code == 200

    # 3. Check health: Storage mode should now be DEGRADED
    health_res = client.get(
        "/api/system/health",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert health_res.status_code == 200
    assert health_res.json()["storage"]["mode"] == "DEGRADED"

    # 4. Download file: Must successfully failover to Drive B (Replica)!
    dl_res = client.get(
        f"/api/files/{file_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dl_res.status_code == 200
    assert dl_res.content == content
    assert dl_res.headers["X-EdgeStore-Degraded-Fallback"] == "true"

    # 5. Recover Primary drive and trigger rebuild
    rec_res = client.post(
        "/api/simulation/drive",
        json={"drive": "primary", "action": "recover"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rec_res.status_code == 200

    rebuild_res = client.post(
        "/api/replication/rebuild",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rebuild_res.status_code == 200
    assert rebuild_res.json()["success"] is True


def test_key_sd_removal_locks_vault(client, admin_token):
    # 1. Simulate Key-SD removal
    rm_res = client.post(
        "/api/simulation/key-sd",
        json={"action": "remove"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rm_res.status_code == 200
    assert rm_res.json()["status"]["present"] is False

    # 2. Lock vault
    lock_res = client.post(
        "/api/storage/vault/lock",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert lock_res.status_code == 200

    # 3. Attempting upload while locked should fail with HTTP 423 Locked
    upload_res = client.post(
        "/api/files/upload",
        files={"file": ("blocked.txt", io.BytesIO(b"Locked Data"), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert upload_res.status_code == 423

    # 4. Reinsert Key-SD
    ins_res = client.post(
        "/api/simulation/key-sd",
        json={"action": "insert", "valid": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert ins_res.status_code == 200

    # 5. Unlock vault
    unlock_res = client.post(
        "/api/storage/vault/unlock",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert unlock_res.status_code == 200
    assert unlock_res.json()["success"] is True
