# EdgeStore Troubleshooting & Diagnostics Guide

This document covers common diagnostic workflows, error codes, and operational recovery steps.

---

## 1. Common HTTP Status Codes

| Status Code | Meaning in EdgeStore | Resolution |
|---|---|---|
| **401 Unauthorized** | Missing or expired JWT token | Re-authenticate at `/api/auth/login` |
| **403 Forbidden** | RBAC permission violation (e.g. standard operator attempting admin action) | Perform action with an account assigned the `admin` role |
| **422 Unprocessable** | SHA-256 integrity verification failed (data corruption or tampering detected) | Check physical disk health and run cross-drive verify |
| **423 Locked** | Storage vault is locked or Key-SD is missing | Insert valid physical Key-SD and trigger unlock via `/api/storage/vault/unlock` |
| **503 Service Unavailable** | Both Drive A and Drive B are offline or unmounted | Inspect USB/SATA cables, check `dmesg`, verify `/mnt/edgestore/*` mountpoints |

---

## 2. Storage & Hardware Troubleshooting

### Symptom: Vault Fails to Unlock
1. Verify Key-SD presence:
```bash
lsblk -o NAME,FSTYPE,UUID,MOUNTPOINT
```
2. Verify Key-SD UUID matches `/etc/edgestore/edgestore.env`:
```bash
blkid | grep EDGESTORE-KEY-01
```
3. Check `vault.key` permissions (must be readable by root or `edgestore` group):
```bash
ls -l /mnt/edgestore/key_sd/vault.key
```

### Symptom: Drive A Failed / Storage Degraded
1. The dashboard will show: `Storage Operating in DEGRADED Mode`.
2. Check disk health via `dmesg | grep -E "sd[a-z]|EXT4|Buffer I/O"`.
3. If drive must be replaced:
   - Unplug failed drive and connect replacement drive.
   - Run `/opt/edgestore/linux/scripts/setup_luks.sh <device> <mapper> <keyfile>`.
   - In the EdgeStore console, navigate to **Replication** and click **Initiate Semi-Automated Replica Rebuild**.
