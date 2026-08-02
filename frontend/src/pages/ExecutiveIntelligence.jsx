// Track 19.16 · Phase D · Executive Intelligence Center.
import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { AlertTriangle, ArrowUpRight, TrendingDown, TrendingUp, Activity, ShieldAlert } from "lucide-react";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { PortalShell } from "@/design-system/PortalShell";

function adminConfig() {
  return { skipSessionStatus: true, headers: buildScopedPortalAuthHeaders(["admin"]) };
}

async function loadAll() {
  const cfg = adminConfig();
  const [home, rc, capa, projects, fleet, learn, brief, portfolio, confidenceRows] = await Promise.all([
    api.get("/incident-intelligence/home", cfg).then(r => r.data).catch(() => ({ company_health: {} })),
    api.get("/incident-intelligence/root-causes", cfg).then(r => r.data).catch(() => null),
    api.get("/incident-intelligence/corrective-actions", cfg).then(r => r.data).catch(() => null),
    api.get("/incident-intelligence/projects", cfg).then(r => r.data).catch(() => null),
    api.get("/incident-intelligence/fleet", cfg).then(r => r.data).catch(() => null),
    api.get("/incident-intelligence/learning", cfg).then(r => r.data).catch(() => null),
    api.get("/incident-intelligence/brief", cfg).then(r => r.data).catch(() => null),
    // Track 19.38 · additive · portfolio attention feed. Fails soft.
    api.get("/incident-intelligence/portfolio-attention", cfg).then(r => r.data).catch(() => null),
    api.get("/project-health", cfg).then((r) => ({
      summary: {
        average_score: r.data?.rows?.length ? Number((r.data.rows.reduce((sum, row) => sum + Number(row.production_confidence?.score || 0), 0) / r.data.rows.length).toFixed(2)) : 0,
        high_confidence: (r.data?.rows || []).filter((row) => row.production_confidence?.band === "high_confidence").length,
        watch: (r.data?.rows || []).filter((row) => row.production_confidence?.band === "watch").length,
        low_confidence: (r.data?.rows || []).filter((row) => row.production_confidence?.band === "low_confidence").length,
        critical: (r.data?.rows || []).filter((row) => row.production_confidence?.band === "critical").length,
      },
      projects: (r.data?.rows || []).slice(0, 12).map((row) => ({
        project_number: row.project_number,
        project_name: row.project_name,
        production_confidence: row.production_confidence,
        governance: row.production_confidence_governance,
      })),
    })).catch(() => null),
  ]);
  return { home, rc, capa, projects, fleet, learn, brief, portfolio, confidence: confidenceRows };
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
  const { pathname } = useLocation();
  const isAdminRoute = pathname.startsWith("/admin/");
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  const adminShellProps = {
    pageTitle: "Executive Intelligence",
    subtitle: "Cross-functional operational signal, incident intelligence, and portfolio confidence.",
    portalRole: "Admin · Executive Intelligence",
    crumbs: [
      { label: "Operations Control" },
      { label: "Executive Intelligence" },
    ],
    testId: "admin-executive-intelligence-shell",
  };

  useEffect(() => {
    if (!isAdminRoute) return undefined;
    loadAll().then(setData).catch((e) => setErr(e?.response?.data?.detail?.detail || e.message));
    return undefined;
  }, [isAdminRoute]);

  if (!isAdminRoute) {
    return (
      <PortalShell
        portalName="MASCI"
        portalRole={t("Safety")}
        pageTitle={t("Executive Intelligence")}
        subtitle={t("Leadership signal and safety attention stay visible without leaving the Safety workspace.")}
        homeHref="/safety"
        backHref="/safety"
        showBack
        showSearch={false}
        showNotifications={false}
        showPortalSwitcher={false}
        showSignOut={false}
      >
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-8" data-testid="safety-executive-intelligence-shell">
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-[0_18px_44px_rgba(15,23,42,0.08)]">
            <div className="flex items-start gap-4">
              <div className="wp17-hero-icon-shell wp17-hero-icon-shell--red" data-testid="safety-exec-preview-icon">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <div className="space-y-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
                  {t("Safety · Executive Intelligence")}
                </div>
                <h1 className="font-display text-3xl font-black tracking-tight text-slate-950">
                  {t("Executive Intelligence")}
                </h1>
                <p className="max-w-3xl text-sm leading-7 text-slate-700">
                  {t("Executive intelligence is shown in the Administration workspace in this preview. Safety leaders can keep using cards, cases, and forms here without a broken shell or auth noise.")}
                </p>
                <div className="grid gap-3 sm:grid-cols-3 pt-2" data-testid="safety-exec-preview-links">
                  <a href="/safety/cards" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900 hover:border-red-300 hover:bg-red-50">{t("Open Field Safety Cards")}</a>
                  <a href="/safety/forms" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900 hover:border-red-300 hover:bg-red-50">{t("Open Safety Forms")}</a>
                  <a href="/safety" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900 hover:border-red-300 hover:bg-red-50">{t("Back to Safety")}</a>
                </div>
              </div>
            </div>
          </section>
        </div>
      </PortalShell>
    );
  }

  if (err) {
    const errorContent = (
      <div className="min-h-screen bg-slate-50 p-6" data-testid="executive-intelligence-error">
        <div className="max-w-md rounded-xl border-2 border-red-300 bg-white p-6 mx-auto">
          <div className="font-mono text-[10px] uppercase tracking-widest text-red-800">{t("Error")}</div>
          <div className="font-display text-xl font-black">{t("Could not load intelligence")}</div>
          <p className="text-sm text-slate-700 mt-2">{err}</p>
          <button className="mt-4 h-10 px-4 rounded-md bg-slate-900 text-white" onClick={() => navigate(-1)}>{t("Back")}</button>
        </div>
      </div>
    );
    return isAdminRoute ? <AdminRouteShell {...adminShellProps}>{errorContent}</AdminRouteShell> : errorContent;
  }
  if (!data) {
    const loadingContent = <div className="min-h-screen bg-slate-50 p-6" data-testid="executive-intelligence-loading">{t("Loading intelligence…")}</div>;
    return isAdminRoute ? <AdminRouteShell {...adminShellProps}>{loadingContent}</AdminRouteShell> : loadingContent;
  }

  const H = data.home?.company_health || {};
  const trend = H.trend_30d || "flat";
  const TrendIcon = trend === "worsening" ? TrendingUp : trend === "improving" ? TrendingDown : Activity;
  const trendTone = trend === "worsening" ? "text-red-700" : trend === "improving" ? "text-emerald-700" : "text-slate-600";

  const content = (
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

        <section className="rounded-xl border-2 border-slate-300 bg-white p-4" data-testid="exec-intel-production-confidence">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">Production Confidence Score</div>
                <div className="font-display text-lg font-black text-slate-900">Explainable, canonical, and executive-ready</div>
              </div>
              <div className="flex flex-wrap gap-2 text-sm">
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2" data-testid="exec-intel-confidence-average">Avg {data.confidence?.summary?.average_score ?? 0}</div>
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2" data-testid="exec-intel-confidence-high">High {data.confidence?.summary?.high_confidence ?? 0}</div>
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2" data-testid="exec-intel-confidence-watch">Watch {data.confidence?.summary?.watch ?? 0}</div>
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2" data-testid="exec-intel-confidence-critical">Critical {data.confidence?.summary?.critical ?? 0}</div>
              </div>
            </div>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {(data.confidence?.projects || []).slice(0, 6).map((row) => (
                <div key={row.project_number} className="rounded-xl border border-slate-200 bg-slate-50 p-4" data-testid={`exec-intel-confidence-project-${row.project_number}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-mono text-[11px] uppercase tracking-widest text-slate-500">{row.project_number}</div>
                      <div className="font-semibold text-slate-900">{row.project_name}</div>
                    </div>
                    <div className={`text-2xl font-black ${Number(row.production_confidence?.score || 0) >= 85 ? "text-emerald-700" : Number(row.production_confidence?.score || 0) >= 70 ? "text-amber-700" : "text-red-700"}`}>{Math.round(Number(row.production_confidence?.score || 0))}</div>
                  </div>
                  <div className="mt-2 text-xs text-slate-600">{(row.production_confidence?.explainability || []).slice(0, 2).join(" • ")}</div>
                  <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
                    <span className="rounded-full border border-slate-200 bg-white px-2 py-1">Band: {String(row.production_confidence?.band || "critical").replaceAll("_", " ")}</span>
                    <span className="rounded-full border border-slate-200 bg-white px-2 py-1">Snapshots: {row.governance?.snapshot_count || 0}</span>
                  </div>
                </div>
              ))}
              {!(data.confidence?.projects || []).length ? (
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
                  Confidence rows are waiting on preview auth, but the executive module remains mounted safely.
                </div>
              ) : null}
            </div>
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

          {/* Track 19.38 · Portfolio Attention Feed — read-only rollup of
              per-case attention signals. Cases sorted by attention_score
              DESC. Deep-links into the Executive Case Report. */}
          {data.portfolio && (data.portfolio.cases || []).length > 0 && (
            <section className="rounded-xl border-2 border-slate-200 bg-white p-4 sm:p-6" data-testid="portfolio-attention-feed">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-slate-700" aria-hidden />
                <h2 className="font-display text-lg font-black tracking-tight text-slate-900">
                  {t("Portfolio Attention Feed")}
                </h2>
                <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-slate-500" data-testid="portfolio-attention-count">
                  {data.portfolio.count || 0} {t("cases")}
                </span>
              </div>
              <ol className="space-y-1.5" data-testid="portfolio-attention-list">
                {(data.portfolio.cases || []).slice(0, 12).map((row) => (
                  <li key={row.case_id} className="rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors" data-testid={`portfolio-attention-row-${row.case_id}`}>
                    <button
                      onClick={() => navigate(`/safety/cases/${row.case_id}/executive-report`)}
                      className="w-full text-left px-3 py-2 flex flex-wrap items-center gap-2"
                    >
                      <span className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] ${
                        row.attention_level === "high" ? "border-red-300 bg-red-50 text-red-800" :
                        row.attention_level === "medium" ? "border-amber-300 bg-amber-50 text-amber-800" :
                        "border-slate-300 bg-white text-slate-700"
                      }`}>
                        {row.attention_score ?? 0} · {(row.attention_level || "low").toUpperCase()}
                      </span>
                      <span className="font-semibold text-slate-900 text-sm">#{row.case_number || row.case_id.slice(0, 8)}</span>
                      <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                        {row.incident_type} · {row.state}
                      </span>
                      <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500 ml-auto">
                        {t("Open")} {row.days_open ?? "—"}d · {t("CAPA open")} {row.capa_open || 0}
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
              <p className="mt-3 text-[11px] italic text-slate-500 border-l-2 border-slate-200 pl-2" data-testid="portfolio-attention-notice">
                {t("Attention signals prioritize review. Safety owns investigation and classification.")}
              </p>
            </section>
          )}

        </div>
      </main>
    </div>
  );

  return isAdminRoute
    ? <AdminRouteShell {...adminShellProps} contentClassName="px-0 py-0">{content}</AdminRouteShell>
    : content;
}
