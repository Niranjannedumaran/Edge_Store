import React, { createContext, useContext, useState, useEffect } from "react";
import { apiRequest } from "../api/client";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("edgestore_user");
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem("edgestore_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkMe = async () => {
      if (token) {
        try {
          const profile = await apiRequest("/auth/me");
          setUser(profile);
          localStorage.setItem("edgestore_user", JSON.stringify(profile));
        } catch {
          logout();
        }
      }
      setLoading(false);
    };

    checkMe();

    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener("edgestore:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("edgestore:unauthorized", handleUnauthorized);
  }, [token]);

  const login = async (username, password) => {
    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: { username, password },
    });
    localStorage.setItem("edgestore_token", data.access_token);
    localStorage.setItem("edgestore_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    if (token) {
      apiRequest("/auth/logout", { method: "POST" }).catch(() => {});
    }
    localStorage.removeItem("edgestore_token");
    localStorage.removeItem("edgestore_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
