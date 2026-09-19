import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { surveysApi, usersApi } from "../../api/services";
import type { Question, SurveyDetail, UserAccount } from "../../api/types";
import { QuestionEditor } from "../../components/QuestionEditor";
import { extractErrorMessage } from "../../api/client";
import { StatusBadge } from "../../components/StatusBadge";
import { useAuth } from "../../context/AuthContext";

function blankQuestion(orderIndex: number): Question {
  return {
    code: "",
    label: "",
    type: "SHORT_TEXT",
    order_index: orderIndex,
    is_required: false,
    choices: [],
  };
}

export function SurveyBuilderPage() {
  const { surveyId } = useParams();
  const isNew = !surveyId || surveyId === "new";
  const navigate = useNavigate();
  const { user } = useAuth();
  const canEdit = user?.role === "ADMINISTRATOR" || user?.role === "SUPERVISOR";

  const [survey, setSurvey] = useState<SurveyDetail | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [enumerators, setEnumerators] = useState<UserAccount[]>([]);
  const [assignedIds, setAssignedIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(!isNew);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canEdit) return;
    usersApi
      .list()
      .then((all) => setEnumerators(all.filter((u) => u.role === "ENUMERATOR" && u.is_active)))
      .catch(() => setEnumerators([]));
  }, [canEdit]);

  useEffect(() => {
    if (isNew) return;
    (async () => {
      const data = await surveysApi.get(surveyId!);
      setSurvey(data);
      setTitle(data.title);
      setDescription(data.description ?? "");
      setQuestions(data.questions.length > 0 ? data.questions : [blankQuestion(1)]);
      setAssignedIds(data.assigned_enumerator_ids ?? []);
      setIsLoading(false);
    })();
  }, [surveyId, isNew]);

  useEffect(() => {
    if (isNew && questions.length === 0) {
      setQuestions([blankQuestion(1)]);
    }
  }, [isNew, questions.length]);

  function toggleEnumerator(id: string) {
    setAssignedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function updateQuestion(index: number, next: Question) {
    setQuestions((prev) => prev.map((q, i) => (i === index ? next : q)));
  }

  function removeQuestion(index: number) {
    setQuestions((prev) => prev.filter((_, i) => i !== index));
  }

  function moveQuestion(index: number, direction: -1 | 1) {
    setQuestions((prev) => {
      const next = [...prev];
      const target = index + direction;
      if (target < 0 || target >= next.length) return prev;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function addQuestion() {
    setQuestions((prev) => [...prev, blankQuestion(prev.length + 1)]);
  }

  function validateBeforeSave(): string | null {
    if (!title.trim()) return "Give the survey a title.";
    if (questions.length === 0) return "Add at least one question.";
    const codes = new Set<string>();
    for (const q of questions) {
      if (!q.code.trim()) return "Every question needs a field code.";
      if (!q.label.trim()) return `Question "${q.code}" needs a label.`;
      if (codes.has(q.code)) return `Field code "${q.code}" is used more than once.`;
      codes.add(q.code);
    }
    return null;
  }

  async function handleSave() {
    const validationError = validateBeforeSave();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setIsSaving(true);

    const orderedQuestions = questions.map((q, i) => ({ ...q, order_index: i + 1 }));

    try {
      if (isNew) {
        const created = await surveysApi.create({
          title,
          description,
          questions: orderedQuestions,
          assigned_enumerator_ids: assignedIds,
        });
        navigate(`/surveys/${created.id}`);
      } else {
        const updated = await surveysApi.update(surveyId!, {
          title,
          description,
          questions: orderedQuestions,
          assigned_enumerator_ids: assignedIds,
        });
        setSurvey(updated);
        setQuestions(updated.questions);
        setAssignedIds(updated.assigned_enumerator_ids ?? []);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePublish() {
    if (!survey) return;
    setError(null);
    try {
      const updated = await surveysApi.publish(survey.id);
      setSurvey(updated);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  if (isLoading) {
    return <p className="loading-text">Loading survey…</p>;
  }

  if (!canEdit && !isNew) {
    return (
      <div>
        <div className="page-header">
          <div>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          {survey && <StatusBadge status={survey.status} />}
        </div>
        <h2>Questions</h2>
        <table className="registry-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Label</th>
              <th>Type</th>
              <th>Required</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((q, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td>{q.label}</td>
                <td>{q.type}</td>
                <td>{q.is_required ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{isNew ? "New survey" : title || "Edit survey"}</h1>
          <p>
            {isNew
              ? "Define the questions your enumerators will fill in the field."
              : "Editing questions creates a new version — past submissions stay tied to the version they were collected with."}
          </p>
        </div>
        {survey && (
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <StatusBadge status={survey.status} />
            <span className="mono">v{survey.current_version_number}</span>
            {survey.status !== "PUBLISHED" && survey.status !== "ARCHIVED" && (
              <button className="btn btn-secondary" onClick={handlePublish}>
                Publish
              </button>
            )}
          </div>
        )}
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="field">
          <label>Survey title</label>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Household Survey 2026" />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>Description (optional)</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 24 }}>
        <label style={{ display: "block", marginBottom: 8 }}>Who can collect this survey</label>
        <p style={{ marginTop: 0, color: "var(--muted, #6b7280)" }}>
          Leave everyone unchecked to keep this survey open to every enumerator. Check specific people to restrict it
          to only them.
        </p>
        {enumerators.length === 0 ? (
          <p className="loading-text">No enumerator accounts yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {enumerators.map((u) => (
              <label key={u.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input type="checkbox" checked={assignedIds.includes(u.id)} onChange={() => toggleEnumerator(u.id)} />
                {u.full_name} <span style={{ color: "var(--muted, #6b7280)" }}>({u.email})</span>
              </label>
            ))}
          </div>
        )}
      </div>

      <h2>Questions</h2>
      {questions.map((q, i) => (
        <QuestionEditor
          key={i}
          question={q}
          index={i}
          total={questions.length}
          otherQuestions={questions.filter((_, oi) => oi !== i)}
          onChange={(next) => updateQuestion(i, next)}
          onRemove={() => removeQuestion(i)}
          onMoveUp={() => moveQuestion(i, -1)}
          onMoveDown={() => moveQuestion(i, 1)}
        />
      ))}

      <button type="button" className="btn btn-secondary" onClick={addQuestion} style={{ marginBottom: 32 }}>
        Add question
      </button>

      <div>
        <button type="button" className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Saving…" : isNew ? "Create survey" : "Save changes"}
        </button>
      </div>
    </div>
  );
}
