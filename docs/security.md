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

### Layer 4: Role-Based Access Control (RBAC) & JWT
- Salted `bcrypt` password hashing (cost factor 12).
- Signed JWT access tokens (HS256) with strict expiration.
- Roles:
  - `USER`: Upload, download, verify, and delete owned files.
  - `ADMIN`: User provisioning, hardware telemetry, fault controls, audit logs, vault lock/unlock, semi-automated rebuilds.

### Layer 5: Data Integrity (SHA-256)
- Checksum computed during initial binary upload.
- Verified on replica volume immediately after transfer.
- Verified before file stream download.
- Cross-drive verification endpoint allows administrators to audit file integrity on demand.

### Layer 6: Redundant Dual-Drive Availability
- Primary and secondary drives mirror data.
- Read failover provides uninterrupted availability if Drive A fails.

---

## 2. Security Hygiene Rules
- Passwords, JWT secrets, and raw LUKS key material are **NEVER logged**.
- Structured logger automatically redacts sensitive keywords (`password`, `token`, `secret`, `luks_key`).
- Path traversal protection strictly validates relative paths against volume roots.
