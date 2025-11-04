import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

import { login as apiLogin, setAuthToken } from "../api/client";

interface AuthContextValue {
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "okak_admin_token";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setToken(stored);
      setAuthToken(stored);
    }
  }, []);

  const handleLogin = async (password: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiLogin(password);
      setError(null);
      setToken(response.access_token);
      setAuthToken(response.access_token);
      localStorage.setItem(STORAGE_KEY, response.access_token);
    } catch (err) {
      console.error(err);
      setError("Неверный пароль или доступ запрещен");
      setToken(null);
      setAuthToken(null);
      localStorage.removeItem(STORAGE_KEY);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setAuthToken(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  const value = useMemo(
    () => ({ token, loading, error, login: handleLogin, logout: handleLogout }),
    [token, loading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
};
