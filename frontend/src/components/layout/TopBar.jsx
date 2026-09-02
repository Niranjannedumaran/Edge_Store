import React from "react";
import { Sun, Moon, Battery, BatteryCharging, ShieldAlert, Cpu, RefreshCw } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import { useHardware } from "../../context/HardwareContext";
import { StatusBadge } from "../common/StatusBadge";

export function TopBar({ currentTab }) {
  const { theme, toggleTheme } = useTheme();
  const { health, refreshHealth, loading } = useHardware();

  const isSimulated = health?.is_simulated ?? true;
  const power = health?.power;
  const sys = health?.system_resources;

  const tabTitles = {
    dashboard: "System Overview & Telemetry",
    files: "Secure File Vault Explorer",
    storage: "Dual-Drive Storage Volumes",
    replication: "Block & File Replication Engine",
    security: "Key-SD & Cryptographic Vault",
    system: "Power Management & Host Diagnostics",
    admin: "Appliance Administration & Audit Trail",
  };

  return (
    <header className="app-topbar">
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-main)" }}>
          {tabTitles[currentTab] || "EdgeStore Console"}
        </h1>
        <span
          className="badge badge-info"
          style={{
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            background: isSimulated ? "rgba(210, 153, 34, 0.15)" : "rgba(35, 134, 54, 0.15)",
            color: isSimulated ? "var(--status-warning-text)" : "var(--status-healthy-text)",
            borderColor: isSimulated ? "var(--status-warning-border)" : "var(--status-healthy-border)",
          }}
        >
          {isSimulated ? "DEVELOPMENT / SIMULATION MODE" : "HARDWARE: RASPBERRY PI 4"}
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        {/* Battery & Power Pill */}
        {power && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              padding: "4px 8px",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "var(--bg-surface-raised)",
              border: "1px solid var(--border-color)",
            }}
          >
            {power.is_charging ? <BatteryCharging size={14} color="var(--status-healthy-text)" /> : <Battery size={14} />}
            <span>{power.battery_percent}%</span>
            <span style={{ fontSize: 10, color: "var(--text-dim)" }}>({power.power_mode})</span>
          </div>
        )}

        {/* CPU & Temp pill */}
        {sys && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              color: "var(--text-muted)",
            }}
          >
            <span>CPU: {sys.cpu_percent}%</span>
            {sys.temperature_celsius && <span>Temp: {sys.temperature_celsius}°C</span>}
          </div>
        )}

        {/* Manual Refresh */}
        <button
          onClick={refreshHealth}
          className="btn btn-secondary btn-sm"
          title="Refresh Telemetry"
          style={{ padding: "5px 8px" }}
        >
          <RefreshCw size={13} className={loading ? "spin" : ""} />
        </button>

        {/* Theme Switcher */}
        <button
          onClick={toggleTheme}
          className="btn btn-secondary btn-sm"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
          style={{ padding: "5px 8px" }}
        >
          {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
        </button>
      </div>
    </header>
  );
}
