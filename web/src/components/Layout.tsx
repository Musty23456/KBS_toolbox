import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();

  const canManageSurveys = user?.role === "ADMINISTRATOR" || user?.role === "SUPERVISOR";
  const canManageUsers = user?.role === "ADMINISTRATOR" || user?.role === "SUPERVISOR";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="sidebar-brand">
            KBS Toolbox
            <small>Field survey registry</small>
          </div>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
            Overview
          </NavLink>
          <NavLink to="/surveys" className={({ isActive }) => (isActive ? "active" : "")}>
            Surveys
          </NavLink>
          <NavLink to="/submissions" className={({ isActive }) => (isActive ? "active" : "")}>
            Submissions
          </NavLink>
          {canManageSurveys && (
            <NavLink to="/analytics" className={({ isActive }) => (isActive ? "active" : "")}>
              Analytics
            </NavLink>
          )}
          {canManageUsers && (
            <NavLink to="/users" className={({ isActive }) => (isActive ? "active" : "")}>
              Enumerators &amp; staff
            </NavLink>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="who">{user?.full_name}</div>
          <div className="role">{user?.role.toLowerCase()}</div>
          <button onClick={() => logout()}>Log out</button>
        </div>
      </aside>
      <main className="main">
        <Outlet context={{ canManageSurveys, canManageUsers }} />
      </main>
    </div>
  );
}
