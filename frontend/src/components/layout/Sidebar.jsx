import React from "react";
import {
  LayoutDashboard,
  FolderLock,
  HardDrive,
  RefreshCw,
  ShieldCheck,
  Activity,
  Users,
  Terminal,
  LogOut,
  Shield,
  Server
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useHardware } from "../../context/HardwareContext";
import { StatusBadge } from "../common/StatusBadge";

export function Sidebar({ currentTab, setCurrentTab }) {
  const { user, logout, isAdmin } = useAuth();
  const { health } = useHardware();

  const navItems = [
    { id: "dashboard", label: "Overview", icon: LayoutDashboard },
    { id: "files", label: "File Vault", icon: FolderLock },
    { id: "storage", label: "Storage Volumes", icon: HardDrive },
    { id: "replication", label: "Replication", icon: RefreshCw },
    { id: "security", label: "Key & Security", icon: ShieldCheck },
    { id: "system", label: "System & Power", icon: Activity },
  ];

  if (isAdmin) {
    navItems.push({ id: "admin", label: "Administration", icon: Users });
  }

  const isSimulated = health?.is_simulated ?? true;
  const overallStatus = health?.overall_status || "UNKNOWN";

  return (
    <aside className="app-sidebar">
      <div className="brand-header">
        <div className="brand-icon">
          <Shield size={16} />
        </div>
        <div className="brand-title">
          <span>EdgeStore</span>
          <span className="brand-badge">{isSimulated ? "SIM" : "RPI4"}</span>
        </div>
      </div>

      <div className="nav-section">
        <div className="nav-label">Appliance Controls</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = currentTab === item.id;
          return (
            <div
              key={item.id}
              className={`nav-item ${active ? "active" : ""}`}
              onClick={() => setCurrentTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </div>
          );
        })}
      </div>

      <div className="sidebar-footer">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase" }}>Vault Health</span>
          <StatusBadge status={overallStatus} />
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Server size={14} color="var(--text-muted)" />
            <span style={{ fontWeight: 600, color: "var(--text-main)" }}>{user?.username || "Operator"}</span>
            <span style={{ fontSize: 10, color: "var(--text-dim)" }}>({user?.role})</span>
          </div>
          <button
            onClick={logout}
            className="btn btn-secondary btn-sm"
            title="Sign Out"
            style={{ padding: "3px 6px" }}
          >
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </aside>
  );
}
