# EdgeStore Security Threat Model & Defense-in-Depth Analysis

**Document Version**: 1.0  
**Target Appliance**: EdgeStore Security Storage Appliance (Raspberry Pi 4 / Linux / Local Hardware)  
**Classification**: Defense-in-Depth Architecture Specification

---

## 1. Executive Summary & Security Philosophy

EdgeStore is an on-premises, physical edge storage appliance engineered to safeguard sensitive data under untrusted or hostile operational environments. It enforces **Defense-in-Depth** across physical hardware, Linux kernel cryptographic primitives, operating system isolation, transport encryption, and granular application-level authorization.

Security is not implemented as an afterthought or visual veneer. Every protective barrier is enforced on the server. Client-side controls exist exclusively for user experience.

---

## 2. Architecture & Data Flow Diagram

```
                 UNTRUSTED INTERNET / LOCAL SUBNET
                                 │
                                 ▼
                     TLS 1.3 / HTTPS Ingress
                     [Strict Headers, HSTS, CORS]
                                 │
                                 ▼
                     Application Gateway / API
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
      Authentication Layer                  Rate Limiter & DoS
   [bcrypt, JTI, Lockout]                [Sliding Window, 100MB Cap]
              │                                     │
              └──────────────────┬──────────────────┘
                                 ▼
                    RBAC Authorization Matrix
                 [35 Capabilities & IDOR Checks]
                                 │
                                 ▼
                      Business Domain Core
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        File Operations     Replication Engine  Security Audits
        [SHA-256 Intact]     [Cross-Drive Sync]   [Tamper-Evident]
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
                   Hardware Abstraction Layer (HAL)
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
       Physical Key-SD                      LUKS2 dm-crypt Engine
    [UUID Validation, Key]                  [aes-xts-512, argon2id]
              │                                     │
              └──────────────────┬──────────────────┘
                                 ▼
                     Underlying Storage Media
                      ┌──────────┴──────────┐
                      ▼                     ▼
                 Primary HDD           Replica HDD
                 (Drive A)             (Drive B)
```

---

## 3. Asset Inventory & Security Requirements Matrix

Every sensitive asset in EdgeStore has distinct security requirements across the CIA triad, Authentication, and Authorization:

| Asset | Confidentiality | Integrity | Availability | Authentication | Authorization | Implementation Mechanism |
|---|---|---|---|---|---|---|
| **User Accounts** | High | High | High | Required | Super/Security Admin | SQLite `users` table, unique index, salted passwords. |
| **Passwords** | Critical | Critical | High | N/A | Server-only verify | Salted `bcrypt` (12 rounds), never logged, constant-time compare. |
| **Auth Tokens (JWT)** | High | Critical | High | Required | Cryptographic Sign | HS256 signed tokens, embedded UUID `jti`, short expiration. |
| **Session State** | High | Critical | High | Required | Bearer + JTI | `user_sessions` table, real-time revocation checking. |
| **Stored Files** | Critical | Critical | High | Required | Owner + Files RBAC | LUKS2 encryption, non-predictable UUID storage paths, SHA-256. |
| **File Metadata** | Medium | Critical | High | Required | Files RBAC | Indexed SQLite schema, sanitized filenames, IDOR validation. |
| **Encryption Metadata** | Critical | Critical | Critical | Hardware | Key-SD Only | `cryptsetup` LUKS2 header, 512-bit master key. |
| **LUKS Storage Container** | Critical | Critical | High | Key-SD Token | System Level | `dm-crypt` virtual block device (`/dev/mapper/...`). |
| **Physical Key-SD** | Critical | Critical | Critical | Hardware Token | System Level | Detachable SD device with UUID verification, udev lock on removal. |
| **Primary HDD (Drive A)** | Critical | Critical | High | System Mount | Storage Admin | LUKS2 encrypted filesystem with atomic write buffers. |
| **Replica HDD (Drive B)** | Critical | Critical | High | System Mount | Storage Admin | Redundant mirror for fault tolerance and failover read. |
| **Database File** | High | Critical | High | System Level | Internal Engine | SQLite in WAL mode with strict foreign key constraints. |
| **Audit Logs** | Medium | Critical | High | Server-generated | Audit RBAC | Append-only `audit_logs` table with automatic keyword redaction. |
| **System Configuration** | Medium | Critical | High | Required | Super Admin | Environment variables, `.env` file, immutable constants. |
| **Admin Controls** | High | Critical | High | Required | Role Matrix | Backend `require_permission` dependency factory. |
| **Replication Queue** | Medium | High | High | Required | Storage Admin | State machine tracking `PENDING`, `SYNCED`, `FAILED`. |
| **Hardware Telemetry** | Low | High | High | Required | Role-Gated | Real-time HAL queries for temperature, voltage, SMART. |

---

## 4. Threat Actor Profiles

1. **Remote Unauthenticated Attacker**:
   - Attacks: Volumetric DoS, brute-force password attacks, credential stuffing, API fuzzing, injection attacks, path traversal.
   - Mitigations: Rate limiting (sliding window), brute-force progressive delay & temporary lockout, request size cap (100MB), parameterized queries, strict filename sanitization.
2. **Local Subnet Attacker (Untrusted LAN)**:
   - Attacks: Man-in-the-middle eavesdropping, ARP spoofing, session hijacking.
   - Mitigations: TLS 1.3 / HTTPS encryption, HSTS headers, secure token bearer format, anti-framing headers (`DENY`), no plaintext credentials over network.
3. **Malicious Local User / Guest**:
   - Attacks: Privilege escalation (vertical), accessing other users' files (horizontal / IDOR), parameter tampering.
   - Mitigations: Strict server-side RBAC enforcement (`HTTP 403 Forbidden`), IDOR ownership checks on download/rename/delete, frontend views strictly driven by backend permissions.
4. **Compromised User Account**:
   - Attacks: Malicious uploads (polyglots, web shells, malware), mass deletions.
   - Mitigations: Dangerous extension restrictions (`.exe`, `.sh`, `.bat`, etc. blocked), non-executable mount policies, audit logging of all actions, instant session revocation.
5. **Compromised Administrator Account**:
   - Attacks: Unauthorized user creation, role modification, data destruction.
   - Mitigations: Immutable super-admin baseline, comprehensive append-only audit trail, session revocation, physical Key-SD requirement for drive mounts.
6. **Malicious USB Device Insertion**:
   - Attacks: BadUSB spoofing, untrusted storage mounting, data exfiltration.
   - Mitigations: Explicit hardware UUID matching for Key-SD, strict mount-point controls, no automatic execution of arbitrary USB storage.
7. **Attacker with Temporary Physical Access**:
   - Attacks: Removing USB drives, pulling power, stealing the appliance chassis.
   - Mitigations: Without the Key-SD, magnetic platters on Drive A & B are inert LUKS2 ciphertexts (`aes-xts-512` with `argon2id`). Removing Key-SD dispatches immediate udev lock script.
8. **Ransomware / Data Destruction Attacker**:
   - Attacks: Overwriting files with encrypted payloads, mass deletion.
   - Mitigations: Dual-drive separation, SHA-256 verification before write acceptance, full audit logging of deletion events.

---

## 5. Honest Real-World Security Limitations

To avoid false or misleading security claims, the following physical and architectural boundaries are explicitly acknowledged:

1. **Volumetric DDoS**: EdgeStore's application-level rate limiting and request caps protect local CPU and memory. However, EdgeStore on a Raspberry Pi cannot absorb multi-gigabit upstream network flooding. Upstream network firewalls, gateways, or reverse proxies are required for Internet-scale DDoS protection.
2. **Physical Possession of Key-SD and Appliance Simultaneously**: If an attacker steals both the Raspberry Pi and the physical Key-SD together while the device is powered on and unlocked, software encryption in RAM can theoretically be extracted via cold-boot or memory acquisition. Physical containment is essential.
3. **Replication vs. Ransomware**: Mirroring data to Drive B provides high hardware availability against disk failure. However, if a valid user account with write/delete capabilities intentionally overwrites or deletes files, the replica will faithfully mirror that state unless soft-delete/offline retention policies are implemented.
