import React, { useState, useEffect } from "react";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { HardwareProvider } from "./context/HardwareContext";
import { Sidebar } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { SimulationDrawer } from "./components/layout/SimulationDrawer";

import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { FileManager } from "./pages/FileManager";
import { StorageView } from "./pages/StorageView";
import { ReplicationView } from "./pages/ReplicationView";
import { SecurityView } from "./pages/SecurityView";
import { SystemView } from "./pages/SystemView";
import { AdminView } from "./pages/AdminView";
import { RolesPermissionsView } from "./pages/RolesPermissionsView";
import { SessionsView } from "./pages/SessionsView";
import { ProfileView } from "./pages/ProfileView";
import { GuestView } from "./pages/GuestView";
import { HeroLanding } from "./pages/HeroLanding";
import { ArrowRight, AlertTriangle, RefreshCw } from "lucide-react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("EdgeStore UI Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#020204",
            color: "#ffffff",
            padding: 24,
            fontFamily: "'Inter', sans-serif",
            textAlign: "center",
          }}
        >
          <div
            style={{
              padding: 16,
              borderRadius: 16,
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              color: "#f87171",
              marginBottom: 16,
            }}
          >
            <AlertTriangle size={32} />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>EdgeStore UI Encountered an Issue</h2>
          <p style={{ fontSize: 13, color: "#94a3b8", maxWidth: 450, marginBottom: 20 }}>
            {this.state.error?.message || "An unexpected error occurred while rendering the console interface."}
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.hash = "#hero";
                window.location.reload();
              }}
              style={{
                padding: "8px 16px",
                borderRadius: 8,
                backgroundColor: "#ffffff",
                color: "#000000",
                fontWeight: 600,
                fontSize: 12,
                border: "none",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <RefreshCw size={13} />
              <span>Reload Appliance Console</span>
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function MainApp() {
  const { user, loading, isGuest, hasPermission } = useAuth();
  const [currentTab, setCurrentTab] = useState("dashboard");

  // Determine active view mode: "hero" | "login" | "app"
  const [viewMode, setViewMode] = useState(() => {
    const h = window.location.hash;
    if (h === "#login") return "login";
    if (h === "#hero") return "hero";
    return null; // dynamic based on auth
  });

  // Listen to browser hash changes
  useEffect(() => {
    const handleHashChange = () => {
      const h = window.location.hash;
      if (h === "#login") {
        setViewMode("login");
      } else if (h === "#hero") {
        setViewMode("hero");
      } else if (h === "#app") {
        setViewMode("app");
      }
    };
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    if (isGuest) {
      setCurrentTab("guest_files");
    } else {
      setCurrentTab("dashboard");
    }
  }, [user?.role]);

  const goToLogin = () => {
    window.location.hash = "#login";
    setViewMode("login");
  };

  const goToHero = () => {
    window.location.hash = "#hero";
    setViewMode("hero");
  };

  const goToApp = () => {
    window.location.hash = "#app";
    setViewMode("app");
    setCurrentTab(isGuest ? "guest_files" : "dashboard");
  };

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          backgroundColor: "#020204",
          color: "#94a3b8",
          fontFamily: "'Inter', sans-serif",
        }}
      >
        Initializing EdgeStore Appliance...
      </div>
    );
  }

  // 1. Explicit Login view (via Get Started click or #login hash)
  if (viewMode === "login") {
    return <Login onBackToLanding={goToHero} onLoginSuccess={goToApp} />;
  }

  // 2. Unauthenticated default: Show Hero landing
  if (!user) {
    return <HeroLanding user={user} onGetStarted={goToLogin} />;
  }

  // 3. Explicit Hero view when operator is logged in
  if (viewMode === "hero" || currentTab === "hero") {
    return (
      <div style={{ position: "relative", width: "100vw", minHeight: "100vh" }}>
        {/* Floating Return Button for Logged-In Operators */}
        <div style={{ position: "fixed", bottom: 28, right: 28, zIndex: 1000 }}>
          <button
            type="button"
            onClick={goToApp}
            style={{
              padding: "11px 22px",
              backgroundColor: "#ffffff",
              color: "#000000",
              fontWeight: 700,
              fontSize: 13,
              borderRadius: 9999,
              border: "none",
              cursor: "pointer",
              boxShadow: "0 10px 30px rgba(0,0,0,0.8)",
              display: "flex",
              alignItems: "center",
              gap: 8,
              transition: "transform 0.15s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
            onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1.0)")}
          >
            <span>Return to Console</span>
            <ArrowRight size={15} />
          </button>
        </div>
        <HeroLanding user={user} onGetStarted={goToLogin} />
      </div>
    );
  }

  // 4. Authenticated Console Workspace (Dashboard, Files, Storage, etc.)
  const renderContent = () => {
    switch (currentTab) {
      case "dashboard":
        return isGuest ? <GuestView /> : <Dashboard onNavigate={(tab) => setCurrentTab(tab)} />;
      case "files":
        return <FileManager />;
      case "guest_files":
        return <GuestView />;
      case "storage":
        return <StorageView />;
      case "replication":
        return <ReplicationView />;
      case "security":
        return <SecurityView />;
      case "system":
        return <SystemView />;
      case "admin":
        return <AdminView onNavigate={(tab) => setCurrentTab(tab)} />;
      case "roles":
        return <RolesPermissionsView />;
      case "sessions":
        return <SessionsView />;
      case "profile":
        return <ProfileView />;
      default:
        return isGuest ? <GuestView /> : <Dashboard onNavigate={(tab) => setCurrentTab(tab)} />;
    }
  };

  const showSimulationDrawer = !isGuest && hasPermission("hardware.manage");

  return (
    <div className="app-shell">
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          if (tab === "hero") {
            goToHero();
          } else {
            setCurrentTab(tab);
          }
        }}
      />
      <div className="app-main">
        <TopBar
          currentTab={currentTab}
          setCurrentTab={(tab) => {
            if (tab === "hero") {
              goToHero();
            } else {
              setCurrentTab(tab);
            }
          }}
        />
        <main className="app-content">{renderContent()}</main>
      </div>
      {showSimulationDrawer && <SimulationDrawer />}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <HardwareProvider>
            <MainApp />
          </HardwareProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
