import React from "react";

export function MetricCard({ title, value, subtext, icon: Icon, badgeStatus, badgeLabel, children }) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">
          {Icon && <Icon size={16} />}
          <span>{title}</span>
        </span>
        {badgeStatus && (
          <span className={`badge badge-${badgeStatus.toLowerCase()}`}>
            {badgeLabel || badgeStatus.toUpperCase()}
          </span>
        )}
      </div>
      {value !== undefined && <div className="card-value">{value}</div>}
      {children}
      {subtext && <div className="card-subtext" style={{ marginTop: 8 }}>{subtext}</div>}
    </div>
  );
}

export function ProgressBar({ percent = 0, status = "healthy", height = 8 }) {
  const clamped = Math.max(0, Math.min(100, Number(percent) || 0));
  let colorClass = "progress-healthy";
  if (clamped > 85 || status === "critical") {
    colorClass = "progress-critical";
  } else if (clamped > 70 || status === "warning") {
    colorClass = "progress-warning";
  }

  return (
    <div className="progress-container" style={{ height }}>
      <div className={`progress-bar ${colorClass}`} style={{ width: `${clamped}%` }} />
    </div>
  );
}
