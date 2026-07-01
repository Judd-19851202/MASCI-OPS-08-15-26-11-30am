// Track 19.16 · Phase C · Safety Case Workspace.
// The command center for post-report investigation.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import * as api from "@/lib/caseWorkspaceApi";
import { INCIDENT_FLOWS } from "@/lib/incidentReportSchema";
import {
  Activity, AlertTriangle, CheckCircle2, ChevronLeft, Clipboard,
  FileText, Heart, MessageSquare, Paperclip, Shield, Users, Wrench,
} from "lucide-react";

const TABS = [
  { key: "timeline",       label: "Timeline",           icon: Activity },
  { key: "evidence",       label: "Evidence",           icon: Paperclip },
  { key: "witnesses",      label: "Witnesses",          icon: Users },
  { key: "medical",        label: "Medical",            icon: Heart },
  { key: "agency",         label: "Police / Agency",    icon: Shield },
  { key: "rca",            label: "Root Cause",         icon: AlertTriangle },
  { key: "capa",           label: "Corrective Actions", icon: Wrench },
  { key: "communications", label: "Communications",    icon: MessageSquare },
  { key: "tasks",          label: "Safety Tasks",       icon: Clipboard },
  { key: "linked",         label: "Linked Records",     icon: FileText },
];

function _fmt(dt) {
  if (!dt) return "—";
  try { return new Date(dt).toLocaleString(); } catch { return dt; }
}

function CaseHeader({ caseDoc }) {
  const { t } = useT();
  if (!caseDoc) return null;
  const fb = caseDoc.field_block || {};
  const flow = INCIDENT_FLOWS[fb.incident_type];
  const daysOpen = caseDoc.submitted_at
    ? Math.max(0, Math.floor((Date.now() - new Date(caseDoc.submitted_at).getTime()) / 86400000))
    : 0;
  return (
    <div className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5" data-testid="case-header">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Case")} #{caseDoc.case_number || caseDoc.id.slice(0, 8)}
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
            {flow ? t(flow.label) : t("Incident")}
          </h1>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-700">
            <span data-testid="case-header-state" className="inline-flex items-center gap-1">
              <span className="rounded-md bg-slate-900 text-white px-2 py-0.5 text-[10px] font-mono tracking-widest">
                {caseDoc.state}
              </span>
            </span>
            <span>{t("Location")}: {fb.location_label || "—"}</span>
            <span>{t("Job")}: {fb.job_number || "—"}</span>
            <span>{t("Reporter")}: {fb.reporter_name || "—"}</span>
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Days open")}</div>
          <div className="font-display text-2xl font-black text-slate-900" data-testid="case-header-days-open">{daysOpen}</div>
        </div>
      </div>
    </div>
  );
}

function CaseHealth({ health }) {
  const { t } = useT();
  if (!health) return null;
  const pct = health.completeness_pct || 0;
  const barColor = pct >= 80 ? "bg-emerald-600" : pct >= 50 ? "bg-amber-500" : "bg-red-600";
  return (
    <div className="rounded-xl border-2 border-slate-300 bg-white p-4" data-testid="case-health">
      <div className="flex items-center justify-between">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Case health")}</div>
        <div className="font-display text-lg font-black text-slate-900" data-testid="case-health-pct">{pct}%</div>
      </div>
      <div className="mt-2 h-2 rounded-full bg-slate-200 overflow-hidden" aria-hidden>
        <div className={`h-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      {health.blockers && health.blockers.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm" data-testid="case-health-blockers">
          {health.blockers.map((b) => (
            <li key={b} className="flex items-center gap-2 text-amber-800">
              <AlertTriangle className="w-4 h-4" aria-hidden />
              <span data-testid={`case-health-blocker-${b}`}>{t(b.replace(/_/g, " "))}</span>
            </li>
          ))}
        </ul>
      )}
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
        {Object.entries(health.counts || {}).map(([k, v]) => (
          <div key={k} className="rounded-md bg-slate-50 border border-slate-200 px-2 py-1">
            <dt className="font-mono text-[9px] uppercase tracking-[0.14em] text-slate-500">{t(k.replace(/_/g, " "))}</dt>
            <dd className="font-bold text-slate-900">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function ExecutiveSnapshot({ snap }) {
  const { t } = useT();
  if (!snap) return null;
  return (
    <div className="rounded-xl border-2 border-slate-900 bg-slate-900 text-white p-4" data-testid="case-exec-snapshot">
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400">{t("Executive snapshot")}</div>
      <div className="mt-1 grid gap-2 text-sm">
        <div><span className="text-slate-400">{t("Incident")}: </span><span className="font-semibold">{snap.incident_type?.replace(/_/g, " ")}</span></div>
        <div><span className="text-slate-400">{t("OSHA recordable")}: </span><span className="font-semibold">{snap.osha_recordable == null ? t("Unset") : snap.osha_recordable ? t("Yes") : t("No")}</span></div>
        <div><span className="text-slate-400">{t("Lost time (days)")}: </span><span className="font-semibold">{snap.lost_time_days || 0}</span></div>
        <div><span className="text-slate-400">{t("Root cause")}: </span><span className="font-semibold">{snap.root_cause_summary ? "✓" : t("Pending")}</span></div>
        <div><span className="text-slate-400">{t("Readiness")}: </span><span className="font-semibold">{snap.readiness?.completeness_pct || 0}%</span></div>
      </div>
    </div>
  );
}

function TimelinePanel({ events }) {
  const { t } = useT();
  return (
    <div className="space-y-3" data-testid="case-timeline">
      {events.length === 0 && <p className="text-slate-500 text-sm">{t("No timeline entries yet.")}</p>}
      {events.map((e) => (
        <div key={e.id} className="rounded-lg border border-slate-200 bg-white p-3" data-testid={`case-timeline-event-${e.id}`}>
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">{e.event_type}</span>
            <span className="text-[11px] text-slate-500">{_fmt(e.at)}</span>
          </div>
          <div className="text-sm text-slate-800 mt-1">
            {e.actor_name || e.actor_role} · {e.from_state && `${e.from_state} → `}{e.to_state || ""}
          </div>
          {e.reason && <div className="text-xs text-slate-600 mt-1">{t("Reason")}: {e.reason}</div>}
        </div>
      ))}
    </div>
  );
}

function EvidencePanel({ evidence }) {
  const { t } = useT();
  return (
    <div className="grid gap-2 sm:grid-cols-2" data-testid="case-evidence">
      {evidence.length === 0 && <p className="text-slate-500 text-sm col-span-full">{t("No evidence yet.")}</p>}
      {evidence.map((e) => (
        <div key={e.id} className={`rounded-lg border p-3 ${e.withdrawn ? "border-red-300 bg-red-50" : "border-slate-200 bg-white"}`} data-testid={`case-evidence-${e.id}`}>
          <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">{e.evidence_type}</div>
          <div className="font-semibold text-slate-900 truncate">{e.label || "—"}</div>
          <div className="text-xs text-slate-500 mt-1">{_fmt(e.added_at)} · {e.added_by_role}</div>
          {e.withdrawn && <div className="mt-1 text-xs text-red-800 font-bold">{t("Withdrawn")}: {e.withdrawal_reason}</div>}
        </div>
      ))}
    </div>
  );
}

function WitnessPanel({ witnesses, onAdd, onUpdate }) {
  const { t } = useT();
  const [draft, setDraft] = useState({ kind: "internal_employee", name: "", contact: "", statement: "" });
  return (
    <div className="space-y-3" data-testid="case-witnesses">
      <div className="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
        <input className="w-full h-11 rounded-md border border-slate-300 px-3" placeholder={t("Witness name")}
          value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          data-testid="case-witnesses-new-name" />
        <input className="w-full h-11 rounded-md border border-slate-300 px-3" placeholder={t("Contact")}
          value={draft.contact} onChange={(e) => setDraft({ ...draft, contact: e.target.value })}
          data-testid="case-witnesses-new-contact" />
        <textarea className="w-full rounded-md border border-slate-300 px-3 py-2" rows={2} placeholder={t("Statement / notes")}
          value={draft.statement} onChange={(e) => setDraft({ ...draft, statement: e.target.value })}
          data-testid="case-witnesses-new-statement" />
        <button className="h-10 px-4 rounded-md bg-slate-900 text-white font-bold" data-testid="case-witnesses-add"
          disabled={!draft.name.trim()} onClick={async () => { await onAdd(draft); setDraft({ kind: "internal_employee", name: "", contact: "", statement: "" }); }}>
          {t("Add witness")}
        </button>
      </div>
      {witnesses.map((w) => (
        <div key={w.id} className="rounded-lg border border-slate-200 bg-white p-3" data-testid={`case-witnesses-row-${w.id}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-slate-900">{w.name}</div>
              <div className="text-xs text-slate-500 font-mono uppercase tracking-widest">{w.kind}</div>
            </div>
            <select className="h-9 rounded-md border border-slate-300 px-2 text-sm"
              value={w.status} onChange={(e) => onUpdate(w.id, { status: e.target.value })}
              data-testid={`case-witnesses-row-${w.id}-status`}>
              {["pending", "scheduled", "interviewed", "statement_received", "follow_up_needed", "unable_to_reach"].map((s) => (
                <option key={s} value={s}>{t(s.replace(/_/g, " "))}</option>
              ))}
            </select>
          </div>
          {w.statement && <p className="mt-2 text-sm text-slate-700">{w.statement}</p>}
        </div>
      ))}
    </div>
  );
}

function GenericList({ items, keyFn, render, empty, testId }) {
  const { t } = useT();
  return (
    <div className="space-y-2" data-testid={testId}>
      {items.length === 0 && <p className="text-slate-500 text-sm">{t(empty)}</p>}
      {items.map((it) => (
        <div key={keyFn(it)} className="rounded-lg border border-slate-200 bg-white p-3" data-testid={`${testId}-item-${keyFn(it)}`}>
          {render(it)}
        </div>
      ))}
    </div>
  );
}

function RCAPanel({ caseDoc, onSave }) {
  const { t } = useT();
  const sb = caseDoc?.safety_block || {};
  const [summary, setSummary] = useState(sb.root_cause_summary || "");
  const [factors, setFactors] = useState((sb.contributing_factors || []).join("\n"));
  useEffect(() => {
    setSummary(sb.root_cause_summary || "");
    setFactors((sb.contributing_factors || []).join("\n"));
  }, [caseDoc?.id]);
  return (
    <div className="space-y-3" data-testid="case-rca">
      <div>
        <label className="block text-sm font-semibold text-slate-800 mb-1">{t("Root cause summary")}</label>
        <textarea className="w-full rounded-md border border-slate-300 px-3 py-2" rows={4}
          value={summary} onChange={(e) => setSummary(e.target.value)}
          data-testid="case-rca-summary" />
      </div>
      <div>
        <label className="block text-sm font-semibold text-slate-800 mb-1">{t("Contributing factors (one per line)")}</label>
        <textarea className="w-full rounded-md border border-slate-300 px-3 py-2" rows={4}
          value={factors} onChange={(e) => setFactors(e.target.value)}
          data-testid="case-rca-factors" />
      </div>
      <button className="h-10 px-4 rounded-md bg-slate-900 text-white font-bold" data-testid="case-rca-save"
        onClick={() => onSave({
          root_cause_summary: summary,
          contributing_factors: factors.split("\n").map((s) => s.trim()).filter(Boolean),
        })}>
        {t("Save root cause")}
      </button>
    </div>
  );
}

export default function SafetyCaseWorkspace() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const { t } = useT();
  const [tab, setTab] = useState("timeline");
  const [caseDoc, setCaseDoc] = useState(null);
  const [health, setHealth] = useState(null);
  const [snap, setSnap] = useState(null);
  const [events, setEvents] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [witnesses, setWitnesses] = useState([]);
  const [medical, setMedical] = useState([]);
  const [agency, setAgency] = useState([]);
  const [comms, setComms] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [capa, setCapa] = useState([]);
  const [err, setErr] = useState("");

  const refreshAll = useCallback(async () => {
    setErr("");
    try {
      const [c, h, s, ev, e, w, m, a, cm, ts, ca] = await Promise.all([
        api.getCase(caseId),
        api.getHealth(caseId).catch(() => null),
        api.getExecutiveSnapshot(caseId).catch(() => null),
        api.listTimeline(caseId).catch(() => []),
        api.listEvidence(caseId).catch(() => []),
        api.listWitnesses(caseId).catch(() => []),
        api.listMedical(caseId).catch(() => []),
        api.listAgency(caseId).catch(() => []),
        api.listCommunications(caseId).catch(() => []),
        api.listTasks(caseId).catch(() => []),
        api.listCorrectiveActions(caseId).catch(() => []),
      ]);
      setCaseDoc(c); setHealth(h); setSnap(s);
      setEvents(ev); setEvidence(e); setWitnesses(w); setMedical(m);
      setAgency(a); setComms(cm); setTasks(ts); setCapa(ca);
    } catch (e) {
      setErr(e?.response?.data?.detail?.detail || e.message || "load_failed");
    }
  }, [caseId]);

  useEffect(() => { refreshAll(); }, [refreshAll]);

  if (err) {
    return (
      <div className="min-h-screen bg-slate-50 p-6" data-testid="safety-case-workspace-error">
        <div className="max-w-md mx-auto rounded-xl border-2 border-red-300 bg-white p-6">
          <div className="font-mono text-[10px] uppercase tracking-widest text-red-800">{t("Error")}</div>
          <div className="font-display text-xl font-black text-slate-900 mt-1">{t("Could not load case")}</div>
          <p className="mt-2 text-sm text-slate-700">{err}</p>
          <button className="mt-4 h-10 px-4 rounded-md bg-slate-900 text-white" onClick={() => navigate(-1)}>{t("Back")}</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100" data-testid="safety-case-workspace">
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="h-9 w-9 rounded-md border border-slate-300 hover:bg-slate-100 flex items-center justify-center" aria-label={t("Back")}>
          <ChevronLeft className="w-4 h-4" />
        </button>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Safety Case Workspace")}</div>
          <div className="font-display text-base font-black text-slate-900">{caseDoc?.case_number || "…"}</div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 sm:p-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          <CaseHeader caseDoc={caseDoc} />
          <div className="rounded-xl border border-slate-200 bg-white overflow-x-auto">
            <div className="flex" role="tablist" aria-label={t("Case sections")}>
              {TABS.map((t0) => {
                const Icon = t0.icon;
                const active = tab === t0.key;
                return (
                  <button
                    key={t0.key}
                    role="tab"
                    aria-selected={active}
                    onClick={() => setTab(t0.key)}
                    className={`px-3 py-2 border-b-2 font-mono text-[10px] uppercase tracking-[0.14em] inline-flex items-center gap-1 whitespace-nowrap ${active ? "border-slate-900 text-slate-900" : "border-transparent text-slate-500 hover:text-slate-800"}`}
                    data-testid={`case-tab-${t0.key}`}
                  >
                    <Icon className="w-3.5 h-3.5" aria-hidden /> {t(t0.label)}
                  </button>
                );
              })}
            </div>
            <div className="p-3 sm:p-4">
              {tab === "timeline" && <TimelinePanel events={events} />}
              {tab === "evidence" && <EvidencePanel evidence={evidence} />}
              {tab === "witnesses" && (
                <WitnessPanel
                  witnesses={witnesses}
                  onAdd={async (b) => { await api.addWitness(caseId, b); await refreshAll(); }}
                  onUpdate={async (wid, patch) => { await api.updateWitness(caseId, wid, patch); await refreshAll(); }}
                />
              )}
              {tab === "medical" && (
                <GenericList items={medical} keyFn={(m) => m.id} testId="case-medical" empty="No medical entries yet."
                  render={(m) => <div>
                    <div className="font-semibold">{m.subject_name || "—"} · {m.kind}</div>
                    <div className="text-xs text-slate-500">{_fmt(m.at)} · {m.provider}</div>
                    <p className="text-sm mt-1">{m.notes}</p>
                    {m.lost_days > 0 && <div className="text-xs mt-1">{t("Lost days")}: {m.lost_days}</div>}
                  </div>} />
              )}
              {tab === "agency" && (
                <GenericList items={agency} keyFn={(a) => a.id} testId="case-agency" empty="No agency contacts yet."
                  render={(a) => <div>
                    <div className="font-semibold">{a.agency_name}</div>
                    <div className="text-xs text-slate-500">{a.officer_name} · {a.report_number}</div>
                    <p className="text-sm mt-1">{a.notes}</p>
                  </div>} />
              )}
              {tab === "rca" && (
                <RCAPanel caseDoc={caseDoc} onSave={async (patch) => { await api.updateSafetyBlock(caseId, patch); await refreshAll(); }} />
              )}
              {tab === "capa" && (
                <GenericList items={capa} keyFn={(a) => a.id} testId="case-capa" empty="No corrective actions yet."
                  render={(a) => <div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{a.title}</div>
                        <div className="text-xs text-slate-500 font-mono uppercase tracking-widest">{a.action_class} · {a.state}</div>
                      </div>
                      {a.state !== "VERIFIED" && a.state !== "CANCELED" && (
                        <button className="h-9 px-3 rounded-md bg-emerald-700 text-white text-sm font-bold" data-testid={`case-capa-verify-${a.id}`}
                          onClick={async () => { await api.verifyCorrectiveAction(a.id); await refreshAll(); }}>
                          <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" aria-hidden /> {t("Verify")}
                        </button>
                      )}
                    </div>
                    {a.assigned_to_name && <div className="text-xs mt-1">{t("Assigned")}: {a.assigned_to_name}</div>}
                  </div>} />
              )}
              {tab === "communications" && (
                <GenericList items={comms} keyFn={(c) => c.id} testId="case-communications" empty="No communications logged yet."
                  render={(c) => <div>
                    <div className="font-semibold">{c.subject || t(c.kind)}</div>
                    <div className="text-xs text-slate-500">{_fmt(c.at)} · {c.contact_name}</div>
                    <p className="text-sm mt-1">{c.body}</p>
                  </div>} />
              )}
              {tab === "tasks" && (
                <div className="space-y-2" data-testid="case-tasks">
                  {tasks.length === 0 && <p className="text-slate-500 text-sm">{t("No safety tasks yet.")}</p>}
                  {tasks.map((tk) => (
                    <div key={tk.id} className="rounded-lg border border-slate-200 bg-white p-3 flex items-center justify-between" data-testid={`case-tasks-row-${tk.id}`}>
                      <div>
                        <div className="font-semibold">{tk.title}</div>
                        <div className="text-xs text-slate-500">{tk.assigned_to_name || "—"} · {t("Due")}: {tk.due_at || "—"}</div>
                      </div>
                      <select className="h-9 rounded-md border border-slate-300 px-2 text-sm"
                        value={tk.status} onChange={async (e) => { await api.updateTask(caseId, tk.id, { status: e.target.value }); await refreshAll(); }}
                        data-testid={`case-tasks-row-${tk.id}-status`}>
                        {["open", "in_progress", "blocked", "completed", "canceled"].map((s) => (
                          <option key={s} value={s}>{t(s.replace(/_/g, " "))}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              )}
              {tab === "linked" && (
                <div data-testid="case-linked">
                  {caseDoc?.cross_links?.length ? (
                    <ul className="space-y-1">
                      {caseDoc.cross_links.map((l) => (
                        <li key={l.id} className="text-sm">
                          <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">{l.kind}</span>
                          {" · "}{l.target_label || l.target_id}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-slate-500 text-sm">{t("No linked records yet.")}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        <aside className="space-y-4">
          <ExecutiveSnapshot snap={snap} />
          <CaseHealth health={health} />
        </aside>
      </main>
    </div>
  );
}
