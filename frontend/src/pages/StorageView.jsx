import React from "react";
import { HardDrive, Server, Shield, CheckCircle, AlertTriangle, Layers } from "lucide-react";
import { useHardware } from "../context/HardwareContext";
import { StatusBadge } from "../components/common/StatusBadge";
import { ProgressBar } from "../components/common/MetricCard";

export function StorageView() {
  const { health } = useHardware();
  const storage = health?.storage;
  const primary = storage?.primary;
  const replica = storage?.replica;
  const isSimulated = health?.is_simulated ?? true;

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div>
      {/* Storage Mode Banner */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
              <Layers size={18} color="var(--status-info-text)" />
              <span>Storage Subsystem & High-Availability Architecture</span>
            </h3>
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
              EdgeStore implements dual-drive mirroring with independent LUKS2 encryption containers on each block device.
            </p>
          </div>
          <StatusBadge status={storage?.mode} label={`SYSTEM STORAGE: ${storage?.mode}`} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
        {/* Drive A Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <HardDrive size={16} />
              <span>Primary Volume (Drive A)</span>
            </span>
            <StatusBadge status={primary?.state} />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Allocated Usage:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                {formatBytes(primary?.used_bytes)} / {formatBytes(primary?.capacity_bytes)}
              </span>
            </div>
            <ProgressBar percent={primary?.percent_used || 0} status={primary?.state} />
            <div style={{ textAlign: "right", fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>
              {primary?.percent_used || 0}% used ({formatBytes(primary?.free_bytes)} free)
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 12, borderTop: "1px solid var(--border-color)", paddingTop: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Volume Role:</span>
              <span style={{ fontWeight: 600 }}>Active Primary (User R/W)</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Block Target / Mount:</span>
              <span style={{ fontFamily: "var(--font-mono)" }}>{primary?.path || primary?.mount_point}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Mount State:</span>
              <span>{primary?.mounted ? "Mounted (Read/Write)" : "Unmounted / Offline"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Filesystem Type:</span>
              <span style={{ fontFamily: "var(--font-mono)" }}>ext4 (dm-crypt LUKS2)</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Adapter Mode:</span>
              <span>{isSimulated ? "SimulationStorageProvider" : "LinuxStorageProvider"}</span>
            </div>
          </div>
        </div>

        {/* Drive B Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <HardDrive size={16} />
              <span>Replica Volume (Drive B)</span>
            </span>
            <StatusBadge status={replica?.state} />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Allocated Usage:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700 }}>
                {formatBytes(replica?.used_bytes)} / {formatBytes(replica?.capacity_bytes)}
              </span>
            </div>
            <ProgressBar percent={replica?.percent_used || 0} status={replica?.state} />
            <div style={{ textAlign: "right", fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>
              {replica?.percent_used || 0}% used ({formatBytes(replica?.free_bytes)} free)
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 12, borderTop: "1px solid var(--border-color)", paddingTop: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Volume Role:</span>
              <span style={{ fontWeight: 600 }}>Hot Standby & Failover</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Block Target / Mount:</span>
              <span style={{ fontFamily: "var(--font-mono)" }}>{replica?.path || replica?.mount_point}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Mount State:</span>
              <span>{replica?.mounted ? "Mounted (Read/Write)" : "Unmounted / Offline"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Filesystem Type:</span>
              <span style={{ fontFamily: "var(--font-mono)" }}>ext4 (dm-crypt LUKS2)</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Adapter Mode:</span>
              <span>{isSimulated ? "SimulationStorageProvider" : "LinuxStorageProvider"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Storage Architecture Reference */}
      <div className="card">
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.5px" }}>
          LUKS2 Stack & Linux Device Identity Specification
        </h4>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, fontSize: 12 }}>
          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Device Identifier Stability</div>
            <p style={{ color: "var(--text-muted)", lineHeight: 1.6 }}>
              Phase 1 avoids persistent reliance on volatile device nodes like <code>/dev/sda</code> and <code>/dev/sdb</code>.
              The production Linux adapter targets stable PARTUUIDs (<code>/dev/disk/by-partlabel/edgestore-primary</code>)
              and maps into DM devices (<code>/dev/mapper/edgestore_primary</code>).
            </p>
          </div>
          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Safe Locking & Unmounting</div>
            <p style={{ color: "var(--text-muted)", lineHeight: 1.6 }}>
              All unmount operations execute kernel buffer flushes (<code>sync</code>) prior to <code>umount</code> and <code>cryptsetup luksClose</code>.
              This guarantees uncommitted transactions are persisted to physical magnetic platters before power cut or vault lockout.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
