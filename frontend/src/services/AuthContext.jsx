import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiRequest, clearTokens, saveTokens } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      const currentUser = await apiRequest("/auth/me/");
      setUser(currentUser);
      return currentUser;
    } catch {
      clearTokens();
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    loadUser().finally(() => setIsLoading(false));
  }, [loadUser]);

  const login = useCallback(async (credentials) => {
    const data = await apiRequest("/auth/login/", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    saveTokens(data);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback((details) => apiRequest("/auth/register/", {
    method: "POST",
    body: JSON.stringify(details),
  }), []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, login, register, logout, loadUser }),
    [user, isLoading, login, register, logout, loadUser],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
