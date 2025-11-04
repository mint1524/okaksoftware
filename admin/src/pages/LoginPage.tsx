import { FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

const LoginPage = () => {
  const { login, token, loading, error } = useAuth();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const location = useLocation();

  useEffect(() => {
    setMessage(error);
  }, [error]);

  if (token) {
    const redirectTo = (location.state as { from?: Location })?.from?.pathname || "/";
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!password) {
      setMessage("Введите пароль");
      return;
    }
    try {
      await login(password);
    } catch {
      // error already handled in context
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Админ-панель</h1>
        <p>Введите пароль для доступа.</p>
        {message && <div className="alert">{message}</div>}
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
            if (message) setMessage(null);
          }}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Вход..." : "Войти"}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
