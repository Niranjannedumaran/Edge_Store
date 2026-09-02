#!/usr/bin/env bash
# EdgeStore — Production rsync Replication Wrapper
# Runs one-time incremental synchronization or continuous loop.

set -euo pipefail

PRIMARY_MOUNT="${PRIMARY_MOUNT:-/mnt/edgestore/primary}"
REPLICA_MOUNT="${REPLICA_MOUNT:-/mnt/edgestore/replica}"
INTERVAL_SEC="${REPLICATION_INTERVAL_SECONDS:-10}"

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [EdgeStore Replicate] $*"
}

run_sync() {
    if ! mountpoint -q "$PRIMARY_MOUNT" || ! mountpoint -q "$REPLICA_MOUNT"; then
        log "WARNING: One or both volumes are unmounted. Skipping sync cycle."
        return 1
    fi

    log "Executing rsync delta sync with checksum validation..."
    rsync -avz --checksum --inplace --delete \
        --exclude=".gitkeep" \
        --exclude="lost+found" \
        "$PRIMARY_MOUNT/" "$REPLICA_MOUNT/"
    
    sync
    log "Replication cycle completed successfully."
}

if [[ "${1:-}" == "--continuous" ]]; then
    log "Starting continuous replication daemon (interval: ${INTERVAL_SEC}s)..."
    while true; do
        run_sync || true
        sleep "$INTERVAL_SEC"
    done
else
    run_sync
fi
