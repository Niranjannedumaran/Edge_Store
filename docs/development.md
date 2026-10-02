# EdgeStore Development Workflow & Standards

EdgeStore is structured following clean architectural patterns to ensure complete decoupling between domain business logic, the storage abstraction layer, and the execution adapters (Docker appliance, Simulation, and physical Raspberry Pi).

---

## 1. Directory Structure

```
EdgeStore/
├── backend/
│   ├── app/
│   │   ├── config.py              # Pydantic BaseSettings (Modes: docker, simulation, raspberry_pi)
│   │   ├── main.py                # FastAPI lifecycle, SPA routing fallback, security middleware
│   │   ├── api/                   # Modular API routers (/api/auth, /files, /storage, /clients, etc.)
│   │   │   └── endpoints/         # auth.py, files.py, storage.py, clients.py, simulation.py, admin.py
│   │   ├── core/                  # Security (bcrypt, JWT), structured logging, rate limiter, middleware
│   │   ├── db/                    # SQLAlchemy SQLite engine & Motor async MongoDB connection manager
│   │   │   ├── database.py        # SQLite engine & session dependency
│   │   │   ├── init_db.py         # Schema migrations, seed data, and RBAC matrix setup
│   │   │   └── mongo.py           # Motor async MongoDB client & index initialization
│   │   ├── hal/                   # Hardware Abstraction Layer (HAL)
│   │   │   ├── interfaces.py      # Abstract Base Classes (Storage, Key, Crypto, Power, Monitor)
│   │   │   ├── local_storage.py   # Atomic filesystem I/O provider for Docker / Linux
│   │   │   ├── docker_hal.py      # Docker containerized HAL provider implementation
│   │   │   ├── simulation/        # Laptop simulation provider stack with interactive fault injection
│   │   │   └── linux/             # Production Raspberry Pi hardware provider stack (LUKS2, Key-SD)
│   │   ├── models/                # SQLAlchemy database models (User, Role, Permission, StoredFile, Session)
│   │   ├── schemas/               # Pydantic validation schemas (auth, files, storage, clients)
│   │   └── services/              # Business logic (FileService, ReplicationService, ClientService, Audit)
│   └── tests/                     # Comprehensive pytest test suite (51 tests)
├── frontend/                      # Enterprise React 18 Console (Vite + CSS Variables)
├── docker-compose.yml             # Hardened container deployment (Backend + MongoDB + 4 Volumes)
├── deploy-own.ps1                 # Automated Windows PowerShell deployment launcher
├── deploy-own.bat                 # Windows batch shortcut for automated deployment
├── Dockerfile                     # Unprivileged multi-stage container build (UID 10001)
├── requirements.txt               # Backend dependencies (FastAPI, SQLAlchemy, Motor, PyMongo, Pytest)
├── simulation/                    # Local storage volumes for laptop simulation
└── docs/                          # Comprehensive technical documentation & architectural guides
```

---

## 2. Core Development Rules

1. **Hardware-Ready Abstraction**:
   - Never write direct folder access in router endpoints. Always invoke `hal.primary_storage` and `hal.replica_storage`.
2. **Zero Fake Success**:
   - Never return `replica_synced: true` unless the replication provider completed binary transfer and matched SHA-256 hashes.
3. **Absolute Rule #1 — UI Freeze**:
   - The frontend console (`frontend/src/`) is completely frozen. Zero modifications to UI components, layout, or styles.
4. **Defense-in-Depth**:
   - Never store plain passwords or encryption keys in the database.
   - Sanitize all uploaded filenames against path traversal.
   - Run containers strictly as non-root unprivileged users (`edgestore`, UID 10001) with `no-new-privileges:true` and `cap_drop: ALL`.
5. **Data Resilience**:
   - Every file write is atomic (written to a temporary file and renamed atomically) to prevent partial file corruption.
