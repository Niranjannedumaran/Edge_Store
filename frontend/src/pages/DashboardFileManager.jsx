import React, { useState, useEffect } from "react";
import { FolderLock, FileText, UploadCloud, ShieldCheck, ArrowRight, HardDrive } from "lucide-react";
import { useHardware } from "../context/HardwareContext";
import { MetricCard } from "../components/common/MetricCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { apiRequest } from "../api/client";

export function DashboardFileManager({ onNavigate }) {
  const { health } = useHardware();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  const vault = health?.vault;
  const storage = health?.storage;

  const loadFiles = async () => {
    try {
      const data = await apiRequest("/files");
      setFiles(data);
    } catch (err) {
      console.error("Failed to fetch files for file manager:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const totalBytes = files.reduce((acc, f) => acc + (f.file_size || 0), 0);
  const syncedFiles = files.filter((f) => f.replica_status === "synced").length;

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* File Vault Header */}
      <div
        className="card"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            File Operations & Asset Vault
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>
            <span>Total Managed Files: {files.length}</span>
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => onNavigate("files")}>
          <UploadCloud size={14} style={{ marginRight: 6 }} /> Open File Vault
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid-4">
        <MetricCard
          title="Stored Documents"
          value={files.length}
          subValue={`Utilizing ${formatBytes(totalBytes)}`}
          status="HEALTHY"
          icon={FolderLock}
        />
        <MetricCard
          title="Replica Synchronized"
          value={`${syncedFiles} / ${files.length}`}
          subValue="Cross-drive verification intact"
          status={syncedFiles === files.length ? "HEALTHY" : "WARNING"}
          icon={ShieldCheck}
        />
        <MetricCard
          title="Storage Volume State"
          value={storage?.mode || "NORMAL"}
          subValue="Drive A active"
          status={storage?.mode === "NORMAL" ? "HEALTHY" : "WARNING"}
          icon={HardDrive}
        />
        <MetricCard
          title="Vault Security"
          value={vault?.is_unlocked ? "UNLOCKED" : "LOCKED"}
          subValue="Read / Write Enabled"
          status={vault?.is_unlocked ? "HEALTHY" : "CRITICAL"}
          icon={FolderLock}
        />
      </div>

      {/* Recent Files Preview */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
            <FileText size={16} color="var(--accent-primary)" />
            Recently Uploaded Documents
          </h3>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("files")}>
            View All Files <ArrowRight size={13} style={{ marginLeft: 4 }} />
          </button>
        </div>
        {loading ? (
          <div style={{ padding: 30, textAlign: "center", color: "var(--text-muted)" }}>Loading files...</div>
        ) : files.length === 0 ? (
          <div style={{ padding: 30, textAlign: "center", color: "var(--text-muted)" }}>No files uploaded yet.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Size</th>
                  <th>Checksum (SHA-256)</th>
                  <th>Uploaded</th>
                  <th>Replica Sync</th>
                </tr>
              </thead>
              <tbody>
                {files.slice(0, 6).map((f) => (
                  <tr key={f.id}>
                    <td style={{ fontWeight: 600 }}>{f.filename}</td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{formatBytes(f.file_size)}</td>
                    <td>
                      <code style={{ fontSize: 11 }}>{f.sha256_hash?.slice(0, 16)}...</code>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {f.created_at ? new Date(f.created_at).toLocaleDateString() : "-"}
                    </td>
                    <td>
                      <StatusBadge status={f.replica_status?.toUpperCase() || "SYNCED"} />
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
