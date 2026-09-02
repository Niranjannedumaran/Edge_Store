# EdgeStore Automated Testing Guide

Testing is mandatory for all EdgeStore subsystems. Features are not considered operational based on visual inspection alone; every state transition and failure mode is covered by automated unit and integration tests.

---

## 1. Test Suite Overview

| Test Module | Coverage |
|---|---|
| `backend/tests/test_auth.py` | Admin login, operator login, invalid password rejection, JWT token decoding, RBAC privilege enforcement |
| `backend/tests/test_hal_simulation.py` | StorageProvider CRUD, KeyDeviceProvider insertion/removal, EncryptionProvider vault unlock/lock, PowerProvider threshold shifts |
| `backend/tests/test_file_operations.py` | Multi-part upload, SHA-256 generation, synchronous replication to Drive B, download with checksum header, clean deletion |
| `backend/tests/test_fault_injection.py` | Drive A simulated failure, failover read routing to Drive B with degraded indicator, Key-SD removal causing HTTP 423 Locked |
| `backend/tests/test_security.py` | Path traversal protection (`../../`), on-disk malicious tampering detection via SHA-256 verification (HTTP 422), log hygiene verification |

---

## 2. Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest backend/tests/ -v
```

Output:
```
backend/tests/test_auth.py::test_login_success PASSED
backend/tests/test_auth.py::test_login_invalid_password PASSED
backend/tests/test_auth.py::test_get_me PASSED
backend/tests/test_auth.py::test_rbac_admin_endpoint_forbidden_for_user PASSED
backend/tests/test_auth.py::test_rbac_admin_endpoint_allowed_for_admin PASSED
backend/tests/test_fault_injection.py::test_drive_failure_and_failover_download PASSED
backend/tests/test_fault_injection.py::test_key_sd_removal_locks_vault PASSED
backend/tests/test_file_operations.py::test_file_upload_and_replication PASSED
backend/tests/test_hal_simulation.py::test_simulation_storage_crud PASSED
backend/tests/test_hal_simulation.py::test_simulation_key_device_and_encryption PASSED
backend/tests/test_hal_simulation.py::test_simulation_power_provider_thresholds PASSED
backend/tests/test_security.py::test_path_traversal_sanitization PASSED
backend/tests/test_security.py::test_tampered_file_detection PASSED
backend/tests/test_security.py::test_no_plaintext_passwords_in_audit PASSED

14 passed in ~4.3s
```

---

## 3. Frontend Production Build Validation

Validate that React 18 frontend compiles with zero warnings or errors:
```bash
cd frontend
npm run build
```
Result: Transforms 1,836+ modules into compressed distribution assets in under 3 seconds.
