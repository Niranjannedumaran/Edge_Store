import {
  Shield,
  Quote,
  User,
  Lock,
  Eye,
  EyeOff,
  Check,
  ArrowRight,
  ArrowLeft,
  HardDrive,
  Key,
  AlertTriangle,
  Server
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function Login({ onBackToLanding }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("AdminEdgeStore2026!");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || "Authentication failed. Verify credentials.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleFillCredentials = (u, p) => {
    setUsername(u);
    setPassword(p);
    setError(null);
  };

  return (
    <div
      style={{
        display: "flex",
        width: "100vw",
        minHeight: "100vh",
        backgroundColor: "#000000",
        color: "#ffffff",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        overflowX: "hidden",
      }}
    >
      {/* =========================================================================
          LEFT VISUAL PANEL (Corporate Dark Infrastructure Aesthetic)
          ========================================================================= */}
      <div
        className="login-left-panel"
        style={{
          width: "50%",
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "56px 64px",
          backgroundColor: "#09090b",
          borderRight: "1px solid #18181b",
          overflow: "hidden",
        }}
      >
        {/* Layer 0: Noise Grain Overlay */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.035'/%3E%3C/svg%3E")`,
            pointerEvents: "none",
            zIndex: 1,
          }}
        />

        {/* Layer 1: Ambient Blur Blobs */}
        <div
          style={{
            position: "absolute",
            width: "80%",
            height: "80%",
            top: "-20%",
            left: "-20%",
            backgroundColor: "rgba(39, 39, 42, 0.4)",
            filter: "blur(120px)",
            borderRadius: "50%",
            pointerEvents: "none",
            zIndex: 1,
          }}
        />
        <div
          style={{
            position: "absolute",
            width: "60%",
            height: "60%",
            bottom: "-10%",
            right: "-10%",
            backgroundColor: "rgba(24, 24, 27, 0.6)",
            filter: "blur(100px)",
            borderRadius: "50%",
            pointerEvents: "none",
            zIndex: 1,
          }}
        />

        {/* Layer 2: Subtle 60px Tech Grid */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
            pointerEvents: "none",
            zIndex: 2,
          }}
        />

        {/* Layer 3: Foreground Content */}
        {/* Brand Header */}
        <div style={{ position: "relative", zIndex: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 8,
                backgroundColor: "#ffffff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#000000",
                boxShadow: "0 0 25px rgba(255,255,255,0.15)",
              }}
            >
              <Shield size={20} strokeWidth={2.5} />
            </div>
            <div>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  letterSpacing: "-0.05em",
                  color: "#ffffff",
                  textTransform: "uppercase",
                }}
              >
                EDGESTORE
              </div>
              <div style={{ fontSize: 11, color: "#71717a", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Appliance Console • RPi4
              </div>
            </div>
          </div>
        </div>

        {/* Center Quote / Security Statement */}
        <div style={{ position: "relative", zIndex: 10, maxWidth: 520, margin: "40px 0" }}>
          <Quote size={32} color="#52525b" style={{ marginBottom: 16 }} />
          <p
            style={{
              fontSize: 22,
              lineHeight: 1.45,
              fontWeight: 300,
              color: "#e4e4e7",
              letterSpacing: "-0.02em",
              marginBottom: 28,
            }}
          >
            "Design is not just what it looks like and feels like. Design is how it works. EdgeStore provides
            the hardware-bound, cryptographically encrypted local storage that powers resilience at the edge."
          </p>

          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: "50%",
                backgroundColor: "#27272a",
                border: "1px solid #3f3f46",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: 14,
                color: "#f4f4f5",
              }}
            >
              JD
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, color: "#ffffff" }}>Julian Davis</div>
              <div style={{ fontSize: 12, color: "#a1a1aa" }}>Chief Hardware Security Architect, EdgeStore</div>
            </div>
          </div>
        </div>

        {/* Left Panel Footer */}
        <div
          style={{
            position: "relative",
            zIndex: 10,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 11,
            color: "#52525b",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            borderTop: "1px solid #18181b",
            paddingTop: 20,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                backgroundColor: "#22c55e",
                display: "inline-block",
                boxShadow: "0 0 8px #22c55e",
              }}
            />
            <span style={{ color: "#a1a1aa", fontWeight: 500 }}>System Status: Optimal (Key-SD Verified)</span>
          </div>
          <div>© 2026 EdgeStore Appliance • LUKS2 Dual-Drive</div>
        </div>
      </div>

      {/* =========================================================================
          RIGHT LOGIN PANEL (High-Precision Minimalist Corporate Form)
          ========================================================================= */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "40px 24px",
          backgroundColor: "#000000",
          position: "relative",
          zIndex: 20,
        }}
      >
        <div style={{ width: "100%", maxWidth: 420 }}>
          {/* Mobile Header Logo */}
          <div className="login-mobile-header" style={{ display: "none", marginBottom: 32, alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 6,
                backgroundColor: "#ffffff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#000000",
              }}
            >
              <Shield size={18} strokeWidth={2.5} />
            </div>
            <span style={{ fontSize: 16, fontWeight: 800, letterSpacing: "-0.04em", textTransform: "uppercase" }}>
              EDGESTORE
            </span>
          </div>

          {/* Back to Overview Link */}
          {onBackToLanding && (
            <button
              type="button"
              onClick={onBackToLanding}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                background: "none",
                border: "none",
                color: "#71717a",
                fontSize: 12,
                cursor: "pointer",
                padding: "0 0 16px 0",
                transition: "color 0.15s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#ffffff")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#71717a")}
            >
              <ArrowLeft size={14} />
              <span>Back to Overview</span>
            </button>
          )}

          {/* Form Header */}
          <div style={{ marginBottom: 28 }}>
            <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.03em", color: "#ffffff", margin: 0 }}>
              Welcome back
            </h1>
            <p style={{ fontSize: 13, color: "#71717a", marginTop: 6, lineHeight: 1.5 }}>
              Enter your credentials to access the EdgeStore appliance workspace.
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              style={{
                padding: "12px 14px",
                marginBottom: 20,
                borderRadius: 8,
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#f87171",
                fontSize: 12,
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* Username Input */}
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: 12,
                  fontWeight: 500,
                  color: "#d4d4d8",
                  marginBottom: 6,
                }}
              >
                Operator Username
              </label>
              <div style={{ position: "relative" }}>
                <User
                  size={15}
                  style={{
                    position: "absolute",
                    left: 14,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "#71717a",
                  }}
                />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. admin or operator"
                  style={{
                    width: "100%",
                    padding: "11px 14px 11px 40px",
                    backgroundColor: "#09090b",
                    border: "1px solid #27272a",
                    borderRadius: 8,
                    color: "#ffffff",
                    fontSize: 13,
                    outline: "none",
                    transition: "all 0.2s ease",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#71717a")}
                  onBlur={(e) => (e.target.style.borderColor = "#27272a")}
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: "#d4d4d8" }}>Password</label>
                <span style={{ fontSize: 11, color: "#52525b" }}>argon2id / bcrypt</span>
              </div>
              <div style={{ position: "relative" }}>
                <Lock
                  size={15}
                  style={{
                    position: "absolute",
                    left: 14,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "#71717a",
                  }}
                />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: "100%",
                    padding: "11px 42px 11px 40px",
                    backgroundColor: "#09090b",
                    border: "1px solid #27272a",
                    borderRadius: 8,
                    color: "#ffffff",
                    fontSize: 13,
                    outline: "none",
                    transition: "all 0.2s ease",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#71717a")}
                  onBlur={(e) => (e.target.style.borderColor = "#27272a")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: "absolute",
                    right: 12,
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    color: "#71717a",
                    cursor: "pointer",
                    padding: 4,
                  }}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  fontSize: 12,
                  color: "#a1a1aa",
                  cursor: "pointer",
                  userSelect: "none",
                }}
                onClick={() => setRememberMe(!rememberMe)}
              >
                <div
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: 4,
                    backgroundColor: rememberMe ? "#ffffff" : "#18181b",
                    border: rememberMe ? "1px solid #ffffff" : "1px solid #27272a",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 0.15s ease",
                  }}
                >
                  {rememberMe && <Check size={12} color="#000000" strokeWidth={3} />}
                </div>
                <span>Remember this appliance session</span>
              </label>
              <span style={{ fontSize: 11, color: "#71717a" }}>TLS 1.3</span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting}
              style={{
                width: "100%",
                padding: "11px 0",
                backgroundColor: "#ffffff",
                color: "#000000",
                fontWeight: 600,
                fontSize: 13,
                borderRadius: 8,
                border: "none",
                cursor: submitting ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                transition: "all 0.2s ease",
                boxShadow: "0 0 20px rgba(255, 255, 255, 0.1)",
                opacity: submitting ? 0.7 : 1,
              }}
              onMouseEnter={(e) => {
                if (!submitting) e.target.style.backgroundColor = "#e4e4e7";
              }}
              onMouseLeave={(e) => {
                if (!submitting) e.target.style.backgroundColor = "#ffffff";
              }}
            >
              <span>{submitting ? "Authenticating Session..." : "Access Workspace"}</span>
              <ArrowRight size={14} />
            </button>
          </form>

          {/* =========================================================================
              DEFAULT CREDENTIALS (Requested explicitly: Click-to-Auto-fill all roles)
              ========================================================================= */}
          <div
            style={{
              marginTop: 24,
              padding: "16px 18px",
              backgroundColor: "#09090b",
              border: "1px solid #18181b",
              borderRadius: 10,
            }}
          >
            <div
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "#71717a",
                marginBottom: 12,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span>Default Credentials (One-Click Fill)</span>
              <Server size={13} color="#52525b" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {/* Super Admin */}
              <div
                onClick={() => handleFillCredentials("admin", "AdminEdgeStore2026!")}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 12px",
                  borderRadius: 6,
                  backgroundColor: "#121215",
                  border: "1px solid #1f1f23",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#3f3f46")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1f1f23")}
                title="Click to auto-fill Super Administrator credentials"
              >
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#ffffff" }}>Super Administrator</div>
                  <div style={{ fontSize: 11, color: "#71717a", fontFamily: "var(--font-mono)" }}>
                    admin / AdminEdgeStore2026!
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: "#ffffff",
                    backgroundColor: "#27272a",
                    padding: "3px 8px",
                    borderRadius: 4,
                  }}
                >
                  Auto-Fill
                </span>
              </div>

              {/* Storage Operator */}
              <div
                onClick={() => handleFillCredentials("operator", "OperatorEdgeStore2026!")}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 12px",
                  borderRadius: 6,
                  backgroundColor: "#121215",
                  border: "1px solid #1f1f23",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#3f3f46")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1f1f23")}
                title="Click to auto-fill Storage Operator credentials"
              >
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#ffffff" }}>Storage Operator</div>
                  <div style={{ fontSize: 11, color: "#71717a", fontFamily: "var(--font-mono)" }}>
                    operator / OperatorEdgeStore2026!
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: "#ffffff",
                    backgroundColor: "#27272a",
                    padding: "3px 8px",
                    borderRadius: 4,
                  }}
                >
                  Auto-Fill
                </span>
              </div>

              {/* Guest Viewer */}
              <div
                onClick={() => handleFillCredentials("guest", "GuestEdgeStore2026!")}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 12px",
                  borderRadius: 6,
                  backgroundColor: "#121215",
                  border: "1px solid #1f1f23",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#3f3f46")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1f1f23")}
                title="Click to auto-fill Project Reviewer (Guest) credentials"
              >
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#ffffff" }}>Project Reviewer (Guest)</div>
                  <div style={{ fontSize: 11, color: "#71717a", fontFamily: "var(--font-mono)" }}>
                    guest / GuestEdgeStore2026!
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: "#ffffff",
                    backgroundColor: "#27272a",
                    padding: "3px 8px",
                    borderRadius: 4,
                  }}
                >
                  Auto-Fill
                </span>
              </div>
            </div>
          </div>

          {/* Footer Security Badge */}
          <div
            style={{
              marginTop: 20,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              fontSize: 11,
              color: "#52525b",
            }}
          >
            <Key size={13} color="#71717a" />
            <span>Hardware Token Security: Key-SD & LUKS2 Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
