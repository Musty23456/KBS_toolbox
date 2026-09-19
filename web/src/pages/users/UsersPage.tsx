import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { usersApi } from "../../api/services";
import type { Role, UserAccount } from "../../api/types";
import { useAuth } from "../../context/AuthContext";
import { extractErrorMessage } from "../../api/client";

const ROLES: Role[] = ["ADMINISTRATOR", "SUPERVISOR", "ENUMERATOR"];

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const isAdmin = currentUser?.role === "ADMINISTRATOR";

  const [users, setUsers] = useState<UserAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("ENUMERATOR");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function reload() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await usersApi.list();
      setUsers(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }
  useEffect(() => {
    reload();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await usersApi.create({ full_name: fullName, email, password, role });
      setFullName("");
      setEmail("");
      setPassword("");
      setRole("ENUMERATOR");
      setShowForm(false);
      await reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleToggleActive(u: UserAccount) {
    setError(null);
    try {
      if (u.is_active) {
        await usersApi.deactivate(u.id);
      } else {
        await usersApi.update(u.id, { is_active: true });
      }
      await reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleRoleChange(u: UserAccount, newRole: Role) {
    setError(null);
    try {
      await usersApi.update(u.id, { role: newRole });
      await reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Enumerators &amp; staff</h1>
          <p>Manage who can log in to the field app and the admin dashboard.</p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "Add person"}
          </button>
        )}
      </div>

      {error && <div className="form-error">{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} className="panel" style={{ marginBottom: 24 }}>
          <div className="field-row">
            <div className="field">
              <label>Full name</label>
              <input type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div className="field">
              <label>Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label>Temporary password</label>
              <input
                type="text"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="field">
              <label>Role</label>
              <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r.charAt(0) + r.slice(1).toLowerCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? "Adding…" : "Add person"}
          </button>
        </form>
      )}

      {isLoading ? (
        <p className="loading-text">Loading…</p>
      ) : (
        <table className="registry-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              {isAdmin && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td>
                  {isAdmin ? (
                    <select value={u.role} onChange={(e) => handleRoleChange(u, e.target.value as Role)}>
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r.charAt(0) + r.slice(1).toLowerCase()}
                        </option>
                      ))}
                    </select>
                  ) : (
                    u.role.charAt(0) + u.role.slice(1).toLowerCase()
                  )}
                </td>
                <td>{u.is_active ? "Active" : "Deactivated"}</td>
                {isAdmin && (
                  <td>
                    <button
                      className="btn btn-secondary btn-icon"
                      onClick={() => handleToggleActive(u)}
                      disabled={u.id === currentUser?.id}
                    >
                      {u.is_active ? "Deactivate" : "Reactivate"}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
