import React, { useState, useEffect, useCallback } from "react";
import {
  Upload,
  Search,
  Download,
  Trash2,
  ShieldCheck,
  FileText,
  Copy,
  Check,
  RefreshCw,
  Edit2,
  AlertTriangle
} from "lucide-react";
import { apiRequest } from "../api/client";
import { useHardware } from "../context/HardwareContext";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/common/StatusBadge";

export function FileManager() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [verifyData, setVerifyData] = useState(null);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [copiedHash, setCopiedHash] = useState(null);
  const [renamingFile, setRenamingFile] = useState(null);
  const [newFilename, setNewFilename] = useState("");

  const { health, refreshHealth } = useHardware();
  const { hasPermission } = useAuth();

  const canUpload = hasPermission("files.upload");
  const canDelete = hasPermission("files.delete");
  const canRename = hasPermission("files.rename");
  const canDownload = hasPermission("files.download");

  const isVaultLocked = !health?.vault?.unlocked;

  const loadFiles = useCallback(async () => {
    setLoading(true);
    try {
      let url = "/files?";
      if (search) url += `search=${encodeURIComponent(search)}&`;
      if (statusFilter) url += `status=${encodeURIComponent(statusFilter)}&`;
      const data = await apiRequest(url);
      setFiles(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (isVaultLocked) {
      alert("Storage vault is locked. Unlock using Key-SD before uploading.");
      return;
    }

    setUploading(true);
    setUploadProgress(20);

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploadProgress(60);
      await apiRequest("/files/upload", {
        method: "POST",
        body: formData,
      });
      setUploadProgress(100);
      await loadFiles();
      await refreshHealth();
    } catch (err) {
      alert(`Upload Failed: ${err.message}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      e.target.value = "";
    }
  };

  const handleDownload = async (file) => {
    try {
      const res = await apiRequest(`/files/${file.id}/download`);
      const blob = res.blob;
      const isDegraded = res.headers.get("X-EdgeStore-Degraded-Fallback") === "true";

      if (isDegraded) {
        alert("Note: File was served from Drive B (Replica) because Primary storage is currently degraded.");
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Download Failed: ${err.message}`);
    }
  };

  const handleRenameSubmit = async (e) => {
    e.preventDefault();
    if (!renamingFile || !newFilename.trim()) return;

    try {
      await apiRequest(`/files/${renamingFile.id}/rename`, {
        method: "PUT",
        body: { new_filename: newFilename.trim() }
      });
      setRenamingFile(null);
      setNewFilename("");
      await loadFiles();
    } catch (err) {
      alert(`Rename Failed: ${err.message}`);
    }
  };

  const handleDelete = async (file) => {
    if (!window.confirm(`Are you sure you want to delete '${file.filename}' from both primary and replica storage?`)) {
      return;
    }

    try {
      const res = await apiRequest(`/files/${file.id}`, { method: "DELETE" });
      if (res.status === "DELETE_PENDING") {
        alert("Warning: Partial deletion. Drive B was offline; scheduled for background reconciliation.");
      }
      await loadFiles();
      await refreshHealth();
    } catch (err) {
      alert(`Delete Failed: ${err.message}`);
    }
  };

  const handleVerify = async (file) => {
    setVerifyLoading(true);
    setVerifyData(null);
    try {
      const data = await apiRequest(`/files/${file.id}/verify`);
      setVerifyData(data);
    } catch (err) {
      alert(`Integrity Check Failed: ${err.message}`);
    } finally {
      setVerifyLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div>
      {/* Vault Locked Banner */}
      {isVaultLocked && (
        <div
          style={{
            padding: "12px 16px",
            marginBottom: 20,
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--status-critical-border)",
            backgroundColor: "var(--status-critical-bg)",
            color: "var(--status-critical-text)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <AlertTriangle size={18} />
            <span>
              <strong>Storage Vault is Locked.</strong> File upload, download, and delete operations are restricted until unlocked with Key-SD.
            </span>
          </div>
        </div>
      )}

      {/* Upload Dropzone Header (Conditional on files.upload) */}
      {canUpload && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Encrypted File Ingestion</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Files uploaded are SHA-256 hashed, stored to Drive A, and replicated with integrity verification to Drive B.
              </p>
            </div>
            <div>
              <label
                className={`btn btn-primary ${uploading || isVaultLocked ? "btn-disabled" : ""}`}
                style={{ cursor: uploading || isVaultLocked ? "not-allowed" : "pointer" }}
              >
                <Upload size={16} />
                <span>{uploading ? `Uploading (${uploadProgress}%)...` : "Upload File"}</span>
                <input
                  type="file"
                  disabled={uploading || isVaultLocked}
                  onChange={handleFileUpload}
                  style={{ display: "none" }}
                />
              </label>
            </div>
          </div>
          {uploading && (
            <div style={{ marginTop: 12 }}>
              <div className="progress-container">
                <div className="progress-bar progress-info" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <div style={{ position: "relative", flex: 1 }}>
          <Search size={15} style={{ position: "absolute", left: 10, top: 10, color: "var(--text-dim)" }} />
          <input
            type="text"
            className="input"
            placeholder="Search files by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: "100%", paddingLeft: 32 }}
          />
        </div>

        <select
          className="input"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ width: 180 }}
        >
          <option value="">All Replica States</option>
          <option value="synced">Synced (Mirrored)</option>
          <option value="pending">Pending Sync</option>
          <option value="failed">Replication Failed</option>
          <option value="degraded">Degraded</option>
          <option value="delete_pending">Delete Pending</option>
        </select>

        <button onClick={loadFiles} className="btn btn-secondary btn-sm" title="Reload List">
          <RefreshCw size={14} className={loading ? "spin" : ""} />
        </button>
      </div>

      {/* File Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>File Name</th>
              <th>Size</th>
              <th>Owner</th>
              <th>SHA-256 Checksum</th>
              <th>Replica Status</th>
              <th>Created</th>
              <th style={{ textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: 30, color: "var(--text-muted)" }}>
                  Loading files from vault...
                </td>
              </tr>
            ) : files.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                  <FileText size={28} style={{ opacity: 0.4, margin: "0 auto 8px auto", display: "block" }} />
                  <div>No files found in vault storage.</div>
                </td>
              </tr>
            ) : (
              files.map((file) => (
                <tr key={file.id}>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <FileText size={16} color="var(--status-info-text)" />
                      <span style={{ fontWeight: 600 }}>{file.filename}</span>
                    </div>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)" }}>{formatBytes(file.file_size)}</td>
                  <td>{file.owner_username}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>
                        {file.sha256_hash.substring(0, 14)}...
                      </span>
                      <button
                        onClick={() => copyToClipboard(file.sha256_hash)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "2px 5px" }}
                        title="Copy full SHA-256"
                      >
                        {copiedHash === file.sha256_hash ? <Check size={11} color="var(--status-healthy-text)" /> : <Copy size={11} />}
                      </button>
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={file.replica_status} />
                  </td>
                  <td style={{ fontSize: 12, color: "var(--text-dim)" }}>
                    {file.created_at ? new Date(file.created_at).toLocaleString() : "-"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: 6 }}>
                      <button
                        onClick={() => handleVerify(file)}
                        className="btn btn-secondary btn-sm"
                        title="Verify SHA-256 on drives"
                      >
                        <ShieldCheck size={13} />
                      </button>

                      {canRename && (
                        <button
                          onClick={() => {
                            setRenamingFile(file);
                            setNewFilename(file.filename);
                          }}
                          className="btn btn-secondary btn-sm"
                          title="Rename file"
                        >
                          <Edit2 size={13} />
                        </button>
                      )}

                      {canDownload && (
                        <button
                          onClick={() => handleDownload(file)}
                          className="btn btn-secondary btn-sm"
                          title="Download file"
                        >
                          <Download size={13} />
                        </button>
                      )}

                      {canDelete && (
                        <button
                          onClick={() => handleDelete(file)}
                          className="btn btn-danger btn-sm"
                          title="Delete file"
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

      {/* Rename Dialog */}
      {renamingFile && (
        <div className="modal-overlay" onClick={() => setRenamingFile(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 450 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Rename File</h3>
            <form onSubmit={handleRenameSubmit}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                  New Filename:
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={newFilename}
                  onChange={(e) => setNewFilename(e.target.value)}
                  autoFocus
                  required
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRenamingFile(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SHA-256 Cross-Drive Verification Modal */}
      {(verifyLoading || verifyData) && (
        <div className="modal-overlay" onClick={() => !verifyLoading && setVerifyData(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                <ShieldCheck size={18} color="var(--status-info-text)" />
                <span>Cryptographic File Integrity Audit</span>
              </h3>
              <button
                onClick={() => setVerifyData(null)}
                className="btn btn-secondary btn-sm"
                style={{ padding: "4px 8px" }}
              >
                Close
              </button>
            </div>

            {verifyLoading ? (
              <div style={{ padding: 30, textAlign: "center", color: "var(--text-muted)" }}>
                Auditing drive checksums...
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: 14, fontSize: 13 }}>
                  <strong>File:</strong> {verifyData.filename}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div className="card" style={{ padding: 12, background: "var(--surface-sunken)" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Drive A (Primary)</div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                      <code style={{ fontSize: 11 }}>{verifyData.primary.hash || "Not Found"}</code>
                      <StatusBadge status={verifyData.primary.intact ? "HEALTHY" : "FAILED"} />
                    </div>
                  </div>

                  <div className="card" style={{ padding: 12, background: "var(--surface-sunken)" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Drive B (Replica)</div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                      <code style={{ fontSize: 11 }}>{verifyData.replica.hash || "Not Found"}</code>
                      <StatusBadge status={verifyData.replica.intact ? "HEALTHY" : "FAILED"} />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
