import { Outlet, Navigate, Route, Routes, Link, useLocation } from "react-router-dom";

import { useAuth } from "./hooks/useAuth";
import DashboardPage from "./pages/DashboardPage";
import FilesPage from "./pages/FilesPage";
import LoginPage from "./pages/LoginPage";
import ProductsPage from "./pages/ProductsPage";
import PurchasesPage from "./pages/PurchasesPage";

const RequireAuth = () => {
  const { token } = useAuth();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
};

const AdminLayout = () => {
  const location = useLocation();
  const { logout } = useAuth();

  const links = [
    { to: "/", label: "Дашборд" },
    { to: "/products", label: "Товары" },
    { to: "/purchases", label: "Покупки" },
    { to: "/files", label: "Файлы" }
  ];

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">OKAK Admin</div>
        <nav>
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={location.pathname === link.to ? "active" : ""}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <button className="logout" onClick={logout}>
          Выйти
        </button>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
};

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="purchases" element={<PurchasesPage />} />
          <Route path="files" element={<FilesPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
