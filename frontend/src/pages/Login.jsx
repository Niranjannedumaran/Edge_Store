import React, { useState } from "react";
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
  Key,
  AlertTriangle,
  Server,
  CheckCircle2,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { EdgeStoreLogo } from "../components/common/EdgeStoreLogo";
import { apiRequest } from "../api/client";

export function Login({ onBackToLanding, onLoginSuccess }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("AdminEdgeStore2026!");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Bot gate - always starts false (single-use per login)
  const [botVerified, setBotVerified] = useState(false);
  const [botLoading, setBotLoading] = useState(false);
  const [botChallenge, setBotChallenge] = useState(null);
  const [botSolution, setBotSolution] = useState("");
  const [botError, setBotError] = useState(null);

  const { login } = useAuth();

  // Step 1: Click "I'm not a robot" -> fetch challenge
  const handleStartBotChallenge = async () => {
    if (botVerified || botChallenge) return;
    setBotLoading(true);
    setBotError(null);
    try {
      const data = await apiRequest("/security/anti-bot/challenge");
      setBotChallenge(data);
    } catch {
      setBotError("Failed to reach server. Please retry.");
    } finally {
      setBotLoading(false);
    }
  };

  // Step 1b: Verify answer -> unlock login form
  const handleVerifyBotChallenge = async (e) => {
    e?.preventDefault();
    if (!botChallenge || !botSolution.trim()) return;
    setBotLoading(true);
    setBotError(null);
    try {
      const data = await apiRequest("/security/anti-bot/verify", {
        method: "POST",
        body: {
          challenge_id: botChallenge.challenge_id,
          solution: botSolution.trim(),
        },
      });
      localStorage.setItem("edgestore_anti_bot_token", data.anti_bot_token);
      setBotVerified(true);
      setBotChallenge(null);
      setBotSolution("");
      setError(null);
    } catch (err) {
      setBotError(err.message || "Verification failed. Try again.");
    } finally {
      setBotLoading(false);
    }
  };

  // Step 2: Login
  const handleSubmit = async (e) => {
    e?.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      // Consume token - single use per login
      localStorage.removeItem("edgestore_anti_bot_token");
      setBotVerified(false);
      setBotChallenge(null);
      setBotSolution("");
      if (onLoginSuccess) onLoginSuccess();
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
    <div style={{ display: "flex", width: "100vw", minHeight: "100vh", backgroundColor: "#000000", color: "#ffffff", fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif", overflowX: "hidden" }}>

      {/* LEFT PANEL */}
      <div className="login-left-panel" style={{ width: "50%", position: "relative", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: "56px 64px", backgroundColor: "#09090b", borderRight: "1px solid #18181b", overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E")`, pointerEvents: "none", zIndex: 1 }} />
        <div style={{ position: "absolute", width: "80%", height: "80%", top: "-20%", left: "-20%", backgroundColor: "rgba(39,39,42,0.4)", filter: "blur(120px)", borderRadius: "50%", pointerEvents: "none", zIndex: 1 }} />
        <div style={{ position: "absolute", width: "60%", height: "60%", bottom: "-10%", right: "-10%", backgroundColor: "rgba(24,24,27,0.6)", filter: "blur(100px)", borderRadius: "50%", pointerEvents: "none", zIndex: 1 }} />
        <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)", backgroundSize: "60px 60px", pointerEvents: "none", zIndex: 2 }} />

        <div style={{ position: "relative", zIndex: 10 }}>
          <EdgeStoreLogo size={42} showText={true} textClassName="font-extrabold text-xl tracking-tight text-white uppercase" subtitle="Appliance Console" />
        </div>

        <div style={{ position: "relative", zIndex: 10, maxWidth: 520, margin: "40px 0" }}>
          <Quote size={32} color="#52525b" style={{ marginBottom: 16 }} />
          <p style={{ fontSize: 22, lineHeight: 1.45, fontWeight: 300, color: "#e4e4e7", letterSpacing: "-0.02em", marginBottom: 28 }}>
            "Design is not just what it looks like and feels like. Design is how it works. EdgeStore provides the hardware-bound, cryptographically encrypted local storage that powers resilience at the edge."
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 44, height: 44, borderRadius: "50%", backgroundColor: "#27272a", border: "1px solid #3f3f46", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 14, color: "#f4f4f5" }}>JD</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, color: "#ffffff" }}>Julian Davis</div>
              <div style={{ fontSize: 12, color: "#a1a1aa" }}>Chief Hardware Security Architect, EdgeStore</div>
            </div>
          </div>
        </div>

        <div style={{ position: "relative", zIndex: 10, display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, color: "#52525b", letterSpacing: "0.05em", textTransform: "uppercase", borderTop: "1px solid #18181b", paddingTop: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", backgroundColor: "#22c55e", display: "inline-block", boxShadow: "0 0 8px #22c55e" }} />
            <span style={{ color: "#a1a1aa", fontWeight: 500 }}>System Status: Optimal (Key-SD Verified)</span>
          </div>
          <div>2026 EdgeStore Appliance LUKS2 Dual-Drive</div>
        </div>
      </div>

      {/* RIGHT PANEL - 2-Step Gate */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "40px 24px", backgroundColor: "#000000", position: "relative", zIndex: 20, overflow: "hidden" }}>

        {/* STEP 1: Bot Gate */}
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "40px 24px", transition: "opacity 0.4s ease, transform 0.4s ease", opacity: botVerified ? 0 : 1, transform: botVerified ? "translateY(-28px)" : "translateY(0)", pointerEvents: botVerified ? "none" : "auto" }}>
          <div style={{ width: "100%", maxWidth: 400, textAlign: "center" }}>

            {onBackToLanding && (
              <div style={{ textAlign: "left", marginBottom: 28 }}>
                <button type="button" onClick={onBackToLanding} style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "none", border: "none", color: "#71717a", fontSize: 12, cursor: "pointer", padding: 0 }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#ffffff")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "#71717a")}>
                  <ArrowLeft size={14} /><span>Back to Overview</span>
                </button>
              </div>
            )}

            {/* Shield icon */}
            <div style={{ width: 80, height: 80, borderRadius: "50%", margin: "0 auto 28px", backgroundColor: "#0a0a0d", border: botChallenge ? "2px solid #3b82f6" : "2px solid #1f1f23", display: "flex", alignItems: "center", justifyContent: "center", transition: "border-color 0.3s ease, box-shadow 0.3s ease", boxShadow: botChallenge ? "0 0 32px rgba(59,130,246,0.18)" : "none" }}>
              {botLoading
                ? <div style={{ width: 30, height: 30, border: "3px solid #3f3f46", borderTopColor: "#3b82f6", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
                : <Shield size={34} color={botChallenge ? "#3b82f6" : "#3f3f46"} />
              }
            </div>

            <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.03em", color: "#ffffff", margin: "0 0 10px" }}>
              {botChallenge ? "Prove you're human" : "Security Checkpoint"}
            </h1>
            <p style={{ fontSize: 13, color: "#71717a", lineHeight: 1.6, maxWidth: 320, margin: "0 auto 36px" }}>
              {botChallenge
                ? "Solve the challenge below to unlock the login form."
                : "Click the button to begin a quick check. The login form loads only after you pass."}
            </p>

            {/* "I'm not a robot" button */}
            {!botChallenge && (
              <button type="button" onClick={handleStartBotChallenge} disabled={botLoading}
                style={{ width: "100%", padding: "15px 20px", backgroundColor: "#0d0d10", border: "1px solid #2d2d35", borderRadius: 10, color: "#ffffff", fontSize: 14, fontWeight: 600, cursor: botLoading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: 14, transition: "all 0.2s ease" }}
                onMouseEnter={(e) => { if (!botLoading) { e.currentTarget.style.borderColor = "#52525b"; e.currentTarget.style.backgroundColor = "#111116"; } }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "#2d2d35"; e.currentTarget.style.backgroundColor = "#0d0d10"; }}
              >
                <div style={{ width: 24, height: 24, borderRadius: 5, flexShrink: 0, border: "2px solid #52525b", backgroundColor: "#18181b", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {botLoading && <div style={{ width: 11, height: 11, border: "2px solid #71717a", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />}
                </div>
                <span style={{ flex: 1 }}>I'm not a robot</span>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <Shield size={13} color="#52525b" />
                    <span style={{ fontSize: 9, color: "#52525b", fontWeight: 700, letterSpacing: "0.06em" }}>ANTI-BOT</span>
                  </div>
                  <span style={{ fontSize: 8, color: "#3f3f46" }}>EdgeStore Shield</span>
                </div>
              </button>
            )}

            {/* Math challenge */}
            {botChallenge && (
              <div style={{ backgroundColor: "#080810", border: "1px solid #1e3554", borderRadius: 12, padding: "22px", textAlign: "left" }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: "#6b7280", textTransform: "uppercase", marginBottom: 10 }}>Human Verification</div>
                <div style={{ fontSize: 15, color: "#93c5fd", fontWeight: 600, marginBottom: 18, lineHeight: 1.5 }}>{botChallenge.prompt}</div>
                <div style={{ display: "flex", gap: 10 }}>
                  <input type="number" value={botSolution} onChange={(e) => setBotSolution(e.target.value)} placeholder="Your answer"
                    onKeyDown={(e) => { if (e.key === "Enter") handleVerifyBotChallenge(e); }}
                    style={{ flex: 1, padding: "11px 14px", backgroundColor: "#0e0e18", border: "1px solid #1e3554", borderRadius: 8, color: "#ffffff", fontSize: 15, outline: "none", fontWeight: 700 }}
                    autoFocus />
                  <button type="button" onClick={handleVerifyBotChallenge} disabled={botLoading || !botSolution.trim()}
                    style={{ padding: "11px 22px", backgroundColor: (!botLoading && botSolution.trim()) ? "#3b82f6" : "#1e3554", border: "none", borderRadius: 8, color: "#ffffff", fontSize: 13, fontWeight: 700, cursor: (botLoading || !botSolution.trim()) ? "not-allowed" : "pointer", transition: "background-color 0.2s ease", whiteSpace: "nowrap" }}>
                    {botLoading ? "..." : "Verify"}
                  </button>
                </div>
                {botError && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#f87171", marginTop: 12 }}>
                    <AlertTriangle size={13} /><span>{botError}</span>
                  </div>
                )}
              </div>
            )}

            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 11, color: "#3f3f46", marginTop: 20 }}>
              <Key size={11} color="#3f3f46" />
              <span>Login form is hidden until verification passes</span>
            </div>
          </div>
        </div>

        {/* STEP 2: Login Form */}
        <div style={{ width: "100%", maxWidth: 420, transition: "opacity 0.45s ease, transform 0.45s ease", opacity: botVerified ? 1 : 0, transform: botVerified ? "translateY(0)" : "translateY(32px)", pointerEvents: botVerified ? "auto" : "none" }}>

          {onBackToLanding && (
            <button type="button" onClick={onBackToLanding}
              style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "none", border: "none", color: "#71717a", fontSize: 12, cursor: "pointer", padding: "0 0 16px 0" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#ffffff")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#71717a")}>
              <ArrowLeft size={14} /><span>Back to Overview</span>
            </button>
          )}

          {/* Verified badge */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 13px", borderRadius: 8, marginBottom: 22, backgroundColor: "rgba(16,185,129,0.07)", border: "1px solid rgba(16,185,129,0.22)" }}>
            <CheckCircle2 size={14} color="#10b981" />
            <span style={{ fontSize: 12, color: "#10b981", fontWeight: 500 }}>Human verified &middot; Login form unlocked</span>
          </div>

          <div style={{ marginBottom: 28 }}>
            <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.03em", color: "#ffffff", margin: 0 }}>Welcome back</h1>
            <p style={{ fontSize: 13, color: "#71717a", marginTop: 6, lineHeight: 1.5 }}>Enter your credentials to access the EdgeStore appliance workspace.</p>
          </div>

          {error && (
            <div style={{ padding: "12px 14px", marginBottom: 20, borderRadius: 8, backgroundColor: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", fontSize: 12, display: "flex", alignItems: "center", gap: 10 }}>
              <AlertTriangle size={16} /><span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* Username */}
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#d4d4d8", marginBottom: 6 }}>Operator Username</label>
              <div style={{ position: "relative" }}>
                <User size={15} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "#71717a" }} />
                <input type="text" required value={username} onChange={(e) => setUsername(e.target.value)} placeholder="e.g. admin or operator"
                  style={{ width: "100%", padding: "11px 14px 11px 40px", backgroundColor: "#09090b", border: "1px solid #27272a", borderRadius: 8, color: "#ffffff", fontSize: 13, outline: "none" }}
                  onFocus={(e) => (e.target.style.borderColor = "#71717a")}
                  onBlur={(e) => (e.target.style.borderColor = "#27272a")} />
              </div>
            </div>

            {/* Password */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <label style={{ fontSize: 12, fontWeight: 500, color: "#d4d4d8" }}>Password</label>
                <span style={{ fontSize: 11, color: "#52525b" }}>argon2id / bcrypt</span>
              </div>
              <div style={{ position: "relative" }}>
                <Lock size={15} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "#71717a" }} />
                <input type={showPassword ? "text" : "password"} required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="������������"
                  style={{ width: "100%", padding: "11px 42px 11px 40px", backgroundColor: "#09090b", border: "1px solid #27272a", borderRadius: 8, color: "#ffffff", fontSize: 13, outline: "none" }}
                  onFocus={(e) => (e.target.style.borderColor = "#71717a")}
                  onBlur={(e) => (e.target.style.borderColor = "#27272a")} />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "#71717a", cursor: "pointer", padding: 4 }}>
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Remember me */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12, color: "#a1a1aa", cursor: "pointer", userSelect: "none" }} onClick={() => setRememberMe(!rememberMe)}>
                <div style={{ width: 16, height: 16, borderRadius: 4, backgroundColor: rememberMe ? "#ffffff" : "#18181b", border: rememberMe ? "1px solid #ffffff" : "1px solid #27272a", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.15s ease" }}>
                  {rememberMe && <Check size={12} color="#000000" strokeWidth={3} />}
                </div>
                <span>Remember this appliance session</span>
              </label>
              <span style={{ fontSize: 11, color: "#71717a" }}>TLS 1.3</span>
            </div>

            {/* Submit */}
            <button type="submit" disabled={submitting}
              style={{ width: "100%", padding: "12px 0", backgroundColor: "#ffffff", color: "#000000", fontWeight: 600, fontSize: 13, borderRadius: 8, border: "none", cursor: submitting ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, boxShadow: "0 0 20px rgba(255,255,255,0.08)", opacity: submitting ? 0.7 : 1, transition: "background-color 0.2s ease" }}
              onMouseEnter={(e) => { if (!submitting) e.currentTarget.style.backgroundColor = "#e4e4e7"; }}
              onMouseLeave={(e) => { if (!submitting) e.currentTarget.style.backgroundColor = "#ffffff"; }}>
              <span>{submitting ? "Authenticating Session..." : "Access Workspace"}</span>
              <ArrowRight size={14} />
            </button>
          </form>

          {/* Default credentials */}
          <div style={{ marginTop: 24, padding: "16px 18px", backgroundColor: "#09090b", border: "1px solid #18181b", borderRadius: 10 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "#71717a", marginBottom: 12, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>Default Credentials (One-Click Fill)</span>
              <Server size={13} color="#52525b" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { label: "Super Administrator", u: "admin", p: "AdminEdgeStore2026!" },
                { label: "Storage Operator", u: "operator", p: "OperatorEdgeStore2026!" },
                { label: "Project Reviewer (Guest)", u: "guest", p: "GuestEdgeStore2026!" },
              ].map(({ label, u, p }) => (
                <div key={u} onClick={() => handleFillCredentials(u, p)}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", borderRadius: 6, backgroundColor: "#121215", border: "1px solid #1f1f23", cursor: "pointer", transition: "border-color 0.15s ease" }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#3f3f46")}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1f1f23")}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#ffffff" }}>{label}</div>
                    <div style={{ fontSize: 11, color: "#71717a", fontFamily: "monospace" }}>{u} / {p}</div>
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 500, color: "#ffffff", backgroundColor: "#27272a", padding: "3px 8px", borderRadius: 4 }}>Auto-Fill</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 20, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontSize: 11, color: "#52525b" }}>
            <Key size={13} color="#71717a" />
            <span>Hardware Token Security: Key-SD and LUKS2 Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}

