import React, { useState, useEffect } from "react";
import { ShieldCheck, ShieldAlert, Users, Laptop, Key, AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";
import { useHardware } from "../context/HardwareContext";
import { MetricCard } from "../components/common/MetricCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { apiRequest } from "../api/client";

export function DashboardSecurityAdmin({ onNavigate }) {
  const { health } = useHardware();
  const [usersCount, setUsersCount] = useState(0);
  const [sessionsCount, setSessionsCount] = useState(0);
  const [recentAudits, setRecentAudits] = useState([]);
  const [loading, setLoading] = useState(true);

  const vault = health?.vault;

  const loadSecurityStats = async () => {
    try {
      const [users, sessions, audits] = await Promise.all([
        apiRequest("/admin/users").catch(() => []),
        apiRequest("/admin/sessions").catch(() => []),
        apiRequest("/admin/audit-logs?limit=8").catch(() => [])
      ]);
      setUsersCount(users.length);
      setSessionsCount(sessions.filter((s) => !s.is_revoked).length);
      setRecentAudits(audits);
    } catch (err) {
      console.error("Failed to fetch security admin stats:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSecurityStats();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Security Perimeter Header */}
      <div
        className="card"
        style={{
          borderLeft: `4px solid ${
            vault?.is_unlocked ? "var(--status-healthy)" : "var(--status-critical)"
          }`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Security Perimeter & Defense-in-Depth Status
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4, display: "flex", alignItems: "center", gap: 10 }}>
            <span>Vault Status: {vault?.is_unlocked ? "UNLOCKED & OPERATIONAL" : "LOCKED"}</span>
            <StatusBadge status={vault?.is_unlocked ? "HEALTHY" : "CRITICAL"} />
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("roles")}>
            Roles & Matrix <ArrowRight size={13} style={{ marginLeft: 4 }} />
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => onNavigate("sessions")}>
            Active Sessions <ArrowRight size={13} style={{ marginLeft: 4 }} />
          </button>
        </div>
      </div>

      {/* Security Cards Row */}
      <div className="grid-4">
        <MetricCard
          title="Physical Key-SD Token"
          value={vault?.key_sd_present ? "PRESENT" : "MISSING"}
          subValue={vault?.key_sd_device || "UUID Verified"}
          status={vault?.key_sd_present ? "HEALTHY" : "CRITICAL"}
          icon={Key}
        />
        <MetricCard
          title="LUKS2 Encryption"
          value={vault?.luks_mode?.toUpperCase() || "AES-XTS-512"}
          subValue={vault?.is_unlocked ? "dm-crypt Activated" : "Containers Closed"}
          status={vault?.is_unlocked ? "HEALTHY" : "CRITICAL"}
          icon={vault?.is_unlocked ? ShieldCheck : ShieldAlert}
        />
        <MetricCard
          title="Active User Sessions"
          value={sessionsCount}
          subValue="Valid JWT Bearer Tokens"
          status={sessionsCount > 0 ? "HEALTHY" : "WARNING"}
          icon={Laptop}
        />
        <MetricCard
          title="Provisioned Accounts"
          value={usersCount}
          subValue="RBAC Authorized Identities"
          status="HEALTHY"
          icon={Users}
        />
      </div>

      {/* Security Audit Trail */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
            <ShieldAlert size={16} color="var(--accent-primary)" />
            Recent Security & Authentication Events
          </h3>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("admin")}>
            Full Audit Log <ArrowRight size={13} style={{ marginLeft: 4 }} />
          </button>
        </div>
        {recentAudits.length === 0 ? (
          <div style={{ padding: 30, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            No security audit records.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Actor</th>
                  <th>Description</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {recentAudits.map((a) => (
                  <tr key={a.id}>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "-"}
                    </td>
                    <td>
                      <code style={{ fontSize: 11 }}>{a.event_type}</code>
                    </td>
                    <td style={{ fontWeight: 600 }}>{a.username || "System"}</td>
                    <td style={{ maxWidth: 360, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {a.description}
                    </td>
                    <td>
                      <span className={`badge ${a.severity === "CRITICAL" || a.severity === "WARNING" ? "badge-warning" : "badge-info"}`}>
                        {a.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
