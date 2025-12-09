// src/context/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../services/api";

type User = {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (accessToken: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On app load, try to load user if token is present
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    api
      .get<User>("/auth/me")
      .then((u) => setUser(u))
      .catch(() => {
        // token invalid / expired
        localStorage.removeItem("access_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (accessToken: string) => {
    // 1) save token
    localStorage.setItem("access_token", accessToken);

    // 2) fetch user using that token (api.ts will attach Authorization header)
    const me = await api.get<User>("/auth/me");
    setUser(me);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
    window.location.hash = "#/login"; // or use navigate('/login')
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
