import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { submissionsApi, surveysApi } from "../../api/services";
import type { Question, SurveyDetail } from "../../api/types";
import { extractErrorMessage } from "../../api/client";

// Question types the web form can capture directly. Photo/audio/signature/
// barcode need device camera/mic access that this simple web form doesn't
// attempt to replicate — those stay Android-only for now.
const UNSUPPORTED_TYPES = new Set(["PHOTO", "AUDIO", "SIGNATURE", "BARCODE"]);

function inputForType(question: Question, value: string, onChange: (v: string) => void) {
  switch (question.type) {
    case "LONG_TEXT":
      return <textarea value={value} onChange={(e) => onChange(e.target.value)} />;
    case "INTEGER":
      return <input type="number" step="1" value={value} onChange={(e) => onChange(e.target.value)} />;
    case "DECIMAL":
      return <input type="number" step="any" value={value} onChange={(e) => onChange(e.target.value)} />;
    case "DATE":
      return <input type="date" value={value} onChange={(e) => onChange(e.target.value)} />;
    case "TIME":
      return <input type="time" value={value} onChange={(e) => onChange(e.target.value)} />;
    case "DATETIME":
      return <input type="datetime-local" value={value} onChange={(e) => onChange(e.target.value)} />;
    case "YES_NO":
      return (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">Select…</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>
      );
    case "SINGLE_CHOICE":
    case "DROPDOWN":
      return (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">Select…</option>
          {question.choices.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      );
    default:
      return <input type="text" value={value} onChange={(e) => onChange(e.target.value)} />;
  }
}

export function FillSurveyPage() {
  const { surveyId } = useParams();
  const navigate = useNavigate();
  const [survey, setSurvey] = useState<SurveyDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [multiAnswers, setMultiAnswers] = useState<Record<string, string[]>>({});
  const [gpsCapture, setGpsCapture] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    (async () => {
      const data = await surveysApi.get(surveyId!);
      setSurvey(data);
      setIsLoading(false);
    })();
  }, [surveyId]);

  function setAnswer(questionId: string, value: string) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  function toggleMultiAnswer(questionId: string, value: string) {
    setMultiAnswers((prev) => {
      const current = prev[questionId] ?? [];
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
      return { ...prev, [questionId]: next };
    });
  }

  function captureGps(questionId: string) {
    if (!navigator.geolocation) {
      setError("This browser doesn't support location capture.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const text = `${pos.coords.latitude.toFixed(6)},${pos.coords.longitude.toFixed(6)}`;
        setGpsCapture((prev) => ({ ...prev, [questionId]: text }));
      },
      () => setError("Couldn't get your location — check location permission for this site.")
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!survey || !survey.current_version_id) return;
    setError(null);

    const missingRequired = survey.questions.find((q) => {
      if (!q.is_required) return false;
      if (q.type === "MULTIPLE_CHOICE") return (multiAnswers[q.id ?? ""] ?? []).length === 0;
      if (q.type === "GPS") return !gpsCapture[q.id ?? ""];
      if (UNSUPPORTED_TYPES.has(q.type)) return true; // can never be answered here
      return !answers[q.id ?? ""];
    });
    if (missingRequired) {
      setError(
        UNSUPPORTED_TYPES.has(missingRequired.type)
          ? `"${missingRequired.label}" requires the Android app (photo/audio/signature/barcode capture isn't available on the web yet) — this survey can't be fully completed here.`
          : `"${missingRequired.label}" is required.`
      );
      return;
    }

    const answerPayload = survey.questions
      .filter((q) => !UNSUPPORTED_TYPES.has(q.type))
      .map((q) => {
        const id = q.id ?? "";
        let value_text: string | null = null;
        if (q.type === "MULTIPLE_CHOICE") {
          const picked = multiAnswers[id] ?? [];
          value_text = picked.length > 0 ? JSON.stringify(picked) : null;
        } else if (q.type === "GPS") {
          value_text = gpsCapture[id] ?? null;
        } else {
          value_text = answers[id] || null;
        }
        return { question_id: id, value_text };
      })
      .filter((a) => a.value_text !== null);

    setIsSubmitting(true);
    try {
      await submissionsApi.create({
        client_submission_uuid: crypto.randomUUID(),
        survey_id: survey.id,
        survey_version_id: survey.current_version_id,
        collected_at: new Date().toISOString(),
        answers: answerPayload,
      });
      setSubmitted(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) return <p className="loading-text">Loading survey…</p>;
  if (!survey) return <p className="loading-text">Survey not found.</p>;

  if (submitted) {
    return (
      <div className="empty-state">
        <h3>Submitted — thank you!</h3>
        <p>Your response to "{survey.title}" has been recorded.</p>
        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>
            Fill another response
          </button>
          <Link to="/surveys" className="btn btn-secondary">
            Back to surveys
          </Link>
        </div>
      </div>
    );
  }

  if (survey.status !== "PUBLISHED") {
    return (
      <div className="empty-state">
        <h3>This survey isn't published</h3>
        <p>Only published surveys can be filled in.</p>
        <Link to="/surveys" className="btn btn-secondary">
          Back to surveys
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{survey.title}</h1>
          {survey.description && <p>{survey.description}</p>}
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      <form onSubmit={handleSubmit}>
        {survey.questions.map((q) => {
          const id = q.id ?? "";
          const isUnsupported = UNSUPPORTED_TYPES.has(q.type);
          return (
            <div className="field" key={id}>
              <label>
                {q.label}
                {q.is_required && " *"}
              </label>
              {q.hint && <p style={{ marginTop: -6, color: "var(--muted, #6b7280)", fontSize: 13 }}>{q.hint}</p>}

              {isUnsupported ? (
                <p style={{ color: "var(--muted, #6b7280)", fontStyle: "italic" }}>
                  This question needs the Android app (photo/audio/signature/barcode capture isn't supported on the
                  web yet).
                </p>
              ) : q.type === "MULTIPLE_CHOICE" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {q.choices.map((c) => (
                    <label key={c.value} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <input
                        type="checkbox"
                        checked={(multiAnswers[id] ?? []).includes(c.value)}
                        onChange={() => toggleMultiAnswer(id, c.value)}
                      />
                      {c.label}
                    </label>
                  ))}
                </div>
              ) : q.type === "GPS" ? (
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <button type="button" className="btn btn-secondary" onClick={() => captureGps(id)}>
                    Get current location
                  </button>
                  {gpsCapture[id] && <span className="mono">{gpsCapture[id]}</span>}
                </div>
              ) : (
                inputForType(q, answers[id] ?? "", (v) => setAnswer(id, v))
              )}
            </div>
          );
        })}

        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? "Submitting…" : "Submit"}
        </button>
      </form>
    </div>
  );
}
