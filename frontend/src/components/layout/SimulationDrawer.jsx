import React, { useState } from "react";
import { ChevronUp, ChevronDown, Wrench, AlertTriangle, Key, Battery, RefreshCw, HardDrive } from "lucide-react";
import { apiRequest } from "../../api/client";
import { useHardware } from "../../context/HardwareContext";
import { useAuth } from "../../context/AuthContext";

export function SimulationDrawer() {
  const [collapsed, setCollapsed] = useState(true);
  const [busy, setBusy] = useState(false);
  const { health, refreshHealth } = useHardware();
  const { isAdmin } = useAuth();

  if (!isAdmin || health?.is_simulated === false) {
    return null;
  }

  const primary = health?.storage?.primary;
  const replica = health?.storage?.replica;
  const keySd = health?.vault?.key_sd;
  const power = health?.power;
  const rep = health?.replication;

  const handleDriveAction = async (drive, action) => {
    setBusy(true);
    try {
      await apiRequest("/simulation/drive", {
        method: "POST",
        body: { drive, action },
      });
      await refreshHealth();
    } catch (err) {
      alert(`Simulation Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleKeyAction = async (action, valid = true) => {
    setBusy(true);
    try {
      await apiRequest("/simulation/key-sd", {
        method: "POST",
        body: { action, valid },
      });
      await refreshHealth();
    } catch (err) {
      alert(`Simulation Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleBatteryChange = async (level) => {
    setBusy(true);
    try {
      await apiRequest("/simulation/battery", {
        method: "POST",
        body: { level, charging: level > 25 },
      });
      await refreshHealth();
    } catch (err) {
      alert(`Simulation Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleReplicationFault = async (enabled) => {
    setBusy(true);
    try {
      await apiRequest("/simulation/replication-fault", {
        method: "POST",
        body: { simulate_failure: enabled },
      });
      await refreshHealth();
    } catch (err) {
      alert(`Simulation Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`simulation-dock ${collapsed ? "collapsed" : ""}`}>
      <div className="dock-header" onClick={() => setCollapsed(!collapsed)}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Wrench size={15} />
          <span>DEVELOPER HARDWARE FAULT INJECTION DOCK</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 10, opacity: 0.8 }}>{collapsed ? "Expand Controls" : "Collapse"}</span>
          {collapsed ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {!collapsed && (
        <div className="dock-body">
          {/* Drive A Simulation */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <span style={{ fontWeight: 600 }}>Drive A (Primary): </span>
              <span className={`badge badge-${primary?.state === "healthy" ? "healthy" : "critical"}`}>
                {primary?.state?.toUpperCase()}
              </span>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                disabled={busy || primary?.state === "failed"}
                onClick={() => handleDriveAction("primary", "fail")}
                className="btn btn-danger btn-sm"
              >
                Fail Drive A
              </button>
              <button
                disabled={busy || primary?.state === "healthy"}
                onClick={() => handleDriveAction("primary", "recover")}
                className="btn btn-secondary btn-sm"
              >
                Recover
              </button>
            </div>
          </div>

          {/* Drive B Simulation */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <span style={{ fontWeight: 600 }}>Drive B (Replica): </span>
              <span className={`badge badge-${replica?.state === "healthy" ? "healthy" : "critical"}`}>
                {replica?.state?.toUpperCase()}
              </span>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                disabled={busy || replica?.state === "failed"}
                onClick={() => handleDriveAction("replica", "fail")}
                className="btn btn-danger btn-sm"
              >
                Fail Drive B
              </button>
              <button
                disabled={busy || replica?.state === "healthy"}
                onClick={() => handleDriveAction("replica", "recover")}
                className="btn btn-secondary btn-sm"
              >
                Recover
              </button>
            </div>
          </div>

          {/* Key-SD Simulation */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: "1px solid var(--border-color)", paddingTop: 8 }}>
            <div>
              <span style={{ fontWeight: 600 }}>Physical Key-SD: </span>
              <span className={`badge badge-${keySd?.present ? "healthy" : "critical"}`}>
                {keySd?.present ? "INSERTED" : "REMOVED"}
              </span>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                disabled={busy || !keySd?.present}
                onClick={() => handleKeyAction("remove")}
                className="btn btn-danger btn-sm"
              >
                Remove Key-SD
              </button>
              <button
                disabled={busy || keySd?.present}
                onClick={() => handleKeyAction("insert", true)}
                className="btn btn-secondary btn-sm"
              >
                Insert Key-SD
              </button>
            </div>
          </div>

          {/* Battery Telemetry Slider */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: "1px solid var(--border-color)", paddingTop: 8 }}>
            <span style={{ fontWeight: 600 }}>Simulate Battery Level:</span>
            <div style={{ display: "flex", gap: 4 }}>
              {[100, 50, 20, 5].map((lvl) => (
                <button
                  key={lvl}
                  disabled={busy}
                  onClick={() => handleBatteryChange(lvl)}
                  className={`btn btn-sm ${power?.battery_percent === lvl ? "btn-primary" : "btn-secondary"}`}
                >
                  {lvl}%
                </button>
              ))}
            </div>
          </div>

          {/* Replication Fault Toggle */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: "1px solid var(--border-color)", paddingTop: 8 }}>
            <span style={{ fontWeight: 600 }}>Replication Engine Fault:</span>
            <button
              disabled={busy}
              onClick={() => handleReplicationFault(rep?.engine_state !== "failed")}
              className={`btn btn-sm ${rep?.engine_state === "failed" ? "btn-danger" : "btn-secondary"}`}
            >
              {rep?.engine_state === "failed" ? "Injecting Faults (Active)" : "Simulate Fault"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
