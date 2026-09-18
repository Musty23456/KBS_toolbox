import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { submissionsApi, surveysApi, usersApi } from "../../api/services";
import type { Submission, SurveyDetail, SurveySummary, UserAccount } from "../../api/types";
import { CHOICE_TYPES } from "../../api/types";

const CHART_COLORS = ["#2f6f4f", "#c98a2c", "#4d7ea8", "#a8474d", "#7a5ea8", "#3f9c8a", "#c2703f"];

function dateKey(iso: string | null): string {
  if (!iso) return "Unknown date";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Unknown date";
  return d.toISOString().slice(0, 10);
}

export function AnalyticsPage() {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>("");
  const [surveyDetail, setSurveyDetail] = useState<SurveyDetail | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [surveyList, userList] = await Promise.all([surveysApi.list(), usersApi.list().catch(() => [])]);
      setSurveys(surveyList);
      setUsers(userList);
      if (surveyList.length > 0) {
        setSelectedSurveyId(surveyList[0].id);
      } else {
        setIsLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedSurveyId) return;
    setIsLoading(true);
    setSelectedQuestionId("");
    (async () => {
      const [detail, subs] = await Promise.all([
        surveysApi.get(selectedSurveyId),
        submissionsApi.list({ survey_id: selectedSurveyId }),
      ]);
      setSurveyDetail(detail);
      setSubmissions(subs);
      const firstChoiceQuestion = detail.questions.find((q) => CHOICE_TYPES.includes(q.type));
      if (firstChoiceQuestion) setSelectedQuestionId(firstChoiceQuestion.id ?? "");
      setIsLoading(false);
    })();
  }, [selectedSurveyId]);

  const userNameById = useMemo(() => {
    const map = new Map<string, string>();
    users.forEach((u) => map.set(u.id, u.full_name));
    return map;
  }, [users]);

  const submissionsByDate = useMemo(() => {
    const counts = new Map<string, number>();
    submissions.forEach((s) => {
      const key = dateKey(s.collected_at ?? s.created_at);
      counts.set(key, (counts.get(key) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([date, count]) => ({ date, count }));
  }, [submissions]);

  const submissionsByEnumerator = useMemo(() => {
    const counts = new Map<string, number>();
    submissions.forEach((s) => {
      const name = userNameById.get(s.submitted_by_id) ?? "Unknown";
      counts.set(name, (counts.get(name) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
  }, [submissions, userNameById]);

  const choiceQuestions = useMemo(
    () => (surveyDetail?.questions ?? []).filter((q) => CHOICE_TYPES.includes(q.type)),
    [surveyDetail]
  );

  const selectedQuestion = choiceQuestions.find((q) => q.id === selectedQuestionId);

  const answerDistribution = useMemo(() => {
    if (!selectedQuestion) return [];
    const labelByValue = new Map<string, string>();
    selectedQuestion.choices.forEach((c) => labelByValue.set(c.value, c.label));
    const counts = new Map<string, number>();
    submissions.forEach((s) => {
      const answer = s.answers.find((a) => a.question_id === selectedQuestion.id);
      if (!answer?.value_text) return;
      // MULTIPLE_CHOICE answers are stored as a JSON array string; everything
      // else (single choice / dropdown) is a plain value string.
      let values: string[];
      try {
        const parsed = JSON.parse(answer.value_text);
        values = Array.isArray(parsed) ? parsed : [answer.value_text];
      } catch {
        values = [answer.value_text];
      }
      values.forEach((v) => {
        const label = labelByValue.get(v) ?? v;
        counts.set(label, (counts.get(label) ?? 0) + 1);
      });
    });
    return Array.from(counts.entries()).map(([label, count]) => ({ name: label, value: count }));
  }, [selectedQuestion, submissions]);

  const syncedCount = submissions.filter((s) => s.status === "SYNCED" || s.status === "UPLOADED").length;
  const uniqueEnumerators = new Set(submissions.map((s) => s.submitted_by_id)).size;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <p>How data collection is progressing for each survey.</p>
        </div>
      </div>

      <div className="toolbar">
        <select value={selectedSurveyId} onChange={(e) => setSelectedSurveyId(e.target.value)}>
          {surveys.length === 0 && <option value="">No surveys yet</option>}
          {surveys.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="loading-text">Loading…</p>
      ) : surveys.length === 0 ? (
        <div className="empty-state">
          <h3>No surveys yet</h3>
          <p>Create and publish a survey to see analytics here.</p>
        </div>
      ) : submissions.length === 0 ? (
        <div className="empty-state">
          <h3>No submissions yet</h3>
          <p>Once enumerators start submitting responses for this survey, charts will appear here.</p>
        </div>
      ) : (
        <>
          <div className="stat-row">
            <div className="stat-box">
              <div className="stat-value">{submissions.length}</div>
              <div className="stat-label">Total submissions</div>
            </div>
            <div className="stat-box">
              <div className="stat-value">{syncedCount}</div>
              <div className="stat-label">Synced to server</div>
            </div>
            <div className="stat-box">
              <div className="stat-value">{uniqueEnumerators}</div>
              <div className="stat-label">Enumerators who submitted</div>
            </div>
            <div className="stat-box">
              <div className="stat-value">{submissionsByDate.length}</div>
              <div className="stat-label">Days with activity</div>
            </div>
          </div>

          <h2>Submissions over time</h2>
          <div style={{ width: "100%", height: 280, marginBottom: 40 }}>
            <ResponsiveContainer>
              <BarChart data={submissionsByDate}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" name="Submissions" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <h2>Submissions by enumerator</h2>
          <div style={{ width: "100%", height: Math.max(200, submissionsByEnumerator.length * 44), marginBottom: 40 }}>
            <ResponsiveContainer>
              <BarChart data={submissionsByEnumerator} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" name="Submissions" fill={CHART_COLORS[1]} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {choiceQuestions.length > 0 && (
            <>
              <h2>Answer distribution</h2>
              <div className="toolbar">
                <select value={selectedQuestionId} onChange={(e) => setSelectedQuestionId(e.target.value)}>
                  {choiceQuestions.map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.label}
                    </option>
                  ))}
                </select>
              </div>
              {answerDistribution.length === 0 ? (
                <p className="loading-text">No answers recorded for this question yet.</p>
              ) : (
                <div style={{ width: "100%", height: 320, marginBottom: 24 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie
                        data={answerDistribution}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={110}
                        label={(entry) => `${entry.name} (${entry.value})`}
                      >
                        {answerDistribution.map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend />
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
