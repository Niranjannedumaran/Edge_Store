import React, { useState, useEffect } from "react";
import { Shield, Key, Save, CheckCircle2, AlertCircle, RefreshCw, Lock } from "lucide-react";
import { apiRequest } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function RolesPermissionsView() {
  const { hasPermission, refreshProfile } = useAuth();
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [rolePermMap, setRolePermMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [savingRoleId, setSavingRoleId] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);

  const canEdit = hasPermission("roles.update");

  const loadData = async () => {
    setLoading(true);
    try {
      const [rolesData, permsData] = await Promise.all([
        apiRequest("/admin/roles"),
        apiRequest("/admin/permissions")
      ]);
      setRoles(rolesData);
      setPermissions(permsData);

      // Initialize mapping { roleId: Set of permCodes }
      const map = {};
      rolesData.forEach((r) => {
        map[r.id] = new Set(r.permissions || []);
      });
      setRolePermMap(map);
    } catch (err) {
      console.error("Failed to load roles and permissions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const togglePermission = (roleId, permCode, isSystemSuperAdmin) => {
    if (isSystemSuperAdmin || !canEdit) return;
    setRolePermMap((prev) => {
      const currentSet = new Set(prev[roleId] || []);
      if (currentSet.has(permCode)) {
        currentSet.delete(permCode);
      } else {
        currentSet.add(permCode);
      }
      return { ...prev, [roleId]: currentSet };
    });
  };

  const handleSaveRole = async (role) => {
    if (!canEdit || role.name === "super_admin") return;
    setSavingRoleId(role.id);
    setStatusMsg(null);
    try {
      const permCodes = Array.from(rolePermMap[role.id] || []);
      await apiRequest(`/admin/roles/${role.id}/permissions`, {
        method: "PUT",
        body: { permission_codes: permCodes }
      });
      setStatusMsg({ type: "success", text: `Permissions saved for role: ${role.display_name}` });
      await refreshProfile();
    } catch (err) {
      setStatusMsg({ type: "error", text: `Failed to save role: ${err.message}` });
    } finally {
      setSavingRoleId(null);
    }
  };

  // Group permissions by category
  const categories = {};
  permissions.forEach((p) => {
    if (!categories[p.category]) categories[p.category] = [];
    categories[p.category].push(p);
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header Info */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
              <Shield size={20} color="var(--accent-primary)" />
              Database-Driven Role & Permission Matrix
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "4px 0 0 0" }}>
              Configure role capabilities across all appliance subsystems. Changes are immediately audited and enforced server-side.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
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
            {statusMsg.type === "success" ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{statusMsg.text}</span>
          </div>
        )}
      </div>

      {/* Role Save Controls */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {roles.map((r) => (
          <div
            key={r.id}
            className="card"
            style={{
              flex: "1 1 200px",
              padding: "12px 16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{r.display_name}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                {rolePermMap[r.id]?.size || 0} permissions
              </div>
            </div>
            {r.name === "super_admin" ? (
              <span className="badge badge-info" style={{ fontSize: 10, display: "flex", alignItems: "center", gap: 4 }}>
                <Lock size={10} /> Immutable
              </span>
            ) : canEdit ? (
              <button
                className="btn btn-primary btn-sm"
                onClick={() => handleSaveRole(r)}
                disabled={savingRoleId === r.id}
                style={{ padding: "4px 8px", fontSize: 11 }}
              >
                <Save size={11} style={{ marginRight: 4 }} />
                {savingRoleId === r.id ? "Saving..." : "Save"}
              </button>
            ) : null}
          </div>
        ))}
      </div>

      {/* Matrix Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
            Loading authorization matrix...
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ minWidth: 220 }}>Permission Capability</th>
                  <th style={{ width: 90 }}>Code</th>
                  {roles.map((r) => (
                    <th key={r.id} style={{ textAlign: "center", minWidth: 120 }}>
                      <div>{r.display_name}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(categories).map(([category, perms]) => (
                  <React.Fragment key={category}>
                    <tr style={{ background: "var(--surface-sunken)" }}>
                      <td
                        colSpan={2 + roles.length}
                        style={{
                          fontWeight: 700,
                          fontSize: 12,
                          textTransform: "uppercase",
                          letterSpacing: "0.5px",
                          color: "var(--accent-primary)",
                          padding: "8px 14px"
                        }}
                      >
                        Subsystem: {category}
                      </td>
                    </tr>
                    {perms.map((p) => (
                      <tr key={p.code}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{p.name}</div>
                          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{p.description}</div>
                        </td>
                        <td>
                          <code style={{ fontSize: 10 }}>{p.code}</code>
                        </td>
                        {roles.map((r) => {
                          const isSuper = r.name === "super_admin";
                          const isAssigned = isSuper || (rolePermMap[r.id]?.has(p.code) ?? false);
                          return (
                            <td key={r.id} style={{ textAlign: "center" }}>
                              <input
                                type="checkbox"
                                checked={isAssigned}
                                disabled={isSuper || !canEdit}
                                onChange={() => togglePermission(r.id, p.code, isSuper)}
                                style={{
                                  cursor: isSuper || !canEdit ? "default" : "pointer",
                                  accentColor: "var(--accent-primary)",
                                  width: 16,
                                  height: 16
                                }}
                              />
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
