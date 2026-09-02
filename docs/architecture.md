# EdgeStore Architecture Specification

EdgeStore is an enterprise-grade secure local storage appliance engineered for single-node Raspberry Pi 4 deployment with dual-drive replication (Drive A & Drive B), LUKS2 full-disk encryption, removable physical Key-SD authentication, SHA-256 integrity verification, and battery-aware energy policy.

---

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph ClientLayer["Client Layer"]
        WebBrowser["Modern Web Browser (React 18 Console)"]
    end

    subgraph SecurityPerimeter["Appliance Network Perimeter"]
        TLS["HTTPS / TLS Termination"]
    end

    subgraph HardwareAppliance["EdgeStore Single-Node Appliance (Raspberry Pi 4)"]
        subgraph ComputeHost["Compute & System Host"]
            FastAPI["FastAPI Application Server"]
            ReplicationDaemon["Replication Engine Daemon"]
            HealthWatchdog["System & Power Watchdog"]
            SQLite[("SQLite Metadata & Audit Store")]
        end

        subgraph HardwareAbstractionLayer["Hardware Abstraction Layer (HAL)"]
            StorageInterface["StorageProvider"]
            KeyInterface["KeyDeviceProvider"]
            CryptoInterface["EncryptionProvider"]
            PowerInterface["PowerProvider"]
        end

        subgraph PhysicalDevices["Physical / Simulated Hardware"]
            KeySD["Physical Key-SD (Removable LUKS Key)"]
            DriveA["Drive A - Primary (LUKS2 ext4)"]
            DriveB["Drive B - Replica (LUKS2 ext4)"]
            UPS["UPS / Battery Telemetry"]
        end
    end

    WebBrowser -->|HTTPS / REST API| TLS
    TLS --> FastAPI
    FastAPI --> SQLite
    FastAPI --> HardwareAbstractionLayer
    ReplicationDaemon --> HardwareAbstractionLayer
    HealthWatchdog --> HardwareAbstractionLayer
    StorageInterface --> DriveA
    StorageInterface --> DriveB
    KeyInterface --> KeySD
    CryptoInterface --> DriveA
    CryptoInterface --> DriveB
    PowerInterface --> UPS
```

---

## 2. Hardware Architecture

```mermaid
graph TD
    subgraph EdgeStoreAppliance["Raspberry Pi 4 Single-Node Appliance"]
        RPi4["Raspberry Pi 4 Model B (4GB/8GB RAM)"]
        OS_SD["MicroSD Slot: Raspberry Pi OS (64-bit Lite)"]
        USB_Hub["USB 3.0 High-Speed Bus"]
        GPIO["GPIO / I2C Bus"]
        
        subgraph StorageSubsystem["Storage Subsystem"]
            DriveA["HDD A: Primary Storage (USB 3.0 /dev/sda)"]
            DriveB["HDD B: Replica Mirror (USB 3.0 /dev/sdb)"]
        end

        subgraph AuthenticationSubsystem["Authentication Subsystem"]
            KeySD["Key-SD Card Reader (USB /dev/sdc or dedicated slot)"]
        end

        subgraph PowerSubsystem["Power & Energy Subsystem"]
            UPS_Hat["UPS Power Hat / Battery Backup"]
        end
    end

    RPi4 --> OS_SD
    RPi4 --> USB_Hub
    RPi4 --> GPIO
    USB_Hub --> DriveA
    USB_Hub --> DriveB
    USB_Hub --> KeySD
    GPIO --> UPS_Hat
```

---

## 3. Software Architecture

```mermaid
graph LR
    subgraph Frontend["Enterprise React Frontend"]
        UI_Shell["App Shell & Navigation"]
        Auth_Context["AuthContext (JWT)"]
        Hardware_Context["HardwareContext (Live Polling)"]
        Simulation_Dock["Developer Simulation Dock"]
    end

    subgraph Backend["FastAPI Backend Service"]
        API_Routers["API Routers (/api/auth, /files, /storage, /replication, /system, /admin)"]
        Auth_Service["Auth & RBAC Service (bcrypt + pyjwt)"]
        File_Service["File Service (SHA-256 + Stream I/O)"]
        Replication_Service["Replication Coordinator"]
        KeyVault_Service["Key & Vault Coordinator"]
        Health_Service["Health & Energy Service"]
    end

    subgraph HAL["Hardware Abstraction Layer"]
        HAL_Factory["HAL Container Factory"]
        Sim_Adapter["Simulation Providers (Laptop Dev)"]
        Linux_Adapter["Linux Hardware Providers (Raspberry Pi)"]
    end

    Frontend -->|REST API Requests| API_Routers
    API_Routers --> Auth_Service
    API_Routers --> File_Service
    API_Routers --> Replication_Service
    API_Routers --> KeyVault_Service
    API_Routers --> Health_Service
    File_Service --> HAL_Factory
    Replication_Service --> HAL_Factory
    KeyVault_Service --> HAL_Factory
    Health_Service --> HAL_Factory
    HAL_Factory --> Sim_Adapter
    HAL_Factory --> Linux_Adapter
```

---

## 4. Layered Architecture

```mermaid
graph TD
    L1["Layer 1: User Experience & Admin Presentation (React 18 + Pure CSS Tokens)"]
    L2["Layer 2: RESTful API Gateway & Security Interceptors (FastAPI + JWT)"]
    L3["Layer 3: Domain Application Services (File, Replication, KeyVault, Health, Audit)"]
    L4["Layer 4: Data Persistence & Metadata (SQLite with WAL Mode + Foreign Keys)"]
    L5["Layer 5: Hardware Abstraction Layer Interfaces (Storage, Key, Crypto, Power, Monitor)"]
    L6["Layer 6: Platform Adapters (Simulation Provider Stack / Linux Production Stack)"]
    L7["Layer 7: OS Kernel & Physical Infrastructure (Linux 6.x, dm-crypt, udev, systemd, HDDs)"]

    L1 --> L2
    L2 --> L3
    L3 --> L4
    L3 --> L5
    L5 --> L6
    L6 --> L7
```

---

## 5. Security Architecture (Defense-in-Depth)

```mermaid
graph TD
    subgraph Layer1["Layer 1: Physical Security"]
        KeySD["Removable Key-SD Hardware Token (Required for Vault Unlock)"]
    end

    subgraph Layer2["Layer 2: Storage Encryption"]
        LUKS2["Linux LUKS2 Full-Disk Encryption (AES-XTS-Plain64 512-bit)"]
    end

    subgraph Layer3["Layer 3: Transport Security"]
        TLS["HTTPS / TLS 1.3 Strict Transport Security"]
    end

    subgraph Layer4["Layer 4: Application Access Control"]
        RBAC["JWT Bearer Tokens + Salted Bcrypt Password Hashing + RBAC (USER / ADMIN)"]
    end

    subgraph Layer5["Layer 5: Cryptographic Data Integrity"]
        SHA256["End-to-End SHA-256 Checksums (Ingestion, Sync, and Download)"]
    end

    subgraph Layer6["Layer 6: High Availability & Redundancy"]
        Replication["Dual-Drive Mirroring with Hot-Standby Failover Routing"]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Layer5
    Layer5 --> Layer6
```

---

## 6. Storage Architecture

```mermaid
graph TD
    subgraph UserSpace["Application Space"]
        App["EdgeStore Application Service"]
        PosixFS["POSIX File API (open, read, write, unlink)"]
    end

    subgraph FilesystemLayer["Filesystem Layer"]
        MountA["/mnt/edgestore/primary (ext4)"]
        MountB["/mnt/edgestore/replica (ext4)"]
    end

    subgraph KernelCrypto["Linux Kernel dm-crypt Subsystem"]
        MapperA["/dev/mapper/edgestore_primary"]
        MapperB["/dev/mapper/edgestore_replica"]
    end

    subgraph BlockDevices["Physical Storage Hardware"]
        DevA["Drive A: /dev/disk/by-partlabel/edgestore-primary (LUKS2)"]
        DevB["Drive B: /dev/disk/by-partlabel/edgestore-replica (LUKS2)"]
    end

    App --> PosixFS
    PosixFS --> MountA
    PosixFS --> MountB
    MountA --> MapperA
    MountB --> MapperB
    MapperA --> DevA
    MapperB --> DevB
```

---

## 7. Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Browser
    participant API as FastAPI /api/auth/login
    participant Sec as Security Engine
    participant DB as SQLite DB
    participant Audit as Audit Service

    User->>API: POST /api/auth/login {username, password}
    API->>DB: Query User by username
    alt User Not Found
        API->>Audit: Log LOGIN_FAILED
        API-->>User: 401 Unauthorized (Invalid credentials)
    else User Exists
        API->>Sec: verify_password(plain_password, hashed_password)
        alt Password Mismatch
            API->>Audit: Log LOGIN_FAILED
            API-->>User: 401 Unauthorized (Invalid credentials)
        else Password Valid
            Sec->>Sec: create_access_token(claims={sub, role, id})
            API->>DB: Update last_login_at
            API->>Audit: Log LOGIN_SUCCESS
            API-->>User: 200 OK {access_token, token_type: "bearer", user}
        end
    end
```

---

## 8. Key-SD Unlock Flow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrator
    participant API as /api/storage/vault/unlock
    participant KeyMgr as KeyVaultService
    participant KeySD as KeyDeviceProvider
    participant Crypto as EncryptionProvider
    participant Storage as StorageProvider
    participant Audit as AuditService

    Admin->>API: POST /api/storage/vault/unlock (Bearer Token: ADMIN)
    API->>KeyMgr: unlock_vault()
    KeyMgr->>KeySD: is_present() & validate()
    alt Key-SD Missing or Invalid
        KeyMgr-->>API: Raise VaultLockedException
        API-->>Admin: 423 Locked ("Key-SD missing or invalid")
    else Key-SD Valid
        KeySD->>KeyMgr: Extract raw key material
        KeyMgr->>Crypto: unlock(key_material)
        Crypto->>Crypto: cryptsetup luksOpen / mapper activate
        KeyMgr->>Storage: mount() primary & replica
        KeyMgr->>Audit: Log VAULT_UNLOCKED
        KeyMgr-->>API: {success: true, message: "Vault unlocked"}
        API-->>Admin: 200 OK
    end
```

---

## 9. Key-SD Removal Flow

```mermaid
sequenceDiagram
    autonumber
    actor Sys as Physical Hardware / Udev
    participant Udev as Udev Rule (99-edgestore-keysd.rules)
    participant LockScript as lock_storage.sh
    participant Linux as Linux Kernel
    participant App as EdgeStore Backend

    Sys->>Udev: Key-SD Removed (ACTION=="remove")
    Udev->>LockScript: Exec lock_storage.sh
    LockScript->>Linux: sync (flush filesystem cache buffers)
    LockScript->>Linux: umount /mnt/edgestore/primary
    LockScript->>Linux: umount /mnt/edgestore/replica
    LockScript->>Linux: cryptsetup luksClose edgestore_primary
    LockScript->>Linux: cryptsetup luksClose edgestore_replica
    App->>App: Health watchdog detects unmounted/locked state
    App-->>App: All file read/write routes enforce HTTP 423 Locked
```

---

## 10. File Upload Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Browser
    participant API as POST /api/files/upload
    participant FileSvc as FileService
    participant Storage as StorageProvider (Primary)
    participant RepSvc as ReplicationService
    participant Replica as StorageProvider (Replica)
    participant DB as SQLite DB

    User->>API: Multipart upload (file, filename, Bearer token)
    API->>FileSvc: upload_file(data, filename)
    FileSvc->>FileSvc: Validate filename & compute SHA-256
    FileSvc->>Storage: write(rel_path, data)
    FileSvc->>DB: INSERT StoredFile (replica_status: PENDING)
    FileSvc->>RepSvc: replicate_file(stored_file)
    RepSvc->>Storage: read(rel_path)
    RepSvc->>Replica: write(rel_path, data)
    RepSvc->>Replica: verify(rel_path, expected_sha256)
    alt Replication Succeeded
        RepSvc->>DB: UPDATE StoredFile replica_status = SYNCED
        FileSvc-->>API: {file, primary_write: true, replica_synced: true, is_degraded: false}
    else Replication Failed
        RepSvc->>DB: UPDATE StoredFile replica_status = FAILED
        FileSvc-->>API: {file, primary_write: true, replica_synced: false, is_degraded: true}
    end
    API-->>User: 201 Created (truthful status)
```

---

## 11. File Download Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Browser
    participant API as GET /api/files/{id}/download
    participant FileSvc as FileService
    participant StoreMgr as StorageManager
    participant Primary as Drive A (Primary)
    participant Replica as Drive B (Replica)

    User->>API: Download Request with Bearer Token
    API->>FileSvc: download_file(file_id)
    FileSvc->>StoreMgr: resolve_read_provider(storage_path)
    alt Primary Healthy
        StoreMgr-->>FileSvc: (Primary, "Drive A", is_degraded: false)
        FileSvc->>Primary: read(storage_path)
    else Primary Failed & Replica Healthy
        StoreMgr-->>FileSvc: (Replica, "Drive B", is_degraded: true)
        FileSvc->>Replica: read(storage_path)
    end
    FileSvc->>FileSvc: verify SHA-256 against database record
    alt Checksum Matches
        FileSvc-->>API: Return binary stream + headers
        API-->>User: 200 OK (X-EdgeStore-Degraded-Fallback: true/false)
    else Checksum Mismatch
        FileSvc-->>API: Raise IntegrityVerificationException
        API-->>User: 422 Unprocessable Entity ("Integrity check failed")
    end
```

---

## 12. Replication Flow

```mermaid
graph TD
    Start([File Upload / Triggered Sync]) --> CheckSource{Primary Drive Available?}
    CheckSource -->|No| StateDegraded[State: DEGRADED]
    CheckSource -->|Yes| CheckReplica{Replica Drive Available?}
    CheckReplica -->|No| EnqueuePending[Mark File: FAILED / PENDING Queue]
    CheckReplica -->|Yes| ExecSync[Transfer Binary Buffer / rsync Delta]
    ExecSync --> HashCheck{Target SHA-256 == Source SHA-256?}
    HashCheck -->|Match| StateSynced[Mark File: SYNCED]
    HashCheck -->|Mismatch| StateFailed[Mark File: FAILED - Raise Alert]
```

---

## 13. Failure Recovery Flow (Semi-Automated Rebuild)

```mermaid
sequenceDiagram
    autonumber
    actor Admin as System Administrator
    participant Storage as Storage Subsystem
    participant API as EdgeStore Management API
    participant RepEngine as ReplicationEngine

    Note over Storage: Drive A Hardware Failure Detected
    Storage-->>API: Health Status becomes DEGRADED
    API-->>Admin: Dashboard Alert: Primary Drive Offline (Failover to B Active)
    Admin->>Storage: Physically replace Drive A with new drive
    Admin->>Storage: Run setup_luks.sh on replacement drive
    Admin->>API: POST /api/replication/rebuild
    API->>RepEngine: rebuild(source=Replica, target=Primary)
    RepEngine->>RepEngine: Copy all files + compute & verify SHA-256
    RepEngine-->>API: Rebuild Complete (N files synced, 0 errors)
    API-->>Admin: System Storage Mode Restored to NORMAL
```

---

## 14. Database ER Diagram

```mermaid
erDiagram
    USERS ||--o{ FILES : owns
    USERS ||--o{ AUDIT_EVENTS : triggers

    USERS {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string role
        boolean is_active
        datetime created_at
        datetime last_login_at
    }

    FILES {
        string id PK
        int owner_id FK
        string filename
        bigint file_size
        string sha256_hash
        string storage_path UK
        string content_type
        string replica_status
        datetime created_at
        datetime updated_at
        datetime last_verified_at
    }

    AUDIT_EVENTS {
        int id PK
        datetime timestamp
        string event_type
        int user_id FK
        string username
        string ip_address
        text description
        string severity
    }
```

---

## 15. API Architecture

```mermaid
graph LR
    subgraph Client["API Consumer (Web / CLI)"]
        Req["HTTP Request + Bearer JWT"]
    end

    subgraph FastAPIRouter["FastAPI Routing Pipeline"]
        CORS["CORS Middleware"]
        AuthDep["get_current_user Dependency"]
        RBACDep["require_admin Dependency"]
        VaultDep["require_vault_unlocked Dependency"]
    end

    subgraph RouteHandlers["Endpoint Routers (/api)"]
        AuthRouter["/api/auth (login, logout, me)"]
        FileRouter["/api/files (upload, download, delete, verify)"]
        StorageRouter["/api/storage (status, vault lock/unlock)"]
        RepRouter["/api/replication (status, sync, rebuild)"]
        SysRouter["/api/system (health, telemetry, metrics)"]
        AdminRouter["/api/admin (users, audit-logs)"]
        SimRouter["/api/simulation (drive, key-sd, battery, faults)"]
    end

    Req --> CORS
    CORS --> AuthDep
    AuthDep --> RBACDep
    AuthDep --> VaultDep
    AuthDep --> AuthRouter
    VaultDep --> FileRouter
    AuthDep --> StorageRouter
    AuthDep --> RepRouter
    AuthDep --> SysRouter
    RBACDep --> AdminRouter
    RBACDep --> SimRouter
```

---

## 16. Linux Boot Flow

```mermaid
sequenceDiagram
    autonumber
    participant Kernel as Linux Kernel (RPi OS)
    participant Systemd as systemd Init (PID 1)
    participant Storage as Storage Mappers
    participant Udev as Udev Subsystem
    participant EdgeStore as edgestore-backend.service

    Kernel->>Systemd: System initialization
    Systemd->>Systemd: Mount OS root (microSD)
    Systemd->>Udev: Start systemd-udevd
    alt Key-SD Already Inserted at Boot
        Udev->>Systemd: Trigger edgestore-unlock.service
        Systemd->>Storage: cryptsetup luksOpen & mount /mnt/edgestore/*
    end
    Systemd->>EdgeStore: Start edgestore-backend.service
    EdgeStore->>EdgeStore: Initialize SQLite WAL and bind to port 8000
    EdgeStore-->>Systemd: Service Active (Running)
```

---

## 17. systemd / udev Interaction

```mermaid
graph TD
    KernelBlock["Linux Kernel Block Subsystem"] -->|Hotplug Add/Remove Event| UdevDaemon["systemd-udevd"]
    UdevDaemon -->|Rule: ENV{ID_FS_UUID}=='EDGESTORE-KEY-01'| RuleMatch{"Match Event"}
    RuleMatch -->|ACTION=='add'| StartUnlock["systemctl start edgestore-unlock.service"]
    RuleMatch -->|ACTION=='remove'| StartLock["systemctl start edgestore-lock.service"]
    StartUnlock --> ScriptUnlock["/opt/edgestore/linux/scripts/unlock_storage.sh"]
    StartLock --> ScriptLock["/opt/edgestore/linux/scripts/lock_storage.sh"]
    ScriptUnlock --> MountFilesystems["Mount Ext4 to /mnt/edgestore/primary & replica"]
    ScriptLock --> UnmountFilesystems["Sync & Umount & cryptsetup luksClose"]
```

---

## 18. Simulation-to-Hardware Architecture

```mermaid
graph TD
    subgraph CoreApplication["EdgeStore Core Application Logic"]
        FastAPI_App["FastAPI Routes & Services (Unchanged)"]
        DB_Logic["SQLite Schema & Repositories (Unchanged)"]
        React_UI["React 18 Console UI (Unchanged)"]
    end

    subgraph ConfigLayer["Environment Configuration"]
        EnvSwitch{"ENVIRONMENT_MODE"}
    end

    subgraph SimulationImplementation["Simulation Mode (Laptop Dev)"]
        SimDir["Local Filesystem Folders: ./simulation/primary, ./simulation/replica"]
        SimKey["Local Keyfile: ./simulation/key_sd/vault.key"]
        SimFaults["SimulationDrawer Fault Injection Controls"]
    end

    subgraph RealHardwareImplementation["Raspberry Pi 4 Hardware Mode"]
        LinuxDrives["Physical USB HDDs: /dev/mapper/edgestore_primary, edgestore_replica"]
        LinuxKey["Physical Removable Key-SD with UUID Identification"]
        LinuxSystem["systemd services, udev rules, native cryptsetup LUKS2 & rsync"]
    end

    CoreApplication --> EnvSwitch
    EnvSwitch -->|simulation| SimulationImplementation
    EnvSwitch -->|raspberry_pi| RealHardwareImplementation
```
