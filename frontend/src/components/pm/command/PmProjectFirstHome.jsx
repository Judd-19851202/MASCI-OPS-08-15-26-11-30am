// PmProjectFirstHome.jsx — Track 13 · §6 PM Portal Rebuild.
//
// The previous PM Command Center first screen was a 12-tile
// fleet/haul/material strip with tabs ordered by RESOURCE TYPE
// (Resources · Hauls · Materials · Shop · Safety · Timeline). That
// audit (Track 13A.5, Five-Pillar score 12/25) proved it failed the
// 5:30 AM 10-second test: a PM could not answer "which of my projects
// need attention today" without drilling.
//
// This component replaces the default first-screen experience with a
// PROJECT-first surface honoring Track 13B's four sections:
//
//   A — Project Command     : my projects, status, what needs PM today
//   B — Field Truth          : latest dailies, photos, missing reports
//   C — Project Risk         : open issues / safety on my jobs
//   D — Documents & Plans    : DRs · JHPs · Safety · Photos · Plans
//
// Plus a small support-resource footer (E) that demotes the old
// fleet/haul tiles to a "project support resources" rollup card —
// honest about what they are without elevating them above project
// truth.
//
// Click-through is mandatory (Track 13 · §7). Every visible count
// opens the actual list/detail view. Empty states are narrative
// (Track 13 · §11) — no bare zeros.
//
// No new backend endpoints. Reuses:
//   - /api/pm/command-center/overview      (counts)
//   - /api/pm/command-center/safety-impact (project risk feed)
//   - /api/pm/command-center/shop-impact   (defects feed)
//   - /api/pm/command-center/timeline      (recent activity)
//   - /api/job-photos                       (recent photos)
//   - /api/daily-reports                    (daily report list)

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Briefcase, FileText, Camera, ShieldAlert, Wrench,
  ClipboardList, ArrowRight, ExternalLink, BookMarked,
} from "lucide-react";
import { useT } from "@/lib/i18n";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function _authHeaders() {
  const t =
    sessionStorage.getItem("masci.pm.token") ||
    sessionStorage.getItem("masci.admin.token") ||
    "";
  return t ? { "X-Admin-Token": t } : {};
}

// ── shared visual primitives (inherit platform baseline) ──────────
function SectionShell({ kicker, title, lede, children, testId }) {
  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 print:break-inside-avoid"
      data-testid={testId}
    >
      <div className="mb-4 pb-3 border-b-2 border-slate-200">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
          {kicker}
        </div>
        <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900 mt-1">
          {title}
        </h2>
        {lede ? (
          <p className="text-sm text-slate-600 mt-1.5">{lede}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function ActionTile({ to, icon: Icon, label, count, hint, tone = "slate", testId }) {
  const TONE = {
    rose:    "border-rose-300 bg-rose-50 hover:border-rose-500 text-rose-800",
    amber:   "border-amber-300 bg-amber-50 hover:border-amber-500 text-amber-800",
    emerald: "border-emerald-300 bg-emerald-50 hover:border-emerald-500 text-emerald-800",
    slate:   "border-slate-200 bg-white hover:border-slate-400 text-slate-800",
  };
  return (
    <Link
      to={to}
      data-testid={testId}
      className={`group border-2 rounded-md p-4 transition-colors ${TONE[tone] || TONE.slate}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] font-bold opacity-80">
          {label}
        </div>
        <Icon className="w-4 h-4 opacity-70 shrink-0" />
      </div>
      <div className="text-3xl font-display font-black tabular-nums">{count}</div>
      {hint ? <div className="text-[11px] leading-snug opacity-80 mt-1">{hint}</div> : null}
      <div className="mt-2 inline-flex items-center text-[11px] font-mono uppercase tracking-wider opacity-70 group-hover:opacity-100">
        {label === "Active Projects" ? "View" : "Open"} <ArrowRight className="w-3 h-3 ml-1" />
      </div>
    </Link>
  );
}

function EmptyRow({ children, testId }) {
  return (
    <div
      data-testid={testId}
      className="text-sm text-slate-600 italic border border-dashed border-slate-300 rounded-md px-3 py-2"
    >
      {children}
    </div>
  );
}

// ── Section A — Project Command (Track 13.1 — per-project rollup list)
// Track 13.2 — project rows now include health-at-a-glance signals
// (dailies-this-week count + next-action).
function ProjectCommand({ overview, loading, dailies = [], incidents = [], shop = null }) {
  const { t } = useT();
  const scopedProjects = overview?.scoped_projects;
  // "all" means super-admin / unscoped — show count only.
  const isAdminScope = scopedProjects === "all" || scopedProjects == null;
  const projects = Array.isArray(scopedProjects) ? scopedProjects : [];
  const counts = overview?.counts || {};

  // Group dailies + incidents per project_number for per-project rollup.
  function _by(arr, key) {
    const m = {};
    (arr || []).forEach((r) => {
      const k = r?.[key];
      if (!k) return;
      m[k] = (m[k] || 0) + 1;
    });
    return m;
  }
  const dailyByPn = _by(dailies, "project_number");
  const incidentsByPn = _by(incidents, "project_number");
  // Latest daily per pn for "last activity" string.
  const latestDailyByPn = {};
  (dailies || []).forEach((d) => {
    const pn = d?.project_number;
    if (!pn) return;
    const t0 = d?.created_at || d?.report_date;
    if (!t0) return;
    if (!latestDailyByPn[pn] || latestDailyByPn[pn] < t0) latestDailyByPn[pn] = t0;
  });

  function nextActionFor(pn) {
    if ((incidentsByPn[pn] ?? 0) > 0) return t("Review Safety Item");
    if ((dailyByPn[pn] ?? 0) === 0) return t("Missing Daily Report");
    return t("Review Daily Report");
  }
  const _nowMs = Date.now();
  function relAgo(iso) {
    if (!iso) return "";
    const secs = Math.max(0, Math.floor((_nowMs - new Date(iso).getTime()) / 1000));
    if (secs < 60) return `${secs}s ago`;
    if (secs < 3600) return `${Math.floor(secs/60)}m ago`;
    if (secs < 86400) return `${Math.floor(secs/3600)}h ago`;
    return `${Math.floor(secs/86400)}d ago`;
  }

  return (
    <SectionShell
      kicker={t("Section A · My Projects")}
      title={t("Projects Assigned to You")}
      lede={isAdminScope
        ? t("Admin / super-admin sees all MASCI projects. Click any project to drill in.")
        : t("Each PM only sees projects they've been assigned through the Admin Project Manager Directory.")}
      testId="pm-pfh-project-command"
    >
      {loading ? (
        <div className="space-y-1.5">
          {[1,2,3].map((i) => (<div key={i} className="h-14 bg-slate-100 rounded animate-pulse" />))}
        </div>
      ) : isAdminScope ? (
        // Admin-view summary — KPI tile (admins don't need per-project rows here).
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" data-testid="pm-pfh-admin-summary">
          <ActionTile
            to="/admin/projects"
            icon={Briefcase}
            label={t("Active Projects (admin scope)")}
            count={counts.active_assignments ?? 0}
            tone="slate"
            hint={t("Admin / super-admin sees the full roster.")}
            testId="pm-pfh-tile-admin-projects"
          />
          <ActionTile
            to="/incidents"
            icon={ShieldAlert}
            label={t("Open Incidents")}
            count={counts.incidents_open ?? 0}
            tone={(counts.incidents_open ?? 0) > 0 ? "rose" : "slate"}
            hint={t("Across every project (admin scope).")}
            testId="pm-pfh-tile-incidents"
          />
          <ActionTile
            to="/admin/capas"
            icon={ClipboardList}
            label={t("Open CAPAs")}
            count={counts.capas_open ?? 0}
            tone={(counts.capas_open ?? 0) > 0 ? "amber" : "slate"}
            hint={t("Across every project (admin scope).")}
            testId="pm-pfh-tile-capas"
          />
        </div>
      ) : projects.length === 0 ? (
        <EmptyRow testId="pm-pfh-projects-empty">
          {t("No projects assigned to this PM yet. Admin can assign projects via the Project Manager Directory.")}
          {" "}
          <Link to="/admin/project-managers" className="underline font-bold not-italic">
            {t("Open Project Manager Directory")} →
          </Link>
        </EmptyRow>
      ) : (
        <ul className="space-y-2" data-testid="pm-pfh-project-list">
          {projects.map((pn) => {
            const dailyCount = dailyByPn[pn] ?? 0;
            const incidentCount = incidentsByPn[pn] ?? 0;
            const lastIso = latestDailyByPn[pn];
            const action = nextActionFor(pn);
            const actionTone =
              action === t("Missing Daily Report") ? "amber"
              : action === t("Review Safety Item") ? "rose"
              : "slate";
            const ATONE = {
              rose: "bg-rose-100 text-rose-800 border-rose-200",
              amber: "bg-amber-100 text-amber-800 border-amber-200",
              slate: "bg-slate-100 text-slate-700 border-slate-200",
            };
            return (
              <li key={pn}>
                <Link
                  to={`/pm/command-center?project_number=${encodeURIComponent(pn)}`}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 rounded-md border-2 border-slate-200 hover:border-red-400 hover:bg-red-50 transition-colors"
                  data-testid={`pm-pfh-project-row-${pn}`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Briefcase className="w-4 h-4 text-red-700 shrink-0" />
                    <div className="min-w-0">
                      <div className="font-bold text-slate-900 text-sm font-mono">{pn}</div>
                      <div className="text-[11px] text-slate-500">
                        {lastIso
                          ? `${t("Last activity")}: ${relAgo(lastIso)}`
                          : t("No recent activity logged.")}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-[11px]">
                    <span className="font-mono uppercase tracking-wider text-slate-600">
                      <span className="font-black text-base tabular-nums text-slate-900">{dailyCount}</span>{" "}
                      {t("Dailies (week)")}
                    </span>
                    <span className="font-mono uppercase tracking-wider text-slate-600">
                      <span className={`font-black text-base tabular-nums ${incidentCount > 0 ? "text-rose-700" : "text-slate-900"}`}>{incidentCount}</span>{" "}
                      {t("Incidents")}
                    </span>
                    <span className={`inline-flex items-center font-mono uppercase tracking-wider text-[10px] px-2 py-0.5 rounded border ${ATONE[actionTone]}`}>
                      {action}
                    </span>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-red-700">
                      {t("Open Project")} <ArrowRight className="w-3 h-3 inline ml-1" />
                    </span>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </SectionShell>
  );
}

// ── Section B — Field Truth ───────────────────────────────────────
function FieldTruth({ photos, dailies, loading }) {
  const { t } = useT();
  return (
    <SectionShell
      kicker={t("Section B · Field Truth")}
      title={t("Latest Dailies & Photos from the Field")}
      lede={t("What the crews submitted at end-of-shift. Click any row to open the record.")}
      testId="pm-pfh-field-truth"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">
            {t("Recent Daily Reports")}
            <Link to="/daily" data-testid="pm-pfh-daily-view-all" className="ml-2 text-red-700 hover:underline normal-case tracking-normal font-bold">
              {t("View all")} →
            </Link>
          </div>
          {loading ? (
            <div className="space-y-1.5">{[1,2,3].map((i) => (<div key={i} className="h-9 bg-slate-100 rounded animate-pulse" />))}</div>
          ) : (dailies && dailies.length > 0) ? (
            <ul className="space-y-1.5" data-testid="pm-pfh-daily-list">
              {dailies.slice(0, 5).map((d) => (
                <li key={d.id || d.report_id}>
                  <Link
                    to={`/daily/${d.id || d.report_id}`}
                    className="flex items-center justify-between gap-2 px-3 py-2 rounded border border-slate-200 hover:border-slate-400 hover:bg-slate-50"
                    data-testid={`pm-pfh-daily-row-${d.id || d.report_id || 'r'}`}
                  >
                    <span className="font-mono text-xs text-slate-700 truncate">
                      {d.report_id || (d.id || "").slice(0, 8)}
                    </span>
                    <span className="text-xs text-slate-500 truncate flex-1 mx-2">
                      {d.project_name || d.project_number || t("(no project)")}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 shrink-0">
                      {d.created_at ? new Date(d.created_at).toLocaleDateString() : ""}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyRow testId="pm-pfh-daily-empty">
              {t("No Daily Reports submitted today on your projects.")}{" "}
              <Link to="/daily" className="underline font-bold not-italic">
                {t("View this week or contact Admin if a project is missing.")}
              </Link>
            </EmptyRow>
          )}
        </div>

        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">
            {t("Recent Photos")}
            <Link to="/pm/photos" data-testid="pm-pfh-photo-view-all" className="ml-2 text-red-700 hover:underline normal-case tracking-normal font-bold">
              {t("View all")} →
            </Link>
          </div>
          {loading ? (
            <div className="grid grid-cols-4 gap-1.5">{[1,2,3,4].map((i) => (<div key={i} className="aspect-square bg-slate-100 rounded animate-pulse" />))}</div>
          ) : (photos && photos.length > 0) ? (
            <div className="grid grid-cols-4 gap-1.5" data-testid="pm-pfh-photo-grid">
              {photos.slice(0, 8).map((p) => (
                <Link
                  key={p.id}
                  to={p.source === "daily_report" ? `/daily/${p.source_id}` : `/pm/photos?source_id=${p.source_id}`}
                  className="aspect-square block bg-slate-200 rounded overflow-hidden hover:ring-2 hover:ring-red-400 transition-shadow"
                  data-testid={`pm-pfh-photo-${p.id}`}
                  title={`${p.project_number || ""} ${p.record_date || ""}`}
                >
                  {p.thumb_url || p.url ? (
                    <img
                      src={p.thumb_url || p.url}
                      alt={p.project_number || "photo"}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-400">
                      <Camera className="w-4 h-4" />
                    </div>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <EmptyRow testId="pm-pfh-photo-empty">
              {t("No photos submitted on your projects this week.")}{" "}
              {t("Photos appear when field reports include attachments.")}
            </EmptyRow>
          )}
        </div>
      </div>
    </SectionShell>
  );
}

// ── Section C — Project Risk ──────────────────────────────────────
function ProjectRisk({ safety, shop, loading }) {
  const { t } = useT();
  const incidents = safety?.incidents || [];
  const defects = shop?.rows || [];
  return (
    <SectionShell
      kicker={t("Section C · Project Risk")}
      title={t("What Needs PM Action")}
      lede={t("Safety, equipment, and accountability items that block project work.")}
      testId="pm-pfh-project-risk"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2 flex items-center justify-between">
            <span><ShieldAlert className="w-3 h-3 inline mr-1" /> {t("Open Safety Items")} ({incidents.length})</span>
            <Link to="/incidents" className="text-red-700 hover:underline normal-case tracking-normal font-bold" data-testid="pm-pfh-risk-safety-all">
              {t("View all")} →
            </Link>
          </div>
          {loading ? (
            <div className="space-y-1.5">{[1,2,3].map((i) => (<div key={i} className="h-9 bg-slate-100 rounded animate-pulse" />))}</div>
          ) : incidents.length === 0 ? (
            <EmptyRow testId="pm-pfh-risk-safety-empty">
              {t("No open safety items on your projects. Good.")}
            </EmptyRow>
          ) : (
            <ul className="space-y-1.5" data-testid="pm-pfh-risk-safety-list">
              {incidents.slice(0, 5).map((row) => (
                <li key={row.incident_id}>
                  <Link
                    to={`/incidents/${row.incident_id}`}
                    className="flex items-center gap-2 px-3 py-2 rounded border border-rose-200 hover:border-rose-400 hover:bg-rose-50"
                    data-testid={`pm-pfh-risk-safety-row-${row.incident_id}`}
                  >
                    <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 shrink-0">
                      {row.severity || "near_miss"}
                    </span>
                    <span className="text-xs text-slate-700 truncate flex-1">
                      {row.summary || row.incident_id?.slice(0, 8) || "—"}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 shrink-0">
                      {row.project_number || ""}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2 flex items-center justify-between">
            <span><Wrench className="w-3 h-3 inline mr-1" /> {t("Equipment Defects")} ({defects.length})</span>
            <Link to="/shop" className="text-red-700 hover:underline normal-case tracking-normal font-bold" data-testid="pm-pfh-risk-defect-all">
              {t("Open Shop portal")} →
            </Link>
          </div>
          {loading ? (
            <div className="space-y-1.5">{[1,2,3].map((i) => (<div key={i} className="h-9 bg-slate-100 rounded animate-pulse" />))}</div>
          ) : defects.length === 0 ? (
            <EmptyRow testId="pm-pfh-risk-defect-empty">
              {t("No defects currently scoped to your projects. Unscoped defects are handled in Shop.")}
            </EmptyRow>
          ) : (
            <ul className="space-y-1.5" data-testid="pm-pfh-risk-defect-list">
              {defects.slice(0, 5).map((row) => (
                <li key={row.unit_number}>
                  <Link
                    to={`/shop?unit=${encodeURIComponent(row.unit_number || "")}`}
                    className="flex items-center gap-2 px-3 py-2 rounded border border-amber-200 hover:border-amber-400 hover:bg-amber-50"
                    data-testid={`pm-pfh-risk-defect-row-${row.unit_number}`}
                  >
                    <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 shrink-0">
                      {row.severity || "open"}
                    </span>
                    <span className="font-mono text-xs text-slate-700 shrink-0">{row.unit_number}</span>
                    <span className="text-xs text-slate-500 truncate flex-1">
                      {row.item_text || row.category || "—"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </SectionShell>
  );
}

// ── Section D — Documents & Plans ─────────────────────────────────
function DocumentsAndPlans() {
  const { t } = useT();
  const links = [
    { to: "/daily", icon: FileText, label: t("Daily Reports"), hint: t("All submitted dailies, filterable by project."), testId: "pm-pfh-doc-daily" },
    { to: "/jha", icon: BookMarked, label: t("Job Hazard Plans"), hint: t("Active JHPs / JHAs across your projects."), testId: "pm-pfh-doc-jhp" },
    { to: "/pm/photos", icon: Camera, label: t("Photo Library"), hint: t("Every field photo submitted with a report."), testId: "pm-pfh-doc-photos" },
    { to: "/pm/jobs", icon: Briefcase, label: t("Project Roster"), hint: t("All projects you can access."), testId: "pm-pfh-doc-projects" },
  ];
  return (
    <SectionShell
      kicker={t("Section D · Documents & Plans")}
      title={t("Reports, JHPs, Photos, and Project Roster")}
      lede={t("Direct paths into the records that back up project decisions.")}
      testId="pm-pfh-documents"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {links.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className="border-2 border-slate-200 hover:border-red-400 rounded-md p-4 transition-colors group"
            data-testid={l.testId}
          >
            <l.icon className="w-5 h-5 text-red-700 mb-2" />
            <div className="font-bold text-slate-900 text-sm">{l.label}</div>
            <div className="text-[11px] text-slate-500 mt-1">{l.hint}</div>
            <div className="mt-2 inline-flex items-center text-[10px] font-mono uppercase tracking-wider text-red-700 opacity-80 group-hover:opacity-100">
              {t("Open")} <ArrowRight className="w-3 h-3 ml-1" />
            </div>
          </Link>
        ))}
      </div>
    </SectionShell>
  );
}

// ── Section E — Support Resources (demoted footer) ────────────────
function SupportResources({ overview, onOpenDetailedView }) {
  const { t } = useT();
  const c = overview?.counts || {};
  return (
    <SectionShell
      kicker={t("Section E · Project Support Resources")}
      title={t("Equipment, Trucks, Trailers & Specialty Assets")}
      lede={t("Asset-level rollups across your projects. These are context, not command — open the detailed operational view for tabbed drill-down.")}
      testId="pm-pfh-support-resources"
    >
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {[
          { label: t("Equipment"),     value: c.equipment_assigned ?? 0, tid: "pm-pfh-supp-equipment" },
          { label: t("Trucks"),        value: c.trucks_assigned ?? 0, tid: "pm-pfh-supp-trucks" },
          { label: t("Drivers"),       value: c.drivers_assigned ?? 0, tid: "pm-pfh-supp-drivers" },
          { label: t("Trailers"),      value: c.trailers_assigned ?? 0, tid: "pm-pfh-supp-trailers" },
          { label: t("Road Plates"),   value: c.road_plates_assigned ?? 0, tid: "pm-pfh-supp-roadplates" },
          { label: t("Specialty"),     value: c.specialty_assets_assigned ?? 0, tid: "pm-pfh-supp-specialty" },
        ].map((row) => (
          <div
            key={row.tid}
            data-testid={row.tid}
            className="border border-slate-200 rounded-md px-3 py-2 bg-slate-50"
          >
            <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500 font-bold">
              {row.label}
            </div>
            <div className="text-xl font-display font-black tabular-nums text-slate-700">
              {row.value}
            </div>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={onOpenDetailedView}
        data-testid="pm-pfh-open-detailed-view"
        className="mt-4 inline-flex items-center min-h-[44px] px-4 rounded-md border-2 border-slate-300 hover:border-slate-500 text-slate-700 hover:text-slate-900 font-bold tracking-wide text-sm"
      >
        <ExternalLink className="w-4 h-4 mr-2" />
        {t("Detailed operational view (Resources · Hauls · Materials · Shop · Safety · Timeline)")}
      </button>
    </SectionShell>
  );
}

// ── orchestrator ──────────────────────────────────────────────────
export default function PmProjectFirstHome({ overview, loading, onOpenDetailedView }) {
  const [extra, setExtra] = useState({
    safety: null, shop: null, photos: null, dailies: null, loading: true,
  });

  useEffect(() => {
    let cancelled = false;
    const headers = _authHeaders();
    Promise.all([
      fetch(`${API}/pm/command-center/safety-impact`, { headers }).then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/pm/command-center/shop-impact`, { headers }).then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/job-photos?limit=8`, { headers }).then((r) => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/daily-reports?limit=5`, { headers }).then((r) => r.ok ? r.json() : null).catch(() => null),
    ]).then(([safety, shop, photosResp, dailiesResp]) => {
      if (cancelled) return;
      const photos = photosResp?.items || [];
      const dailies = Array.isArray(dailiesResp) ? dailiesResp : (dailiesResp?.items || []);
      setExtra({ safety, shop, photos, dailies, loading: false });
    });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-4" data-testid="pm-project-first-home">
      <ProjectCommand
        overview={overview}
        loading={loading}
        dailies={extra.dailies}
        incidents={extra.safety?.incidents}
        shop={extra.shop}
      />
      <FieldTruth photos={extra.photos} dailies={extra.dailies} loading={extra.loading} />
      <ProjectRisk safety={extra.safety} shop={extra.shop} loading={extra.loading} />
      <DocumentsAndPlans />
      <SupportResources overview={overview} onOpenDetailedView={onOpenDetailedView} />
    </div>
  );
}
