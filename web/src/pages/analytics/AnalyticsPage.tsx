import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { analyticsApi, surveysApi } from "../../api/services";
import type { SurveySummary } from "../../api/types";

const CHART_COLORS = ["#2f6f4f", "#c98a2c", "#4d7ea8", "#a8474d", "#7a5ea8", "#3f9c8a", "#c2703f"];

type AnalyticsOverview = {
  total_submissions: number;
  synced_submissions: number;
  failed_submissions: number;
  unique_enumerators: number;
  active_days: number;
  submissions_over_time: { date: string; count: number }[];
  status_distribution: { name: string; value: number }[];
  review_distribution: { name: string; value: number }[];
  enumerator_performance: { user_id: string; name: string; submissions: number }[];
  survey_comparison: { survey_id: string; title: string; submissions: number }[];
};

type QuestionStat = {
  question_id: string;
  code: string;
  label: string;
  type: string;
  response_count: number;
  missing_count: number;
  distribution: { name: string; value: number }[];
};

export function AnalyticsPage() {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [selectedSurveyId, setSelectedSurveyId] = useState("");
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [questions, setQuestions] = useState<QuestionStat[]>([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    surveysApi.list().then((items) => {
      setSurveys(items);
      setSelectedSurveyId(items[0]?.id ?? "");
      if (!items.length) setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedSurveyId) return;
    setLoading(true);
    Promise.all([
      analyticsApi.overview({ survey_id: selectedSurveyId, date_from: dateFrom || undefined, date_to: dateTo || undefined }),
      analyticsApi.questions(selectedSurveyId),
    ]).then(([o, q]) => {
      setOverview(o);
      setQuestions(q);
      setSelectedQuestionId(q[0]?.question_id ?? "");
    }).finally(() => setLoading(false));
  }, [selectedSurveyId, dateFrom, dateTo]);

  const selectedQuestion = useMemo(() => questions.find((q) => q.question_id === selectedQuestionId), [questions, selectedQuestionId]);

  if (!surveys.length && !loading) return <div className="empty-state"><h3>No surveys yet</h3><p>Create a survey and collect submissions to see advanced analytics.</p></div>;

  return (
    <div>
      <div className="page-header"><div><h1>Advanced Analytics</h1><p>Measure collection progress, review workflow, enumerator activity and question responses.</p></div></div>
      <div className="toolbar">
        <select value={selectedSurveyId} onChange={(e) => setSelectedSurveyId(e.target.value)}>{surveys.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</select>
        <label>From <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /></label>
        <label>To <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></label>
      </div>
      {loading || !overview ? <p className="loading-text">Loading analytics…</p> : (
        <>
          <div className="stat-row">
            <div className="stat-box"><div className="stat-value">{overview.total_submissions}</div><div className="stat-label">Total submissions</div></div>
            <div className="stat-box"><div className="stat-value">{overview.synced_submissions}</div><div className="stat-label">Synced / uploaded</div></div>
            <div className="stat-box"><div className="stat-value">{overview.failed_submissions}</div><div className="stat-label">Failed syncs</div></div>
            <div className="stat-box"><div className="stat-value">{overview.unique_enumerators}</div><div className="stat-label">Active enumerators</div></div>
            <div className="stat-box"><div className="stat-value">{overview.active_days}</div><div className="stat-label">Active days</div></div>
          </div>

          <h2>Submissions over time</h2>
          <div style={{ width: "100%", height: 280, marginBottom: 40 }}><ResponsiveContainer><LineChart data={overview.submissions_over_time}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis allowDecimals={false} /><Tooltip /><Line type="monotone" dataKey="count" name="Submissions" stroke={CHART_COLORS[0]} strokeWidth={3} /></LineChart></ResponsiveContainer></div>

          <div className="analytics-grid">
            <section><h2>Submission status</h2><div style={{ width: "100%", height: 300 }}><ResponsiveContainer><PieChart><Pie data={overview.status_distribution} dataKey="value" nameKey="name" outerRadius={100} label>{overview.status_distribution.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div></section>
            <section><h2>Review workflow</h2><div style={{ width: "100%", height: 300 }}><ResponsiveContainer><PieChart><Pie data={overview.review_distribution} dataKey="value" nameKey="name" outerRadius={100} label>{overview.review_distribution.map((_, i) => <Cell key={i} fill={CHART_COLORS[(i + 2) % CHART_COLORS.length]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div></section>
          </div>

          <h2>Enumerator performance</h2>
          <div style={{ width: "100%", height: Math.max(220, overview.enumerator_performance.length * 48), marginBottom: 40 }}><ResponsiveContainer><BarChart data={overview.enumerator_performance} layout="vertical" margin={{ left: 30 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="name" width={150} /><Tooltip /><Bar dataKey="submissions" name="Submissions" fill={CHART_COLORS[1]} radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>

          <h2>Survey comparison</h2>
          <div style={{ width: "100%", height: Math.max(220, overview.survey_comparison.length * 48), marginBottom: 40 }}><ResponsiveContainer><BarChart data={overview.survey_comparison} layout="vertical" margin={{ left: 30 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="title" width={180} /><Tooltip /><Bar dataKey="submissions" name="Submissions" fill={CHART_COLORS[2]} radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>

          <h2>Question-level statistics</h2>
          <div className="toolbar"><select value={selectedQuestionId} onChange={(e) => setSelectedQuestionId(e.target.value)}>{questions.map((q) => <option key={q.question_id} value={q.question_id}>{q.code} — {q.label}</option>)}</select></div>
          {selectedQuestion && <div className="analytics-grid"><section className="stat-box"><div className="stat-value">{selectedQuestion.response_count}</div><div className="stat-label">Answered</div><div className="stat-value" style={{ marginTop: 12 }}>{selectedQuestion.missing_count}</div><div className="stat-label">Missing</div></section><section><div style={{ width: "100%", height: 320 }}><ResponsiveContainer><BarChart data={selectedQuestion.distribution}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="value" name="Responses" fill={CHART_COLORS[3]} /></BarChart></ResponsiveContainer></div></section></div>}
        </>
      )}
    </div>
  );
}
