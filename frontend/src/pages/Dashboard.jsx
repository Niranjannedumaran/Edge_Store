import React from "react";
import {
  HardDrive,
  RefreshCw,
  Key,
  ShieldCheck,
  ShieldAlert,
  Cpu,
  Battery,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Unlock,
  Activity,
  ArrowRight
} from "lucide-react";
import { useHardware } from "../context/HardwareContext";
import { useAuth } from "../context/AuthContext";
import { MetricCard, ProgressBar } from "../components/common/MetricCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { DashboardStorageAdmin } from "./DashboardStorageAdmin";
import { DashboardSecurityAdmin } from "./DashboardSecurityAdmin";
import { DashboardFileManager } from "./DashboardFileManager";

export function Dashboard({ onNavigate }) {
  const { user } = useAuth();
  const { health, loading } = useHardware();

  // Role-specific dashboard routing
  if (user?.role === "storage_admin") {
    return <DashboardStorageAdmin onNavigate={onNavigate} />;
  }
  if (user?.role === "security_admin") {
    return <DashboardSecurityAdmin onNavigate={onNavigate} />;
  }
  if (user?.role === "file_manager") {
    return <DashboardFileManager onNavigate={onNavigate} />;
  }

  if (loading && !health) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
        Loading EdgeStore hardware telemetry...
      </div>
    );
  }

  const storage = health?.storage;
  const primary = storage?.primary;
  const replica = storage?.replica;
  const vault = health?.vault;
  const rep = health?.replication;
  const sys = health?.system_resources;
  const power = health?.power;

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div>
      {/* Critical Storage Alert if Degraded or Offline */}
      {storage?.mode !== "NORMAL" && (
        <div
          style={{
            padding: "12px 16px",
            marginBottom: 20,
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--status-warning-border)",
            backgroundColor: "var(--status-warning-bg)",
            color: "var(--status-warning-text)",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <AlertTriangle size={20} />
          <div>
            <strong>Storage Operating in {storage?.mode} Mode. </strong>
            <span>
              {storage?.mode === "DEGRADED"
                ? "One of the mirrored drives is unavailable. High-availability redundancy is impaired; failover routing active."
                : "All storage volumes are currently offline or unmounted. File operations will be blocked."}
            </span>
          </div>
        </div>
      )}

      {/* Top Telemetry Grid */}
      <div className="grid-cards">
        {/* Drive A Card */}
        <MetricCard
          title="Drive A (Primary)"
          icon={HardDrive}
          badgeStatus={primary?.state === "healthy" ? "healthy" : "critical"}
          badgeLabel={primary?.state?.toUpperCase()}
          value={formatBytes(primary?.used_bytes)}
          subtext={`Total Capacity: ${formatBytes(primary?.capacity_bytes)} (${primary?.percent_used || 0}% used)`}
        >
          <ProgressBar percent={primary?.percent_used || 0} status={primary?.state} />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-dim)", marginTop: 4 }}>
            <span>Mount: {primary?.mounted ? "Active (/mnt)" : "Unmounted"}</span>
            <span>{primary?.is_available ? "Online" : "I/O Inactive"}</span>
          </div>
        </MetricCard>

        {/* Drive B Card */}
        <MetricCard
          title="Drive B (Replica)"
          icon={HardDrive}
          badgeStatus={replica?.state === "healthy" ? "healthy" : "critical"}
          badgeLabel={replica?.state?.toUpperCase()}
          value={formatBytes(replica?.used_bytes)}
          subtext={`Total Capacity: ${formatBytes(replica?.capacity_bytes)} (${replica?.percent_used || 0}% used)`}
        >
          <ProgressBar percent={replica?.percent_used || 0} status={replica?.state} />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-dim)", marginTop: 4 }}>
            <span>Sync: {rep?.engine_state?.toUpperCase()}</span>
            <span>{replica?.is_available ? "Ready" : "Offline"}</span>
          </div>
        </MetricCard>

        {/* Key-SD & LUKS Vault Card */}
        <MetricCard
          title="Physical Key-SD & Vault"
          icon={Key}
          badgeStatus={vault?.unlocked ? "healthy" : "critical"}
          badgeLabel={vault?.unlocked ? "VAULT UNLOCKED" : "VAULT LOCKED"}
          value={vault?.key_sd?.present ? "Key-SD Connected" : "Key-SD Missing"}
          subtext={`Cipher: ${vault?.encryption?.cipher || "LUKS2"}`}
        >
          <div style={{ margin: "10px 0", fontSize: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ color: "var(--text-muted)" }}>Token Validation:</span>
              <span style={{ fontWeight: 600 }}>{vault?.key_sd?.valid ? "Valid SHA-256 Token" : "Missing / Invalid"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Hardware Lockout:</span>
              <span>{vault?.unlocked ? "Disarmed" : "Active (423 Locked)"}</span>
            </div>
          </div>
        </MetricCard>

        {/* Replication State Card */}
        <MetricCard
          title="Replication Engine"
          icon={RefreshCw}
          badgeStatus={rep?.engine_state === "synced" ? "healthy" : (rep?.engine_state === "failed" ? "critical" : "warning")}
          badgeLabel={rep?.engine_state?.toUpperCase()}
          value={`${rep?.db_stats?.synced_count || 0} Files Synced`}
          subtext={`Pending Queue: ${rep?.db_stats?.pending_count || 0} | Failed: ${rep?.db_stats?.failed_count || 0}`}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}>
            <button
              onClick={() => onNavigate("replication")}
              className="btn btn-secondary btn-sm"
              style={{ width: "100%" }}
            >
              Open Replication Console
            </button>
          </div>
        </MetricCard>
      </div>

      {/* Dual Drive Replication Flow Visualizer */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <RefreshCw size={16} />
            <span>Dual-Drive High-Availability Replication Pipeline</span>
          </span>
          <StatusBadge status={storage?.mode} label={`STORAGE: ${storage?.mode}`} />
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-around",
            padding: "20px 10px",
            backgroundColor: "var(--bg-surface-raised)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-color)",
          }}
        >
          {/* Drive A Node */}
          <div style={{ textAlign: "center", width: 140 }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: "var(--radius-md)",
                backgroundColor: primary?.is_available ? "var(--status-healthy-bg)" : "var(--status-critical-bg)",
                border: `1px solid ${primary?.is_available ? "var(--status-healthy-border)" : "var(--status-critical-border)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 8px auto",
              }}
            >
              <HardDrive size={24} color={primary?.is_available ? "var(--status-healthy-text)" : "var(--status-critical-text)"} />
            </div>
            <div style={{ fontWeight: 700, fontSize: 13 }}>Drive A (Primary)</div>
            <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{primary?.state}</div>
          </div>

          {/* Sync Connection Arrow */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-muted)" }}>
              {rep?.engine}
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--status-info-text)" }}>
              <span>────────</span>
              <ArrowRight size={18} />
            </div>
            <span className={`badge badge-${rep?.engine_state === "synced" ? "healthy" : "warning"}`}>
              {rep?.engine_state?.toUpperCase()}
            </span>
          </div>

          {/* Drive B Node */}
          <div style={{ textAlign: "center", width: 140 }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: "var(--radius-md)",
                backgroundColor: replica?.is_available ? "var(--status-healthy-bg)" : "var(--status-critical-bg)",
                border: `1px solid ${replica?.is_available ? "var(--status-healthy-border)" : "var(--status-critical-border)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 8px auto",
              }}
            >
              <HardDrive size={24} color={replica?.is_available ? "var(--status-healthy-text)" : "var(--status-critical-text)"} />
            </div>
            <div style={{ fontWeight: 700, fontSize: 13 }}>Drive B (Replica)</div>
            <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{replica?.state}</div>
          </div>
        </div>
      </div>

      {/* System Resources & Battery Telemetry */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Host Diagnostics */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Cpu size={16} />
              <span>Host Telemetry & Resources</span>
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Platform:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{sys?.platform || "Linux ARM64"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>CPU Utilization:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{sys?.cpu_percent}%</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Memory Allocated:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                {formatBytes(sys?.memory?.used_bytes)} / {formatBytes(sys?.memory?.total_bytes)} ({sys?.memory?.percent}%)
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>SoC Temperature:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{sys?.temperature_celsius}°C</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>System Uptime:</span>
              <span style={{ fontFamily: "var(--font-mono)" }}>{Math.floor((sys?.uptime_seconds || 0) / 60)} minutes</span>
            </div>
          </div>
        </div>

        {/* Battery & Power Mode */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Battery size={16} />
              <span>Energy & Battery Policy</span>
            </span>
            <StatusBadge status={power?.power_mode} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Battery Level:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700 }}>{power?.battery_percent}%</span>
            </div>
            <ProgressBar percent={power?.battery_percent || 0} status={power?.power_mode === "critical" ? "critical" : "healthy"} />
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Charging State:</span>
              <span>{power?.is_charging ? "AC Connected (Charging)" : "On Battery Supply"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--text-muted)" }}>Policy Mode:</span>
              <span style={{ fontWeight: 600 }}>{power?.power_mode?.toUpperCase()}</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 4 }}>
              Normal &gt; 50% | Conservation 25-50% | Critical &lt; 10% (configurable thresholds)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
