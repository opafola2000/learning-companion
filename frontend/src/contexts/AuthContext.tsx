import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getMe } from "../api/auth";
import {
  clearAuthTokens,
  getAccessToken,
  storeAuthTokens,
} from "../utils/authStorage";

interface User {
  id: number;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  setTokens: (access: string, refresh: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  setTokens: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const data = await getMe();
      setUser(data);
    } catch {
      clearAuthTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const setTokens = useCallback(
    (access: string, refresh: string) => {
      storeAuthTokens(access, refresh);
      setLoading(true);
      fetchUser();
    },
    [fetchUser]
  );

  const logout = useCallback(() => {
    clearAuthTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, setTokens, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
