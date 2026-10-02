# EdgeStore Automated Testing Guide

Testing is mandatory across all EdgeStore subsystems. Features are not considered operational based on visual inspection alone; every state transition, access permission, and failure mode is covered by automated regression and unit test suites.

---

## 1. Test Suite Overview (57 Automated Tests)

| Test Module | Tests | Subsystem Coverage |
|---|---|---|
| `backend/tests/test_anti_bot_ddos.py` | 6 | 'Not a Robot' mathematical challenge issuance, challenge verification, 24-hour verified human cache, DDoS burst attack detection, automated IP quarantine cache (HTTP 429), unblocking via captcha, and real-time shield telemetry |
| `backend/tests/test_auth.py` | 5 | Admin login, operator login, invalid password rejection, JWT token decoding, RBAC privilege enforcement |
| `backend/tests/test_cybersecurity.py` | 7 | Security headers (CSP, HSTS), path traversal containment, account enumeration defense, brute force lockout, IDOR protection, SQL injection resilience, security telemetry |
| `backend/tests/test_docker_backend.py` | 11 | LocalStorageProvider atomic read/write, path traversal, deletion, DockerReplicationProvider SHA-256 verification, differential recovery, honest hardware telemetry, IDOR cross-tenant isolation |
| `backend/tests/test_fault_injection.py` | 2 | Simulated Drive A failure, automated failover read routing to Drive B, Key-SD removal causing vault lockout |
| `backend/tests/test_file_operations.py` | 1 | Multi-part upload, SHA-256 calculation, dual-drive synchronous replication, download with checksum header, clean deletion |
| `backend/tests/test_hal_simulation.py` | 3 | StorageProvider CRUD, KeyDeviceProvider insertion/removal, EncryptionProvider vault unlock/lock, PowerProvider threshold shifts |
| `backend/tests/test_mongo_clients.py` | 8 | Client creation, duplicate email rejection (409 Conflict), invalid ObjectId handling, client updates, client deletion, and protected endpoint access |
| `backend/tests/test_rbac_matrix.py` | 4 | Guest read-only enforcement, Storage Admin vs Security Admin duty separation, guest expiration, and instant session revocation |
| `backend/tests/test_security.py` | 3 | Path traversal sanitization, on-disk file tampering detection via SHA-256 verification (HTTP 422), log hygiene verification |
| `backend/tests/test_storage_security.py` | 7 | IDOR download blocking, internal UUID path safety, dangerous executable upload blocking, temporary guest share tokens, preview-only shares, replication failure resilience, truthful storage telemetry |

---

## 2. Running Automated Tests

Run the full pytest suite:
```bash
# Windows PowerShell:
$env:PYTHONPATH="."
python -m pytest backend/tests/ -v

# Linux / macOS:
PYTHONPATH=. python -m pytest backend/tests/ -v
```

Expected result:
```
======================= 51 passed in ~28s =======================
```

---

## 3. Live Integration Testing

For testing running Docker containers with MongoDB:
```bash
python ./.gemini/antigravity-ide/brain/<conversation-id>/scratch/test_live_clients_mongo.py
```
Validates:
1. Administrator authentication & JWT generation
2. Live appliance health probe
3. Client creation in MongoDB
4. Unique email collision rejection (`409 Conflict`)
5. ID lookup and text search across address, company, and notes
6. Client updates and EdgeStore audit log verification

---

## 4. Frontend Production Build Validation

Validate that React 18 frontend compiles cleanly:
```bash
cd frontend
npm run build
```
Result: Builds production distribution bundle into `frontend/dist/`.
