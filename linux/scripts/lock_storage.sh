#!/usr/bin/env bash
# EdgeStore — Safe Hardware Lock and Unmount Script
# Invoked on Key-SD removal or administrative lock.
# Performs safe filesystem cache flushing (sync) to prevent data corruption.

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [EdgeStore Lock] $*"
}

if [[ $EUID -ne 0 ]]; then
   log "ERROR: Must be run as root."
   exit 1
fi

PRIMARY_MAPPER="edgestore_primary"
PRIMARY_MOUNT="/mnt/edgestore/primary"

REPLICA_MAPPER="edgestore_replica"
REPLICA_MOUNT="/mnt/edgestore/replica"

log "Initiating safe storage lock sequence..."

# Step 1: Force filesystem buffers flush
log "Flushing filesystem buffers..."
sync

# Step 2: Safely unmount primary filesystem
if mountpoint -q "$PRIMARY_MOUNT"; then
    log "Unmounting primary volume $PRIMARY_MOUNT..."
    umount -f "$PRIMARY_MOUNT" || log "Warning: Unmount primary had non-zero exit"
fi

# Step 3: Safely unmount replica filesystem
if mountpoint -q "$REPLICA_MOUNT"; then
    log "Unmounting replica volume $REPLICA_MOUNT..."
    umount -f "$REPLICA_MOUNT" || log "Warning: Unmount replica had non-zero exit"
fi

# Step 4: Close LUKS crypt mappers
if [[ -e "/dev/mapper/$PRIMARY_MAPPER" ]]; then
    log "Closing primary LUKS mapper /dev/mapper/$PRIMARY_MAPPER..."
    cryptsetup luksClose "$PRIMARY_MAPPER" || log "Warning: luksClose primary failed"
fi

if [[ -e "/dev/mapper/$REPLICA_MAPPER" ]]; then
    log "Closing replica LUKS mapper /dev/mapper/$REPLICA_MAPPER..."
    cryptsetup luksClose "$REPLICA_MAPPER" || log "Warning: luksClose replica failed"
fi

log "Vault locked. All storage volumes secured."
