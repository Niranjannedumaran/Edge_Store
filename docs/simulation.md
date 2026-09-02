# Hardware Simulation & Fault Injection Guide

EdgeStore Phase 1 implements a **Hardware-Ready Abstraction**. When developing on a laptop where physical Raspberry Pi boards, LUKS volumes, Key-SD readers, and external HDDs are absent, EdgeStore operates through the **Simulation Adapter**.

---

## 1. How the Simulation Mode Works

The application layer does NOT hardcode mock logic or superficial strings. Instead, it interacts exclusively with the abstract `Hardware Abstraction Layer (HAL)`:

```
FastAPI / Services
       ↓
HAL Interfaces (StorageProvider, KeyDeviceProvider, EncryptionProvider, ...)
       ↓
Simulation Providers (Authentic file I/O on ./simulation/ folders)
```

### Key Behaviors in Simulation Mode:
- **True File I/O**: Files are written to `./simulation/primary/` and verified with genuine SHA-256 computation.
- **Genuine Replication**: Replication writes actual mirrored files into `./simulation/replica/`, followed by binary read-back and hash comparison.
- **State Machine Fidelity**: Drives, keys, and volumes maintain true software state machines (`HEALTHY`, `DEGRADED`, `FAILED`, `DISCONNECTED`, `UNMOUNTED`, `LOCKED`, `UNLOCKED`).
- **Failover Routing**: When Drive A fails, the read router dynamically reads the surviving replica copy from Drive B and flags the response with `X-EdgeStore-Degraded-Fallback: true`.
- **Physical Key Emulation**: Key-SD removal sets the physical key token state to `REMOVED`. Triggering a vault lock unmounts volumes and enforces HTTP `423 Locked` on all file upload and download endpoints.

---

## 2. Interactive Developer Hardware Dock

In the React UI, administrators have access to the collapsible **DEVELOPER HARDWARE FAULT INJECTION DOCK** at the bottom right.

### Available Fault Controls:
1. **Drive A (Primary) Controls**:
   - `Fail Drive A`: Sets Drive A state to `FAILED`. Subsequent writes raise `StorageUnavailableException`; reads fail over to Drive B.
   - `Recover`: Re-enables Drive A.
2. **Drive B (Replica) Controls**:
   - `Fail Drive B`: Sets Drive B state to `FAILED`. Storage operational mode becomes `DEGRADED`; files cannot replicate and enter the `FAILED` replication queue.
   - `Recover`: Re-enables Drive B.
3. **Key-SD Controls**:
   - `Remove Key-SD`: Emulates physical removal of the Key-SD hardware token.
   - `Insert Key-SD`: Emulates physical insertion of the Key-SD hardware token.
4. **Battery Telemetry Controls**:
   - Buttons: `100%`, `50%`, `20%`, `5%`.
   - Adjusts battery percentage to observe policy mode shifts between `NORMAL`, `CONSERVATION`, and `CRITICAL`.
5. **Replication Fault Simulation**:
   - `Simulate Fault`: Injects synthetic hash mismatches or network/bus transfer failures during replication.

---

## 3. Automated Simulation Tests

Run the dedicated test suite validating fault injection and failover:
```bash
python -m pytest backend/tests/test_fault_injection.py -v
```
All state transitions are proven with automated assertions.
