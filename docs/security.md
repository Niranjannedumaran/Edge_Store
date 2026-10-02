# EdgeStore Security Architecture & Policy

EdgeStore enforces a strict **Defense-in-Depth** model designed for physical edge appliances where devices may be exposed to untrusted physical environments.

---

## 1. Security Layers

### Layer 1: Removable Physical Key-SD
- The physical Key-SD contains raw cryptographic key material required to unlock dm-crypt LUKS2 volumes.
- It is physically isolated from OS storage.
- Key removal dispatches an automated udev event triggering `lock_storage.sh`:
  1. Filesystem write buffers flushed (`sync`).
  2. Encrypted volumes unmounted (`umount`).
  3. Device mappers deactivated (`cryptsetup luksClose`).
  4. Application vault state set to LOCKED (enforcing HTTP `423 Locked`).

### Layer 2: LUKS2 Full-Disk Encryption
- Cipher: `aes-xts-plain64` with 512-bit key size.
- Key derivation: `argon2id`.
- Underlying blocks on magnetic platters are unreadable without the Key-SD.
- Even if physical HDDs are stolen, data remains encrypted.

### Layer 3: Transport Security (TLS)
- All client-to-appliance traffic is encrypted using TLS 1.3 / HTTPS.

### Layer 4: Enterprise Role-Based Access Control (RBAC) & Sessions
- Salted `bcrypt` password hashing (cost factor 12).
- Signed JWT access tokens with unique `jti` session binding.
- Session revocation: Administrators can immediately revoke active tokens by setting `is_revoked=True` in the database.
- Temporary Guest accounts: Automatic expiration enforcement where expired accounts immediately receive `HTTP 401 Unauthorized`.
- **5 Standard Roles**:
  1. **Super Admin**: Full appliance control (Storage, replication, users, roles matrix, security, sessions, power).
  2. **Storage Admin**: Storage volumes, replication engine, semi-automated rebuilds, file operations, hardware health.
  3. **Security Admin**: User provisioning, role & permission matrix, access policies, session revocation, security audits.
  4. **File Manager**: Upload, preview, download, rename, and delete files.
  5. **Guest / Viewer**: Strictly read-only file list and preview. Uploads, modifications, deletions, and administrative endpoints are rejected with `HTTP 403 Forbidden`.

### Layer 5: Data Integrity (SHA-256)
- Checksum computed during initial binary upload.
- Verified on replica volume immediately after transfer.
- Verified before file stream download.
- Cross-drive verification endpoint allows administrators to audit file integrity on demand.

### Layer 6: Redundant Dual-Drive Availability
- Primary and secondary drives mirror data.
- Read failover provides uninterrupted availability if Drive A fails.

### Layer 7: Resource-Level Authorization (IDOR Protection)
- Every file access (download, view, delete, update) validates that the resource belongs to the authenticated `user_id`.
- Knowledge or enumeration of file IDs (e.g. `/api/v1/files/102`) across users is blocked with `HTTP 404 Not Found` or `HTTP 403 Forbidden`.
- Administrative bypass is restricted strictly to users with `users.manage` authority.

### Layer 8: Storage & I/O Hardening
- **Safe UUID Storage Decoupling**: User-supplied filenames are never used as filesystem path components. Files are stored as `files/{user_id}/{uuid}` on disk. Original filenames are preserved strictly in SQLite database metadata.
- **Atomic Writes**: Incoming byte streams are written to a `.tmp_{uuid}` staging file, calculating SHA-256 in real time. Upon complete stream verification, an atomic `os.replace` commits the file, preventing partial file corruption.
- **Pre-Write Disk Headroom Check**: Disks maintain a minimum safety buffer (`MIN_DISK_HEADROOM_MB`, default 50MB). Writes that would breach this buffer are rejected with `HTTP 507 Insufficient Storage`.
- **Executable Upload Blocking**: Blacklist filtering blocks dangerous extensions (`.exe`, `.dll`, `.bat`, `.cmd`, `.sh`, `.vbs`, `.ps1`, `.com`, `.scr`) to prevent hosting malicious binaries.

### Layer 9: Temporary Guest File Sharing
- Secure cryptographic share tokens (64-character URL-safe tokens) for time-limited guest access.
- Granular expiration timestamps and maximum download counters.
- Dedicated guest download endpoint (`GET /api/v1/files/shared/{token}`) with strict tracking and automatic revocation upon limit exhaustion.

### Layer 10: Anti-Bot & DDoS Attack Mitigation Shield ("Not a Robot" Cache)
- **Sliding-Window Flood Detection**: Analyzes traffic burst frequency (default: max 40 requests per 5-second sliding window).
- **Automated Quarantine Cache**: IPs triggering flood heuristics are automatically quarantined in a fast in-memory blacklist cache for 180 seconds, terminating requests immediately with `HTTP 429 Too Many Requests` before hitting the database or disk.
- **"Not a Robot" Challenge System**: Issues lightweight, zero-dependency cryptographic math challenges (`GET /api/security/anti-bot/challenge`).
- **Verified Human Whitelist Cache**: Solving the challenge (`POST /api/security/anti-bot/verify`) instantly lifts any active DDoS quarantine on the IP and caches the client in the 24-hour Verified Human Cache with an issued `X-Anti-Bot-Token`.
- **Live Shield Telemetry**: Endpoint `GET /api/security/ddos/stats` provides real-time visibility into screened requests, blocked attacks, and active cached sessions.

---


## 2. Granular Permissions (35 Capabilities)

| Subsystem | Capabilities |
|---|---|
| **Files** | `files.read`, `files.preview`, `files.download`, `files.upload`, `files.modify`, `files.rename`, `files.delete`, `files.move`, `files.share` |
| **Users** | `users.read`, `users.create`, `users.update`, `users.disable`, `users.delete`, `users.reset_password`, `users.revoke_sessions` |
| **Roles** | `roles.read`, `roles.create`, `roles.update`, `roles.delete`, `roles.assign` |
| **Storage** | `storage.read`, `storage.manage` |
| **Replication** | `replication.read`, `replication.manage`, `replication.rebuild` |
| **Security** | `security.read`, `security.manage` |
| **Audit** | `audit.read` |
| **System** | `system.read`, `system.manage` |
| **Hardware** | `hardware.read`, `hardware.manage` |
| **Power** | `power.read`, `power.manage` |

---

## 3. Security Hygiene Rules
- Passwords, JWT secrets, and raw LUKS key material are **NEVER logged**.
- Structured logger automatically redacts sensitive keywords (`password`, `token`, `secret`, `luks_key`).
- Path traversal protection strictly validates relative paths against volume roots.
- Container execution runs as unprivileged user `edgestore` (`UID 10001`).
- All protected endpoints enforce authorization on the backend; frontend visibility toggles are strictly for UX.

