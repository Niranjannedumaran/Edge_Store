# EdgeStore Database & Metadata Architecture

EdgeStore Phase 1 utilizes **SQLite** for metadata, file indexing, and audit records. File payloads and encryption key material are **NEVER stored in SQLite**.

---

## 1. Design Principles

- **File Contents on Encrypted Filesystem**: Only metadata (ID, owner, filename, size, SHA-256 hash, storage path, replica status) is recorded in SQLite.
- **Zero Plaintext Secrets**: Cryptographic key material is restricted to the physical Key-SD device and dm-crypt kernel memory. Passwords use salted bcrypt hashes.
- **Foreign Key Constraints & WAL Mode**:
  - `PRAGMA foreign_keys = ON`: Strict referential integrity.
  - `PRAGMA journal_mode = WAL`: Concurrency for simultaneous telemetry readers and write transactions.
  - `PRAGMA synchronous = NORMAL`: Balances performance with power resilience.

---

## 2. Entity Schemas

### `users`
- `id` (INTEGER PK AUTOINCREMENT)
- `username` (VARCHAR(64) UNIQUE)
- `email` (VARCHAR(128) UNIQUE)
- `hashed_password` (VARCHAR(256))
- `role` (VARCHAR(16)): `admin` or `user`
- `is_active` (BOOLEAN)
- `created_at` (DATETIME)
- `last_login_at` (DATETIME)

### `files`
- `id` (VARCHAR(36) PK UUID)
- `owner_id` (INTEGER FK `users.id` ON DELETE CASCADE)
- `filename` (VARCHAR(255))
- `file_size` (BIGINT)
- `sha256_hash` (VARCHAR(64) INDEX)
- `storage_path` (VARCHAR(512) UNIQUE)
- `content_type` (VARCHAR(128))
- `replica_status` (VARCHAR(32)): `synced`, `pending`, `failed`, `degraded`, `delete_pending`
- `created_at` (DATETIME)
- `updated_at` (DATETIME)
- `last_verified_at` (DATETIME)

### `audit_events`
- `id` (INTEGER PK AUTOINCREMENT)
- `timestamp` (DATETIME INDEX)
- `event_type` (VARCHAR(64) INDEX)
- `user_id` (INTEGER FK `users.id`)
- `username` (VARCHAR(64))
- `ip_address` (VARCHAR(45))
- `description` (TEXT)
- `severity` (VARCHAR(16)): `INFO`, `WARNING`, `ERROR`, `CRITICAL`
