import React from "react";

export function StatusBadge({ status, label, icon: Icon }) {
  const norm = (status || "").toLowerCase();

  let badgeClass = "badge-info";
  if (["healthy", "synced", "online", "normal", "connected", "mounted", "completed"].includes(norm)) {
    badgeClass = "badge-healthy";
  } else if (["warning", "degraded", "pending", "conservation", "recovering"].includes(norm)) {
    badgeClass = "badge-warning";
  } else if (["critical", "failed", "locked", "error", "disconnected", "unmounted", "delete_pending", "offline"].includes(norm)) {
    badgeClass = "badge-critical";
  } else if (["security", "luks", "encrypted"].includes(norm)) {
    badgeClass = "badge-security";
  }

  const displayText = label || (status ? status.toUpperCase() : "UNKNOWN");

  return (
    <span className={`badge ${badgeClass}`}>
      {Icon ? <Icon size={12} /> : <span style={{ fontSize: 9 }}>●</span>}
      <span>{displayText}</span>
    </span>
  );
}
