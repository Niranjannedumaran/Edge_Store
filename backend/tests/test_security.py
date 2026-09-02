import io
import hashlib
from backend.app.hal import hal
from backend.app.models.file import StoredFile


def test_path_traversal_sanitization(client, admin_token):
    traversal_name = "../../../evil_script.sh"
    content = b"echo 'hacked'"

    res = client.post(
        "/api/files/upload",
        files={"file": (traversal_name, io.BytesIO(content), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    file_info = res.json()["file"]
    # Verify name was sanitized and storage_path does not escape root
    assert ".." not in file_info["filename"]
    assert ".." not in file_info["storage_path"]


def test_tampered_file_detection(client, admin_token, db_session):
    # 1. Upload legitimate file
    original_data = b"Original pristine file content"
    res = client.post(
        "/api/files/upload",
        files={"file": ("pristine.txt", io.BytesIO(original_data), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    file_id = res.json()["file"]["id"]
    storage_path = res.json()["file"]["storage_path"]

    # 2. Directly tamper with the file on the primary storage drive
    tampered_data = b"Maliciously altered content!"
    hal.primary_storage.write(storage_path, tampered_data)

    # 3. Attempting download should trigger IntegrityVerificationException (422)
    dl_res = client.get(
        f"/api/files/{file_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dl_res.status_code == 422
    assert "Integrity check failed" in dl_res.json()["message"]


def test_no_plaintext_passwords_in_audit(client, admin_token):
    res = client.get(
        "/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    logs = res.json()
    for log in logs:
        desc = log["description"].lower()
        assert "adminedgestore2026!" not in desc
        assert "operatoredgestore2026!" not in desc
