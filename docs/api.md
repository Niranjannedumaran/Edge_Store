# EdgeStore REST API Specification

All endpoints are prefixed with `/api` and return structured JSON responses. Protected endpoints require a valid JWT Bearer token in the `Authorization` header (`Bearer <token>`).

---

## 1. Authentication Endpoints (`/api/auth`)

### `POST /api/auth/login`
- **Request Body**: `{"username": "admin", "password": "AdminEdgeStore2026!"}`
- **Response**: `{"access_token": "<jwt>", "token_type": "bearer", "user": {...}}`

### `GET /api/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Current user profile object.

### `POST /api/auth/logout`
- Invalidates session and logs audit event.

---

## 2. File Operations (`/api/files`)

### `POST /api/files/upload`
- **Content-Type**: `multipart/form-data` (`file`)
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
{
  "file": {
    "id": "c1f7a098-...",
    "filename": "backup.tar.gz",
    "file_size": 1048576,
    "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "replica_status": "synced"
  },
  "primary_write": true,
  "replica_synced": true,
  "is_degraded": false
}
```

### `GET /api/files`
- **Query Params**: `search` (string), `status` (synced, pending, failed, degraded)
- **Response**: Array of StoredFile metadata records.

### `GET /api/files/{id}/download`
- **Response**: Binary file stream.
- **Custom Headers**:
  - `X-EdgeStore-SHA256`: Expected checksum.
  - `X-EdgeStore-Degraded-Fallback`: `true` if read was served from Drive B because Drive A was unavailable.

### `DELETE /api/files/{id}`
- **Response**: Deletes file from primary and replica volumes. Returns `status: "COMPLETED"` or `status: "DELETE_PENDING"` if partial failure occurred.

### `GET /api/files/{id}/verify`
- Audits SHA-256 on primary and replica storage and returns cross-drive integrity status.

---

## 3. Storage & Vault Endpoints (`/api/storage`)

### `GET /api/storage/status`
- Returns Drive A and Drive B telemetry, operational mode (`NORMAL`, `DEGRADED`, `OFFLINE`), and LUKS vault state.

### `POST /api/storage/vault/unlock` (Admin Only)
- Reads Key-SD, unlocks LUKS containers, and mounts filesystems.

### `POST /api/storage/vault/lock` (Admin Only)
- Flushes buffers (`sync`), unmounts filesystems, and closes LUKS crypt mappers.

---

## 4. Replication Endpoints (`/api/replication`)

### `GET /api/replication/status`
- Returns replication engine state, sync timestamp, and error queue.

### `POST /api/replication/sync` (Admin Only)
- Retries pending or failed replication files.

### `POST /api/replication/rebuild` (Admin Only)
- Initiates Semi-Automated Replica Rebuild from surviving drive to replacement drive.

---

## 5. Hardware Simulation Endpoints (`/api/simulation`)

*Available only when `ENVIRONMENT_MODE=simulation`*

### `POST /api/simulation/drive`
- Injects drive state: `{"drive": "primary", "action": "fail" | "recover" | "disconnect"}`

### `POST /api/simulation/key-sd`
- Controls Key-SD state: `{"action": "remove" | "insert", "valid": true}`

### `POST /api/simulation/battery`
- Adjusts battery level and charging state: `{"level": 20, "charging": false}`

### `POST /api/simulation/replication-fault`
- Injects synthetic replication write failures: `{"simulate_failure": true}`

---

## 6. Client Management Endpoints (`/api/clients`)

Stores, updates, searches, and manages client details in **MongoDB** (`clients` collection).

### `POST /api/clients`
- **Description**: Stores new client details in MongoDB with email uniqueness validation.
- **Request Body**:
```json
{
  "name": "Acme Innovations",
  "email": "contact@acme.com",
  "phone": "+1-800-555-0199",
  "company": "Acme Global",
  "address": "100 Enterprise Way, Suite 300",
  "notes": "Enterprise tier storage client",
  "metadata": {
    "tier": "enterprise",
    "region": "us-west"
  }
}
```
- **Response (`201 Created`)**:
```json
{
  "id": "6aa541b82ebb832ffbf1dd12",
  "name": "Acme Innovations",
  "email": "contact@acme.com",
  "phone": "+1-800-555-0199",
  "company": "Acme Global",
  "address": "100 Enterprise Way, Suite 300",
  "notes": "Enterprise tier storage client",
  "metadata": { "tier": "enterprise", "region": "us-west" },
  "created_at": "2026-09-12T12:12:40.123456Z",
  "updated_at": "2026-09-12T12:12:40.123456Z",
  "created_by": "client_frontend"
}
```

### `GET /api/clients`
- **Query Params**:
  - `skip` (integer, default: 0): Pagination offset.
  - `limit` (integer, default: 50): Number of items per page.
  - `q` (string, optional): Search query across `name`, `company`, `email`, `phone`, `address`, and `notes`.
- **Response (`200 OK`)**:
```json
{
  "total": 12,
  "page": 1,
  "limit": 50,
  "items": [...]
}
```

### `GET /api/clients/{client_id}`
- **Response (`200 OK`)**: Single ClientResponse object matching MongoDB ObjectId.

### `PUT /api/clients/{client_id}`
- **Description**: Partially updates client fields.
- **Response (`200 OK`)**: Updated ClientResponse.

### `DELETE /api/clients/{client_id}`
- **Headers**: `Authorization: Bearer <token>` (Protected operation)
- **Response (`204 No Content`)**: Deletes client document and records `CLIENT_DELETE` in audit log.

---

## 8. Security Shield & Anti-Bot Endpoints (`/api/security`)

### `GET /api/security/anti-bot/challenge`
- **Description**: Issues a 'Not a Robot' mathematical challenge to prove authenticity and bypass flood rate-limiting or DDoS quarantine.
- **Response (`200 OK`)**:
```json
{
  "challenge_id": "4b2e1f89-8d76-4a11-b452-e9a2b5e0c65d",
  "prompt": "Please prove you are human: What is 23 + 41?",
  "expires_in_seconds": 300,
  "verification_endpoint": "/api/security/anti-bot/verify"
}
```

### `POST /api/security/anti-bot/verify`
- **Description**: Verifies client solution. On success, caches IP in 24-hour verified human cache, unbans quarantined IP, and returns `anti_bot_token`.
- **Request Body**: `{"challenge_id": "...", "solution": "64"}`
- **Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Human verification successful. IP unblocked and cached.",
  "anti_bot_token": "human_3f1b4a92c0d8...",
  "verified_ip": "192.168.1.105",
  "cache_duration_hours": 24
}
```

### `GET /api/security/ddos/stats`
- **Description**: Real-time DDoS mitigation shield and cache telemetry.
- **Response (`200 OK`)**:
```json
{
  "status": "ACTIVE",
  "total_requests_screened": 1420,
  "floods_blocked": 15,
  "active_quarantined_ips": 1,
  "quarantined_ips_detail": { "203.0.113.42": 145 },
  "verified_humans_in_cache": 3,
  "burst_limit_config": {
    "max_burst_requests": 40,
    "burst_window_seconds": 5,
    "quarantine_duration_seconds": 180,
    "human_cache_duration_seconds": 86400
  }
}
```

