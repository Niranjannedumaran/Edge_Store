import React, { useState } from "react";
import { RefreshCw, Play, Wrench, CheckCircle, AlertTriangle, ArrowRight, HardDrive } from "lucide-react";
import { apiRequest } from "../api/client";
import { useHardware } from "../context/HardwareContext";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/common/StatusBadge";
import { MetricCard } from "../components/common/MetricCard";

export function ReplicationView() {
  const { health, refreshHealth } = useHardware();
  const { isAdmin } = useAuth();
  const [busy, setBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  const rep = health?.replication;
  const storage = health?.storage;

  const handleSyncRetry = async () => {
    setBusy(true);
    setActionMessage(null);
    try {
      const res = await apiRequest("/replication/sync", { method: "POST" });
      setActionMessage(`Sync Complete: Retried ${res.retried} files (Succeeded: ${res.succeeded}, Failed: ${res.failed})`);
      await refreshHealth();
    } catch (err) {
      alert(`Sync Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleRebuild = async () => {
    if (!window.confirm("Perform Semi-Automated Replica Rebuild? This will synchronize all files from Drive A to Drive B with SHA-256 verification.")) {
      return;
    }
    setBusy(true);
    setActionMessage(null);
    try {
      const res = await apiRequest("/replication/rebuild", { method: "POST" });
      setActionMessage(res.message);
      await refreshHealth();
    } catch (err) {
      alert(`Rebuild Error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {/* Action Notification */}
      {actionMessage && (
        <div
          style={{
            padding: "12px 16px",
            marginBottom: 20,
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--status-info-border)",
            backgroundColor: "var(--status-info-bg)",
            color: "var(--status-info-text)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <CheckCircle size={16} />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid-cards">
        <MetricCard
          title="Replication State Machine"
          icon={RefreshCw}
          badgeStatus={rep?.engine_state === "synced" ? "healthy" : (rep?.engine_state === "failed" ? "critical" : "warning")}
          badgeLabel={rep?.engine_state?.toUpperCase()}
          value={rep?.engine_state?.toUpperCase()}
          subtext={`Engine: ${rep?.engine || "BufferSync"}`}
        />

        <MetricCard
          title="Synchronized Files"
          value={`${rep?.db_stats?.synced_count || 0}`}
          subtext="Cryptographically verified on Drive B"
        />

        <MetricCard
          title="Pending Queue"
          value={`${rep?.db_stats?.pending_count || 0}`}
          badgeStatus={rep?.db_stats?.pending_count > 0 ? "warning" : "healthy"}
          badgeLabel={rep?.db_stats?.pending_count > 0 ? "QUEUEING" : "CLEAR"}
          subtext="Awaiting secondary disk write"
        />

        <MetricCard
          title="Replication Errors"
          value={`${rep?.db_stats?.failed_count || 0}`}
          badgeStatus={rep?.db_stats?.failed_count > 0 ? "critical" : "healthy"}
          badgeLabel={rep?.db_stats?.failed_count > 0 ? "ATTENTION" : "NONE"}
          subtext="Failed attempts / checksum mismatch"
        />
      </div>

      {/* Administrative Rebuild & Retry Actions */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Wrench size={16} />
            <span>Replication Operations & Semi-Automated Recovery</span>
          </span>
        </div>

        <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
          EdgeStore avoids dangerous autonomous formatting of unknown drives. When replacement storage is connected,
          an administrator initiates a <strong>Semi-Automated Replica Rebuild</strong> to copy and verify data from the surviving volume.
        </p>

        <div style={{ display: "flex", gap: 12 }}>
          <button
            disabled={busy || !isAdmin}
            onClick={handleSyncRetry}
            className="btn btn-secondary"
          >
            <Play size={14} />
            <span>Retry Failed & Pending Syncs</span>
          </button>

          <button
            disabled={busy || !isAdmin || storage?.mode === "OFFLINE"}
            onClick={handleRebuild}
            className="btn btn-primary"
          >
            <RefreshCw size={14} className={busy ? "spin" : ""} />
            <span>Initiate Semi-Automated Replica Rebuild</span>
          </button>
        </div>
      </div>

      {/* Failed Files Queue Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <span>Replication Error Queue ({rep?.failed_files?.length || 0})</span>
          </span>
        </div>

        {rep?.failed_files && rep.failed_files.length > 0 ? (
          <div className="table-container" style={{ border: "none" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Relative Storage Path</th>
                  <th>Status</th>
                  <th>Suggested Action</th>
                </tr>
              </thead>
              <tbody>
                {rep.failed_files.map((path, idx) => (
                  <tr key={idx}>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{path}</td>
                    <td>
                      <StatusBadge status="failed" label="SYNC FAILED" />
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Verify target volume mount and click "Retry Failed Syncs"
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            <CheckCircle size={24} color="var(--status-healthy-text)" style={{ margin: "0 auto 8px auto", display: "block" }} />
            All files are currently synchronized and cryptographically intact across Drive A and Drive B.
          </div>
        )}
      </div>
    </div>
  );
}
