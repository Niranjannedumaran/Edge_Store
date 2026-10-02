# EdgeStore — Secure Edge Storage Appliance

![EdgeStore Security](https://img.shields.io/badge/Architecture-Hardware--Ready%20HAL-blue)
![Encryption](https://img.shields.io/badge/Encryption-LUKS2%20512--bit-purple)
![Replication](https://img.shields.io/badge/Replication-Dual--Drive%20Mirror-green)
![Integrity](https://img.shields.io/badge/Integrity-SHA--256-orange)
![Docker](https://img.shields.io/badge/Docker-Production--Hardened-2496ED)
![MongoDB](https://img.shields.io/badge/MongoDB-Async%20Client%20Store-47A248)

**EdgeStore** is an enterprise-grade, secure edge storage appliance featuring dual-drive replication with cryptographic SHA-256 validation, unprivileged containerized security, integrated MongoDB client storage, and a hardened management dashboard.

---

## Deployment Modes

EdgeStore operates in three distinct environments via its universal **Hardware Abstraction Layer (HAL)**:

1. **Docker Appliance Mode (Recommended)**:
   - Hardened container architecture running non-root (`UID 10001`) with dropped Linux capabilities (`cap_drop: ALL`).
   - Real persistent named volumes for Primary (`/data/primary`), Replica (`/data/replica`), SQLite Database (`/data/db`), and MongoDB (`edgestore_mongo_data`).
   - Instant one-click private deployment via `deploy-own.ps1` or `docker compose up -d --build`.
2. **Laptop Simulation Mode**:
   - Executes locally on Windows, macOS, or Linux with authentic atomic file operations.
   - Interactive fault injection testing drive failures, Key-SD token removal, and battery shifts.
3. **Raspberry Pi 4 Hardware Mode**:
   - Production hardware setup with dual USB 3.0 HDDs formatted with LUKS2 (`aes-xts-plain64`, 512-bit), physical Key-SD device authentication, and systemd automation.

---

## Quickstart — One-Line Deployment (Copy & Paste)

Deploy the complete stack (**Web Console + Backend API + MongoDB + Dual Storage**) with one terminal command:

```bash
docker compose up -d --build
```
> 💡 **Windows users:** You can also just double-click [`start.bat`](start.bat) to start, and [`stop.bat`](stop.bat) to stop!

- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Default Login**: `admin` / `AdminEdgeStore2026!`
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Custom Private Deployment (Windows PowerShell)
To set your own custom password, custom port, and auto-generated 256-bit JWT secret:
```powershell
.\deploy-own.ps1
```
*(Or double-click `deploy-own.bat`)*

Check status anytime:
```bash
docker compose ps
```

---

## Default Credentials

| Account | Username | Default Password | Assigned Role | Capabilities |
|---|---|---|---|---|
| **System Administrator** | `admin` | `AdminEdgeStore2026!` | `super_admin` | Full appliance administration (All 35 permissions) |
| **Storage Operator** | `operator` | `OperatorEdgeStore2026!` | `storage_admin` | Drive management, replication, semi-automated rebuilds |
| **Guest / Reviewer** | `guest` | `GuestEdgeStore2026!` | `guest` | Strictly read-only file list & preview (Zero write/delete) |

*(Note: Custom credentials configured via `deploy-own.ps1` or `.env` override these defaults).*

---

## Automated Verification & Testing

Run all **51 automated tests** covering authentication, RBAC, IDOR protection, MongoDB client operations, atomic writes, fault injection, and replication:

```bash
# Windows PowerShell
$env:PYTHONPATH="."
python -m pytest backend/tests/ -v

# Linux / macOS
PYTHONPATH=. python -m pytest backend/tests/ -v
```

Validate frontend production build:
```bash
cd frontend
npm run build
```

---

## Technical Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:
- [Custom Private Deployment Guide](docs/custom-deployment.md)
- [Setup & Quickstart Guide](docs/setup.md)
- [System Architecture & Diagrams](docs/architecture.md)
- [REST API Specification](docs/api.md)
- [Database & MongoDB Architecture](docs/database.md)
- [Security & Defense-in-Depth](docs/security.md)
- [Automated Testing Guide](docs/testing.md)
- [Simulation & Fault Injection](docs/simulation.md)
- [Raspberry Pi Hardware Deployment](docs/raspberry-pi-deployment.md)
- [Storage & Replication State Machine](docs/storage.md)
- [Troubleshooting & Diagnostics](docs/troubleshooting.md)
- [Development Workflow & Standards](docs/development.md)
