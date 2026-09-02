import React from "react";
import { Activity, Battery, BatteryCharging, Cpu, HardDrive, Terminal, Zap } from "lucide-react";
import { useHardware } from "../context/HardwareContext";
import { StatusBadge } from "../components/common/StatusBadge";
import { MetricCard, ProgressBar } from "../components/common/MetricCard";

export function SystemView() {
  const { health } = useHardware();
  const sys = health?.system_resources;
  const power = health?.power;

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div>
      <div className="grid-cards">
        {/* Battery Card */}
        <MetricCard
          title="Battery Telemetry"
          icon={Battery}
          badgeStatus={power?.power_mode === "critical" ? "critical" : (power?.power_mode === "conservation" ? "warning" : "healthy")}
          badgeLabel={power?.power_mode?.toUpperCase()}
          value={`${power?.battery_percent || 0}%`}
          subtext={power?.is_charging ? "AC Connected (Charging)" : "Operating on Battery"}
        >
          <ProgressBar percent={power?.battery_percent || 0} status={power?.power_mode === "critical" ? "critical" : "healthy"} />
        </MetricCard>

        {/* CPU Card */}
        <MetricCard
          title="CPU Utilization"
          icon={Cpu}
          value={`${sys?.cpu_percent || 0}%`}
          subtext={`Temperature: ${sys?.temperature_celsius || "N/A"}°C`}
        >
          <ProgressBar percent={sys?.cpu_percent || 0} status={sys?.cpu_percent > 85 ? "critical" : "healthy"} />
        </MetricCard>

        {/* RAM Card */}
        <MetricCard
          title="Memory Consumption"
          icon={Activity}
          value={`${sys?.memory?.percent || 0}%`}
          subtext={`${formatBytes(sys?.memory?.used_bytes)} / ${formatBytes(sys?.memory?.total_bytes)}`}
        >
          <ProgressBar percent={sys?.memory?.percent || 0} status={sys?.memory?.percent > 85 ? "critical" : "healthy"} />
        </MetricCard>
      </div>

      {/* Energy Policy Specification */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Zap size={16} />
            <span>Battery-Aware Policy & Thresholds</span>
          </span>
          <StatusBadge status={power?.power_mode} />
        </div>

        <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
          EdgeStore implements configurable engineering policy thresholds to protect disk integrity and prioritize essential services during brownout or battery operation.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-healthy-text)", marginBottom: 4 }}>
              NORMAL MODE (&gt; 50%)
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Full performance. Background replication daemon runs continuously, on-demand checksum audits permitted, all user services active.
            </div>
          </div>

          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-warning-text)", marginBottom: 4 }}>
              CONSERVATION MODE (25% - 50%)
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Power saving active. Background heavy maintenance and rebuilds paused; urgent writes and reads permitted.
            </div>
          </div>

          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-critical-text)", marginBottom: 4 }}>
              CRITICAL MODE (&lt; 10%)
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Emergency protection. Writes throttled or paused; initiates graceful buffer sync to prevent filesystem journal corruption.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
