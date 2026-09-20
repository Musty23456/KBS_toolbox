import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { surveysApi } from "../../api/services";
import type { SurveySummary } from "../../api/types";
import { StatusBadge } from "../../components/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { extractErrorMessage } from "../../api/client";

export function SurveyListPage() {
  const { user } = useAuth();
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const canManage = user?.role === "ADMINISTRATOR" || user?.role === "SUPERVISOR";
  const canArchive = user?.role === "ADMINISTRATOR";

  async function reload() {
    setIsLoading(true);
    const data = await surveysApi.list();
    setSurveys(data);
    setIsLoading(false);
  }

  useEffect(() => {
    reload();
  }, []);

  async function handlePublishToggle(survey: SurveySummary) {
    setError(null);
    try {
      if (survey.status === "PUBLISHED") {
        await surveysApi.unpublish(survey.id);
      } else {
        await surveysApi.publish(survey.id);
      }
      await reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleArchive(survey: SurveySummary) {
    if (!window.confirm(`Archive "${survey.title}"? It will no longer sync to field devices.`)) return;
    setError(null);
    try {
      await surveysApi.archive(survey.id);
      await reload();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Surveys</h1>
          <p>Create, publish, and version the forms your enumerators collect data with.</p>
        </div>
        {canManage && (
          <Link to="/surveys/new" className="btn btn-primary">
            New survey
          </Link>
        )}
      </div>

      {error && <div className="form-error">{error}</div>}

      {isLoading ? (
        <p className="loading-text">Loading…</p>
      ) : surveys.length === 0 ? (
        <div className="empty-state">
          <h3>No surveys yet</h3>
          <p>Create your first survey to define the questions enumerators will fill in the field.</p>
          {canManage && (
            <Link to="/surveys/new" className="btn btn-primary">
              Create a survey
            </Link>
          )}
        </div>
      ) : (
        <table className="registry-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Version</th>
              <th>Created</th>
              <th>Fill</th>
              {canManage && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {surveys.map((survey) => (
              <tr key={survey.id}>
                <td>
                  <Link to={`/surveys/${survey.id}`}>{survey.title}</Link>
                  {survey.description && (
                    <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 2 }}>{survey.description}</div>
                  )}
                </td>
                <td>
                  <StatusBadge status={survey.status} />
                </td>
                <td className="mono">v{survey.current_version_number ?? "—"}</td>
                <td>{new Date(survey.created_at).toLocaleDateString()}</td>
                <td>
                  {survey.status === "PUBLISHED" && (
                    <Link to={`/surveys/${survey.id}/fill`} className="btn btn-primary btn-icon">
                      Fill
                    </Link>
                  )}
                </td>
                {canManage && (
                  <td>
                    <div style={{ display: "flex", gap: 6 }}>
                      <Link to={`/surveys/${survey.id}`} className="btn btn-secondary btn-icon" title="Edit">
                        Edit
                      </Link>
                      {survey.status !== "ARCHIVED" && (
                        <button className="btn btn-secondary btn-icon" onClick={() => handlePublishToggle(survey)}>
                          {survey.status === "PUBLISHED" ? "Unpublish" : "Publish"}
                        </button>
                      )}
                      {canArchive && survey.status !== "ARCHIVED" && (
                        <button className="btn btn-danger btn-icon" onClick={() => handleArchive(survey)}>
                          Archive
                        </button>
                      )}
                    </div>
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
