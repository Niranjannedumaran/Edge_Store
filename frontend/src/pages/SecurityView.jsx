import React, { useState } from "react";
import { Key, Lock, Unlock, ShieldCheck, ShieldAlert, Shield, CheckCircle, AlertTriangle } from "lucide-react";
import { apiRequest } from "../api/client";
import { useHardware } from "../context/HardwareContext";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/common/StatusBadge";
import { MetricCard } from "../components/common/MetricCard";

export function SecurityView() {
  const { health, refreshHealth } = useHardware();
  const { isAdmin } = useAuth();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  const vault = health?.vault;
  const keySd = vault?.key_sd;
  const enc = vault?.encryption;

  const handleUnlock = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await apiRequest("/storage/vault/unlock", { method: "POST" });
      setMessage({ type: "success", text: res.message });
      await refreshHealth();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  };

  const handleLock = async () => {
    if (!window.confirm("Lock storage vault now? All active volumes will be unmounted safely.")) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const res = await apiRequest("/storage/vault/lock", { method: "POST" });
      setMessage({ type: "warning", text: res.message });
      await refreshHealth();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {/* Status Notification */}
      {message && (
        <div
          style={{
            padding: "12px 16px",
            marginBottom: 20,
            borderRadius: "var(--radius-md)",
            border: `1px solid var(--status-${message.type === "error" ? "critical" : (message.type === "warning" ? "warning" : "healthy")}-border)`,
            backgroundColor: `var(--status-${message.type === "error" ? "critical" : (message.type === "warning" ? "warning" : "healthy")}-bg)`,
            color: `var(--status-${message.type === "error" ? "critical" : (message.type === "warning" ? "warning" : "healthy")}-text)`,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          {message.type === "error" ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Security Status Cards */}
      <div className="grid-cards">
        <MetricCard
          title="Physical Key-SD"
          icon={Key}
          badgeStatus={keySd?.present ? "healthy" : "critical"}
          badgeLabel={keySd?.present ? "INSERTED" : "REMOVED"}
          value={keySd?.present ? "Hardware Present" : "Missing / Removed"}
          subtext={`UUID: ${keySd?.uuid || "EDGESTORE-KEY-01"}`}
        />

        <MetricCard
          title="LUKS2 Encryption Layer"
          icon={Lock}
          badgeStatus={vault?.unlocked ? "healthy" : "critical"}
          badgeLabel={vault?.unlocked ? "CONTAINER OPEN" : "LOCKED"}
          value={vault?.unlocked ? "Volume Unlocked" : "Volume Locked"}
          subtext={enc?.cipher || "aes-xts-plain64 512-bit"}
        />

        <MetricCard
          title="Token Integrity"
          value={keySd?.valid ? "Token Verified" : "Invalid Token"}
          badgeStatus={keySd?.valid ? "healthy" : "critical"}
          badgeLabel={keySd?.valid ? "VALID" : "INVALID"}
          subtext={`Keyfile: ${keySd?.key_file || "vault.key"}`}
        />
      </div>

      {/* Vault Control Card */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Shield size={16} />
            <span>Cryptographic Vault Management</span>
          </span>
          <StatusBadge
            status={vault?.unlocked ? "healthy" : "critical"}
            label={vault?.unlocked ? "VAULT UNLOCKED" : "VAULT LOCKED"}
          />
        </div>

        <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
          When the Key-SD is inserted, administrators can unlock the LUKS2 containers to mount ext4 filesystems.
          Removing the Key-SD or manually locking the vault executes a clean buffer flush (<code>sync</code>), unmounts the filesystems,
          and closes the dm-crypt device mapper (<code>cryptsetup luksClose</code>).
        </p>

        <div style={{ display: "flex", gap: 12 }}>
          <button
            disabled={busy || !isAdmin || vault?.unlocked || !keySd?.present}
            onClick={handleUnlock}
            className="btn btn-primary"
          >
            <Unlock size={14} />
            <span>Unlock Vault & Mount Volumes</span>
          </button>

          <button
            disabled={busy || !isAdmin || !vault?.unlocked}
            onClick={handleLock}
            className="btn btn-danger"
          >
            <Lock size={14} />
            <span>Lock Vault (Safe Unmount)</span>
          </button>
        </div>
      </div>

      {/* Defense in Depth Architecture */}
      <div className="card">
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.5px" }}>
          Defense-in-Depth Layered Security Model
        </h4>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, fontSize: 12 }}>
          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-security-text)", marginBottom: 4 }}>Layer 1: Physical Security</div>
            <div style={{ color: "var(--text-muted)" }}>Removable physical Key-SD holds raw key material; removing it triggers instant unmount & lock.</div>
          </div>

          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-info-text)", marginBottom: 4 }}>Layer 2: Disk Encryption</div>
            <div style={{ color: "var(--text-muted)" }}>LUKS2 full-disk encryption with aes-xts-plain64 and 512-bit keys across both physical drives.</div>
          </div>

          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-healthy-text)", marginBottom: 4 }}>Layer 3: Application Auth</div>
            <div style={{ color: "var(--text-muted)" }}>Role-based access control (USER / ADMIN) with salted bcrypt passwords and signed JWT tokens.</div>
          </div>

          <div style={{ padding: 12, background: "var(--bg-surface-raised)", borderRadius: "var(--radius-md)" }}>
            <div style={{ fontWeight: 700, color: "var(--status-warning-text)", marginBottom: 4 }}>Layer 4: Data Integrity</div>
            <div style={{ color: "var(--text-muted)" }}>Every file is verified via SHA-256 upon ingestion, replication, and before streaming download.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
