import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { Role } from "../api/types";

export function ProtectedRoute({ children, allowedRoles }: { children: ReactNode; allowedRoles?: Role[] }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="loading-text">Loading…</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="empty-state">
        <h3>Not authorized</h3>
        <p>Your role ({user.role.toLowerCase()}) doesn't have access to this page.</p>
      </div>
    );
  }

  return <>{children}</>;
}
