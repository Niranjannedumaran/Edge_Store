import React, { useEffect, useState } from "react";
import { User, Shield, Key, Clock, Laptop, CheckCircle2, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../api/client";
import { StatusBadge } from "../components/common/StatusBadge";

export function ProfileView() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const data = await apiRequest("/auth/my-sessions");
        setSessions(data);
      } catch (err) {
        console.error("Failed to load personal sessions:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSessions();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "var(--surface-sunken)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--accent-primary)",
              border: "2px solid var(--border-subtle)"
            }}
          >
            <User size={28} />
          </div>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
              {user?.display_name || user?.username}
            </h2>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4 }}>
              <span style={{ color: "var(--text-muted)", fontSize: 13 }}>@{user?.username}</span>
              <span className="badge badge-info" style={{ textTransform: "uppercase", fontSize: 11 }}>
                {user?.role_name || user?.role}
              </span>
              <StatusBadge status={user?.is_active ? "HEALTHY" : "CRITICAL"} />
              {user?.is_expired && (
                <span className="badge badge-danger">EXPIRED</span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Account Details */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <Shield size={16} color="var(--accent-primary)" />
            Account Security Details
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-muted)" }}>Email Address</span>
              <span style={{ fontWeight: 500 }}>{user?.email || "Not specified"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-muted)" }}>Account Created</span>
              <span>{user?.created_at ? new Date(user.created_at).toLocaleString() : "System Init"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-muted)" }}>Last Authentication</span>
              <span>{user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Current Session"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
              <span style={{ color: "var(--text-muted)" }}>Temporary Account Expiration</span>
              <span>
                {user?.expires_at ? (
                  <span style={{ color: user.is_expired ? "var(--status-critical)" : "var(--status-warning)" }}>
                    {new Date(user.expires_at).toLocaleString()}
                  </span>
                ) : (
                  <span style={{ color: "var(--status-healthy)" }}>Permanent Account</span>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Permissions Scope */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <Key size={16} color="var(--accent-primary)" />
            Assigned Capabilities ({user?.permissions?.length || 0})
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, maxHeight: 180, overflowY: "auto" }}>
            {user?.role === "super_admin" || user?.role === "admin" ? (
              <span className="badge badge-success" style={{ padding: "6px 12px", fontSize: 12 }}>
                Full System Administrative Access (All Capabilities Granted)
              </span>
            ) : user?.permissions && user.permissions.length > 0 ? (
              user.permissions.map((p) => (
                <span
                  key={p}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                    background: "var(--surface-sunken)",
                    padding: "4px 8px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border-subtle)"
                  }}
                >
                  {p}
                </span>
              ))
            ) : (
              <span style={{ color: "var(--text-muted)", fontSize: 13 }}>No permissions assigned</span>
            )}
          </div>
        </div>
      </div>

      {/* Active Personal Sessions */}
      <div className="card">
        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
          <Laptop size={16} color="var(--accent-primary)" />
          Active Personal Sessions
        </h3>
        {loading ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No active sessions recorded.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Session JTI</th>
                  <th>IP Address</th>
                  <th>Client / User-Agent</th>
                  <th>Login Time</th>
                  <th>Last Activity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{s.token_jti?.slice(0, 10)}...</td>
                    <td>{s.ip_address || "127.0.0.1"}</td>
                    <td style={{ maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {s.user_agent || "Browser Client"}
                    </td>
                    <td>{s.created_at ? new Date(s.created_at).toLocaleTimeString() : "-"}</td>
                    <td>{s.last_activity_at ? new Date(s.last_activity_at).toLocaleTimeString() : "-"}</td>
                    <td>
                      <StatusBadge status={s.is_revoked ? "FAILED" : "HEALTHY"} />
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
