import { useEffect, useMemo, useState } from "react";
import { submissionsApi, surveysApi } from "../../api/services";
import type { ReviewStatus, Submission, SubmissionStatus, SurveySummary } from "../../api/types";
import { StatusBadge } from "../../components/StatusBadge";

const STATUS_OPTIONS: SubmissionStatus[] = ["PENDING", "UPLOADING", "UPLOADED", "SYNCED", "FAILED"];
const REVIEW_OPTIONS: ReviewStatus[] = ["RECEIVED", "UNDER_REVIEW", "HAS_ISSUES", "APPROVED", "REJECTED", "RESUBMIT"];

const REVIEW_LABELS: Record<ReviewStatus, string> = {
  RECEIVED: "Received",
  UNDER_REVIEW: "Under review",
  HAS_ISSUES: "Has issues",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  RESUBMIT: "Resubmit",
};

const REVIEW_CLASS: Record<ReviewStatus, string> = {
  RECEIVED: "badge-pending",
  UNDER_REVIEW: "badge-pending",
  HAS_ISSUES: "badge-failed",
  APPROVED: "badge-published",
  REJECTED: "badge-failed",
  RESUBMIT: "badge-failed",
};

function ReviewBadge({ status }: { status: ReviewStatus }) {
  return <span className={`badge ${REVIEW_CLASS[status]}`}>{REVIEW_LABELS[status]}</span>;
}

export function SubmissionsPage() {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [surveyFilter, setSurveyFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [reviewFilter, setReviewFilter] = useState<string>("");
  const [selected, setSelected] = useState<Submission | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>("UNDER_REVIEW");
  const [comment, setComment] = useState("");
  const [savingReview, setSavingReview] = useState(false);
  const [reviewError, setReviewError] = useState("");

  async function loadSubmissions() {
    setIsLoading(true);
    try {
      const data = await submissionsApi.list({
        survey_id: surveyFilter || undefined,
        status: (statusFilter || undefined) as SubmissionStatus | undefined,
      });
      setSubmissions(reviewFilter ? data.filter((s) => s.review_status === reviewFilter) : data);
      if (selected) {
        const refreshed = data.find((s) => s.id === selected.id);
        if (refreshed) setSelected(refreshed);
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    surveysApi.list().then(setSurveys);
  }, []);

  useEffect(() => {
    loadSubmissions();
  }, [surveyFilter, statusFilter, reviewFilter]);

  function surveyTitle(id: string) {
    return surveys.find((s) => s.id === id)?.title ?? id.slice(0, 8);
  }

  async function submitReview() {
    if (!selected) return;
    setSavingReview(true);
    setReviewError("");
    try {
      await submissionsApi.review(selected.id, { status: reviewStatus, comment: comment || undefined });
      setComment("");
      const refreshed = await submissionsApi.get(selected.id);
      setSelected(refreshed);
      await loadSubmissions();
    } catch (error: any) {
      setReviewError(error?.response?.data?.detail ?? "Unable to save review");
    } finally {
      setSavingReview(false);
    }
  }

  const currentReview = useMemo(() => selected?.reviews?.[0], [selected]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Submissions & Review</h1>
          <p>Inspect field responses and move them through the review workflow.</p>
        </div>
      </div>

      <div className="toolbar">
        <select value={surveyFilter} onChange={(e) => setSurveyFilter(e.target.value)}>
          <option value="">All surveys</option>
          {surveys.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All sync statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={reviewFilter} onChange={(e) => setReviewFilter(e.target.value)}>
          <option value="">All review statuses</option>
          {REVIEW_OPTIONS.map((s) => <option key={s} value={s}>{REVIEW_LABELS[s]}</option>)}
        </select>
      </div>

      {isLoading ? <p className="loading-text">Loading…</p> : submissions.length === 0 ? (
        <div className="empty-state"><h3>No submissions match these filters</h3><p>Responses will appear here when enumerators submit or sync forms.</p></div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 430px" : "1fr", gap: 24 }}>
          <table className="registry-table">
            <thead><tr><th>Submission</th><th>Survey</th><th>Sync</th><th>Review</th><th>Collected</th></tr></thead>
            <tbody>
              {submissions.map((s) => (
                <tr key={s.id} onClick={() => { setSelected(s); setReviewStatus(s.review_status === "RECEIVED" ? "UNDER_REVIEW" : s.review_status); }} style={{ cursor: "pointer" }}>
                  <td className="mono">{s.id.slice(0, 8)}</td>
                  <td>{surveyTitle(s.survey_id)}</td>
                  <td><StatusBadge status={s.status} /></td>
                  <td><ReviewBadge status={s.review_status} /></td>
                  <td>{s.collected_at ? new Date(s.collected_at).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {selected && (
            <div className="panel">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <h3>Submission detail</h3>
                <button className="btn btn-icon" onClick={() => setSelected(null)}>Close</button>
              </div>
              <p className="mono" style={{ fontSize: 12 }}>{selected.id}</p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}><StatusBadge status={selected.status} /><ReviewBadge status={selected.review_status} /></div>
              {selected.gps_latitude != null && <p style={{ marginTop: 12 }}>GPS: {selected.gps_latitude.toFixed(5)}, {selected.gps_longitude?.toFixed(5)}</p>}

              <h3 style={{ marginTop: 20 }}>Review</h3>
              {currentReview && <div className="panel" style={{ marginBottom: 12 }}><ReviewBadge status={currentReview.status} /><p>{currentReview.comment || "No comment"}</p><small>{new Date(currentReview.created_at).toLocaleString()}</small></div>}
              <select value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value as ReviewStatus)} style={{ width: "100%" }}>
                {REVIEW_OPTIONS.map((s) => <option key={s} value={s}>{REVIEW_LABELS[s]}</option>)}
              </select>
              <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Reviewer comment (required for resubmission)" rows={4} style={{ width: "100%", marginTop: 10 }} />
              {reviewError && <p style={{ color: "crimson" }}>{reviewError}</p>}
              <button className="btn btn-primary" disabled={savingReview} onClick={submitReview} style={{ marginTop: 10 }}>{savingReview ? "Saving…" : "Save review"}</button>

              <h3 style={{ marginTop: 20 }}>Answers</h3>
              <table className="registry-table"><tbody>{selected.answers.map((a) => <tr key={a.id}><td className="mono">{a.question_id.slice(0, 8)}{a.group_instance_index != null ? ` #${a.group_instance_index + 1}` : ""}</td><td>{a.value_text ?? a.media_reference ?? "—"}</td></tr>)}</tbody></table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
