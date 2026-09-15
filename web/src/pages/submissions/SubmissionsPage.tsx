import { useEffect, useState } from "react";
import { submissionsApi, surveysApi } from "../../api/services";
import type { Submission, SubmissionStatus, SurveySummary } from "../../api/types";
import { StatusBadge } from "../../components/StatusBadge";

const STATUS_OPTIONS: SubmissionStatus[] = ["PENDING", "UPLOADING", "UPLOADED", "SYNCED", "FAILED"];

export function SubmissionsPage() {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [surveyFilter, setSurveyFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selected, setSelected] = useState<Submission | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    surveysApi.list().then(setSurveys);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    submissionsApi
      .list({
        survey_id: surveyFilter || undefined,
        status: (statusFilter || undefined) as SubmissionStatus | undefined,
      })
      .then((data) => {
        setSubmissions(data);
        setIsLoading(false);
      });
  }, [surveyFilter, statusFilter]);

  function surveyTitle(id: string) {
    return surveys.find((s) => s.id === id)?.title ?? id.slice(0, 8);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Submissions</h1>
          <p>Every response collected in the field, whether entered live or synced from an offline device.</p>
        </div>
      </div>

      <div className="toolbar">
        <select value={surveyFilter} onChange={(e) => setSurveyFilter(e.target.value)}>
          <option value="">All surveys</option>
          {surveys.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="loading-text">Loading…</p>
      ) : submissions.length === 0 ? (
        <div className="empty-state">
          <h3>No submissions match these filters</h3>
          <p>Once enumerators submit forms — online or synced from offline — they'll appear here.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 380px" : "1fr", gap: 24 }}>
          <table className="registry-table">
            <thead>
              <tr>
                <th>Submission</th>
                <th>Survey</th>
                <th>Status</th>
                <th>Collected</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((s) => (
                <tr key={s.id} onClick={() => setSelected(s)} style={{ cursor: "pointer" }}>
                  <td className="mono">{s.id.slice(0, 8)}</td>
                  <td>{surveyTitle(s.survey_id)}</td>
                  <td>
                    <StatusBadge status={s.status} />
                  </td>
                  <td>{s.collected_at ? new Date(s.collected_at).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {selected && (
            <div className="panel">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <h3>Submission detail</h3>
                <button className="btn btn-icon" onClick={() => setSelected(null)}>
                  Close
                </button>
              </div>
              <p className="mono" style={{ fontSize: 12 }}>
                {selected.id}
              </p>
              <StatusBadge status={selected.status} />
              {selected.gps_latitude != null && (
                <p style={{ marginTop: 12 }}>
                  GPS: {selected.gps_latitude.toFixed(5)}, {selected.gps_longitude?.toFixed(5)}
                </p>
              )}
              <h3 style={{ marginTop: 20 }}>Answers</h3>
              <table className="registry-table">
                <tbody>
                  {selected.answers.map((a) => (
                    <tr key={a.id}>
                      <td className="mono">{a.question_id.slice(0, 8)}</td>
                      <td>{a.value_text ?? a.media_reference ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
