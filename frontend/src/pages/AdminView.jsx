import React, { useState, useEffect, useCallback } from "react";
import { Users, UserPlus, ShieldAlert, History, UserCheck, UserX, AlertTriangle, RefreshCw } from "lucide-react";
import { apiRequest } from "../api/client";
import { StatusBadge } from "../components/common/StatusBadge";

export function AdminView() {
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [severityFilter, setSeverityFilter] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({ username: "", email: "", password: "", role: "user" });

  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const data = await apiRequest("/admin/users");
      setUsers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  const loadLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      let url = "/admin/audit-logs?limit=50";
      if (severityFilter) url += `&severity=${encodeURIComponent(severityFilter)}`;
      const data = await apiRequest(url);
      setAuditLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingLogs(false);
    }
  }, [severityFilter]);

  useEffect(() => {
    loadUsers();
    loadLogs();
  }, [loadUsers, loadLogs]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await apiRequest("/admin/users", {
        method: "POST",
        body: formData,
      });
      setShowCreateModal(false);
      setFormData({ username: "", email: "", password: "", role: "user" });
      await loadUsers();
      await loadLogs();
    } catch (err) {
      alert(`Failed to create user: ${err.message}`);
    }
  };

  const handleDeactivate = async (user) => {
    if (!window.confirm(`Deactivate user '${user.username}'?`)) return;
    try {
      await apiRequest(`/admin/users/${user.id}`, { method: "DELETE" });
      await loadUsers();
      await loadLogs();
    } catch (err) {
      alert(`Deactivation failed: ${err.message}`);
    }
  };

  return (
    <div>
      {/* User Management Section */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Users size={16} />
            <span>Authorized Appliance Users & RBAC</span>
          </span>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary btn-sm">
            <UserPlus size={14} />
            <span>Create New User</span>
          </button>
        </div>

        <div className="table-container" style={{ border: "none" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Login</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loadingUsers ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: 20 }}>Loading user accounts...</td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id}>
                    <td style={{ fontFamily: "var(--font-mono)" }}>{u.id}</td>
                    <td style={{ fontWeight: 600 }}>{u.username}</td>
                    <td>{u.email || "-"}</td>
                    <td>
                      <StatusBadge
                        status={u.role === "admin" ? "security" : "info"}
                        label={u.role.toUpperCase()}
                      />
                    </td>
                    <td>
                      <StatusBadge
                        status={u.is_active ? "healthy" : "critical"}
                        label={u.is_active ? "ACTIVE" : "DISABLED"}
                      />
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-dim)" }}>
                      {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "Never"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {u.is_active && (
                        <button
                          onClick={() => handleDeactivate(u)}
                          className="btn btn-secondary btn-sm"
                          title="Deactivate account"
                        >
                          <UserX size={12} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Logs Section */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <History size={16} />
            <span>Appliance Security & Operation Audit Trail</span>
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            <select
              className="input"
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              style={{ fontSize: 12, padding: "4px 8px" }}
            >
              <option value="">All Severities</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
            <button onClick={loadLogs} className="btn btn-secondary btn-sm">
              <RefreshCw size={13} className={loadingLogs ? "spin" : ""} />
            </button>
          </div>
        </div>

        <div className="table-container" style={{ border: "none" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Severity</th>
                <th>Event Type</th>
                <th>Operator</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {loadingLogs ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: 20 }}>Loading audit records...</td>
                </tr>
              ) : auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: 20, color: "var(--text-muted)" }}>
                    No audit records match the filter criteria.
                  </td>
                </tr>
              ) : (
                auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", whiteSpace: "nowrap" }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <StatusBadge status={log.severity} label={log.severity} />
                    </td>
                    <td style={{ fontWeight: 600, fontSize: 12 }}>{log.event_type}</td>
                    <td>{log.username || "SYSTEM"}</td>
                    <td style={{ fontSize: 12, color: "var(--text-main)" }}>{log.description}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Provision New Appliance Account</h3>
            <form onSubmit={handleCreateUser} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Username</label>
                <input
                  type="text"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Email (Optional)</label>
                <input
                  type="email"
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Password</label>
                <input
                  type="password"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Role</label>
                <select
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="user">Operator (Standard User)</option>
                  <option value="admin">System Administrator</option>
                </select>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 12 }}>
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
