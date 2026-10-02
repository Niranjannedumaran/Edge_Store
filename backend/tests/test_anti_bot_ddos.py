import pytest
import re
from fastapi.testclient import TestClient
from backend.app.core.anti_bot import AntiBotDDoSShield


@pytest.fixture(autouse=True)
def reset_shield():
    AntiBotDDoSShield.reset()
    yield
    AntiBotDDoSShield.reset()


def test_get_anti_bot_challenge(client: TestClient):
    """Verify the 'Not a Robot' challenge endpoint issues a valid mathematical challenge."""
    res = client.get("/api/security/anti-bot/challenge")
    assert res.status_code == 200
    data = res.json()
    assert "challenge_id" in data
    assert "prompt" in data
    assert "What is" in data["prompt"]
    assert data["expires_in_seconds"] > 0


def test_verify_challenge_success_and_cache(client: TestClient):
    """Verify solving the 'Not a Robot' challenge returns a token and caches verified human status."""
    res = client.get("/api/security/anti-bot/challenge")
    assert res.status_code == 200
    data = res.json()
    challenge_id = data["challenge_id"]
    prompt = data["prompt"]

    # Extract numbers from "What is X + Y?"
    match = re.search(r"What is (\d+) \+ (\d+)\?", prompt)
    assert match is not None
    answer = str(int(match.group(1)) + int(match.group(2)))

    # Verify challenge
    verify_res = client.post(
        "/api/security/anti-bot/verify",
        json={"challenge_id": challenge_id, "solution": answer}
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["success"] is True
    assert "anti_bot_token" in verify_data
    assert verify_data["anti_bot_token"].startswith("human_")

    # Check that IP is now verified in cache
    assert AntiBotDDoSShield.is_verified_human("testclient") is True


def test_verify_challenge_incorrect_answer(client: TestClient):
    """Verify incorrect solution is rejected with HTTP 400."""
    res = client.get("/api/security/anti-bot/challenge")
    assert res.status_code == 200
    challenge_id = res.json()["challenge_id"]

    verify_res = client.post(
        "/api/security/anti-bot/verify",
        json={"challenge_id": challenge_id, "solution": "999999"}
    )
    assert verify_res.status_code == 400
    assert "Incorrect answer" in verify_res.json()["detail"]


def test_ddos_burst_flood_triggers_quarantine_cache(client: TestClient):
    """Verify that rapid flood requests trigger DDoS quarantine cache and return HTTP 429."""
    # Send 45 requests rapidly (burst limit is 40 in 5 seconds)
    responses = []
    for _ in range(45):
        r = client.get("/api/clients?limit=1")
        responses.append(r.status_code)

    # At least some of the later requests must be blocked with HTTP 429
    assert 429 in responses
    last_res = client.get("/api/clients?limit=1")
    assert last_res.status_code == 429
    assert "Retry-After" in last_res.headers
    body = last_res.json()
    assert body["error"] == "DDoSAttackMitigation"
    assert "anti_bot_verification_url" in body["details"]


def test_not_a_robot_unquarantines_ip(client: TestClient):
    """Verify that solving the 'Not a Robot' challenge immediately clears an IP from DDoS quarantine."""
    # 1. Trigger DDoS quarantine
    for _ in range(45):
        client.get("/api/clients?limit=1")

    # Verify IP is quarantined
    blocked_res = client.get("/api/clients?limit=1")
    assert blocked_res.status_code == 429

    # 2. Request a challenge (exempt path)
    ch_res = client.get("/api/security/anti-bot/challenge")
    assert ch_res.status_code == 200
    ch_data = ch_res.json()
    challenge_id = ch_data["challenge_id"]
    match = re.search(r"What is (\d+) \+ (\d+)\?", ch_data["prompt"])
    answer = str(int(match.group(1)) + int(match.group(2)))

    # 3. Solve challenge
    solve_res = client.post(
        "/api/security/anti-bot/verify",
        json={"challenge_id": challenge_id, "solution": answer}
    )
    assert solve_res.status_code == 200

    # 4. Subsequent requests from this IP must now succeed immediately!
    unblocked_res = client.get("/api/clients?limit=1")
    assert unblocked_res.status_code == 200


def test_ddos_telemetry_stats(client: TestClient):
    """Verify live telemetry reflects screenings, blocks, and cache state."""
    stats_res = client.get("/api/security/ddos/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["status"] == "ACTIVE"
    assert "total_requests_screened" in stats
    assert "floods_blocked" in stats
    assert "verified_humans_in_cache" in stats


def test_login_with_not_a_robot_cache_token(client: TestClient):
    """Verify solving the 'Not a Robot' challenge generates a cache token that enables authenticated login."""
    # 1. Obtain challenge
    ch = client.get("/api/security/anti-bot/challenge").json()
    m = re.search(r"What is (\d+) \+ (\d+)\?", ch["prompt"])
    ans = str(int(m.group(1)) + int(m.group(2)))

    # 2. Solve challenge and obtain token
    v = client.post(
        "/api/security/anti-bot/verify",
        json={"challenge_id": ch["challenge_id"], "solution": ans}
    ).json()
    token = v["anti_bot_token"]
    assert token.startswith("human_")

    # 3. Authenticate with verified token
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "AdminEdgeStore2026!", "anti_bot_token": token},
        headers={"x-anti-bot-token": token}
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

