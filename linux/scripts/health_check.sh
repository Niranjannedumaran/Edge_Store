#!/usr/bin/env bash
# EdgeStore — Hardware Health Watchdog Script
# Periodically monitors drive connectivity, temperature, and service status.

set -euo pipefail

log() {
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [EdgeStore HealthCheck] $*"
}

check_health() {
    local status="HEALTHY"

    # Check primary mount
    if ! mountpoint -q "/mnt/edgestore/primary"; then
        log "WARNING: Primary volume is NOT mounted"
        status="DEGRADED"
    fi

    # Check replica mount
    if ! mountpoint -q "/mnt/edgestore/replica"; then
        log "WARNING: Replica volume is NOT mounted"
        status="DEGRADED"
    fi

    # Check temperature if vcgencmd exists
    if command -v vcgencmd >/dev/null 2>&1; then
        temp=$(vcgencmd measure_temp)
        log "SoC Thermal reading: $temp"
    fi

    # Check backend HTTP ping
    if command -v curl >/dev/null 2>&1; then
        if ! curl -s -f http://127.0.0.1:8000/health >/dev/null; then
            log "ERROR: EdgeStore backend HTTP API is unresponsive"
            status="CRITICAL"
        fi
    fi

    log "Health check evaluated status: $status"
}

if [[ "${1:-}" == "--daemon" ]]; then
    log "Starting health check watchdog daemon..."
    while true; do
        check_health || true
        sleep 30
    done
else
    check_health
fi
