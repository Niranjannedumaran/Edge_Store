# EdgeStore — Secure Edge Storage Appliance

![EdgeStore Security](https://img.shields.io/badge/Architecture-Hardware--Ready%20HAL-blue)
![Encryption](https://img.shields.io/badge/Encryption-LUKS2%20512--bit-purple)
![Replication](https://img.shields.io/badge/Replication-Dual--Drive%20Mirror-green)
![Integrity](https://img.shields.io/badge/Integrity-SHA--256-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

**EdgeStore** is an enterprise-grade secure local storage appliance engineered for single-node **Raspberry Pi 4** physical hardware, featuring dual-drive replication, LUKS2 full-disk encryption, removable physical **Key-SD** authentication, and a modern enterprise management console.

During local development without physical hardware, EdgeStore executes on a realistic **Hardware Abstraction Layer (HAL)** with a full-fidelity **Simulation Adapter** that models drive failures, Key-SD removal, and replication states with genuine file operations and SHA-256 validation.

---

## Key Features

1. **Hardware-Ready Abstraction Layer (HAL)**:
   - Unified interfaces: `StorageProvider`, `KeyDeviceProvider`, `EncryptionProvider`, `ReplicationProvider`, `PowerProvider`, `SystemMonitorProvider`.
   - Dual implementations:
     - **Simulation Adapter**: Runs on laptop, performs real file I/O, supports interactive fault injection.
     - **Linux Hardware Adapter**: Production-ready for Raspberry Pi OS with `cryptsetup`, `mount`, `udev`, `systemd`, and `rsync`.
2. **Physical Key-SD Authentication**:
   - Hardware key material stored exclusively on removable Key-SD token.
   - Removing the Key-SD triggers automated filesystem buffer flushing (`sync`), volume unmounting (`umount`), crypt mapper closing (`cryptsetup luksClose`), and vault lockout (`HTTP 423 Locked`).
3. **LUKS2 Full-Disk Storage Encryption**:
   - `aes-xts-plain64` with 512-bit key size and `argon2id` key derivation across both drives.
4. **Dual-Drive Redundancy & Hot Failover**:
   - Primary (Drive A) and Replica (Drive B) mirror all user uploads with post-copy SHA-256 verification.
   - If Drive A fails, read requests automatically fail over to Drive B with degraded state flagging.
5. **Semi-Automated Replica Rebuild**:
   - Avoids dangerous autonomous formatting of unknown drives.
   - Allows administrators to rebuild replacement drives with complete cryptographic verification.
6. **Enterprise Web Console**:
   - High-density, professional React 18 interface with custom CSS design tokens.
   - Dark and Light themes with WCAG AAA accessibility.
   - Interactive **Developer Hardware Simulation Dock** for testing faults (drive failure, key removal, battery level).

---

## Quickstart (Simulation Mode)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm 9+

### 2. Install & Run Backend
```bash
# Clone & install dependencies
python -m pip install -r requirements.txt

# Initialize database & seed admin
python -m backend.app.db.init_db

# Start FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 3. Install & Run Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/` in your browser.

### 4. Default Credentials
| Account | Username | Password | Assigned Role | Capabilities |
|---|---|---|---|---|
| **System Administrator** | `admin` | `AdminEdgeStore2026!` | `super_admin` | Full appliance administration (All 35 permissions) |
| **Storage Operator** | `operator` | `OperatorEdgeStore2026!` | `storage_admin` | Drive management, replication, semi-automated rebuilds |
| **Guest / Reviewer** | `guest` | `GuestEdgeStore2026!` | `guest` | Strictly read-only file list & preview (Zero write/delete) |

---

## Automated Verification

Run all automated pytest suites (unit, integration, security, fault injection):
```bash
python -m pytest backend/tests/ -v
```

Validate frontend production build:
```bash
cd frontend
npm run build
```

---

## Technical Documentation & Architecture Diagrams

Comprehensive documentation is available in the `docs/` directory:
- [Architecture & 18 Mermaid Diagrams](docs/architecture.md)
- [Setup Guide](docs/setup.md)
- [Simulation & Fault Injection](docs/simulation.md)
- [Raspberry Pi Hardware Deployment](docs/raspberry-pi-deployment.md)
- [Storage & Replication State Machine](docs/storage.md)
- [Security & Defense-in-Depth](docs/security.md)
- [REST API Specification](docs/api.md)
- [Database & Metadata Architecture](docs/database.md)
- [Automated Testing Guide](docs/testing.md)
- [Troubleshooting & Diagnostics](docs/troubleshooting.md)
- [Development Workflow](docs/development.md)
