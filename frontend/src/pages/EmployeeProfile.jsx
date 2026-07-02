// Track 19.21 · Employee 360° · single-page consolidated profile view.
// Reads GET /api/hr/employees/{id}/accountability/timeline (already
// exists; fans out across 10 sources including Track 19.21 incident
// cases) and renders the "one complete lifecycle" view.
//
// Design pattern mirrors SafetyCaseWorkspace (Track 19.18):
//   * Identity header with auto-composed Employee Story paragraph
//   * Next-Action chip driven by expiring/expired counts
//   * Visual timeline spine with color-coded category dots
//   * Right rail with Current State + Category totals + HR Brief PDF export
//
// Zero drift: reads only. No mutation from this page.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import {
  Activity, AlertTriangle, ArrowLeft, CheckCircle2, ClipboardList,
  Download, FileText, HardHat, Shield, User, Wrench,
} from "lucide-react";

// ── Category → dot colour ───────────────────────────────────────────
const CAT_COLOR = {
  "Training":              "bg-blue-600",
  "PPE & Equipment":       "bg-emerald-600",
  "Incidents":             "bg-red-600",
  "Field Leadership":      "bg-amber-600",
  "Driver Qualification":  "bg-purple-600",
  "HR Lifecycle":          "bg-slate-900",
};

const CAT_ICON = {
  "Training":             ClipboardList,
  "PPE & Equipment":      HardHat,
  "Incidents":            AlertTriangle,
  "Field Leadership":     Shield,
  "Driver Qualification": FileText,
  "HR Lifecycle":         User,
};

function _fmt(dt) {
  if (!dt) return "—";
  try { return new Date(dt).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }); }
  catch { return dt; }
}

// Auto-compose Employee Story paragraph — mirrors composeCaseStory in
// SafetyCaseWorkspace. Reads only from the aggregate response.
function composeEmployeeStory(emp, current, t) {
  if (!emp) return "";
  const trade = emp.trade || t("worker");
  const dept = emp.department ? ` for the ${emp.department} Department` : "";
  const hire = emp.hire_date ? _fmt(emp.hire_date) : t("an unrecorded date");
  const status = emp.lifecycle_status || (current?.is_active ? "Active" : "Inactive");
  const cdlBit = current?.cdl_holder
    ? ` · ${t("Approved company driver")}${current.cdl_state ? ` · ${t("CDL")} ${current.cdl_state}` : ""}`
    : "";
  return `${t("Hired")} ${hire} ${t("as a")} ${trade}${dept}. ${t("Currently")} ${status}.${cdlBit}`;
}

function _tokenHeader() {
  const token = localStorage.getItem("safetyToken")
    || localStorage.getItem("adminToken")
    || localStorage.getItem("pmToken");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function EmployeeProfile() {
  const { empId } = useParams();
  const navigate = useNavigate();
  const { t } = useT();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("timeline");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/hr/employees/${empId}/accountability/timeline`,
        { headers: { "Content-Type": "application/json", ..._tokenHeader() } },
      );
      if (!res.ok) throw new Error(`Failed to load employee (${res.status})`);
      setData(await res.json());
      setErr(null);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }, [empId]);

  useEffect(() => { load(); }, [load]);

  const filteredEvents = useMemo(() => {
    if (!data) return [];
    if (tab === "timeline") return data.events || [];
    const catMap = {
      training:   "Training",
      ppe:        "PPE & Equipment",
      incidents:  "Incidents",
      discipline: "Field Leadership",
      driver:     "Driver Qualification",
      hr:         "HR Lifecycle",
    };
    const targetCat = catMap[tab];
    return (data.events || []).filter((e) => e.category === targetCat);
  }, [data, tab]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500 font-mono text-sm" data-testid="employee-profile-loading">
          {t("Loading employee record…")}
        </div>
      </div>
    );
  }

  if (err || !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="max-w-md p-6 rounded-xl border-2 border-red-300 bg-white">
          <div className="font-display text-lg font-black text-red-900" data-testid="employee-profile-error">
            {t("Could not load employee")}
          </div>
          <p className="mt-2 text-sm text-slate-600">{err || t("Unknown error")}</p>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="mt-4 inline-flex items-center gap-2 rounded-md bg-slate-900 text-white px-3 py-1.5 text-sm font-semibold"
            data-testid="employee-profile-back"
          >
            <ArrowLeft className="w-4 h-4" /> {t("Back")}
          </button>
        </div>
      </div>
    );
  }

  const { employee: emp, current_state: cur, category_counts: cats, events, expiring_within_90d, expired_items, total_events } = data;
  const story = composeEmployeeStory(emp, cur, t);
  const daysTenure = emp?.hire_date
    ? Math.max(0, Math.floor((Date.now() - new Date(emp.hire_date).getTime()) / 86400000))
    : 0;
  const nextExpiring = expiring_within_90d?.[0];

  const tabs = [
    { key: "timeline",   label: "All timeline",        icon: Activity },
    { key: "training",   label: "Training",            icon: ClipboardList },
    { key: "ppe",        label: "PPE / Assets",        icon: HardHat },
    { key: "incidents",  label: "Incidents",           icon: AlertTriangle },
    { key: "discipline", label: "Discipline",          icon: Shield },
    { key: "driver",     label: "Driver Qual",         icon: FileText },
    { key: "hr",         label: "HR Lifecycle",        icon: User },
  ];

  return (
    <div className="min-h-screen bg-slate-50" data-testid="employee-profile">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
          data-testid="employee-profile-back"
        >
          <ArrowLeft className="w-4 h-4" /> {t("Back")}
        </button>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4">
            {/* Identity header */}
            <div className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5" data-testid="employee-profile-header">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                    {t("Employee")} · {emp.employee_id || emp.id?.slice(0, 8) || "—"}
                  </div>
                  <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900" data-testid="employee-profile-name">
                    {emp.name || t("Unknown")}
                  </h1>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-700">
                    <span>{emp.trade || "—"}</span>
                    <span>{emp.department || "—"}</span>
                    <span>{t("Supervisor")}: {emp.supervisor || "—"}</span>
                    <span>
                      <span className="rounded-md bg-slate-900 text-white px-2 py-0.5 text-[10px] font-mono tracking-widest">
                        {emp.lifecycle_status || "Active"}
                      </span>
                    </span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Days tenure")}</div>
                  <div className="font-display text-2xl font-black text-slate-900" data-testid="employee-profile-days-tenure">{daysTenure}</div>
                </div>
              </div>
              {story && (
                <p className="mt-3 text-[13.5px] leading-relaxed text-slate-700 border-l-4 border-slate-300 pl-3"
                   data-testid="employee-profile-story">
                  {story}
                </p>
              )}
              {nextExpiring && (
                <div className="mt-3 inline-flex items-center gap-2 rounded-md bg-amber-100 border border-amber-300 px-3 py-1.5 text-sm font-semibold text-amber-900"
                     data-testid="employee-profile-next-action">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  {t("Next action")}: {nextExpiring.title} · {t("expires")} {_fmt(nextExpiring.expiration_date)}
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="rounded-xl border-2 border-slate-300 bg-white p-2 flex flex-wrap gap-1" data-testid="employee-profile-tabs">
              {tabs.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setTab(key)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors ${
                    tab === key ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                  }`}
                  data-testid={`employee-profile-tab-${key}`}
                >
                  <Icon className="w-3.5 h-3.5" /> {t(label)}
                </button>
              ))}
            </div>

            {/* Timeline spine — same pattern as SafetyCaseWorkspace */}
            <div className="rounded-xl border-2 border-slate-300 bg-white p-4" data-testid="employee-profile-timeline-wrap">
              <div className="flex items-center justify-between mb-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {tab === "timeline" ? t("Complete lifecycle") : t(tabs.find(x => x.key === tab)?.label || "")}
                </div>
                <div className="text-xs text-slate-500">
                  {filteredEvents.length} / {total_events} {t("events")}
                </div>
              </div>
              {filteredEvents.length === 0 ? (
                <p className="text-slate-500 text-sm" data-testid="employee-profile-timeline-empty">
                  {t("No entries in this category yet.")}
                </p>
              ) : (
                <ol className="relative space-y-3 pl-6 before:absolute before:left-2 before:top-1 before:bottom-1 before:w-px before:bg-slate-200"
                    data-testid="employee-profile-timeline">
                  {filteredEvents.slice(0, 200).map((e) => {
                    const CIcon = CAT_ICON[e.category] || Activity;
                    return (
                      <li key={e.id} className="relative" data-testid={`employee-event-${e.source}-${e.source_id}`}>
                        <span className={`absolute -left-[18px] top-2 w-3 h-3 rounded-full ring-2 ring-white ${CAT_COLOR[e.category] || "bg-slate-500"}`} />
                        <div className="rounded-lg border border-slate-200 bg-white p-3">
                          <div className="flex items-center justify-between gap-2">
                            <span className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
                              <CIcon className="w-3 h-3" /> {e.category}
                            </span>
                            <span className="text-[11px] text-slate-500">{_fmt(e.ts)}</span>
                          </div>
                          <div className="text-sm font-semibold text-slate-900 mt-1">{e.title}</div>
                          {e.description && (
                            <div className="text-xs text-slate-600 mt-0.5">{e.description}</div>
                          )}
                          {e.expiration_date && (
                            <div className="text-[11px] text-amber-800 mt-1">
                              {t("Expires")}: {_fmt(e.expiration_date)}
                            </div>
                          )}
                          {e.archived && (
                            <div className="text-[10px] text-slate-500 italic mt-1">{t("Archived")}</div>
                          )}
                        </div>
                      </li>
                    );
                  })}
                </ol>
              )}
            </div>
          </div>

          {/* Right rail */}
          <aside className="space-y-4">
            {/* Executive one-liner */}
            <div className="rounded-xl border-2 border-slate-900 bg-slate-900 text-white p-4" data-testid="employee-profile-exec">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400">{t("Current state")}</div>
              <div className="mt-1 font-display text-base font-black leading-snug" data-testid="employee-profile-exec-headline">
                {emp.lifecycle_status || "Active"}
                {cur?.expired > 0 && ` · ${cur.expired} ${t("expired")}`}
                {cur?.expiring_within_90d > 0 && ` · ${cur.expiring_within_90d} ${t("expiring")}`}
              </div>
              <div className="mt-3 grid gap-1.5 text-sm">
                {cur?.cdl_holder && (
                  <div><span className="text-slate-400">{t("CDL")}: </span><span className="font-semibold">
                    {cur.cdl_state || "—"} · {t("Expires")} {_fmt(cur.cdl_expiration_date)}
                  </span></div>
                )}
                {cur?.last_training && (
                  <div><span className="text-slate-400">{t("Last training")}: </span><span className="font-semibold">{_fmt(cur.last_training)}</span></div>
                )}
                {cur?.last_ppe_issuance && (
                  <div><span className="text-slate-400">{t("Last PPE issued")}: </span><span className="font-semibold">{_fmt(cur.last_ppe_issuance)}</span></div>
                )}
                {cur?.last_incident && (
                  <div><span className="text-slate-400">{t("Last incident")}: </span><span className="font-semibold">{_fmt(cur.last_incident)}</span></div>
                )}
              </div>
            </div>

            {/* Category totals (empty-state elimination) */}
            {cats && Object.keys(cats).length > 0 && (
              <div className="rounded-xl border-2 border-slate-300 bg-white p-4" data-testid="employee-profile-category-counts">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 mb-2">
                  {t("Records by category")}
                </div>
                <dl className="grid grid-cols-2 gap-2 text-xs">
                  {Object.entries(cats).filter(([, v]) => v > 0).map(([k, v]) => (
                    <div key={k} className="rounded-md bg-slate-50 border border-slate-200 px-2 py-1.5">
                      <dt className="font-mono text-[9px] uppercase tracking-[0.14em] text-slate-500">{t(k)}</dt>
                      <dd className="font-bold text-slate-900">{v}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {/* HR Compliance Brief PDF export (existing endpoint) */}
            <div className="rounded-xl border-2 border-slate-300 bg-white p-4" data-testid="employee-profile-exports">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 mb-2">
                {t("Exports")}
              </div>
              <a
                href={`${process.env.REACT_APP_BACKEND_URL}/api/hr/employees/${empId}/accountability/brief.pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-md bg-slate-900 text-white px-3 py-1.5 text-sm font-semibold hover:bg-slate-800"
                data-testid="employee-profile-brief-pdf"
              >
                <Download className="w-3.5 h-3.5" /> {t("HR Compliance Brief (PDF)")}
              </a>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
