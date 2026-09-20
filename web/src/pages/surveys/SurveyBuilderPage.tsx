import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { surveysApi, usersApi } from "../../api/services";
import type { Question, QuestionGroup, SurveyDetail, SurveySection, UserAccount } from "../../api/types";
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
  const [sections, setSections] = useState<SurveySection[]>([{ title: "Section 1", description: "", order_index: 1 }]);
  const [groups, setGroups] = useState<QuestionGroup[]>([]);
  const [enumerators, setEnumerators] = useState<UserAccount[]>([]);
  const [assignedIds, setAssignedIds] = useState<string[]>([]);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [previewValues, setPreviewValues] = useState<Record<string, string | string[]>>({});
  const [history, setHistory] = useState<Question[][]>([]);
  const [future, setFuture] = useState<Question[][]>([]);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
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
      setSections(data.sections?.length ? data.sections : [{ title: "Section 1", description: "", order_index: 1 }]);
      setGroups(data.groups ?? []);
      setAssignedIds(data.assigned_enumerator_ids ?? []);
      setIsLoading(false);
    })();
  }, [surveyId, isNew]);

  useEffect(() => {
    if (isNew && questions.length === 0) {
      setQuestions([blankQuestion(1)]);
      setSections([{ title: "Section 1", description: "", order_index: 1 }]);
      setGroups([]);
    }
  }, [isNew, questions.length]);

  function toggleEnumerator(id: string) {
    setAssignedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function commitQuestions(updater: (prev: Question[]) => Question[]) {
    setQuestions((prev) => {
      const next = updater(prev);
      if (next === prev) return prev;
      setHistory((h) => [...h.slice(-19), prev]);
      setFuture([]);
      return next;
    });
  }

  function updateQuestion(index: number, next: Question) {
    commitQuestions((prev) => prev.map((q, i) => (i === index ? next : q)));
  }

  function removeQuestion(index: number) {
    commitQuestions((prev) => prev.filter((_, i) => i !== index));
  }

  function moveQuestion(index: number, direction: -1 | 1) {
    commitQuestions((prev) => {
      const next = [...prev];
      const target = index + direction;
      if (target < 0 || target >= next.length) return prev;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function duplicateQuestion(index: number) {
    commitQuestions((prev) => {
      const source = prev[index];
      const copy: Question = {
        ...source,
        id: undefined,
        code: source.code ? `${source.code}_copy` : "",
        label: source.label ? `${source.label} (copy)` : "",
        choices: source.choices.map((c) => ({ ...c, id: undefined })),
      };
      return [...prev.slice(0, index + 1), copy, ...prev.slice(index + 1)];
    });
  }

  function reorderQuestions(from: number, to: number) {
    commitQuestions((prev) => {
      if (from === to || from < 0 || to < 0 || from >= prev.length || to >= prev.length) return prev;
      const next = [...prev];
      const [item] = next.splice(from, 1);
      next.splice(to, 0, item);
      return next;
    });
  }

  function addQuestion() {
    commitQuestions((prev) => [...prev, { ...blankQuestion(prev.length + 1), section_id: sections[0]?.id }]);
  }

  function addGroup() {
    setGroups((prev) => [...prev, {
      title: `Group ${prev.length + 1}`, description: "", order_index: prev.length + 1,
      section_id: sections[0]?.id ?? `local-0`, repeatable: false, min_repeats: 1, max_repeats: null,
    }]);
  }

  function updateGroup(index: number, patch: Partial<QuestionGroup>) {
    setGroups((prev) => prev.map((g, i) => i === index ? { ...g, ...patch } : g));
  }

  function removeGroup(index: number) {
    const id = groups[index]?.id ?? `local-${index}`;
    setGroups((prev) => prev.filter((_, i) => i !== index));
    commitQuestions((prev) => prev.map(q => q.group_id === id ? { ...q, group_id: null } : q));
  }

  function addSection() {
    setSections((prev) => [...prev, { title: `Section ${prev.length + 1}`, description: "", order_index: prev.length + 1 }]);
  }

  function updateSection(index: number, patch: Partial<SurveySection>) {
    setSections((prev) => prev.map((section, i) => i === index ? { ...section, ...patch } : section));
  }

  function undo() {
    setHistory((h) => {
      if (!h.length) return h;
      const previous = h[h.length - 1];
      setFuture((f) => [questions, ...f].slice(0, 20));
      setQuestions(previous);
      return h.slice(0, -1);
    });
  }

  function redo() {
    setFuture((f) => {
      if (!f.length) return f;
      const next = f[0];
      setHistory((h) => [...h.slice(-19), questions]);
      setQuestions(next);
      return f.slice(1);
    });
  }

  function setPreviewValue(code: string, value: string | string[]) {
    setPreviewValues((prev) => ({ ...prev, [code]: value }));
  }

  function validateBeforeSave(): string | null {
    if (!title.trim()) return "Give the survey a title.";
    if (questions.length === 0) return "Add at least one question.";
    const codes = new Set<string>();
    for (const g of groups) { if (g.repeatable && g.max_repeats !== null && g.max_repeats !== undefined && g.max_repeats < g.min_repeats) return `Group "${g.title}" has a maximum below its minimum.`; }
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

    const orderedSections = sections.map((section, i) => ({ ...section, order_index: i + 1 }));
    const orderedGroups = groups.map((g, i) => ({ ...g, order_index: i + 1, section_id: g.section_id || orderedSections[0]?.id }));
    const orderedQuestions = questions.map((q, i) => ({ ...q, order_index: i + 1, section_id: q.section_id || orderedSections[0]?.id }));

    try {
      if (isNew) {
        const created = await surveysApi.create({
          title,
          description,
          questions: orderedQuestions,
          sections: orderedSections,
          groups: orderedGroups,
          assigned_enumerator_ids: assignedIds,
        });
        navigate(`/surveys/${created.id}`);
      } else {
        const updated = await surveysApi.update(surveyId!, {
          title,
          description,
          questions: orderedQuestions,
          sections: orderedSections,
          groups: orderedGroups,
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

  function evaluateRelevance(expression: string | null | undefined): boolean {
    if (!expression?.trim()) return true;
    // Preview intentionally supports the same common comparison forms used by the builder.
    // Unsupported expressions remain visible rather than silently hiding a question.
    try {
      const normalized = expression.replace(/\bAND\b/gi, " and ").replace(/\bOR\b/gi, " or ");
      const parts = normalized.split(/\s+(and|or)\s+/i);
      let result: boolean | null = null;
      let pending: "and" | "or" = "and";
      for (const part of parts) {
        if (/^(and|or)$/i.test(part.trim())) { pending = part.trim().toLowerCase() as "and" | "or"; continue; }
        const m = part.trim().match(/^([A-Za-z_][\w]*)\s*(==|!=|>=|<=|>|<|contains)\s*(?:'([^']*)'|\"([^\"]*)\"|(-?\d+(?:\.\d+)?)|(true|false))$/i);
        if (!m) return true;
        const actual = previewValues[m[1]];
        const expected = m[3] ?? m[4] ?? m[5] ?? (m[6] ? m[6].toLowerCase() === "true" : "");
        const left = Array.isArray(actual) ? actual.join(",") : (actual ?? "");
        const a = Number(left), b = Number(expected);
        const numeric = left !== "" && expected !== "" && Number.isFinite(a) && Number.isFinite(b);
        let current = false;
        switch (m[2]) {
          case "==": current = numeric ? a === b : String(left) === String(expected); break;
          case "!=": current = numeric ? a !== b : String(left) !== String(expected); break;
          case ">": current = numeric ? a > b : false; break;
          case ">=": current = numeric ? a >= b : false; break;
          case "<": current = numeric ? a < b : false; break;
          case "<=": current = numeric ? a <= b : false; break;
          case "contains": current = String(left).includes(String(expected)); break;
        }
        result = result === null ? current : pending === "and" ? result && current : result || current;
      }
      return result ?? true;
    } catch { return true; }
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
        <div className="panel" style={{ marginBottom: 24 }}>
        <div className="builder-toolbar" style={{ marginBottom: 12 }}>
          <div><h2 style={{ marginBottom: 4 }}>Sections / Pages</h2><span className="builder-meta">{sections.length} section{sections.length === 1 ? "" : "s"}</span></div>
          <button type="button" className="btn btn-secondary" onClick={addSection}>+ Add section</button>
        </div>
        {sections.map((section, i) => (
          <div key={section.id ?? i} className="section-editor-row">
            <input value={section.title} onChange={(e) => updateSection(i, { title: e.target.value })} placeholder="Section title" />
            <input value={section.description ?? ""} onChange={(e) => updateSection(i, { description: e.target.value })} placeholder="Description (optional)" />
          </div>
        ))}
      </div>

      <div className="builder-toolbar">
        <div>
          <h2 style={{ marginBottom: 4 }}>Questions</h2>
          <span className="builder-meta">{questions.length} question{questions.length === 1 ? "" : "s"}</span>
        </div>
        <div className="question-actions">
          <button type="button" className="btn btn-secondary" onClick={undo} disabled={!history.length}>↶ Undo</button>
          <button type="button" className="btn btn-secondary" onClick={redo} disabled={!future.length}>↷ Redo</button>
          <button type="button" className="btn btn-secondary" onClick={() => { setPreviewValues({}); setIsPreviewOpen(true); }}>👁 Preview</button>
        </div>
      </div>
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

      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="builder-toolbar" style={{ marginBottom: 12 }}>
          <div><h2 style={{ marginBottom: 4 }}>Sections / Pages</h2><span className="builder-meta">{sections.length} section{sections.length === 1 ? "" : "s"}</span></div>
          <button type="button" className="btn btn-secondary" onClick={addSection}>+ Add section</button>
        </div>
        {sections.map((section, i) => (
          <div key={section.id ?? i} className="section-editor-row">
            <input value={section.title} onChange={(e) => updateSection(i, { title: e.target.value })} placeholder="Section title" />
            <input value={section.description ?? ""} onChange={(e) => updateSection(i, { description: e.target.value })} placeholder="Description (optional)" />
          </div>
        ))}
      </div>

      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="builder-toolbar" style={{ marginBottom: 12 }}>
          <div><h2 style={{ marginBottom: 4 }}>Question Groups</h2><span className="builder-meta">{groups.length} group{groups.length === 1 ? "" : "s"}</span></div>
          <button type="button" className="btn btn-secondary" onClick={addGroup}>+ Add group</button>
        </div>
        {groups.map((group, i) => {
          const gid = group.id ?? `local-${i}`;
          return <div key={gid} className="section-editor-row" style={{ alignItems: "center" }}>
            <input value={group.title} onChange={(e) => updateGroup(i, { title: e.target.value })} placeholder="Group title" />
            <input value={group.description ?? ""} onChange={(e) => updateGroup(i, { description: e.target.value })} placeholder="Description (optional)" />
            <label style={{ display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap" }}>
              <input type="checkbox" checked={group.repeatable} onChange={(e) => updateGroup(i, { repeatable: e.target.checked })} /> Repeatable
            </label>
            {group.repeatable && <>
              <input style={{ maxWidth: 80 }} type="number" min={1} value={group.min_repeats} onChange={(e) => updateGroup(i, { min_repeats: Math.max(1, Number(e.target.value) || 1) })} title="Minimum repeats" />
              <input style={{ maxWidth: 90 }} type="number" min={1} value={group.max_repeats ?? ""} onChange={(e) => updateGroup(i, { max_repeats: e.target.value ? Math.max(1, Number(e.target.value)) : null })} placeholder="Max" title="Maximum repeats" />
            </>}
            <button type="button" className="btn btn-danger btn-icon" onClick={() => removeGroup(i)}>Remove</button>
          </div>;
        })}
        {groups.length === 0 && <p className="loading-text">Groups let you keep related questions together. Mark a group repeatable for repeated household/member records.</p>}
      </div>

      <div className="builder-toolbar">
        <div>
          <h2 style={{ marginBottom: 4 }}>Questions</h2>
          <span className="builder-meta">{questions.length} question{questions.length === 1 ? "" : "s"}</span>
        </div>
        <div className="question-actions">
          <button type="button" className="btn btn-secondary" onClick={undo} disabled={!history.length}>↶ Undo</button>
          <button type="button" className="btn btn-secondary" onClick={redo} disabled={!future.length}>↷ Redo</button>
          <button type="button" className="btn btn-secondary" onClick={() => { setPreviewValues({}); setIsPreviewOpen(true); }}>👁 Preview</button>
        </div>
      </div>
      {questions.map((q, i) => (
        <div key={`wrap-${i}`} className="question-section-wrap">
          <label className="section-select-label">Section
            <select value={q.section_id ?? ""} onChange={(e) => updateQuestion(i, { ...q, section_id: e.target.value || null })}>
              <option value="">First section</option>
              {sections.map((section, si) => <option key={section.id ?? si} value={section.id ?? `local-${si}`}>{section.title || `Section ${si + 1}`}</option>)}
            </select>
          </label>
          <label className="section-select-label">Group
            <select value={q.group_id ?? ""} onChange={(e) => updateQuestion(i, { ...q, group_id: e.target.value || null })}>
              <option value="">No group</option>
              {groups.map((group, gi) => <option key={group.id ?? gi} value={group.id ?? `local-${gi}`}>{group.title || `Group ${gi + 1}`}{group.repeatable ? " · repeatable" : ""}</option>)}
            </select>
          </label>
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
          onDuplicate={() => duplicateQuestion(i)}
          draggable
          onDragStart={() => setDragIndex(i)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={() => {
            if (dragIndex !== null) reorderQuestions(dragIndex, i);
            setDragIndex(null);
          }}
        />
        </div>
      ))}

      <button type="button" className="btn btn-secondary" onClick={addQuestion} style={{ marginBottom: 32 }}>
        Add question
      </button>

      <div>
        <button type="button" className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Saving…" : isNew ? "Create survey" : "Save changes"}
        </button>
      </div>

      {isPreviewOpen && (
        <div className="preview-backdrop" role="dialog" aria-modal="true" aria-label="Survey preview">
          <div className="preview-modal">
            <div className="preview-header">
              <div><strong>{title || "Untitled survey"}</strong><span>{description || "Preview mode"}</span></div>
              <button type="button" className="btn btn-icon" onClick={() => setIsPreviewOpen(false)} aria-label="Close preview">✕</button>
            </div>
            <div className="preview-progress">
              <span>Preview</span><span>{questions.length} questions</span>
            </div>
            <div className="preview-body">
              {questions.map((q, i) => {
                if (!evaluateRelevance(q.relevance_expression)) return null;
                const value = previewValues[q.code] ?? (q.type === "MULTIPLE_CHOICE" ? [] : "");
                const set = (v: string | string[]) => setPreviewValue(q.code, v);
                return (
                  <div className="preview-question" key={`${q.code}-${i}`}>
                    <label>{i + 1}. {q.label || "Untitled question"}{q.is_required && <span className="preview-required"> *</span>}</label>
                    {q.hint && <small>{q.hint}</small>}
                    {q.type === "LONG_TEXT" ? <textarea value={String(value)} onChange={(e) => set(e.target.value)} /> :
                    q.type === "SHORT_TEXT" || q.type === "BARCODE" ? <input value={String(value)} onChange={(e) => set(e.target.value)} placeholder={q.type === "BARCODE" ? "Scan or enter value" : "Type your answer"} /> :
                    q.type === "INTEGER" || q.type === "DECIMAL" ? <input type="number" value={String(value)} onChange={(e) => set(e.target.value)} min={q.min_value ?? undefined} max={q.max_value ?? undefined} /> :
                    q.type === "DATE" ? <input type="date" value={String(value)} onChange={(e) => set(e.target.value)} /> :
                    q.type === "TIME" ? <input type="time" value={String(value)} onChange={(e) => set(e.target.value)} /> :
                    q.type === "DATETIME" ? <input type="datetime-local" value={String(value)} onChange={(e) => set(e.target.value)} /> :
                    q.type === "YES_NO" ? <div className="preview-options">{["Yes", "No"].map((x) => <label key={x}><input type="radio" name={q.code} checked={value === x} onChange={() => set(x)} /> {x}</label>)}</div> :
                    q.type === "SINGLE_CHOICE" || q.type === "DROPDOWN" ? <select value={String(value)} onChange={(e) => set(e.target.value)}><option value="">Choose…</option>{q.choices.map((c) => <option key={c.value} value={c.value}>{c.label || c.value}</option>)}</select> :
                    q.type === "MULTIPLE_CHOICE" ? <div className="preview-options">{q.choices.map((c) => { const values = Array.isArray(value) ? value : []; return <label key={c.value}><input type="checkbox" checked={values.includes(c.value)} onChange={(e) => set(e.target.checked ? [...values, c.value] : values.filter((v) => v !== c.value))} /> {c.label || c.value}</label>; })}</div> :
                    q.type === "GPS" ? <div className="preview-placeholder">📍 GPS location will be captured on the Android device.</div> :
                    q.type === "PHOTO" ? <div className="preview-placeholder">📷 Camera capture will be available on Android.</div> :
                    q.type === "AUDIO" ? <div className="preview-placeholder">🎙 Audio recording will be available on Android.</div> :
                    q.type === "SIGNATURE" ? <div className="preview-placeholder">✍️ Signature pad will be available on Android.</div> : null}
                  </div>
                );
              })}
            </div>
            <div className="preview-footer"><button type="button" className="btn btn-secondary" onClick={() => setIsPreviewOpen(false)}>Close preview</button><button type="button" className="btn btn-primary" onClick={() => setPreviewValues({})}>Reset answers</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
