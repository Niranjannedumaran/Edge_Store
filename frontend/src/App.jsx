import React, { useState } from "react";
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

function MainApp() {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState("dashboard");

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          color: "var(--text-muted)",
        }}
      >
        Initializing EdgeStore Appliance...
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  const renderContent = () => {
    switch (currentTab) {
      case "dashboard":
        return <Dashboard onNavigate={(tab) => setCurrentTab(tab)} />;
      case "files":
        return <FileManager />;
      case "storage":
        return <StorageView />;
      case "replication":
        return <ReplicationView />;
      case "security":
        return <SecurityView />;
      case "system":
        return <SystemView />;
      case "admin":
        return <AdminView />;
      default:
        return <Dashboard onNavigate={(tab) => setCurrentTab(tab)} />;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />
      <div className="app-main">
        <TopBar currentTab={currentTab} />
        <main className="app-content">{renderContent()}</main>
      </div>
      <SimulationDrawer />
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
