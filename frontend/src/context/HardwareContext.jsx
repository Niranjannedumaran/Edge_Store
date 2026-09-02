import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiRequest } from "../api/client";
import { useAuth } from "./AuthContext";

const HardwareContext = createContext();

export function HardwareProvider({ children }) {
  const { token } = useAuth();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const data = await apiRequest("/system/health");
      setHealth(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return (
    <HardwareContext.Provider value={{ health, loading, error, refreshHealth: fetchHealth }}>
      {children}
    </HardwareContext.Provider>
  );
}

export function useHardware() {
  return useContext(HardwareContext);
}
