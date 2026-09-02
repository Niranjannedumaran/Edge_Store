import React, { useState, useEffect, useCallback } from "react";
import { Users, UserPlus, History, UserCheck, UserX, Key, Trash2, Shield, RefreshCw } from "lucide-react";
import { apiRequest } from "../api/client";
import { StatusBadge } from "../components/common/StatusBadge";
import { useAuth } from "../context/AuthContext";

export function AdminView({ onNavigate }) {
  const { hasPermission } = useAuth();
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [severityFilter, setSeverityFilter] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [resettingUser, setResettingUser] = useState(null);
  const [newPassword, setNewPassword] = useState("");

  const [formData, setFormData] = useState({
    username: "",
    display_name: "",
    email: "",
    password: "",
    role: "file_manager",
    is_temporary: false,
    expires_in_hours: 24
  });

  const canCreateUser = hasPermission("users.create");
  const canUpdateUser = hasPermission("users.update");
  const canResetPassword = hasPermission("users.reset_password");
  const canDeleteUser = hasPermission("users.delete");

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
      const payload = {
        username: formData.username.trim(),
        display_name: formData.display_name.trim() || formData.username.trim(),
        email: formData.email.trim() || undefined,
        password: formData.password,
        role: formData.role,
        is_temporary: formData.is_temporary,
        expires_in_hours: formData.is_temporary ? parseInt(formData.expires_in_hours, 10) : undefined
      };

      await apiRequest("/admin/users", {
        method: "POST",
        body: payload,
      });
      setShowCreateModal(false);
      setFormData({
        username: "",
        display_name: "",
        email: "",
        password: "",
        role: "file_manager",
        is_temporary: false,
        expires_in_hours: 24
      });
      await loadUsers();
      await loadLogs();
    } catch (err) {
      alert(`Failed to create user: ${err.message}`);
    }
  };

  const handleToggleActive = async (user) => {
    const action = user.is_active ? "deactivate" : "activate";
    if (!window.confirm(`${action.toUpperCase()} user '${user.username}'?`)) return;
    try {
      await apiRequest(`/admin/users/${user.id}`, {
        method: "PATCH",
        body: { is_active: !user.is_active }
      });
      await loadUsers();
      await loadLogs();
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    }
  };

  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!resettingUser || !newPassword) return;

    try {
      await apiRequest(`/admin/users/${resettingUser.id}/reset-password`, {
        method: "POST",
        body: { new_password: newPassword }
      });
      alert(`Password reset successfully for ${resettingUser.username}`);
      setResettingUser(null);
      setNewPassword("");
      await loadLogs();
    } catch (err) {
      alert(`Password reset failed: ${err.message}`);
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Permanently delete user '${user.username}'? This cannot be undone.`)) return;
    try {
      await apiRequest(`/admin/users/${user.id}`, { method: "DELETE" });
      await loadUsers();
      await loadLogs();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div>
      {/* User Management Section */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="card-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Users size={16} />
            <span>Authorized Appliance Users & RBAC</span>
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            {canCreateUser && (
              <button onClick={() => setShowCreateModal(true)} className="btn btn-primary btn-sm">
                <UserPlus size={14} style={{ marginRight: 6 }} />
                <span>Create New User</span>
              </button>
            )}
          </div>
        </div>

        <div className="table-container" style={{ border: "none" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Identity</th>
                <th>Email</th>
                <th>Assigned Role</th>
                <th>Account Status</th>
                <th>Last Login</th>
                <th style={{ textAlign: "right" }}>Controls</th>
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
                    <td>
                      <div style={{ fontWeight: 600 }}>{u.display_name || u.username}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>@{u.username}</div>
                    </td>
                    <td>{u.email || "-"}</td>
                    <td>
                      <span className="badge badge-info" style={{ textTransform: "uppercase", fontSize: 11 }}>
                        {u.role_name || u.role}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <StatusBadge
                          status={u.is_active ? "HEALTHY" : "CRITICAL"}
                          label={u.is_active ? "ACTIVE" : "DISABLED"}
                        />
                        {u.is_expired && <span className="badge badge-danger">EXPIRED</span>}
                      </div>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-dim)" }}>
                      {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "Never"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: 6 }}>
                        {canUpdateUser && (
                          <button
                            onClick={() => handleToggleActive(u)}
                            className={`btn btn-sm ${u.is_active ? "btn-secondary" : "btn-primary"}`}
                            title={u.is_active ? "Deactivate account" : "Activate account"}
                            style={{ padding: "3px 6px" }}
                          >
                            {u.is_active ? <UserX size={13} /> : <UserCheck size={13} />}
                          </button>
                        )}
                        {canResetPassword && (
                          <button
                            onClick={() => {
                              setResettingUser(u);
                              setNewPassword("");
                            }}
                            className="btn btn-secondary btn-sm"
                            title="Reset password"
                            style={{ padding: "3px 6px" }}
                          >
                            <Key size={13} />
                          </button>
                        )}
                        {canDeleteUser && (
                          <button
                            onClick={() => handleDeleteUser(u)}
                            className="btn btn-danger btn-sm"
                            title="Delete user"
                            style={{ padding: "3px 6px" }}
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
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
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="card-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
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
                <th>Actor</th>
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

      {/* Reset Password Modal */}
      {resettingUser && (
        <div className="modal-overlay" onClick={() => setResettingUser(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 400 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>
              Reset Credentials: {resettingUser.username}
            </h3>
            <form onSubmit={handleResetPasswordSubmit}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ fontSize: 12, display: "block", marginBottom: 6 }}>New Password</label>
                <input
                  type="password"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new strong password"
                  autoFocus
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setResettingUser(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Update Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>Provision Appliance Account</h3>
            <form onSubmit={handleCreateUser} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Username *</label>
                <input
                  type="text"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="e.g. jdoe"
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Display Name</label>
                <input
                  type="text"
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  placeholder="e.g. John Doe"
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
                  placeholder="e.g. jdoe@edgestore.local"
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Password *</label>
                <input
                  type="password"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Minimum 8 characters"
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: "block", marginBottom: 4 }}>Assigned Role</label>
                <select
                  className="input"
                  style={{ width: "100%" }}
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="guest">Guest / Viewer (Read-Only)</option>
                  <option value="file_manager">File Manager (Upload, Manage Files)</option>
                  <option value="storage_admin">Storage Administrator (Volumes & Replication)</option>
                  <option value="security_admin">Security Administrator (Users & Policies)</option>
                  <option value="super_admin">Super Administrator (Full System Access)</option>
                </select>
              </div>

              <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 10, marginTop: 4 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 13 }}>
                  <input
                    type="checkbox"
                    checked={formData.is_temporary}
                    onChange={(e) => setFormData({ ...formData, is_temporary: e.target.checked })}
                    style={{ width: 16, height: 16, accentColor: "var(--accent-primary)" }}
                  />
                  <span>Temporary Guest Account (Auto-Expires)</span>
                </label>

                {formData.is_temporary && (
                  <div style={{ marginTop: 8, paddingLeft: 24 }}>
                    <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>
                      Account Validity Duration:
                    </label>
                    <select
                      className="input"
                      value={formData.expires_in_hours}
                      onChange={(e) => setFormData({ ...formData, expires_in_hours: e.target.value })}
                      style={{ width: "100%" }}
                    >
                      <option value={1}>1 Hour (Quick Review)</option>
                      <option value={24}>24 Hours (1 Day)</option>
                      <option value={72}>72 Hours (3 Days)</option>
                      <option value={168}>168 Hours (1 Week)</option>
                      <option value={720}>720 Hours (30 Days)</option>
                    </select>
                  </div>
                )}
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 14 }}>
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Provision User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
