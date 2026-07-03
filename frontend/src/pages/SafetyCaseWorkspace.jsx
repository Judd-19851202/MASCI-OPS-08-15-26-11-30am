// Track 19.16 · Phase C · Safety Case Workspace.
// The command center for post-report investigation.
// Track 19.18 · Operational Readiness Review polish — Case Story,
// Next Action, visual timeline spine, clickable blockers.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import * as api from "@/lib/caseWorkspaceApi";
import { INCIDENT_FLOWS } from "@/lib/incidentReportSchema";
import {
  Activity, AlertTriangle, ArrowRight, CheckCircle2, ChevronLeft, Clipboard,
  FileText, Heart, Lock, MessageSquare, Paperclip, Shield, Users, Wrench,
} from "lucide-react";

const TABS = [
  // Track 19.35 · Field Facts tab — always first · always immutable.
  // Anchors the Safety investigation in the original field report.
  { key: "field_facts",    label: "Field Facts",        icon: Lock },
  { key: "timeline",       label: "Timeline",           icon: Activity },
  { key: "evidence",       label: "Evidence",           icon: Paperclip },
  { key: "witnesses",      label: "Witnesses",          icon: Users },
  { key: "medical",        label: "Medical",            icon: Heart },
  { key: "agency",         label: "Police / Agency",    icon: Shield },
  { key: "rca",            label: "Root Cause",         icon: AlertTriangle },
  { key: "capa",           label: "Corrective Actions", icon: Wrench },
  { key: "communications", label: "Communications",     icon: MessageSquare },
  { key: "tasks",          label: "Safety Tasks",       icon: Clipboard },
  { key: "linked",         label: "Linked Records",     icon: FileText },
  // Track 19.35 · Closeout tab — final classification · safety approval · management review.
  { key: "closeout",       label: "Closeout",           icon: CheckCircle2 },
];

// Track 19.18 · which tab resolves which blocker key.
// Safety Director should be able to jump to the resolving screen with one click.
const BLOCKER_TAB = {
  missing_root_cause: "rca",
  missing_contributing_factors: "rca",
  no_evidence: "evidence",
  no_photos: "evidence",
  no_witnesses: "witnesses",
  missing_medical: "medical",
  missing_agency: "agency",
  missing_corrective_actions: "capa",
  open_corrective_actions: "capa",
  open_tasks: "tasks",
  pending_communications: "communications",
};

function _fmt(dt) {
  if (!dt) return "—";
  try { return new Date(dt).toLocaleString(); } catch { return dt; }
}

function _fmtDate(dt) {
  if (!dt) return "";
  try { return new Date(dt).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }); } catch { return dt; }
}

function _fmtTime(dt) {
  if (!dt) return "";
  try { return new Date(dt).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }); } catch { return ""; }
}

// Track 19.18 · Compose a one-paragraph "case story" straight from field_block.
// Order matches the 12-question Complete Story Validation contract:
// what → where → when → who → what-immediately.
function composeCaseStory(caseDoc, t) {
  if (!caseDoc) return "";
  const fb = caseDoc.field_block || {};
  const flow = INCIDENT_FLOWS[fb.incident_type];
  const typeLabel = flow ? t(flow.label) : t("Incident");
  const dateStr = fb.occurred_at_date ? _fmtDate(fb.occurred_at_date) : (caseDoc.submitted_at ? _fmtDate(caseDoc.submitted_at) : t("an unrecorded date"));
  const timeStr = fb.occurred_at_time || (caseDoc.submitted_at ? _fmtTime(caseDoc.submitted_at) : "");
  const when = timeStr ? `${dateStr} · ${timeStr}` : dateStr;
  const where = fb.location_label ? fb.location_label : t("an unspecified location");
  const job = fb.job_number ? ` (${t("Job")} ${fb.job_number})` : "";
  const who = fb.reporter_name ? `${fb.reporter_name}${fb.reporter_role ? ` · ${fb.reporter_role}` : ""}` : t("the on-site reporter");
  const detail = (fb.observed_conditions || "").trim();
  const detailClip = detail.length > 220 ? `${detail.slice(0, 217).trim()}…` : detail;
  const line1 = t("On {when}, a {type} was reported at {where}{job}.")
    .replace("{when}", when).replace("{type}", typeLabel).replace("{where}", where).replace("{job}", job);
  const line2 = t("Reported by {who}.").replace("{who}", who);
  return detailClip ? `${line1} ${line2} ${detailClip}` : `${line1} ${line2}`;
}

function CaseHeader({ caseDoc, health, onJumpToBlocker }) {
  const { t } = useT();
  if (!caseDoc) return null;
  const fb = caseDoc.field_block || {};
  const flow = INCIDENT_FLOWS[fb.incident_type];
  const daysOpen = caseDoc.submitted_at
    ? Math.max(0, Math.floor((Date.now() - new Date(caseDoc.submitted_at).getTime()) / 86400000))
    : 0;
  const story = composeCaseStory(caseDoc, t);
  const nextBlocker = (health?.blockers || [])[0] || null;
  const nextLabel = nextBlocker ? t(nextBlocker.replace(/_/g, " ")) : "";
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
      {/* Track 19.18 · Case Story · always-visible one-paragraph narrative */}
      {story && (
        <p
          className="mt-3 text-[13.5px] leading-relaxed text-slate-700 border-l-4 border-slate-300 pl-3"
          data-testid="case-header-story"
        >
          {story}
        </p>
      )}
      {/* Track 19.18 · Next Action · clickable jump to the resolving tab */}
      {nextBlocker && onJumpToBlocker && (
        <button
          type="button"
          onClick={() => onJumpToBlocker(nextBlocker)}
          className="mt-3 inline-flex items-center gap-2 rounded-md bg-amber-100 border border-amber-300 px-3 py-1.5 text-sm font-semibold text-amber-900 hover:bg-amber-200"
          data-testid="case-header-next-action"
        >
          <AlertTriangle className="w-3.5 h-3.5" aria-hidden />
          {t("Next action")}: {nextLabel}
          <ArrowRight className="w-3.5 h-3.5" aria-hidden />
        </button>
      )}
    </div>
  );
}

function CaseHealth({ health, onJumpToBlocker }) {
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
            <li key={b}>
              <button
                type="button"
                onClick={() => onJumpToBlocker && onJumpToBlocker(b)}
                className="w-full flex items-center gap-2 text-left text-amber-800 hover:text-amber-900 hover:underline"
                data-testid={`case-health-blocker-${b}`}
              >
                <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden />
                <span>{t(b.replace(/_/g, " "))}</span>
                <ArrowRight className="w-3 h-3 ml-auto opacity-60" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
      {/* Counts only render when there is at least one non-zero — Track 19.18 empty-state elimination */}
      {(() => {
        const nonZero = Object.entries(health.counts || {}).filter(([, v]) => v !== 0 && v !== null && v !== undefined);
        if (nonZero.length === 0) return null;
        return (
          <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
            {nonZero.map(([k, v]) => (
              <div key={k} className="rounded-md bg-slate-50 border border-slate-200 px-2 py-1">
                <dt className="font-mono text-[9px] uppercase tracking-[0.14em] text-slate-500">{t(k.replace(/_/g, " "))}</dt>
                <dd className="font-bold text-slate-900">{v}</dd>
              </div>
            ))}
          </dl>
        );
      })()}
    </div>
  );
}

function ExecutiveSnapshot({ snap }) {
  const { t } = useT();
  if (!snap) return null;
  // Track 19.18 · Operational Confidence · single one-liner headline first.
  const pct = snap.readiness?.completeness_pct || 0;
  const readinessLabel = pct >= 80 ? t("Ready for closeout") : pct >= 50 ? t("Under investigation") : t("Early — evidence gathering");
  return (
    <div className="rounded-xl border-2 border-slate-900 bg-slate-900 text-white p-4" data-testid="case-exec-snapshot">
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400">{t("Executive snapshot")}</div>
      <div className="mt-1 font-display text-base font-black leading-snug" data-testid="case-exec-snapshot-headline">
        {readinessLabel} · {pct}%
      </div>
      <div className="mt-3 grid gap-1.5 text-sm">
        <div><span className="text-slate-400">{t("Incident")}: </span><span className="font-semibold">{snap.incident_type?.replace(/_/g, " ")}</span></div>
        {snap.osha_recordable != null && (
          <div><span className="text-slate-400">{t("OSHA recordable")}: </span><span className="font-semibold">{snap.osha_recordable ? t("Yes") : t("No")}</span></div>
        )}
        {snap.lost_time_days > 0 && (
          <div><span className="text-slate-400">{t("Lost time (days)")}: </span><span className="font-semibold">{snap.lost_time_days}</span></div>
        )}
        <div><span className="text-slate-400">{t("Root cause")}: </span><span className="font-semibold">{snap.root_cause_summary ? "✓" : t("Pending")}</span></div>
      </div>
    </div>
  );
}

// Track 19.18 · Timeline spine — vertical rail with dots color-coded by event kind.
// Reads chronologically at a glance so a VP/OSHA investigator sees the story flow.
function _timelineDotColor(evType) {
  const t = (evType || "").toLowerCase();
  if (t.includes("state") || t.includes("closed") || t.includes("submitted")) return "bg-slate-900";
  if (t.includes("evidence") || t.includes("photo")) return "bg-blue-600";
  if (t.includes("witness") || t.includes("statement")) return "bg-purple-600";
  if (t.includes("medical") || t.includes("agency") || t.includes("police")) return "bg-red-600";
  if (t.includes("capa") || t.includes("corrective") || t.includes("verified")) return "bg-emerald-600";
  if (t.includes("comm") || t.includes("notif")) return "bg-amber-600";
  return "bg-slate-500";
}

function TimelinePanel({ events }) {
  const { t } = useT();
  if (!events || events.length === 0) {
    return <p className="text-slate-500 text-sm" data-testid="case-timeline-empty">{t("No timeline entries yet.")}</p>;
  }
  return (
    <ol className="relative space-y-4 pl-6 before:absolute before:left-2 before:top-1 before:bottom-1 before:w-px before:bg-slate-200" data-testid="case-timeline">
      {events.map((e) => (
        <li key={e.id} className="relative" data-testid={`case-timeline-event-${e.id}`}>
          <span
            className={`absolute -left-[18px] top-2 w-3 h-3 rounded-full ring-2 ring-white ${_timelineDotColor(e.event_type)}`}
            aria-hidden
          />
          <div className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">{e.event_type}</span>
              <span className="text-[11px] text-slate-500">{_fmt(e.at)}</span>
            </div>
            <div className="text-sm text-slate-800 mt-1">
              {e.actor_name || e.actor_role} · {e.from_state && `${e.from_state} → `}{e.to_state || ""}
            </div>
            {e.reason && <div className="text-xs text-slate-600 mt-1">{t("Reason")}: {e.reason}</div>}
          </div>
        </li>
      ))}
    </ol>
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
  // Track 19.35 · Default tab is Field Facts (immutable anchor) so every
  // Safety Manager opening a case starts by reviewing what the field said,
  // not by jumping into investigation notes.
  const [tab, setTab] = useState("field_facts");
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

  // Track 19.18 · Clicking a blocker jumps to the tab that resolves it.
  const jumpToBlocker = useCallback((blockerKey) => {
    const target = BLOCKER_TAB[blockerKey];
    if (target) setTab(target);
  }, []);

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
        {/* Track 19.36 · deep-link to boardroom-grade Executive Case Report. */}
        <button
          onClick={() => navigate(`/safety/cases/${caseId}/executive-report`)}
          className="ml-auto inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          data-testid="case-workspace-open-executive-report"
        >
          <FileText className="w-3.5 h-3.5" aria-hidden /> {t("Executive Report")}
        </button>
        {/* Track 19.58 · deep-link to the Universal Incident Thread. */}
        <button
          onClick={() => navigate(`/safety/incidents/${caseId}/thread`)}
          className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          data-testid="safety-case-open-thread-link"
        >
          {t("Universal Thread")}
        </button>
      </header>

      <main className="max-w-7xl mx-auto p-4 sm:p-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          <CaseHeader caseDoc={caseDoc} health={health} onJumpToBlocker={jumpToBlocker} />
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
              {/* Track 19.35 · Field Facts tab · immutable field report anchor. */}
              {tab === "field_facts" && (
                <div className="space-y-3" data-testid="case-field-facts">
                  <div className="flex items-start gap-2 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2">
                    <Lock className="w-4 h-4 mt-0.5 shrink-0 text-slate-500" aria-hidden />
                    <div className="text-[13px] leading-snug">
                      <span className="font-semibold text-slate-800">{t("Original Field Report — locked record.")}</span>{" "}
                      <span>{t("Facts captured by the field. Cannot be edited from the Safety workspace. Investigation notes, root cause, and OSHA review are recorded in the other tabs.")}</span>
                    </div>
                  </div>
                  <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    <div><dt className="text-slate-500 text-xs uppercase tracking-widest font-mono">{t("Incident type")}</dt><dd className="font-semibold" data-testid="case-field-facts-type">{caseDoc?.incident_type ? t(INCIDENT_FLOWS[caseDoc.incident_type]?.label || caseDoc.incident_type) : "—"}</dd></div>
                    <div><dt className="text-slate-500 text-xs uppercase tracking-widest font-mono">{t("Occurred at")}</dt><dd className="font-semibold">{_fmt(caseDoc?.occurred_at) || "—"}</dd></div>
                    <div><dt className="text-slate-500 text-xs uppercase tracking-widest font-mono">{t("Reporter")}</dt><dd className="font-semibold">{caseDoc?.reporter_name || "—"}</dd></div>
                    <div><dt className="text-slate-500 text-xs uppercase tracking-widest font-mono">{t("Location")}</dt><dd className="font-semibold">{caseDoc?.location || caseDoc?.gps || "—"}</dd></div>
                    <div className="sm:col-span-2"><dt className="text-slate-500 text-xs uppercase tracking-widest font-mono">{t("Summary")}</dt><dd className="whitespace-pre-line">{caseDoc?.summary || caseDoc?.description || "—"}</dd></div>
                    <div className="sm:col-span-2"><dt className="text-slate-500 text-xs uppercase tracking-widest font-mono">{t("Immediate actions")}</dt><dd className="whitespace-pre-line">{caseDoc?.immediate_actions || "—"}</dd></div>
                  </dl>
                </div>
              )}
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
              {/* Track 19.35 · Closeout tab · final classification · Safety approval · management review. */}
              {tab === "closeout" && (
                <div className="space-y-3" data-testid="case-closeout">
                  <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
                    <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-emerald-700" aria-hidden />
                    <div className="text-[13px] leading-snug text-emerald-900">
                      <span className="font-semibold">{t("Case closeout checklist.")}</span>{" "}
                      <span>{t("Confirm each area before final closure. Original field report remains locked · closeout does not destroy history.")}</span>
                    </div>
                  </div>
                  <ul className="space-y-2 text-sm" data-testid="case-closeout-checklist">
                    <li className="flex items-start gap-2"><CheckCircle2 className={`w-4 h-4 mt-0.5 shrink-0 ${(evidence?.length || 0) > 0 ? "text-emerald-600" : "text-slate-300"}`} /><span>{t("Evidence collected")} {(evidence?.length || 0) > 0 ? "✓" : ""}</span></li>
                    <li className="flex items-start gap-2"><CheckCircle2 className={`w-4 h-4 mt-0.5 shrink-0 ${(witnesses?.length || 0) > 0 ? "text-emerald-600" : "text-slate-300"}`} /><span>{t("Witness statements recorded")} {(witnesses?.length || 0) > 0 ? "✓" : ""}</span></li>
                    <li className="flex items-start gap-2"><CheckCircle2 className={`w-4 h-4 mt-0.5 shrink-0 ${caseDoc?.safety_block?.root_cause ? "text-emerald-600" : "text-slate-300"}`} /><span>{t("Root cause / findings documented")} {caseDoc?.safety_block?.root_cause ? "✓" : ""}</span></li>
                    <li className="flex items-start gap-2"><CheckCircle2 className={`w-4 h-4 mt-0.5 shrink-0 ${(capa?.length || 0) > 0 ? "text-emerald-600" : "text-slate-300"}`} /><span>{t("Corrective actions assigned")} {(capa?.length || 0) > 0 ? "✓" : ""}</span></li>
                    <li className="flex items-start gap-2"><CheckCircle2 className={`w-4 h-4 mt-0.5 shrink-0 ${(agency?.length || 0) > 0 ? "text-emerald-600" : "text-slate-300"}`} /><span>{t("Regulatory / agency contacts logged")} {(agency?.length || 0) > 0 ? "✓" : ""}</span></li>
                  </ul>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-[13px] text-slate-700" data-testid="case-closeout-status">
                    <div><strong>{t("Current status")}:</strong> {t(caseDoc?.status || "open")}</div>
                    <div className="mt-1 text-slate-500 text-xs">{t("Final closure state is set from the Executive header. This tab surfaces what's still open.")}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <aside className="space-y-4">
          <ExecutiveSnapshot snap={snap} />
          <CaseHealth health={health} onJumpToBlocker={jumpToBlocker} />
        </aside>
      </main>
    </div>
  );
}
