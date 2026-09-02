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
- All protected endpoints enforce authorization on the backend; frontend visibility toggles are strictly for UX.
