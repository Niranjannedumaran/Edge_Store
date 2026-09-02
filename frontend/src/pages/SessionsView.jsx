import React, { useState, useEffect } from "react";
import { Laptop, ShieldAlert, RefreshCw, XCircle, CheckCircle2 } from "lucide-react";
import { apiRequest } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/common/StatusBadge";

export function SessionsView() {
  const { hasPermission } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [revokingId, setRevokingId] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);

  const canRevoke = hasPermission("users.revoke_sessions");

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await apiRequest("/admin/sessions");
      setSessions(data);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleRevoke = async (session) => {
    if (!canRevoke || session.is_revoked) return;
    if (!window.confirm(`Revoke session for user '${session.username}'? They will be logged out immediately.`)) return;

    setRevokingId(session.id);
    setStatusMsg(null);
    try {
      await apiRequest(`/admin/sessions/${session.id}/revoke`, { method: "POST" });
      setStatusMsg({ type: "success", text: `Session revoked for ${session.username}` });
      await loadSessions();
    } catch (err) {
      setStatusMsg({ type: "error", text: `Revocation failed: ${err.message}` });
    } finally {
      setRevokingId(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
              <Laptop size={20} color="var(--accent-primary)" />
              Active System Sessions & Token Revocation
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "4px 0 0 0" }}>
              Monitor active authentications across all users and revoke unauthorized or stale sessions.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={loadSessions} disabled={loading}>
            <RefreshCw size={13} style={{ marginRight: 6 }} />
            Refresh
          </button>
        </div>

        {statusMsg && (
          <div
            style={{
              marginTop: 14,
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              fontSize: 13,
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: statusMsg.type === "success" ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
              color: statusMsg.type === "success" ? "var(--status-healthy)" : "var(--status-critical)",
              border: `1px solid ${statusMsg.type === "success" ? "var(--status-healthy)" : "var(--status-critical)"}`
            }}
          >
            <CheckCircle2 size={16} />
            <span>{statusMsg.text}</span>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
            Loading active sessions...
          </div>
        ) : sessions.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
            No sessions found.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Session JTI</th>
                  <th>IP Address</th>
                  <th>Client User-Agent</th>
                  <th>Login Timestamp</th>
                  <th>Last Activity</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Revocation Control</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.username}</td>
                    <td>
                      <code style={{ fontSize: 11 }}>{s.token_jti.slice(0, 12)}...</code>
                    </td>
                    <td>{s.ip_address || "127.0.0.1"}</td>
                    <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {s.user_agent || "Browser Client"}
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {s.created_at ? new Date(s.created_at).toLocaleTimeString() : "-"}
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {s.last_activity_at ? new Date(s.last_activity_at).toLocaleTimeString() : "-"}
                    </td>
                    <td>
                      <StatusBadge status={s.is_revoked ? "FAILED" : "HEALTHY"} />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {s.is_revoked ? (
                        <span style={{ fontSize: 11, color: "var(--text-dim)" }}>Revoked</span>
                      ) : canRevoke ? (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleRevoke(s)}
                          disabled={revokingId === s.id}
                          style={{ padding: "3px 8px", fontSize: 11 }}
                        >
                          <XCircle size={12} style={{ marginRight: 4 }} />
                          {revokingId === s.id ? "Revoking..." : "Revoke"}
                        </button>
                      ) : (
                        <span style={{ fontSize: 11, color: "var(--text-dim)" }}>Read-only</span>
                      )}
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
