import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiRequest, clearTokens, hasAccessToken, saveTokens } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  const loadUser = useCallback(async () => {
    if (!hasAccessToken()) { setUser(null); setAuthError(null); return null; }
    try {
      const currentUser = await apiRequest("/auth/me/");
      setUser(currentUser);
      setAuthError(null);
      return currentUser;
    } catch (error) {
      if (error?.status === 401) clearTokens();
      if (error?.status === 401) setUser(null);
      setAuthError(error);
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
    setAuthError(null);
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
    () => ({ user, isLoading, authError, login, register, logout, loadUser }),
    [user, isLoading, authError, login, register, logout, loadUser],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
