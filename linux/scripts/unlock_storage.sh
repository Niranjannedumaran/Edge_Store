#!/usr/bin/env bash
# EdgeStore — Safe Hardware Unlock and Mount Script
# Invoked on Key-SD insertion or system startup.

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [EdgeStore Unlock] $*"
}

if [[ $EUID -ne 0 ]]; then
   log "ERROR: Must be run as root."
   exit 1
fi

KEY_SD_UUID="${KEY_SD_UUID:-EDGESTORE-KEY-01}"
KEY_MOUNT="/mnt/edgestore/key_sd"
KEY_FILE="$KEY_MOUNT/vault.key"

PRIMARY_DEV="${PRIMARY_DEV:-/dev/disk/by-partlabel/edgestore-primary}"
PRIMARY_MAPPER="edgestore_primary"
PRIMARY_MOUNT="/mnt/edgestore/primary"

REPLICA_DEV="${REPLICA_DEV:-/dev/disk/by-partlabel/edgestore-replica}"
REPLICA_MAPPER="edgestore_replica"
REPLICA_MOUNT="/mnt/edgestore/replica"

log "Checking for physical Key-SD device (UUID: $KEY_SD_UUID)..."

if [[ ! -e "/dev/disk/by-uuid/$KEY_SD_UUID" ]]; then
    log "ERROR: Key-SD hardware not detected. Aborting unlock."
    exit 2
fi

# Mount Key-SD read-only
mkdir -p "$KEY_MOUNT"
if ! mountpoint -q "$KEY_MOUNT"; then
    mount -o ro,noexec,nosuid,nodev "/dev/disk/by-uuid/$KEY_SD_UUID" "$KEY_MOUNT"
fi

if [[ ! -f "$KEY_FILE" ]]; then
    log "ERROR: Cryptographic key file missing on Key-SD."
    umount "$KEY_MOUNT" || true
    exit 3
fi

log "Key-SD verified. Unlocking LUKS2 volumes..."

# Unlock Primary Volume
if [[ ! -e "/dev/mapper/$PRIMARY_MAPPER" ]]; then
    if [[ -b "$PRIMARY_DEV" ]]; then
        cryptsetup luksOpen "$PRIMARY_DEV" "$PRIMARY_MAPPER" --key-file "$KEY_FILE"
        log "Primary LUKS volume unlocked."
    else
        log "WARNING: Primary drive device $PRIMARY_DEV not found."
    fi
fi

# Unlock Replica Volume
if [[ ! -e "/dev/mapper/$REPLICA_MAPPER" ]]; then
    if [[ -b "$REPLICA_DEV" ]]; then
        cryptsetup luksOpen "$REPLICA_DEV" "$REPLICA_MAPPER" --key-file "$KEY_FILE"
        log "Replica LUKS volume unlocked."
    else
        log "WARNING: Replica drive device $REPLICA_DEV not found."
    fi
fi

# Immediately unmount Key-SD to reduce physical exposure window
umount "$KEY_MOUNT" || true

# Mount filesystems
mkdir -p "$PRIMARY_MOUNT" "$REPLICA_MOUNT"

if [[ -e "/dev/mapper/$PRIMARY_MAPPER" ]] && ! mountpoint -q "$PRIMARY_MOUNT"; then
    mount -o noatime,commit=60 "/dev/mapper/$PRIMARY_MAPPER" "$PRIMARY_MOUNT"
    log "Mounted Primary volume to $PRIMARY_MOUNT."
fi

if [[ -e "/dev/mapper/$REPLICA_MAPPER" ]] && ! mountpoint -q "$REPLICA_MOUNT"; then
    mount -o noatime,commit=60 "/dev/mapper/$REPLICA_MAPPER" "$REPLICA_MOUNT"
    log "Mounted Replica volume to $REPLICA_MOUNT."
fi

log "Storage unlock and mount workflow completed successfully."
