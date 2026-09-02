# EdgeStore Development Workflow & Standards

EdgeStore is structured following clean architectural patterns to ensure complete decoupling between domain business logic, the storage abstraction layer, and the hardware execution adapters.

---

## 1. Directory Structure

```
EdgeStore/
├── backend/
│   ├── app/
│   │   ├── config.py              # Pydantic BaseSettings (Modes: simulation vs raspberry_pi)
│   │   ├── main.py                # FastAPI lifecycle and error handlers
│   │   ├── api/                   # Modular API routers (/api/auth, /files, /storage, /replication, etc.)
│   │   ├── core/                  # Security (bcrypt, JWT), structured logging, exceptions
│   │   ├── db/                    # SQLAlchemy engine, session generator, init_db seed
│   │   ├── hal/                   # Hardware Abstraction Layer (HAL)
│   │   │   ├── interfaces.py      # Abstract Base Classes (Storage, Key, Crypto, Power, Monitor)
│   │   │   ├── simulation/        # Authentic laptop simulation provider stack
│   │   │   └── linux/             # Production Raspberry Pi hardware provider stack
│   │   ├── models/                # SQLAlchemy database models (User, StoredFile, AuditEvent)
│   │   ├── schemas/               # Pydantic validation schemas
│   │   └── services/              # Business logic (FileService, ReplicationService, KeyVaultService)
│   └── tests/                     # Comprehensive pytest test suite
├── frontend/                      # Enterprise React 18 Console (Vite + CSS Variables)
│   ├── src/
│   │   ├── index.css              # Custom Enterprise Design System (Tokens, Dark & Light modes)
│   │   ├── context/               # AuthContext, ThemeContext, HardwareContext
│   │   ├── components/            # StatusBadge, MetricCard, SimulationDrawer, Sidebar, TopBar
│   │   └── pages/                 # Dashboard, FileManager, StorageView, ReplicationView, SecurityView, AdminView
├── linux/                         # Raspberry Pi automation assets (systemd, udev, shell scripts)
├── simulation/                    # Local storage volumes for laptop simulation
└── docs/                          # Comprehensive technical documentation & 18 Mermaid diagrams
```

---

## 2. Core Development Rules

1. **Hardware-Ready Abstraction**:
   - Never write direct folder access in router endpoints. Call `hal.primary_storage` and `hal.replica_storage`.
2. **Zero Fake Success**:
   - Never return `replica_synced: true` unless the replication provider completed binary transfer and matched SHA-256 hashes.
3. **Defense-in-Depth**:
   - Never store plain passwords or encryption keys in SQLite.
   - Sanitize all uploaded filenames against path traversal.
4. **Theme Parity**:
   - Every UI component must render seamlessly in both Dark theme and Light theme with WCAG compliant contrast.
