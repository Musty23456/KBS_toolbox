import { useEffect, useMemo, useState } from "react";
import { surveysApi, translationsApi } from "../../api/services";
import type { SurveyDetail, SurveySummary, Translation } from "../../api/types";

const key = (t: Pick<Translation, "entity_type"|"entity_id"|"field">) => `${t.entity_type}:${t.entity_id}:${t.field}`;
type Target = { entity_type: Translation["entity_type"]; entity_id: string; field: Translation["field"]; label: string; source: string };

export function TranslationsPage() {
  const [surveys, setSurveys] = useState<SurveySummary[]>([]); const [languages, setLanguages] = useState<{code:string;name:string}[]>([]);
  const [surveyId, setSurveyId] = useState(""); const [language, setLanguage] = useState("ha"); const [detail, setDetail] = useState<SurveyDetail | null>(null);
  const [rows, setRows] = useState<Record<string,string>>({}); const [saving, setSaving] = useState<string | null>(null); const [message, setMessage] = useState("");
  useEffect(() => { Promise.all([surveysApi.list(), translationsApi.languages()]).then(([s,l]) => { setSurveys(s); setLanguages(l); setSurveyId(s[0]?.id ?? ""); }); }, []);
  useEffect(() => { if (surveyId) surveysApi.get(surveyId).then(setDetail); }, [surveyId]);
  useEffect(() => { if (!surveyId) return; translationsApi.list(surveyId).then(items => { const next:Record<string,string>={}; items.filter(x=>x.language_code===language).forEach(x=>next[key(x)]=x.value); setRows(next); }); }, [surveyId, language]);
  const targets = useMemo<Target[]>(() => { if (!detail) return []; const out:Target[]=[{entity_type:"SURVEY",entity_id:detail.id,field:"title",label:"Survey title",source:detail.title},{entity_type:"SURVEY",entity_id:detail.id,field:"description",label:"Survey description",source:detail.description||""}];
    detail.sections.forEach(s=>{out.push({entity_type:"SECTION",entity_id:s.id!,field:"title",label:`Section: ${s.title}`,source:s.title}); if(s.description)out.push({entity_type:"SECTION",entity_id:s.id!,field:"description",label:`Section description: ${s.title}`,source:s.description});});
    detail.groups.forEach(g=>{out.push({entity_type:"GROUP",entity_id:g.id!,field:"title",label:`Group: ${g.title}`,source:g.title}); if(g.description)out.push({entity_type:"GROUP",entity_id:g.id!,field:"description",label:`Group description: ${g.title}`,source:g.description});});
    detail.questions.forEach(q=>{out.push({entity_type:"QUESTION",entity_id:q.id!,field:"label",label:`Question ${q.code}`,source:q.label}); if(q.hint)out.push({entity_type:"QUESTION",entity_id:q.id!,field:"hint",label:`Hint ${q.code}`,source:q.hint}); q.choices.forEach(c=>out.push({entity_type:"CHOICE",entity_id:c.id!,field:"label",label:`Choice ${q.code}: ${c.value}`,source:c.label}));}); return out; }, [detail]);
  async function save(t:Target){const k=key(t);setSaving(k);setMessage("");try{await translationsApi.upsert(surveyId,{...t,value:rows[k]??"",language_code:language});setMessage("Saved.")}catch{setMessage("Could not save translation.")}finally{setSaving(null)}}
  return <div><div className="page-header"><div><h1>Multilingual Surveys</h1><p>Translate survey content without changing stable codes, logic or collected data.</p></div></div>
    <div className="toolbar"><select value={surveyId} onChange={e=>setSurveyId(e.target.value)}>{surveys.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select><select value={language} onChange={e=>setLanguage(e.target.value)}>{languages.filter(l=>l.code!=="en").map(l=><option key={l.code} value={l.code}>{l.name} ({l.code})</option>)}</select>{message&&<span>{message}</span>}</div>
    {!detail?<p className="loading-text">Loading…</p>:<div className="table-wrap"><table><thead><tr><th>Content</th><th>Source</th><th>{languages.find(l=>l.code===language)?.name||language}</th><th></th></tr></thead><tbody>{targets.map(t=>{const k=key(t);return <tr key={k}><td>{t.label}</td><td>{t.source}</td><td><textarea value={rows[k]??""} onChange={e=>setRows({...rows,[k]:e.target.value})} rows={2} placeholder="Enter translation"/></td><td><button className="button" disabled={saving===k} onClick={()=>save(t)}>{saving===k?"Saving…":"Save"}</button></td></tr>})}</tbody></table></div>}</div>;
}
