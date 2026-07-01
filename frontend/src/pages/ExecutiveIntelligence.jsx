// Track 19.16 · Phase D · Executive Intelligence Center.
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import axios from "axios";
import { AlertTriangle, ArrowUpRight, TrendingDown, TrendingUp, Activity } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function _headers() {
  const h = { "Content-Type": "application/json" };
  try {
    const s = localStorage.getItem("safety_token");
    const a = localStorage.getItem("admin_token");
    const p = localStorage.getItem("pm_token");
    if (s) h["X-Safety-Token"] = s;
    if (a) h["X-Admin-Token"] = a;
    if (p) h["X-PM-Token"] = p;
  } catch {}
  return h;
}
const c = () => axios.create({ baseURL: API, headers: _headers(), timeout: 20000 });

async function loadAll() {
  const [home, rc, capa, projects, fleet, learn, brief] = await Promise.all([
    c().get("/incident-intelligence/home").then(r => r.data),
    c().get("/incident-intelligence/root-causes").then(r => r.data).catch(() => null),
    c().get("/incident-intelligence/corrective-actions").then(r => r.data).catch(() => null),
    c().get("/incident-intelligence/projects").then(r => r.data).catch(() => null),
    c().get("/incident-intelligence/fleet").then(r => r.data).catch(() => null),
    c().get("/incident-intelligence/learning").then(r => r.data).catch(() => null),
    c().get("/incident-intelligence/brief").then(r => r.data).catch(() => null),
  ]);
  return { home, rc, capa, projects, fleet, learn, brief };
}

function KpiCard({ label, value, sub, testId, tone }) {
  const tones = {
    critical: "border-red-400 bg-red-50 text-red-900",
    warn:     "border-amber-400 bg-amber-50 text-amber-900",
    ok:       "border-emerald-300 bg-emerald-50 text-emerald-900",
    default:  "border-slate-300 bg-white text-slate-900",
  };
  return (
    <div className={`rounded-xl border-2 p-4 ${tones[tone || "default"]}`} data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] opacity-70">{label}</div>
      <div className="font-display text-3xl font-black mt-1">{value}</div>
      {sub && <div className="text-xs mt-1 opacity-80">{sub}</div>}
    </div>
  );
}

function SlaChip({ label, count, tone, testId }) {
  const tones = {
    ok: "bg-emerald-100 text-emerald-900 border-emerald-300",
    watch: "bg-amber-100 text-amber-900 border-amber-300",
    behind: "bg-orange-100 text-orange-900 border-orange-400",
    missed: "bg-red-100 text-red-900 border-red-500",
    unset: "bg-slate-100 text-slate-700 border-slate-300",
  };
  return (
    <div className={`inline-flex items-baseline gap-2 rounded-md border px-3 py-2 ${tones[tone]}`} data-testid={testId}>
      <span className="font-display font-black text-2xl">{count}</span>
      <span className="font-mono text-[10px] uppercase tracking-widest">{label}</span>
    </div>
  );
}

export default function ExecutiveIntelligence() {
  const { t } = useT();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    loadAll().then(setData).catch((e) => setErr(e?.response?.data?.detail?.detail || e.message));
  }, []);

  if (err) {
    return (
      <div className="min-h-screen bg-slate-50 p-6" data-testid="executive-intelligence-error">
        <div className="max-w-md rounded-xl border-2 border-red-300 bg-white p-6 mx-auto">
          <div className="font-mono text-[10px] uppercase tracking-widest text-red-800">{t("Error")}</div>
          <div className="font-display text-xl font-black">{t("Could not load intelligence")}</div>
          <p className="text-sm text-slate-700 mt-2">{err}</p>
          <button className="mt-4 h-10 px-4 rounded-md bg-slate-900 text-white" onClick={() => navigate(-1)}>{t("Back")}</button>
        </div>
      </div>
    );
  }
  if (!data) {
    return <div className="min-h-screen bg-slate-50 p-6" data-testid="executive-intelligence-loading">{t("Loading intelligence…")}</div>;
  }

  const H = data.home?.company_health || {};
  const trend = H.trend_30d || "flat";
  const TrendIcon = trend === "worsening" ? TrendingUp : trend === "improving" ? TrendingDown : Activity;
  const trendTone = trend === "worsening" ? "text-red-700" : trend === "improving" ? "text-emerald-700" : "text-slate-600";

  return (
    <div className="min-h-screen bg-slate-50" data-testid="executive-intelligence">
      <header className="bg-slate-900 text-white px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400">{t("Executive Intelligence Center")}</div>
            <h1 className="font-display text-xl sm:text-2xl font-black">{t("What needs your attention today")}</h1>
          </div>
          <div className={`inline-flex items-center gap-1 ${trendTone}`} data-testid="exec-intel-trend">
            <TrendIcon className="w-4 h-4" aria-hidden />
            <span className="font-mono text-[11px] uppercase tracking-widest">{t(`Trend ${trend}`)}</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
        {/* Top KPI row */}
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="exec-intel-kpis">
          <KpiCard label={t("Open cases")}       value={H.open_cases ?? 0}          testId="kpi-open"      tone={H.open_cases > 0 ? "default" : "ok"} />
          <KpiCard label={t("Critical cases")}   value={H.critical_cases ?? 0}      testId="kpi-critical"  tone={H.critical_cases > 0 ? "critical" : "ok"} />
          <KpiCard label={t("Avg readiness")}    value={`${H.avg_readiness_pct ?? 0}%`} testId="kpi-readiness" tone={(H.avg_readiness_pct||0) >= 70 ? "ok" : "warn"} />
          <KpiCard label={t("Open CAPAs")}       value={H.corrective_actions_open ?? 0} testId="kpi-capa"    sub={`${H.corrective_actions_total ?? 0} ${t("total")}`} tone={H.corrective_actions_open > 5 ? "warn" : "default"} />
        </section>

        {/* SLA row */}
        <section className="rounded-xl border-2 border-slate-300 bg-white p-4" data-testid="exec-intel-sla">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Case Health SLA")}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <SlaChip label={t("On pace")} count={H.sla?.on_pace ?? 0} tone="ok"     testId="sla-on-pace" />
            <SlaChip label={t("Watch")}   count={H.sla?.watch   ?? 0} tone="watch"  testId="sla-watch" />
            <SlaChip label={t("Behind")}  count={H.sla?.behind  ?? 0} tone="behind" testId="sla-behind" />
            <SlaChip label={t("Missed")}  count={H.sla?.missed  ?? 0} tone="missed" testId="sla-missed" />
            <SlaChip label={t("Unset")}   count={H.sla?.unset   ?? 0} tone="unset"  testId="sla-unset" />
          </div>
        </section>

        {/* Action Queue */}
        <section className="rounded-xl border-2 border-slate-900 bg-white" data-testid="exec-intel-action-queue">
          <div className="border-b border-slate-200 px-4 py-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Leadership action queue")}</div>
            <div className="font-display text-lg font-black text-slate-900">{t("Cases requiring executive action")}</div>
          </div>
          {(data.home?.action_queue || []).length === 0 ? (
            <div className="p-6 text-sm text-slate-600">{t("Nothing needs your attention right now. Nice.")}</div>
          ) : (
            <ul className="divide-y divide-slate-200">
              {(data.home.action_queue || []).map((row) => (
                <li key={row.case_id} className="p-4 flex items-start justify-between gap-3 hover:bg-slate-50 cursor-pointer" onClick={() => navigate(`/safety/cases/${row.case_id}`)} data-testid={`action-queue-row-${row.case_id}`}>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">#{row.case_number || row.case_id.slice(0,8)}</span>
                      <span className="rounded-md bg-slate-900 text-white text-[10px] px-2 py-0.5 font-mono uppercase">{row.state}</span>
                    </div>
                    <div className="font-semibold text-slate-900 mt-1">{t(row.incident_type.replace(/_/g," "))} · {row.location_label}</div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {row.reasons.map((r) => (
                        <span key={r} className="rounded bg-red-50 border border-red-300 text-red-800 text-[10px] font-mono uppercase tracking-widest px-2 py-0.5">{t(r.replace(/_/g," "))}</span>
                      ))}
                    </div>
                    <div className="text-xs text-slate-600 mt-1">{t("Age")}: {row.age_days}d · {t("Recommended")}: <span className="font-semibold">{t(row.recommended_action.replace(/_/g," "))}</span></div>
                  </div>
                  <ArrowUpRight className="w-5 h-5 text-slate-400 shrink-0 mt-1" aria-hidden />
                </li>
              ))}
            </ul>
          )}
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          {/* Root Cause Intelligence */}
          <section className="rounded-xl border border-slate-300 bg-white p-4" data-testid="exec-intel-root-causes">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Root Cause Intelligence")}</div>
            <div className="mt-2 space-y-1">
              {(data.rc?.categories || []).slice(0, 6).map((c) => (
                <div key={c.code} className="flex items-center justify-between text-sm py-1">
                  <span className="capitalize">{t(c.code.replace(/_/g," "))}</span>
                  <span className="font-mono">{c.count}<span className="ml-2 text-xs text-red-700">{c.severity_weighted ? `+${c.severity_weighted} sev` : ""}</span></span>
                </div>
              ))}
              {(!data.rc || data.rc.categories.length === 0) && <p className="text-slate-500 text-sm">{t("No root causes recorded yet.")}</p>}
            </div>
          </section>

          {/* CAPA Intelligence */}
          <section className="rounded-xl border border-slate-300 bg-white p-4" data-testid="exec-intel-capa">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Corrective Action Intelligence")}</div>
            <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
              <div><span className="text-slate-500">{t("Open")}: </span><span className="font-bold">{data.capa?.open ?? 0}</span></div>
              <div><span className="text-slate-500">{t("Verified")}: </span><span className="font-bold">{data.capa?.verified ?? 0}</span></div>
              <div><span className="text-slate-500">{t("Overdue")}: </span><span className={`font-bold ${(data.capa?.overdue||0)>0 ? "text-red-700" : ""}`}>{data.capa?.overdue ?? 0}</span></div>
              <div><span className="text-slate-500">{t("Avg completion (days)")}: </span><span className="font-bold">{data.capa?.avg_completion_days ?? 0}</span></div>
            </div>
          </section>

          {/* Project Intelligence */}
          <section className="rounded-xl border border-slate-300 bg-white p-4" data-testid="exec-intel-projects">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Project Intelligence")}</div>
            <ul className="mt-2 space-y-1 text-sm">
              {(data.projects?.projects || []).slice(0, 5).map((p) => (
                <li key={p.job_number} className="flex items-center justify-between">
                  <span className="font-mono">{p.job_number}</span>
                  <span className="text-xs">{p.critical > 0 && <span className="mr-2 text-red-700 font-bold">{p.critical}⚠</span>}{p.open} {t("open")} / {p.cases} {t("total")}</span>
                </li>
              ))}
              {(!data.projects?.projects || data.projects.projects.length === 0) && <p className="text-slate-500">{t("No project data yet.")}</p>}
            </ul>
          </section>

          {/* Fleet Intelligence */}
          <section className="rounded-xl border border-slate-300 bg-white p-4" data-testid="exec-intel-fleet">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Fleet Intelligence")}</div>
            <div className="mt-2 text-sm space-y-1">
              <div><span className="text-slate-500">{t("Vehicle incidents")}: </span><span className="font-bold">{data.fleet?.vehicle_incidents_total ?? 0}</span></div>
              <div><span className="text-slate-500">{t("Equipment incidents")}: </span><span className="font-bold">{data.fleet?.equipment_incidents_total ?? 0}</span></div>
              {(data.fleet?.repeat_vehicles || []).length > 0 && (
                <div className="mt-2">
                  <div className="font-mono text-[10px] uppercase text-red-700">{t("Repeat vehicles")}</div>
                  <ul className="text-xs">
                    {data.fleet.repeat_vehicles.slice(0, 5).map((r) => <li key={r.id}>{r.id} · {r.count}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </section>

          {/* Learning Intelligence */}
          <section className="rounded-xl border border-slate-300 bg-white p-4 lg:col-span-2" data-testid="exec-intel-learning">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Learning Intelligence")}</div>
            <div className="grid gap-3 sm:grid-cols-3 mt-2 text-sm">
              <div>
                <div className="text-slate-500">{t("Near miss reports")}</div>
                <div className="font-display font-black text-2xl">{data.learn?.near_miss_count ?? 0}</div>
              </div>
              <div>
                <div className="text-slate-500">{t("Most-verified action classes")}</div>
                <ul>
                  {(data.learn?.most_verified_action_classes || []).map((c) => (
                    <li key={c.class} className="capitalize"><span>{c.class.replace(/_/g," ")}</span> · {c.count}</li>
                  ))}
                  {(!data.learn?.most_verified_action_classes || data.learn.most_verified_action_classes.length === 0) && <li className="text-slate-500">{t("No verified actions yet.")}</li>}
                </ul>
              </div>
              <div>
                <div className="text-slate-500">{t("Peak occurrence hours")}</div>
                <ul>
                  {(data.learn?.peak_hours || []).map((h) => (
                    <li key={h.hour}>{h.hour}:00 · {h.count}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
