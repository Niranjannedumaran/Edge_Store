import pytest
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.rate_limiter import RateLimiter, LoginBruteForceTracker


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset in-memory rate limiters and lockouts before each test."""
    RateLimiter.reset()
    yield
    RateLimiter.reset()


def get_token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_security_headers_present(client: TestClient):
    """Verify HTTP security headers are applied to responses."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "default-src" in headers.get("content-security-policy", "")
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_path_traversal_defense_and_containment(client: TestClient):
    """Verify path traversal sequences in filenames are strictly sanitized and contained."""
    token = get_token(client, "admin", "AdminEdgeStore2026!")
    headers = {"Authorization": f"Bearer {token}"}

    traversal_filenames = [
        "../../etc/passwd",
        "..\\..\\windows\\win.ini",
        "nested/../../../boot.ini",
        "file%00traversal.txt"
    ]

    for fname in traversal_filenames:
        file_payload = {"file": (fname, io.BytesIO(b"harmless content"), "text/plain")}
        res = client.post("/api/files/upload", headers=headers, files=file_payload)
        assert res.status_code == 201
        file_info = res.json()["file"]
        # Storage path must never contain traversal sequences
        assert ".." not in file_info["filename"]
        assert ".." not in file_info["storage_path"]
        assert "/etc/" not in file_info["storage_path"]
        assert "/windows/" not in file_info["storage_path"]


def test_account_enumeration_protection(client: TestClient):
    """Verify login failure response is identical for existent and non-existent users."""
    # Existent user with wrong password
    res_exist = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword123!"})
    assert res_exist.status_code == 401

    # Non-existent user
    res_nonexist = client.post("/api/auth/login", json={"username": "ghost_user_999", "password": "WrongPassword123!"})
    assert res_nonexist.status_code == 401

    # Both must return identical generic detail to prevent username harvesting
    assert res_exist.json()["detail"] == res_nonexist.json()["detail"]
    assert res_exist.json()["detail"] == "Incorrect username or password"


def test_brute_force_lockout(client: TestClient):
    """Verify brute-force protection triggers lockout after 5 failed login attempts."""
    username = "admin"
    wrong_payload = {"username": username, "password": "WrongPassword!"}

    # First 5 attempts fail with 401
    for i in range(5):
        res = client.post("/api/auth/login", json=wrong_payload)
        assert res.status_code == 401, f"Attempt {i+1} should fail with 401"

    # 6th attempt must be blocked by rate limiter with 429 Too Many Requests
    res_blocked = client.post("/api/auth/login", json=wrong_payload)
    assert res_blocked.status_code == 429
    assert "Retry-After" in res_blocked.headers
    assert "temporarily locked" in res_blocked.json()["detail"].lower()


def test_idor_object_level_authorization(client: TestClient):
    """Verify User A cannot rename or delete User B's file (IDOR defense)."""
    admin_token = get_token(client, "admin", "AdminEdgeStore2026!")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create User B (user_b)
    client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={"username": "user_b", "password": "UserBPassword2026!", "role": "file_manager"}
    )
    user_b_token = get_token(client, "user_b", "UserBPassword2026!")
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

    # 2. Create User A (user_a)
    client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={"username": "user_a", "password": "UserAPassword2026!", "role": "file_manager"}
    )
    user_a_token = get_token(client, "user_a", "UserAPassword2026!")
    user_a_headers = {"Authorization": f"Bearer {user_a_token}"}

    # 3. User B uploads a file -> 201 Created
    upload_res = client.post(
        "/api/files/upload",
        headers=user_b_headers,
        files={"file": ("confidential_b.txt", io.BytesIO(b"Secret of User B"), "text/plain")}
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["file"]["id"]

    # 4. User A attempts to rename User B's file -> Expect 403 Forbidden
    rename_res = client.put(
        f"/api/files/{file_id}/rename",
        headers=user_a_headers,
        json={"new_filename": "hacked_by_a.txt"}
    )
    assert rename_res.status_code == 403
    assert "ownership required" in rename_res.json().get("message", "").lower()

    # 5. User A attempts to delete User B's file -> Expect 403 Forbidden
    delete_res = client.delete(
        f"/api/files/{file_id}",
        headers=user_a_headers
    )
    assert delete_res.status_code == 403
    assert "ownership required" in delete_res.json().get("message", "").lower()

    # 6. User B deletes their own file -> Expect 200 OK
    delete_own_res = client.delete(
        f"/api/files/{file_id}",
        headers=user_b_headers
    )
    assert delete_own_res.status_code == 200


def test_sql_injection_resilience(client: TestClient):
    """Verify SQL injection payloads in search are treated as literal strings."""
    token = get_token(client, "admin", "AdminEdgeStore2026!")
    headers = {"Authorization": f"Bearer {token}"}

    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "admin'--",
        "UNION SELECT * FROM users"
    ]

    for payload in sqli_payloads:
        res = client.get(f"/api/files?search={payload}", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


def test_security_stats_endpoint(client: TestClient):
    """Verify the /auth/security-stats endpoint returns live runtime telemetry."""
    token = get_token(client, "admin", "AdminEdgeStore2026!")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/auth/security-stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "brute_force_protection" in data
    assert "password_policy" in data
    assert "network_security" in data
    assert data["network_security"]["security_headers"] is True
