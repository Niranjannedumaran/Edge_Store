import React from "react";
import { HardDrive, RefreshCw, AlertTriangle, CheckCircle2, ShieldAlert, ArrowRight, ShieldCheck } from "lucide-react";
import { useHardware } from "../context/HardwareContext";
import { MetricCard, ProgressBar } from "../components/common/MetricCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { apiRequest } from "../api/client";

export function DashboardStorageAdmin({ onNavigate }) {
  const { health } = useHardware();

  const storage = health?.storage;
  const primary = storage?.primary;
  const replica = storage?.replica;
  const rep = health?.replication;
  const vault = health?.vault;

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleTriggerSync = async () => {
    try {
      await apiRequest("/replication/sync", { method: "POST" });
      alert("Replication reconciliation queued.");
    } catch (err) {
      alert("Failed to queue sync: " + err.message);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Storage Mode Banner */}
      <div
        className="card"
        style={{
          borderLeft: `4px solid ${
            storage?.mode === "NORMAL" ? "var(--status-healthy)" : "var(--status-warning)"
          }`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Storage Subsystem Operational Status
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4, display: "flex", alignItems: "center", gap: 10 }}>
            <span>Storage Mode: {storage?.mode || "UNKNOWN"}</span>
            <StatusBadge status={storage?.mode === "NORMAL" ? "HEALTHY" : "DEGRADED"} />
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("storage")}>
            Storage Volumes <ArrowRight size={13} style={{ marginLeft: 4 }} />
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => onNavigate("replication")}>
            Replication Console <ArrowRight size={13} style={{ marginLeft: 4 }} />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid-4">
        <MetricCard
          title="Drive A (Primary)"
          value={primary?.mounted ? "MOUNTED" : "UNMOUNTED"}
          subValue={primary?.filesystem || "ext4"}
          status={primary?.healthy ? "HEALTHY" : "FAILED"}
          icon={HardDrive}
        />
        <MetricCard
          title="Drive B (Replica)"
          value={replica?.mounted ? "MOUNTED" : "UNMOUNTED"}
          subValue={replica?.filesystem || "ext4"}
          status={replica?.healthy ? "HEALTHY" : "FAILED"}
          icon={HardDrive}
        />
        <MetricCard
          title="Replication Engine"
          value={rep?.engine_status || "IDLE"}
          subValue={`Queue: ${rep?.pending_files_count || 0} files`}
          status={rep?.engine_status === "RUNNING" ? "WARNING" : "HEALTHY"}
          icon={RefreshCw}
        />
        <MetricCard
          title="LUKS Vault State"
          value={vault?.is_unlocked ? "UNLOCKED" : "LOCKED"}
          subValue={vault?.key_sd_present ? "Key-SD Token Present" : "Key-SD Missing"}
          status={vault?.is_unlocked ? "HEALTHY" : "CRITICAL"}
          icon={vault?.is_unlocked ? ShieldCheck : ShieldAlert}
        />
      </div>

      {/* Drive Capacity Gauges */}
      <div className="grid-2">
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <HardDrive size={16} color="var(--accent-primary)" />
            Drive A (Primary) Allocation
          </h3>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
            <span>Used: {formatBytes(primary?.used_bytes)}</span>
            <span style={{ color: "var(--text-muted)" }}>Total: {formatBytes(primary?.total_bytes)}</span>
          </div>
          <ProgressBar
            value={primary?.used_bytes || 0}
            max={primary?.total_bytes || 1}
            status={primary?.used_percent > 85 ? "CRITICAL" : "HEALTHY"}
          />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
            <span>Mount: {primary?.mount_point || "/mnt/edgestore/primary"}</span>
            <span>Free: {formatBytes(primary?.free_bytes)}</span>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <HardDrive size={16} color="var(--accent-primary)" />
            Drive B (Replica) Allocation
          </h3>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
            <span>Used: {formatBytes(replica?.used_bytes)}</span>
            <span style={{ color: "var(--text-muted)" }}>Total: {formatBytes(replica?.total_bytes)}</span>
          </div>
          <ProgressBar
            value={replica?.used_bytes || 0}
            max={replica?.total_bytes || 1}
            status={replica?.used_percent > 85 ? "CRITICAL" : "HEALTHY"}
          />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
            <span>Mount: {replica?.mount_point || "/mnt/edgestore/replica"}</span>
            <span>Free: {formatBytes(replica?.free_bytes)}</span>
          </div>
        </div>
      </div>

      {/* Replication Health & Actions */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
            <RefreshCw size={16} color="var(--accent-primary)" />
            Replication Synchronization Pipeline
          </h3>
          <button className="btn btn-secondary btn-sm" onClick={handleTriggerSync}>
            <RefreshCw size={12} style={{ marginRight: 6 }} /> Retry Pending Sync
          </button>
        </div>
        <div style={{ display: "flex", gap: 24, fontSize: 13 }}>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Pending Transfers: </span>
            <strong style={{ color: rep?.pending_files_count > 0 ? "var(--status-warning)" : "var(--text-main)" }}>
              {rep?.pending_files_count || 0} files
            </strong>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Failed Transfers: </span>
            <strong style={{ color: rep?.failed_files_count > 0 ? "var(--status-critical)" : "var(--text-main)" }}>
              {rep?.failed_files_count || 0} files
            </strong>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Last Verification: </span>
            <span>{rep?.last_sync_timestamp ? new Date(rep.last_sync_timestamp).toLocaleTimeString() : "Pending"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
