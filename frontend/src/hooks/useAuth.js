import { createContext, createElement, useContext, useEffect, useMemo, useState } from "react";

import api from "../api/axios.js";

const AuthContext = createContext(null);

function readStoredUser() {
  const raw = localStorage.getItem("healthcare_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem("healthcare_user");
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);
  const [token, setToken] = useState(localStorage.getItem("healthcare_token"));
  const [isLoading, setIsLoading] = useState(Boolean(token));

  useEffect(() => {
    let isMounted = true;

    async function loadUser() {
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const { data } = await api.get("/auth/me");
        if (isMounted) {
          setUser(data);
          localStorage.setItem("healthcare_user", JSON.stringify(data));
        }
      } catch {
        if (isMounted) {
          setUser(null);
          setToken(null);
          localStorage.removeItem("healthcare_token");
          localStorage.removeItem("healthcare_user");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadUser();
    return () => {
      isMounted = false;
    };
  }, [token]);

  async function authenticate(endpoint, payload) {
    const { data } = await api.post(endpoint, payload);
    localStorage.setItem("healthcare_token", data.access_token);
    localStorage.setItem("healthcare_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(user && token),
      login: (payload) => authenticate("/auth/login", payload),
      register: (payload) => authenticate("/auth/register", payload),
      logout: () => {
        localStorage.removeItem("healthcare_token");
        localStorage.removeItem("healthcare_user");
        setUser(null);
        setToken(null);
      },
    }),
    [user, token, isLoading]
  );

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
