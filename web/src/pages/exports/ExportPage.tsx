import { useEffect, useState } from "react";
import { exportsApi, surveysApi, usersApi } from "../../api/services";
import type { SurveySummary, UserAccount } from "../../api/types";

export function ExportPage() {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [surveyId, setSurveyId] = useState("");
  const [status, setStatus] = useState("");
  const [enumerator, setEnumerator] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([surveysApi.list(), usersApi.list()]).then(([s, u]) => {
      setSurveys(s);
      setUsers(u.filter((x) => x.role === "ENUMERATOR"));
    });
  }, []);

  const filters = {
    ...(surveyId ? { survey_id: surveyId } : {}),
    ...(status ? { status } : {}),
    ...(enumerator ? { submitted_by_id: enumerator } : {}),
    ...(dateFrom ? { date_from: dateFrom } : {}),
    ...(dateTo ? { date_to: dateTo } : {}),
  };

  async function download(format: "csv" | "json" | "xlsx" | "pdf") {
    setBusy(format);
    try { await exportsApi.download(format, filters); }
    finally { setBusy(null); }
  }

  return (
    <div className="page-stack">
      <div className="page-header"><div><h1>Export Center</h1><p>Export submission data using the filters below.</p></div></div>
      <section className="card">
        <h2>Filters</h2>
        <div className="form-grid">
          <label>Survey<select value={surveyId} onChange={(e) => setSurveyId(e.target.value)}><option value="">All surveys</option>{surveys.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</select></label>
          <label>Status<select value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option><option value="SYNCED">Synced</option><option value="FAILED">Failed</option><option value="UPLOADED">Uploaded</option><option value="PENDING">Pending</option></select></label>
          <label>Enumerator<select value={enumerator} onChange={(e) => setEnumerator(e.target.value)}><option value="">All enumerators</option>{users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select></label>
          <label>From<input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} /></label>
          <label>To<input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} /></label>
        </div>
      </section>
      <section className="card"><h2>Download</h2><div className="export-grid">
        {(["xlsx", "csv", "json", "pdf"] as const).map((format) => <button className="export-card" key={format} disabled={busy !== null} onClick={() => download(format)}><strong>{busy === format ? "Preparing…" : format.toUpperCase()}</strong><span>{format === "xlsx" ? "Excel spreadsheet" : format === "csv" ? "Flat data for analysis" : format === "json" ? "Structured API data" : "Printable report"}</span></button>)}
      </div></section>
    </div>
  );
}
