import React, { useState, useEffect } from "react";
import { Search, Eye, Download, FileText, ShieldAlert, CheckCircle2, Lock } from "lucide-react";
import { apiRequest } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/common/StatusBadge";

const TEXT_FILE_EXTENSIONS = new Set([
  "csv", "css", "html", "js", "json", "jsx", "log", "md", "py", "ts", "tsx", "txt", "xml", "yaml", "yml"
]);

function isTextFile(filename = "") {
  const extension = filename.split(".").pop()?.toLowerCase();
  return TEXT_FILE_EXTENSIONS.has(extension);
}

export function GuestView() {
  const { user, hasPermission } = useAuth();
  const [files, setFiles] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [previewFile, setPreviewFile] = useState(null);
  const [previewContent, setPreviewContent] = useState(null);
  const [previewKind, setPreviewKind] = useState("text");
  const [previewUrl, setPreviewUrl] = useState(null);

  const canDownload = hasPermission("files.download");

  const loadFiles = async () => {
    setLoading(true);
    try {
      const data = await apiRequest(`/files${search ? `?search=${encodeURIComponent(search)}` : ""}`);
      setFiles(data);
    } catch (err) {
      console.error("Failed to load viewer files:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [search]);

  const handlePreview = async (file) => {
    if (previewUrl) window.URL.revokeObjectURL(previewUrl);
    setPreviewFile(file);
    setPreviewContent("Loading preview content...");
    setPreviewKind("text");
    setPreviewUrl(null);
    try {
      const result = await apiRequest(`/files/${file.id}/download`);
      const contentType = result.headers?.get("content-type") || "";
      const blob = result.blob;
      if (blob && contentType.startsWith("image/")) {
        setPreviewKind("image");
        setPreviewUrl(window.URL.createObjectURL(blob));
        setPreviewContent(null);
        return;
      }
      if (blob && contentType.includes("application/pdf")) {
        setPreviewKind("pdf");
        setPreviewUrl(window.URL.createObjectURL(blob));
        setPreviewContent(null);
        return;
      }
      if (typeof result === "string" || contentType.startsWith("text/") || contentType.includes("application/json") || isTextFile(file.filename)) {
        const text = typeof result === "string"
          ? result
          : blob
            ? await blob.text()
            : JSON.stringify(result, null, 2);
        setPreviewContent(text.slice(0, 4000));
      } else {
        setPreviewContent("Preview unavailable for this binary format or file is encrypted.");
      }
    } catch (err) {
      setPreviewContent("Unable to render file preview.");
    }
  };

  const closePreview = () => {
    if (previewUrl) window.URL.revokeObjectURL(previewUrl);
    setPreviewFile(null);
    setPreviewContent(null);
    setPreviewUrl(null);
  };

  const handleDownload = (file) => {
    apiRequest(`/files/${file.id}/download`)
      .then(result => result.blob || new Blob([result], { type: file.content_type || "application/octet-stream" }))
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = file.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      })
      .catch(err => alert("Download failed: " + err.message));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Read-Only Banner */}
      <div
        style={{
          background: "var(--surface-sunken)",
          border: "1px solid var(--border-subtle)",
          borderLeft: "4px solid var(--accent-primary)",
          padding: "14px 18px",
          borderRadius: "var(--radius-md)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Lock size={20} color="var(--accent-primary)" />
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Read-Only Guest Viewer Mode</div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
              You are authenticated as <strong>{user?.display_name || user?.username}</strong>. You have read-only inspection access to verified storage assets.
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="badge badge-info" style={{ fontSize: 11, textTransform: "uppercase" }}>
            {canDownload ? "Download Permitted" : "Download Restricted"}
          </span>
        </div>
      </div>

      {/* Search Header */}
      <div className="card" style={{ padding: "12px 16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Search size={18} color="var(--text-dim)" />
          <input
            type="text"
            className="form-input"
            placeholder="Search files by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ border: "none", background: "transparent", padding: "6px 0", flex: 1, fontSize: 14 }}
          />
        </div>
      </div>

      {/* Files Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ padding: 30, textAlign: "center", color: "var(--text-muted)" }}>
            Scanning authorized storage assets...
          </div>
        ) : files.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
            <FileText size={32} style={{ margin: "0 auto 10px auto", opacity: 0.5 }} />
            <div>No files available in your authorized scope.</div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Size</th>
                  <th>Integrity Checksum (SHA-256)</th>
                  <th>Created</th>
                  <th>Replication State</th>
                  <th style={{ textAlign: "right" }}>Inspection Action</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr key={f.id}>
                    <td style={{ fontWeight: 600 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <FileText size={16} color="var(--accent-primary)" />
                        {f.filename}
                      </div>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {(f.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td>
                      <code style={{ fontSize: 11, color: "var(--text-dim)" }}>
                        {f.sha256_hash.slice(0, 16)}...
                      </code>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {f.created_at ? new Date(f.created_at).toLocaleDateString() : "-"}
                    </td>
                    <td>
                      <StatusBadge status={f.replica_status?.toUpperCase() || "SYNCED"} />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handlePreview(f)}
                          style={{ display: "flex", alignItems: "center", gap: 6 }}
                        >
                          <Eye size={13} />
                          <span>[PREVIEW]</span>
                        </button>
                        {canDownload && (
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleDownload(f)}
                            style={{ display: "flex", alignItems: "center", gap: 6 }}
                          >
                            <Download size={13} />
                            <span>Download</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Preview Dialog */}
      {previewFile && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 20
          }}
        >
          <div
            className="card"
            style={{
              width: "100%",
              maxWidth: 700,
              maxHeight: "85vh",
              display: "flex",
              flexDirection: "column",
              gap: 16
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-subtle)", paddingBottom: 10 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{previewFile.filename}</h3>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  SHA-256: {previewFile.sha256_hash}
                </span>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={closePreview}
              >
                Close
              </button>
            </div>

            {previewKind === "image" && previewUrl ? (
              <img
                src={previewUrl}
                alt={`Read-only preview of ${previewFile.filename}`}
                style={{ maxWidth: "100%", maxHeight: 420, objectFit: "contain", background: "var(--surface-sunken)", borderRadius: "var(--radius-sm)" }}
              />
            ) : previewKind === "pdf" && previewUrl ? (
              <iframe
                title={`Read-only preview of ${previewFile.filename}`}
                src={previewUrl}
                style={{ width: "100%", height: 420, border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", background: "var(--surface-sunken)" }}
              />
            ) : (
              <div
                style={{
                  flex: 1,
                  background: "var(--surface-sunken)",
                  padding: 14,
                  borderRadius: "var(--radius-sm)",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                  color: "var(--text-main)",
                  maxHeight: 380,
                  border: "1px solid var(--border-subtle)"
                }}
              >
                {previewContent}
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8 }}>
              <span className="badge badge-info">Read-Only Secure Preview</span>
              {canDownload && (
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleDownload(previewFile)}
                >
                  <Download size={13} style={{ marginRight: 6 }} />
                  Download Copy
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
