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

function MainApp() {
  const { user, loading, isGuest, hasPermission } = useAuth();
  const [currentTab, setCurrentTab] = useState("dashboard");
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    if (isGuest) {
      setCurrentTab("guest_files");
    } else {
      setCurrentTab("dashboard");
    }
  }, [user?.role]);

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

  if (!user) {
    if (showLogin) {
      return <Login onBackToLanding={() => setShowLogin(false)} />;
    }
    return <HeroLanding onGetStarted={() => setShowLogin(true)} />;
  }

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
      <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <div className="app-main">
        <TopBar currentTab={currentTab} />
        <main className="app-content">{renderContent()}</main>
      </div>
      {showSimulationDrawer && <SimulationDrawer />}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <HardwareProvider>
          <MainApp />
        </HardwareProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
