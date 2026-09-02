import hashlib
import io


def test_file_upload_and_replication(client, admin_token):
    test_content = b"Confidential EdgeStore Device Payload 2026"
    expected_sha256 = hashlib.sha256(test_content).hexdigest()

    # Upload
    files = {"file": ("test_doc.txt", io.BytesIO(test_content), "text/plain")}
    res = client.post(
        "/api/files/upload",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["primary_write"] is True
    assert data["replica_synced"] is True
    assert data["file"]["sha256_hash"] == expected_sha256
    file_id = data["file"]["id"]

    # Verify endpoint
    verify_res = client.get(
        f"/api/files/{file_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["overall_healthy"] is True
    assert v_data["primary"]["intact"] is True
    assert v_data["replica"]["intact"] is True

    # Download
    dl_res = client.get(
        f"/api/files/{file_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dl_res.status_code == 200
    assert dl_res.content == test_content
    assert dl_res.headers["X-EdgeStore-SHA256"] == expected_sha256
    assert dl_res.headers["X-EdgeStore-Degraded-Fallback"] == "false"

    # Delete
    del_res = client.delete(
        f"/api/files/{file_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "COMPLETED"
