import React, { useState } from "react";
import { Shield, Lock, User, AlertTriangle, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function Login() {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("AdminEdgeStore2026!");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        width: "100vw",
        backgroundColor: "var(--bg-app)",
        padding: 20,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "var(--radius-lg)",
          padding: 32,
          boxShadow: "var(--shadow-dock)",
        }}
      >
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, #1f6feb, #8957e5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              margin: "0 auto 12px auto",
            }}
          >
            <Shield size={22} />
          </div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-main)" }}>EdgeStore Console</h2>
          <p style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>
            Secure Edge Storage Appliance • Phase 1 Single-Node
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: "10px 12px",
              marginBottom: 16,
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--status-critical-bg)",
              border: "1px solid var(--status-critical-border)",
              color: "var(--status-critical-text)",
              fontSize: 12,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <AlertTriangle size={15} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
              Operator Username
            </label>
            <div style={{ position: "relative" }}>
              <User size={15} style={{ position: "absolute", left: 10, top: 10, color: "var(--text-dim)" }} />
              <input
                type="text"
                required
                className="input"
                style={{ width: "100%", paddingLeft: 32 }}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
              Password
            </label>
            <div style={{ position: "relative" }}>
              <Lock size={15} style={{ position: "absolute", left: 10, top: 10, color: "var(--text-dim)" }} />
              <input
                type="password"
                required
                className="input"
                style={{ width: "100%", paddingLeft: 32 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="btn btn-primary"
            style={{ width: "100%", marginTop: 8, padding: "10px 0" }}
          >
            <span>{submitting ? "Authenticating..." : "Authenticate Session"}</span>
            <ArrowRight size={14} />
          </button>
        </form>

        <div
          style={{
            marginTop: 20,
            padding: 12,
            background: "var(--bg-surface-raised)",
            borderRadius: "var(--radius-md)",
            fontSize: 11,
            color: "var(--text-muted)",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Default Credentials:</div>
          <div>Admin: <code>admin</code> / <code>AdminEdgeStore2026!</code></div>
          <div>Operator: <code>operator</code> / <code>OperatorEdgeStore2026!</code></div>
        </div>
      </div>
    </div>
  );
}
