# EdgeStore Storage & Replication Subsystem

This document details the storage architecture, failover mechanics, and replication state machine in EdgeStore Phase 1.

---

## 1. Volume Roles

| Role | Device Identifier | Mountpoint | Purpose |
|---|---|---|---|
| **Drive A (Primary)** | `/dev/mapper/edgestore_primary` | `/mnt/edgestore/primary` | Active user storage for reads and writes |
| **Drive B (Replica)** | `/dev/mapper/edgestore_replica` | `/mnt/edgestore/replica` | Redundant hot-standby copy for high-availability |

---

## 2. Storage Operational Modes

- **NORMAL**: Both Drive A and Drive B are connected, mounted, and healthy. New uploads are mirrored immediately.
- **DEGRADED**: One drive has failed or is unmounted. File reads dynamically fail over to the surviving drive. Writes to surviving drive succeed, but replication enters `FAILED` / `PENDING` queue.
- **OFFLINE**: Both drives are unmounted or failed. All file operations return HTTP `503 Service Unavailable`.

---

## 3. Replication State Machine

```
   [ UPLOAD ]
       │
       ▼
   (PENDING) ───[SYNC IN PROGRESS]───► (RUNNING)
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
              [SHA-256 Verified]                   [Write / Hash Mismatch]
                        │                                   │
                        ▼                                   ▼
                    (SYNCED)                             (FAILED)
                        │                                   │
                        └─────────► (DEGRADED) ◄────────────┘
                                         │
                         [ADMIN INITIATES REBUILD]
                                         │
                                         ▼
                                   (RECOVERING)
                                         │
                                [ALL FILES SYNCED]
                                         │
                                         ▼
                                     (SYNCED)
```

### Semi-Automated Replica Rebuild
EdgeStore avoids dangerous autonomous formatting of unknown replacement drives. When an administrator installs a replacement drive and provisions it with `setup_luks.sh`, they invoke:
```bash
POST /api/replication/rebuild
```
The replication engine synchronizes all files from the healthy surviving drive to the target drive, validating SHA-256 for each item and restoring state to `SYNCED`.
