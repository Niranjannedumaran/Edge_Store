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
