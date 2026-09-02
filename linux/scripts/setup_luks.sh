#!/usr/bin/env bash
# EdgeStore — Real Hardware LUKS2 Setup Script
# Formats physical block storage devices with LUKS2 encryption and ext4 filesystem.
# WARNING: Destructive operation. Requires explicit authorization.

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [EdgeStore LUKS Setup] $*"
}

if [[ $EUID -ne 0 ]]; then
   log "ERROR: This script must be run as root."
   exit 1
fi

DEVICE="${1:-}"
MAPPER_NAME="${2:-}"
KEY_FILE="${3:-}"

if [[ -z "$DEVICE" || -z "$MAPPER_NAME" || -z "$KEY_FILE" ]]; then
    echo "Usage: $0 <block_device> <mapper_name> <key_file_path>"
    echo "Example: $0 /dev/sda1 edgestore_primary /mnt/edgestore/key_sd/vault.key"
    exit 1
fi

if [[ ! -b "$DEVICE" ]]; then
    log "ERROR: Block device $DEVICE does not exist."
    exit 1
fi

if [[ ! -f "$KEY_FILE" ]]; then
    log "ERROR: Key file $KEY_FILE not found."
    exit 1
fi

log "Preparing to format $DEVICE with LUKS2 (Mapper: $MAPPER_NAME)..."

# Step 1: Format LUKS2 container using strong ciphers
cryptsetup luksFormat \
    --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha256 \
    --pbkdf argon2id \
    --key-file "$KEY_FILE" \
    --batch-mode \
    "$DEVICE"

log "LUKS2 format complete. Opening container to create filesystem..."

# Step 2: Open LUKS container
cryptsetup luksOpen "$DEVICE" "$MAPPER_NAME" --key-file "$KEY_FILE"

# Step 3: Create ext4 filesystem with reserved blocks for root
mkfs.ext4 -m 1 -L "$MAPPER_NAME" "/dev/mapper/$MAPPER_NAME"

log "Filesystem formatted successfully."

# Step 4: Close container
cryptsetup luksClose "$MAPPER_NAME"

log "Setup completed successfully for $DEVICE."
