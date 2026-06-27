/**
 * TRACK 16.08 · MASCI Transportation Orientation Center.
 *
 * Native admin surfaces:
 *  - Orientation dashboard widgets (completion % · certificates · expiring)
 *  - Module Manager with placeholder editor (4 languages per module)
 *  - Question Bank per module
 *  - Assignments queue
 *  - Certificates list w/ QR verify link
 *
 * Reuses every existing MASCI primitive: PortalShell · SubNav · adminHeaders.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, NavLink, Routes, Route, Outlet } from "react-router-dom";
import {
  GraduationCap, FileVideo, BadgeCheck, ListChecks, AlertTriangle,
  Languages as LangIcon, ChevronRight, RefreshCw, ShieldCheck, Hash,
} from "lucide-react";
import { api } from "@/lib/api";
import { adminHeaders, Chip, PageHeader, EmptyState } from "./_shared";

const LANGUAGES = [
  { code: "en", label: "English (Primary)" },
  { code: "es", label: "Spanish" },
  { code: "es_CU", label: "Cuban Spanish" },
  { code: "fr", label: "French" },
];

// ────────────────────────────────────────────────────────────────────
// Top wrapper · nested router
// ────────────────────────────────────────────────────────────────────
export function OrientationCenter() {
  return (
    <div data-testid="tx-orientation-center" className="space-y-4">
      <PageHeader
        title="Orientation Center"
        subtitle="MASCI Transportation onboarding · video engine · quiz engine · certificates"
        testid="tx-orientation-header"
      />
      <SubTabs />
      <Routes>
        <Route index element={<OrientationDashboard />} />
        <Route path="modules" element={<ModuleManager />} />
        <Route path="modules/:mid" element={<ModuleDetail />} />
        <Route path="assignments" element={<AssignmentsView />} />
        <Route path="certificates" element={<CertificatesView />} />
      </Routes>
    </div>
  );
}

const SUB_TABS = [
  { to: "", label: "Dashboard", end: true, testid: "tx-orient-tab-dashboard" },
  { to: "modules", label: "Modules", testid: "tx-orient-tab-modules" },
  { to: "assignments", label: "Assignments", testid: "tx-orient-tab-assignments" },
  { to: "certificates", label: "Certificates", testid: "tx-orient-tab-certificates" },
];

function SubTabs() {
  return (
    <nav className="flex flex-wrap gap-1 border-b border-slate-200 pb-2 mb-4" data-testid="tx-orientation-subtabs">
      {SUB_TABS.map((t) => (
        <NavLink
          key={t.label}
          to={`/admin/transportation/orientation/${t.to}`}
          end={t.end}
          data-testid={t.testid}
          className={({ isActive }) =>
            `inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
              isActive ? "bg-amber-700 text-white" : "text-slate-700 hover:bg-slate-100"
            }`
          }
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}

// ────────────────────────────────────────────────────────────────────
// Dashboard
// ────────────────────────────────────────────────────────────────────
function OrientationDashboard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const load = useCallback(async () => {
    try {
      const r = await api.get("/admin/transportation/orientation/dashboard",
        { headers: adminHeaders() });
      setData(r.data);
    } catch (e) {
      setErr(e.message || String(e));
    }
  }, []);
  useEffect(() => { load(); }, [load]);
  if (err) return <EmptyState title="Orientation dashboard unavailable" hint={err} testid="tx-orient-dashboard-err" />;
  if (!data) return <div data-testid="tx-orient-dashboard-loading" className="text-slate-500 text-sm">Loading…</div>;
  const Tile = ({ icon: Icon, label, value, sub, testid, tone = "slate" }) => (
    <div
      data-testid={testid}
      className={`rounded-lg border bg-white p-4 shadow-sm border-${tone}-200`}
    >
      <div className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-wide">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
      {sub ? <div className="text-xs text-slate-500 mt-1">{sub}</div> : null}
    </div>
  );
  return (
    <div data-testid="tx-orient-dashboard" className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Tile testid="tx-orient-kpi-completion" icon={ShieldCheck} label="Completion %" value={`${data.completion_pct}%`} sub={`${data.drivers_orientation_current}/${data.drivers_total} drivers current`} />
        <Tile testid="tx-orient-kpi-awaiting" icon={AlertTriangle} label="Awaiting Orientation" value={data.drivers_orientation_missing} sub="Drivers without all required modules" />
        <Tile testid="tx-orient-kpi-expired" icon={AlertTriangle} label="Expired" value={data.drivers_orientation_expired} sub="Annual refresher overdue" />
        <Tile testid="tx-orient-kpi-expiring" icon={AlertTriangle} label="Expiring Soon" value={data.drivers_expiring_soon} sub="Within 30 days" />
        <Tile testid="tx-orient-kpi-certs-30" icon={BadgeCheck} label="Certs · 30 d" value={data.certificates_30d} />
        <Tile testid="tx-orient-kpi-certs-90" icon={BadgeCheck} label="Certs · 90 d" value={data.certificates_90d} />
        <Tile testid="tx-orient-kpi-modules" icon={FileVideo} label="Modules" value={`${data.modules_active}`} sub={`${data.modules_required} required`} />
        <Tile testid="tx-orient-kpi-avg-quiz" icon={ListChecks} label="Avg Quiz Score" value={`${data.average_quiz_score}%`} />
      </div>
      <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded p-3" data-testid="tx-orient-disclaimer">
        {data.disclaimer}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Module Manager
// ────────────────────────────────────────────────────────────────────
function ModuleManager() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState(null);
  const load = useCallback(async () => {
    try {
      const r = await api.get("/admin/transportation/orientation/modules",
        { headers: adminHeaders() });
      setItems(r.data.items || []);
    } catch (e) { setErr(e.message || String(e)); }
  }, []);
  useEffect(() => { load(); }, [load]);
  if (err) return <EmptyState title="Modules unavailable" hint={err} testid="tx-orient-modules-err" />;
  return (
    <div data-testid="tx-orient-modules" className="space-y-2">
      <div className="text-sm text-slate-600">{items.length} module(s) · placeholders ready for Sky AI video drop-in.</div>
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-3 py-2">Key</th>
              <th className="text-left px-3 py-2">Title</th>
              <th className="text-left px-3 py-2">Category</th>
              <th className="text-left px-3 py-2">Required</th>
              <th className="text-left px-3 py-2">Runtime</th>
              <th className="text-left px-3 py-2">Languages Published</th>
              <th className="text-left px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => {
              const published = (m.placeholders || []).filter(p => p.sky_asset_id).map(p => p.language);
              return (
                <tr key={m.id} className="border-b border-slate-100 hover:bg-amber-50/30" data-testid={`tx-orient-module-row-${m.key}`}>
                  <td className="px-3 py-2 font-mono text-xs text-slate-700">{m.key}</td>
                  <td className="px-3 py-2">{m.title}</td>
                  <td className="px-3 py-2"><Chip value={m.category} testid={`tx-orient-cat-${m.key}`} /></td>
                  <td className="px-3 py-2">{m.required ? <BadgeCheck className="h-4 w-4 text-emerald-600" /> : <span className="text-slate-400 text-xs">optional</span>}</td>
                  <td className="px-3 py-2 text-xs">{(m.runtime_seconds || 0) + "s"}</td>
                  <td className="px-3 py-2 text-xs">
                    {published.length ? published.join(" · ") : <span className="text-slate-400">placeholders only</span>}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <NavLink data-testid={`tx-orient-module-link-${m.key}`} to={`/admin/transportation/orientation/modules/${m.id}`} className="text-amber-700 hover:underline text-xs inline-flex items-center gap-1">
                      Open <ChevronRight className="h-3 w-3" />
                    </NavLink>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Module Detail · placeholder editor + question bank
// ────────────────────────────────────────────────────────────────────
function ModuleDetail() {
  const { mid } = useParams();
  const [mod, setMod] = useState(null);
  const [lang, setLang] = useState("en");
  const [questions, setQuestions] = useState([]);
  const [err, setErr] = useState(null);
  const reload = useCallback(async () => {
    try {
      const list = (await api.get("/admin/transportation/orientation/modules",
        { headers: adminHeaders() })).data.items || [];
      setMod(list.find((m) => m.id === mid) || null);
      const q = (await api.get(
        `/admin/transportation/orientation/modules/${mid}/questions?language=${lang}`,
        { headers: adminHeaders() })).data.items || [];
      setQuestions(q);
    } catch (e) { setErr(e.message || String(e)); }
  }, [mid, lang]);
  useEffect(() => { reload(); }, [reload]);
  if (err) return <EmptyState title="Module unavailable" hint={err} testid="tx-orient-module-err" />;
  if (!mod) return <div data-testid="tx-orient-module-loading" className="text-slate-500 text-sm">Loading…</div>;

  const savePlaceholder = async (language, body) => {
    try {
      await api.patch(`/admin/transportation/orientation/modules/${mid}/placeholder`,
        { language, ...body }, { headers: adminHeaders() });
      await reload();
    } catch (e) { alert("Save failed: " + e.message); }
  };
  const addQuestion = async (q) => {
    try {
      await api.post(`/admin/transportation/orientation/modules/${mid}/questions`,
        { ...q, language: lang }, { headers: adminHeaders() });
      await reload();
    } catch (e) { alert("Add question failed: " + e.message); }
  };

  return (
    <div data-testid="tx-orient-module-detail" className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="text-xs text-slate-500">Module · {mod.category}</div>
          <h3 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-amber-700" /> {mod.title}
          </h3>
          <div className="text-xs text-slate-500 mt-0.5">{mod.key} · v{mod.version} · passing {mod.passing_score}% · max attempts {mod.max_attempts}</div>
        </div>
        <NavLink data-testid="tx-orient-module-back" to="/admin/transportation/orientation/modules" className="text-amber-700 hover:underline text-sm">← All modules</NavLink>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="px-3 py-2 border-b border-slate-200 text-sm font-medium flex items-center gap-2">
          <FileVideo className="h-4 w-4 text-amber-700" /> Video Placeholders (Sky AI drop-in)
        </div>
        <div className="p-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          {(mod.placeholders || []).map((ph) => (
            <PlaceholderCard
              key={ph.language}
              language={ph.language}
              placeholder={ph}
              onSave={savePlaceholder}
            />
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="px-3 py-2 border-b border-slate-200 text-sm font-medium flex items-center justify-between">
          <span className="flex items-center gap-2"><ListChecks className="h-4 w-4 text-amber-700" /> Question Bank</span>
          <div className="flex items-center gap-2 text-xs">
            <LangIcon className="h-3 w-3 text-slate-500" />
            <select data-testid="tx-orient-lang-picker" value={lang} onChange={(e) => setLang(e.target.value)} className="border border-slate-300 rounded px-1 py-0.5">
              {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>
        </div>
        <div className="p-3 space-y-2">
          {questions.length === 0 ? (
            <div className="text-slate-400 text-sm">No questions for {lang} yet.</div>
          ) : questions.map((q, i) => (
            <div key={q.id} className="text-sm border border-slate-200 rounded p-2" data-testid={`tx-orient-question-${i}`}>
              <div className="font-medium">{i + 1}. {q.prompt}</div>
              <ol className="ml-4 list-decimal text-xs text-slate-700 mt-1">
                {q.choices.map((c, ci) => (
                  <li key={ci} className={ci === q.correct_index ? "text-emerald-700 font-semibold" : ""}>{c}</li>
                ))}
              </ol>
            </div>
          ))}
          <QuestionAddForm onAdd={addQuestion} />
        </div>
      </div>
    </div>
  );
}

function PlaceholderCard({ language, placeholder, onSave }) {
  const [asset, setAsset] = useState(placeholder.sky_asset_id || "");
  const [runtime, setRuntime] = useState(placeholder.runtime_seconds || 0);
  const status = placeholder.sky_asset_id ? "published" : "placeholder";
  return (
    <div className="rounded border border-slate-200 p-3" data-testid={`tx-orient-placeholder-${language}`}>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="font-medium">{LANGUAGES.find(l => l.code === language)?.label || language}</span>
        <Chip value={status} testid={`tx-orient-ph-status-${language}`} />
      </div>
      <label className="block text-xs text-slate-500 mt-2">Sky Asset ID</label>
      <input data-testid={`tx-orient-ph-asset-${language}`} type="text" value={asset} onChange={(e) => setAsset(e.target.value)} className="w-full border border-slate-300 rounded px-2 py-1 text-sm font-mono" placeholder="sky_abc123…" />
      <label className="block text-xs text-slate-500 mt-2">Runtime (s)</label>
      <input data-testid={`tx-orient-ph-runtime-${language}`} type="number" value={runtime} onChange={(e) => setRuntime(parseInt(e.target.value, 10) || 0)} className="w-full border border-slate-300 rounded px-2 py-1 text-sm" />
      <button data-testid={`tx-orient-ph-save-${language}`} onClick={() => onSave(language, { sky_asset_id: asset || null, runtime_seconds: runtime })} className="mt-2 inline-flex items-center gap-1 bg-amber-700 text-white text-xs px-3 py-1 rounded hover:bg-amber-800">
        Save
      </button>
    </div>
  );
}

function QuestionAddForm({ onAdd }) {
  const [prompt, setPrompt] = useState("");
  const [choices, setChoices] = useState(["", ""]);
  const [correct, setCorrect] = useState(0);
  const setChoice = (i, v) => {
    const copy = [...choices]; copy[i] = v; setChoices(copy);
  };
  const submit = () => {
    if (!prompt.trim() || choices.some(c => !c.trim())) return;
    onAdd({ prompt, choices, correct_index: correct });
    setPrompt(""); setChoices(["", ""]); setCorrect(0);
  };
  return (
    <div className="border-t border-slate-200 pt-2 mt-2" data-testid="tx-orient-question-add">
      <div className="text-xs font-medium mb-1">Add a question</div>
      <input data-testid="tx-orient-q-prompt" placeholder="Prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} className="w-full border border-slate-300 rounded px-2 py-1 text-sm" />
      <div className="space-y-1 mt-2">
        {choices.map((c, i) => (
          <div key={i} className="flex items-center gap-2">
            <input data-testid={`tx-orient-q-correct-${i}`} type="radio" checked={correct === i} onChange={() => setCorrect(i)} />
            <input data-testid={`tx-orient-q-choice-${i}`} value={c} onChange={(e) => setChoice(i, e.target.value)} placeholder={`Choice ${i + 1}`} className="flex-1 border border-slate-300 rounded px-2 py-1 text-sm" />
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-2">
        <button data-testid="tx-orient-q-add-choice" onClick={() => setChoices([...choices, ""])} className="text-xs text-amber-700 hover:underline">+ Add choice</button>
        <button data-testid="tx-orient-q-submit" onClick={submit} className="ml-auto bg-amber-700 text-white text-xs px-3 py-1 rounded hover:bg-amber-800">Save question</button>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Assignments + Certificates
// ────────────────────────────────────────────────────────────────────
function AssignmentsView() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api.get("/admin/transportation/orientation/assignments",
      { headers: adminHeaders() })
      .then(r => setItems(r.data.items || []))
      .catch(e => setErr(e.message || String(e)));
  }, []);
  if (err) return <EmptyState title="Assignments unavailable" hint={err} testid="tx-orient-assignments-err" />;
  if (items.length === 0) return <EmptyState title="No assignments yet" hint="Drivers will appear here as orientation modules are assigned." testid="tx-orient-assignments-empty" />;
  return (
    <div data-testid="tx-orient-assignments" className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            <th className="text-left px-3 py-2">Driver</th>
            <th className="text-left px-3 py-2">Module</th>
            <th className="text-left px-3 py-2">Language</th>
            <th className="text-left px-3 py-2">Status</th>
            <th className="text-left px-3 py-2">Watched %</th>
            <th className="text-left px-3 py-2">Quiz Score</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.id} className="border-b border-slate-100" data-testid={`tx-orient-assign-${a.id}`}>
              <td className="px-3 py-2 font-mono text-xs">{a.transport_person_id}</td>
              <td className="px-3 py-2">{a.module_key}</td>
              <td className="px-3 py-2">{a.language}</td>
              <td className="px-3 py-2"><Chip value={a.status} testid={`tx-orient-assign-status-${a.id}`} /></td>
              <td className="px-3 py-2 text-xs">{Math.round((a.completion_pct || 0) * 100)}%</td>
              <td className="px-3 py-2 text-xs">{a.best_quiz_score ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CertificatesView() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState(null);
  useEffect(() => {
    api.get("/admin/transportation/orientation/certificates",
      { headers: adminHeaders() })
      .then(r => setItems(r.data.items || []))
      .catch(e => setErr(e.message || String(e)));
  }, []);
  if (err) return <EmptyState title="Certificates unavailable" hint={err} testid="tx-orient-certs-err" />;
  if (items.length === 0) return <EmptyState title="No certificates yet" hint="They are issued automatically when a driver passes a module quiz." testid="tx-orient-certs-empty" />;
  return (
    <div data-testid="tx-orient-certificates" className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            <th className="text-left px-3 py-2">Cert #</th>
            <th className="text-left px-3 py-2">Driver</th>
            <th className="text-left px-3 py-2">Module</th>
            <th className="text-left px-3 py-2">Score</th>
            <th className="text-left px-3 py-2">Completed</th>
            <th className="text-left px-3 py-2">Audit Hash</th>
            <th className="text-left px-3 py-2">QR Verify</th>
          </tr>
        </thead>
        <tbody>
          {items.map((c) => (
            <tr key={c.id} className="border-b border-slate-100" data-testid={`tx-orient-cert-${c.id}`}>
              <td className="px-3 py-2 font-mono text-xs">{c.certificate_number}</td>
              <td className="px-3 py-2 font-mono text-xs">{c.transport_person_id}</td>
              <td className="px-3 py-2">{c.module_key} · {c.language} · v{c.module_version}</td>
              <td className="px-3 py-2 text-xs">{c.quiz_score}%</td>
              <td className="px-3 py-2 text-xs">{(c.completed_at || "").slice(0, 10)}</td>
              <td className="px-3 py-2 font-mono text-xs text-slate-500" title={c.audit_hash}>{(c.audit_hash || "").slice(0, 12)}…</td>
              <td className="px-3 py-2 text-xs">
                <a data-testid={`tx-orient-verify-${c.id}`} className="text-amber-700 hover:underline inline-flex items-center gap-1" href={`/transport-verify/${c.certificate_number}`} target="_blank" rel="noreferrer">
                  <Hash className="h-3 w-3" /> Verify
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
