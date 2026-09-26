import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { authApi } from "../../api/services";
import { extractErrorMessage } from "../../api/client";
import type { PasswordResetRequestItem } from "../../api/types";

export function PasswordResetRequestsPage() {
  const [requests, setRequests] = useState<PasswordResetRequestItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function reload() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await authApi.listPasswordResetRequests("PENDING");
      setRequests(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, []);

  function openResolveForm(requestId: string) {
    setNotice(null);
    setError(null);
    setActiveRequestId(requestId);
    setNewPassword("");
    setShowPassword(false);
  }

  function closeResolveForm() {
    setActiveRequestId(null);
    setNewPassword("");
  }

  async function handleResolve(e: FormEvent) {
    e.preventDefault();
    if (!activeRequestId) return;

    setError(null);
    setIsSubmitting(true);

    try {
      const request = requests.find((r) => r.id === activeRequestId);
      await authApi.resolvePasswordResetRequest(activeRequestId, newPassword);
      setNotice(
        `Sabon password an saita wa ${request?.user_full_name ?? "user"} (${
          request?.user_email ?? ""
        }). Ka aika masa: ${newPassword}`
      );
      closeResolveForm();
      await reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Password reset requests</h1>
          <p>
            When someone taps "Forgot password", their request shows up
            here. Set a new password and pass it on to them yourself
            (phone call, WhatsApp, in person, etc).
          </p>
        </div>
      </div>

      {notice && <div className="form-success">{notice}</div>}
      {error && <div className="form-error">{error}</div>}

      {isLoading ? (
        <p className="loading-text">Loading…</p>
      ) : requests.length === 0 ? (
        <div className="empty-state">
          <h3>No pending requests</h3>
          <p>Nobody is currently waiting on a password reset.</p>
        </div>
      ) : (
        <table className="registry-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Requested</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id}>
                <td>{r.user_full_name}</td>
                <td>{r.user_email}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>
                  {activeRequestId === r.id ? (
                    <button
                      className="btn btn-secondary btn-icon"
                      onClick={closeResolveForm}
                    >
                      Cancel
                    </button>
                  ) : (
                    <button
                      className="btn btn-primary btn-icon"
                      onClick={() => openResolveForm(r.id)}
                    >
                      Set new password
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {activeRequestId && (
        <form onSubmit={handleResolve} className="panel" style={{ marginTop: 24 }}>
          <div className="field">
            <label htmlFor="newPassword">New password</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                id="newPassword"
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
                maxLength={128}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                style={{ flex: 1 }}
              />
              <button
                type="button"
                className="btn btn-secondary btn-icon"
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? "Saving…" : "Save password & resolve request"}
          </button>
        </form>
      )}
    </div>
  );
}
