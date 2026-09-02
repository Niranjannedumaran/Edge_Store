import React from "react";
import {
  LayoutDashboard,
  FolderLock,
  HardDrive,
  RefreshCw,
  ShieldCheck,
  Activity,
  Users,
  Key,
  Laptop,
  History,
  User,
  LogOut,
  Shield,
  Server,
  Globe
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useHardware } from "../../context/HardwareContext";
import { StatusBadge } from "../common/StatusBadge";

export function Sidebar({ currentTab, setCurrentTab }) {
  const {
    user,
    logout,
    isSuperAdmin,
    isStorageAdmin,
    isSecurityAdmin,
    isFileManager,
    isGuest,
    hasPermission
  } = useAuth();
  const { health } = useHardware();

  // Dynamic role-aware navigation configuration
  const buildNavItems = () => {
    if (isGuest) {
      return [
        { id: "guest_files", label: "Authorized Files", icon: FolderLock },
        { id: "profile", label: "My Profile", icon: User },
        { id: "hero", label: "Appliance Intro", icon: Globe },
      ];
    }

    if (isFileManager) {
      return [
        { id: "dashboard", label: "Overview", icon: LayoutDashboard },
        { id: "files", label: "File Vault", icon: FolderLock },
        { id: "profile", label: "My Profile", icon: User },
        { id: "hero", label: "Appliance Intro", icon: Globe },
      ];
    }

    if (isStorageAdmin) {
      return [
        { id: "dashboard", label: "Overview", icon: LayoutDashboard },
        { id: "files", label: "File Vault", icon: FolderLock },
        { id: "storage", label: "Storage Volumes", icon: HardDrive },
        { id: "replication", label: "Replication", icon: RefreshCw },
        { id: "system", label: "System Health", icon: Activity },
        { id: "admin", label: "Audit Logs", icon: History },
        { id: "profile", label: "My Profile", icon: User },
        { id: "hero", label: "Appliance Intro", icon: Globe },
      ];
    }

    if (isSecurityAdmin) {
      return [
        { id: "dashboard", label: "Overview", icon: LayoutDashboard },
        { id: "admin", label: "User Management", icon: Users },
        { id: "roles", label: "Roles & Matrix", icon: Key },
        { id: "security", label: "Security & Key-SD", icon: ShieldCheck },
        { id: "sessions", label: "Active Sessions", icon: Laptop },
        { id: "profile", label: "My Profile", icon: User },
        { id: "hero", label: "Appliance Intro", icon: Globe },
      ];
    }

    // Super Admin: Full administrative menu
    return [
      { id: "dashboard", label: "Overview", icon: LayoutDashboard },
      { id: "files", label: "File Vault", icon: FolderLock },
      { id: "storage", label: "Storage Volumes", icon: HardDrive },
      { id: "replication", label: "Replication", icon: RefreshCw },
      { id: "security", label: "Key & Security", icon: ShieldCheck },
      { id: "admin", label: "Users & Audit", icon: Users },
      { id: "roles", label: "Roles & Matrix", icon: Key },
      { id: "sessions", label: "Active Sessions", icon: Laptop },
      { id: "system", label: "System & Power", icon: Activity },
      { id: "profile", label: "My Profile", icon: User },
      { id: "hero", label: "Appliance Intro", icon: Globe },
    ];
  };

  const navItems = buildNavItems();
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
        <div className="nav-label">
          {isGuest ? "Viewer Navigation" : "Appliance Controls"}
        </div>
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
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontWeight: 600, color: "var(--text-main)", maxWidth: 110, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {user?.display_name || user?.username || "Operator"}
              </span>
              <span style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "capitalize" }}>
                {user?.role?.replace("_", " ")}
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            className="btn btn-secondary btn-sm"
            title="Sign Out"
            style={{ padding: "4px 7px" }}
          >
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </aside>
  );
}
