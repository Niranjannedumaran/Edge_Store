# EdgeStore Database & Metadata Architecture

EdgeStore utilizes a dual-engine database architecture:
1. **SQLite (Relational Core)**: File metadata, RBAC matrices, authentication sessions, and append-only audit trail.
2. **MongoDB (Document Store)**: High-performance, scalable storage for client organization details, customer accounts, and custom metadata attributes.

---

## 1. Design Principles

- **Separation of Concerns**: File payloads are stored on encrypted dual volumes (`/data/primary` and `/data/replica`). Relational metadata resides in SQLite. Client organizational details reside in MongoDB.
- **Zero Plaintext Secrets**: Cryptographic key material is restricted to dm-crypt kernel memory / Key-SD. Passwords use salted bcrypt hashes.
- **SQLite Optimization**:
  - `PRAGMA foreign_keys = ON`: Strict referential integrity.
  - `PRAGMA journal_mode = WAL`: Concurrency for simultaneous telemetry readers and write transactions.
  - `PRAGMA synchronous = NORMAL`: Balances performance with power resilience.
- **MongoDB Indexing**:
  - Unique index on `email` to prevent collision.
  - Compound text search index on `name`, `company`, and `address`.
  - Timestamp index on `created_at`.

---

## 2. SQLite Schemas

### `users`
- `id` (INTEGER PK AUTOINCREMENT)
- `username` (VARCHAR(64) UNIQUE)
- `email` (VARCHAR(128) UNIQUE)
- `hashed_password` (VARCHAR(256))
- `role` (VARCHAR(32)): `super_admin`, `storage_admin`, `file_manager`, `auditor`, `secops`, `guest`
- `is_active` (BOOLEAN)
- `created_at` (DATETIME)
- `last_login_at` (DATETIME)

### `roles` & `permissions`
- Standard RBAC table with `role_permissions` join table enforcing granular permission codes (`files.read`, `files.upload`, `storage.manage`, etc.).

### `user_sessions`
- Tracks active JWT tokens (`token_jti`), IP addresses, user-agent, creation, and last activity timestamps for immediate session revocation.

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
- Append-only security audit log recording every login, upload, replication, client mutation, and administrative action.

---

## 3. MongoDB Document Schema (`edgestore_clients`)

Managed asynchronously via **Motor** and **PyMongo**:

### Collection: `clients`

```json
{
  "_id": ObjectId("6aa541b82ebb832ffbf1dd12"),
  "name": "Acme Innovations",
  "email": "contact@acme.com",
  "phone": "+1-800-555-0199",
  "company": "Acme Global",
  "address": "100 Enterprise Way, Suite 300",
  "notes": "Enterprise tier storage client",
  "metadata": {
    "tier": "enterprise",
    "contract_id": "CNT-2026-992"
  },
  "created_at": ISODate("2026-09-12T12:12:40.123Z"),
  "updated_at": ISODate("2026-09-12T12:12:40.123Z"),
  "created_by": "client_frontend"
}
```

### Collection Indices:
- `idx_client_email_unique`: `{ "email": 1 }` (unique constraint)
- `idx_client_text_search`: `{ "name": "text", "company": "text", "address": "text" }`
- `idx_client_created_at`: `{ "created_at": -1 }`
