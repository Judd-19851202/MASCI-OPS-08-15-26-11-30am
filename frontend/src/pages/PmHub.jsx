// PmHub — /pm Overview (iter105 redesign)
//
// Mirrors AdminHub: KPI tiles + Active Jobs status banner. Every panel
// that used to live on this scroll has been moved to a /pm/{section}
// sub-route reachable from the PmShell sidebar — same architecture as
// the Admin Console.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck, Users, AlertOctagon, ClipboardList, Wrench, Box,
  FileText, ArrowRight, Loader2, ShieldCheck, Image as ImageIcon,
  UserCheck, Briefcase, GraduationCap, Activity, Truck, AlertTriangle, CircleSlash,
} from "lucide-react";
import PmShell from "@/components/PmShell";
import OperationsCenter from "@/components/OperationsCenter";
import DispatchLifecycleTile from "@/components/dispatch/DispatchLifecycleTile";
import PmHaulActivityTile from "@/components/dispatch/PmHaulActivityTile";
import { api } from "@/lib/api";
import { usePageTitle } from "@/lib/usePageTitle";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";
import { FieldMemoryGlance } from "@/components/field_memory/FieldMemoryGlance";
import LastActivityLine from "@/components/admin/LastActivityLine";
import { isPmSidebarV2Enabled } from "@/components/pm/sidebar/SideNavV2";
import GovernanceHealthChip from "@/components/GovernanceHealthChip";
import OperationsActionsTile from "@/components/oa/OperationsActionsTile";
import { setPortalContext } from "@/lib/portalContext";
import { PortalShell } from "@/design-system/PortalShell";

const FORM_TILES = [
  { to: "/tasks",             icon: ClipboardCheck, title: "Tasks & Actions",     countKey: null,         sub: "Open · overdue · cross-portal", accent: "amber" },
  { to: "/po-requests",       icon: ClipboardCheck, title: "PO Requests",         countKey: null,         sub: "Approvals · receipts · spend",  accent: "indigo" },
  { to: "/project-health",    icon: Activity,      title: "Project Health",      countKey: null,         sub: "Operational friction by job",   accent: "emerald" },
  { to: "/asset-transfers",   icon: Truck,         title: "Asset Transfers",     countKey: null,         sub: "Equipment movement · lifecycle", accent: "amber" },
  { to: "/pm/daily",          icon: ClipboardList, title: "Daily Reports",       countKey: "daily",      sub: "reports on file",    accent: "red" },
  { to: "/pm/inspections",    icon: ClipboardCheck, title: "Site Inspections",    countKey: "inspections", sub: "reports on file",   accent: "red" },
  { to: "/pm/meetings",       icon: Users,         title: "Safety Meetings",     countKey: "meetings",   sub: "meetings logged",    accent: "slate" },
  { to: "/pm/jha-plans",      icon: FileText,      title: "Job Hazard Plans",    countKey: "jhaPlans",   sub: "plans uploaded",     accent: "amber" },
  { to: "/pm/trench-boxes",   icon: Box,           title: "Trench Box Data",     countKey: "trenchBoxes", sub: "boxes on file",     accent: "slate" },
  { to: "/pm/incidents",      icon: AlertOctagon,  title: "Incident Reports",    countKey: "incidents",  sub: "reports on file",    accent: "redDeep" },
  { to: "/pm/equipment",      icon: Wrench,        title: "Equipment Pre-Op",    countKey: "equipment",  sub: "inspections on file", accent: "slate" },
  { to: "/pm/qaqc",           icon: ShieldCheck,   title: "QA/QC Inspections", countKey: "qaqc",       sub: "Records on your jobs", accent: "amber" },
  { to: "/pm/photos",         icon: ImageIcon,     title: "Job Photos",          countKey: null,         sub: "All photos by job & week", accent: "rose" },
  { to: "/pm/field-leadership", icon: UserCheck,   title: "Field Leadership",    countKey: null,         sub: "Crew docs · my jobs only", accent: "amber" },
  { to: "/guidance", icon: GraduationCap, title: "Training & Guides", countKey: null,    sub: "Operator guides · PDF download", accent: "slate" },
];

function PmTile({ to, icon: Icon, title, count, sub, accent, testId }) {
  const accentCls =
    accent === "red"     ? "border-red-700 bg-red-700"
    : accent === "amber" ? "border-amber-600 bg-amber-600"
    : accent === "redDeep" ? "border-red-900 bg-red-900"
    : accent === "rose"  ? "border-rose-700 bg-rose-700"
    : "border-slate-800 bg-slate-800";
  // iter326 · calm convergence — PmHub tile now uses the platform
  // family contract (border border-slate-200 + accent stripe via
  // border-l-4 + calm slate hover). Mirrors SafetyHub / HrHub /
  // FieldHub / AdminHub. Tile chrome no longer competes with the
  // KPI count for visual weight.
  const stripeCls =
    accent === "red"     ? "border-l-red-700"
    : accent === "amber" ? "border-l-amber-600"
    : accent === "redDeep" ? "border-l-red-900"
    : accent === "rose"  ? "border-l-rose-700"
    : "border-l-slate-700";
  return (
    <Link
      to={to}
      className={`group relative bg-white border border-slate-200 border-l-4 ${stripeCls} hover:shadow-md hover:border-slate-300 rounded-md p-4 sm:p-5 transition-all duration-150 hover:-translate-y-0.5 flex flex-col`}
      data-testid={testId}
    >
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${accentCls} text-white mb-3`}>
        <Icon className="w-5 h-5" />
      </div>
      <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">{title}</h3>
      <div className="mt-3 pt-2 border-t border-slate-100 flex items-end justify-between">
        <div>
          <div className="font-display text-2xl font-black text-slate-900 leading-none">
            {count == null ? "—" : count}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mt-1">{sub}</div>
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
          Open <ArrowRight className="w-3 h-3" />
        </div>
      </div>
    </Link>
  );
}

// ─── Phase IV-BETA.2 · PM Hub V2 primitives ──────────────────────────
// All inline · no separate file proliferation · governed by single
// `isPmSidebarV2Enabled()` flag with the sidebar.

const HUB_V2_TIER1 = [
  { to: "/pm/daily",       icon: ClipboardList,  title: "Daily Reports", countKey: "daily",       subline: "Field production · review and approve.",     stripe: "red" },
  { to: "/pm/inspections", icon: ClipboardCheck, title: "Inspections",   countKey: "inspections", subline: "Today's field safety and quality checks.",   stripe: "red" },
  { to: "/pm/incidents",   icon: AlertOctagon,   title: "Incidents",     countKey: "incidents",   subline: "Open and recent operational deviations.",    stripe: "orange" },
];

const HUB_V2_TIER2_CHIPS = [
  { to: "/tasks",           icon: ClipboardCheck, label: "My Tasks",        subline: "Action items across all domains." },
  { to: "/po-requests",     icon: ClipboardCheck, label: "PO Requests",     subline: "Approvals · receipts · spend." },
  { to: "/project-health",  icon: Activity,       label: "Project Health",  subline: "Operational friction by job." },
  { to: "/asset-transfers", icon: Truck,          label: "Asset Transfers", subline: "Equipment movement · lifecycle." },
];

const HUB_V2_TIER3_MORE = [
  { to: "/pm/meetings",         icon: Users,        label: "Meetings",         countKey: "meetings" },
  { to: "/pm/equipment",        icon: Wrench,       label: "Pre-Op Checks",    countKey: "equipment" },
  { to: "/pm/qaqc",             icon: ShieldCheck,  label: "QA/QC",            countKey: "qaqc" },
  { to: "/pm/photos",           icon: ImageIcon,    label: "Job Photos",       countKey: null },
  { to: "/pm/jha-plans",        icon: FileText,     label: "JHA Plans",        countKey: "jhaPlans" },
  { to: "/pm/trench-boxes",     icon: Box,          label: "Trench Boxes",     countKey: "trenchBoxes" },
  { to: "/pm/field-leadership", icon: UserCheck,    label: "Field Leadership", countKey: null },
  { to: "/guidance",            icon: GraduationCap, label: "Training Center",        countKey: null },
];

function HubV2QuickTile({ to, icon: Icon, title, count, subline, stripe, testId }) {
  const stripeCls = stripe === "red" ? "border-l-red-600"
                  : stripe === "orange" ? "border-l-orange-600"
                  : "border-l-slate-400";
  return (
    <Link
      to={to}
      data-testid={testId}
      className={`group flex items-start gap-3 bg-white border border-slate-200 border-l-4 ${stripeCls} rounded-md p-4 hover:shadow-sm hover:border-slate-300 transition-all`}
    >
      <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-slate-100 text-slate-700 shrink-0">
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <h3 className="text-base font-semibold text-slate-900 leading-tight">{title}</h3>
          <span className="font-mono text-sm text-slate-500">{count == null ? "—" : count}</span>
        </div>
        <p className="text-xs text-slate-500 mt-0.5 leading-snug">{subline}</p>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-400 mt-1 shrink-0 group-hover:text-slate-700 transition-colors" />
    </Link>
  );
}

function HubV2Chip({ to, icon: Icon, label, subline, testId }) {
  return (
    <Link
      to={to}
      data-testid={testId}
      className="group flex items-center gap-2.5 bg-white border border-slate-200 rounded-md px-3 py-2.5 hover:border-slate-300 hover:bg-slate-50 transition-colors min-h-[56px]"
    >
      <Icon className="w-4 h-4 text-slate-500 shrink-0" />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium text-slate-800 leading-tight">{label}</div>
        <div className="text-[10px] text-slate-500 leading-tight truncate">{subline}</div>
      </div>
    </Link>
  );
}

function HubV2MoreRow({ to, icon: Icon, label, count, testId }) {
  return (
    <Link
      to={to}
      data-testid={testId}
      className="group flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-50 transition-colors min-h-[44px]"
    >
      <Icon className="w-4 h-4 text-slate-400 shrink-0 group-hover:text-slate-600" />
      <span className="text-sm text-slate-700 flex-1">{label}</span>
      {count != null && (
        <span className="font-mono text-xs text-slate-500">{count}</span>
      )}
      <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" />
    </Link>
  );
}

export default function PmHub() {
  usePageTitle("PM · MASCI");
  const [counts, setCounts] = useState({});
  const [crewSummary, setCrewSummary] = useState(null);
  const [pmProjectNumbers, setPmProjectNumbers] = useState([]);
  const [loading, setLoading] = useState(true);
  // Phase IV-BETA.2 · Single unified flag — PM Sidebar V2 + Hub V2 travel
  // together as one cohesive governed PM experience.
  const v2 = isPmSidebarV2Enabled();

  // TRUST-PO-1 · 2026-05-28 — declare portal context on mount.
  useEffect(() => {
    try { setPortalContext("pm"); } catch { /* noop */ }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        // Mirror the per-resource fetch the old PmHub used — every list
        // route already filters by PM scope server-side, so .length is the
        // count for tiles. Failed calls fall back to 0 so the page never
        // dies on a partial outage.
        const [insp, mtg, jha, tb, inc, dr, eq, qa, crew] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/job-hazard-plans").catch(() => ({ data: [] })),
          api.get("/trench-boxes").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
          api.get("/daily-reports").catch(() => ({ data: [] })),
          api.get("/equipment-inspections").catch(() => ({ data: [] })),
          api.get("/qaqc-inspections").catch(() => ({ data: [] })),
          // iter353e-UI · crew compliance roll-up (best-effort)
          api.get("/pm/crew/summary").catch(() => ({ data: null })),
        ]);
        const len = (x) => (Array.isArray(x?.data) ? x.data.length : 0);
        setCounts({
          inspections: len(insp), meetings: len(mtg), jhaPlans: len(jha),
          trenchBoxes: len(tb), incidents: len(inc), daily: len(dr),
          equipment: len(eq), qaqc: len(qa),
        });
        setCrewSummary(crew?.data || null);
        // Extract project_numbers from already-fetched PM-scoped data
        // so the DispatchLifecycleTile can filter without a new API.
        const seen = new Set();
        const pushFrom = (arr) => {
          (Array.isArray(arr) ? arr : []).forEach((r) => {
            const p = r?.project_number || r?.project_no || r?.job_number;
            if (p && typeof p === "string") seen.add(p.trim());
          });
        };
        pushFrom(dr?.data); pushFrom(inc?.data); pushFrom(insp?.data); pushFrom(qa?.data);
        setPmProjectNumbers(Array.from(seen));
      } catch { /* tiles still render with em-dash */ }
      setLoading(false);
    })();
  }, []);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Project Management"
      homeHref="/pm"
      showSearch={false}
      showNotifications={false}
      showPortalSwitcher={false}
      showSignOut={false}
    >
      <PmShell
        title="Overview"
        section="overview"
        intro={
          v2 ? (
            // Phase IV-BETA.2 · Calm operational subline replaces the legacy
            // "Welcome to the PM Portal" marketing-tone intro. Doctrine:
            // CROSS_PORTAL_COACHING_STANDARD.md §V — sentence-case, ≤14 words.
            <p className="text-sm text-slate-600 leading-relaxed" data-testid="pm-hub-v2-subline">
              Today&apos;s operational signal across your assigned projects.
            </p>
          ) : (
            <div className="flex items-start gap-3">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
                <Briefcase className="w-5 h-5" />
              </div>
              <div className="text-sm text-slate-700 leading-relaxed">
                Welcome to the PM Portal. The forms below cover the day-to-day — Daily Reports,
                Inspections, Incidents, Photos, Field Leadership records, and more — scoped to
                jobs assigned to you. Use the sidebar (left, or hamburger on mobile) to dig into
                Active Jobs, Equipment Fleet, People, Suppliers, Posters, Email Routing, and
                Compliance Exports. System recovery and access-control tools remain Admin-only.
              </div>
            </div>
          )
        }
      >
        {loading ? (
          <div className="py-16 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : v2 ? (
          <div data-testid="pm-hub-v2">
          {/* Tier 0 · Operational KPI signal */}
          <OperationsCenter compact />

          {/* OA-1 · Operations Actions tile */}
          <div className="mt-3"><OperationsActionsTile /></div>

          {/* Tier 1 · Crew Compliance — calm slate + orange stripe (Compliance domain) */}
          <Link
            to="/pm/crew-compliance"
            className="block bg-white border border-slate-200 border-l-4 border-l-orange-600 rounded-md p-4 mt-5 hover:shadow-sm hover:border-slate-300 transition-all"
            data-testid="pm-crew-compliance-card"
          >
            <div className="flex items-start gap-3">
              <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-slate-100 text-slate-700 shrink-0">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2 flex-wrap">
                  <h3 className="text-base font-semibold text-slate-900">Crew Compliance</h3>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">180-day scope</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">Training currency, PPE, corrective-action exposure, expirations.</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-3" data-testid="pm-crew-compliance-card-tiles">
                  <div data-testid="pm-crew-card-tile-crew">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 flex items-center gap-1">
                      <Users className="w-3 h-3" /> Crew
                    </div>
                    <div className="text-xl font-semibold text-slate-900 mt-0.5">{crewSummary?.crew_size ?? "—"}</div>
                  </div>
                  <div data-testid="pm-crew-card-tile-expiring">
                    <div className={`text-[10px] font-mono uppercase tracking-wider flex items-center gap-1 ${crewSummary?.expiring_30d ? "text-amber-700" : "text-slate-500"}`}>
                      <AlertTriangle className="w-3 h-3" /> Expiring ≤30d
                    </div>
                    <div className={`text-xl font-semibold mt-0.5 ${crewSummary?.expiring_30d ? "text-amber-700" : "text-slate-900"}`}>{crewSummary?.expiring_30d ?? "—"}</div>
                  </div>
                  <div data-testid="pm-crew-card-tile-expired">
                    <div className={`text-[10px] font-mono uppercase tracking-wider flex items-center gap-1 ${crewSummary?.expired ? "text-orange-700" : "text-slate-500"}`}>
                      <CircleSlash className="w-3 h-3" /> Expired
                    </div>
                    <div className={`text-xl font-semibold mt-0.5 ${crewSummary?.expired ? "text-orange-700" : "text-slate-900"}`}>{crewSummary?.expired ?? "—"}</div>
                  </div>
                  <div data-testid="pm-crew-card-tile-capas">
                    <div className={`text-[10px] font-mono uppercase tracking-wider flex items-center gap-1 ${crewSummary?.open_capas ? "text-amber-700" : "text-slate-500"}`}>
                      <ClipboardCheck className="w-3 h-3" /> Open Corrective Actions
                    </div>
                    <div className={`text-xl font-semibold mt-0.5 ${crewSummary?.open_capas ? "text-amber-700" : "text-slate-900"}`}>{crewSummary?.open_capas ?? "—"}</div>
                  </div>
                </div>
              </div>
            </div>
          </Link>

          {/* Tier 1 · Today — 3 quick-action tiles */}
          <div className="mt-5">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2">Today</div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4" data-testid="pm-hub-v2-tier1">
              {HUB_V2_TIER1.map((t) => (
                <HubV2QuickTile
                  key={t.to} to={t.to} icon={t.icon} title={t.title}
                  count={t.countKey ? counts[t.countKey] : null}
                  subline={t.subline} stripe={t.stripe}
                  testId={`pm-hub-v2-tile-${t.to.split("/").pop()}`}
                />
              ))}
            </div>
          </div>

          {/* Tier 2 · Coordination — 4 compact chips */}
          <div className="mt-5">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2">Coordination</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3" data-testid="pm-hub-v2-tier2">
              {HUB_V2_TIER2_CHIPS.map((c) => (
                <HubV2Chip
                  key={c.to} to={c.to} icon={c.icon} label={c.label} subline={c.subline}
                  testId={`pm-hub-v2-chip-${c.to.replace(/^\//, "")}`}
                />
              ))}
            </div>
          </div>

          {/* Tier 2 · Haul + Dispatch lifecycle (preserved) */}
          <div className="mt-5" data-testid="pm-haul-activity-mount">
            <PmHaulActivityTile projectNumbers={pmProjectNumbers} />
          </div>
          <div className="mt-3" data-testid="pm-dispatch-lifecycle-mount">
            <DispatchLifecycleTile scope="pm" projectNumbers={pmProjectNumbers} testId="pm-dispatch-lifecycle" />
          </div>

          {/* Tier 3 · More forms — compact list (Meetings · Pre-Op · QA/QC · Photos · JHA · Trench · FL · Guides) */}
          <div className="mt-5">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2">More forms</div>
            <div className="bg-white border border-slate-200 rounded-md divide-y divide-slate-100" data-testid="pm-hub-v2-tier3-more">
              {HUB_V2_TIER3_MORE.map((m) => (
                <HubV2MoreRow
                  key={m.to} to={m.to} icon={m.icon} label={m.label}
                  count={m.countKey ? counts[m.countKey] : null}
                  testId={`pm-hub-v2-more-${m.to.split("/").pop()}`}
                />
              ))}
            </div>
          </div>

          {/* Tier 4 · Activity trace */}
          <div className="mt-5">
            <LastActivityLine portal="pm" />
          </div>

          {/* Tier 4.5 · Governance health (iter437 IV-BETA.5A-P1A) */}
          <div className="mt-3">
            <GovernanceHealthChip portal="pm" />
          </div>

          {/* Tier 5 · Field memory + optional enrollment (de-emphasized) */}
          <div className="mt-5">
            <FieldMemoryGlance />
          </div>
          <div className="mt-3">
            <PasskeyEnrollPrompt />
          </div>
          </div>
        ) : (
          <>
          {/* iter429 · Phase 28 · Optional device sign-in enrollment ·
              self-gated · dismissible · single-card · NEVER nags */}
          <div className="mt-5">
            <PasskeyEnrollPrompt />
          </div>

          {/* iter432 · Phase 30 · Part 6 · Option iii · ONE calm additive
              operational-attention surface — read-only Field Memory glance. */}
          <div className="mt-5">
            <FieldMemoryGlance />
          </div>

          {/* iter440 · calm "Last activity" trace. */}
          <div className="mt-5">
            <LastActivityLine portal="pm" />
          </div>

          <OperationsCenter compact className="mt-5" />

          {/* OA-1 · Operations Actions tile · legacy hub */}
          <div className="mt-3"><OperationsActionsTile /></div>

          {/* iter353e-UI · My Crew Compliance — operational accountability awareness */}
          <Link
            to="/pm/crew-compliance"
            className="block bg-white border-2 border-amber-600 rounded-md p-4 sm:p-5 mt-5 hover:shadow-md transition-shadow group"
            data-testid="pm-crew-compliance-card"
          >
            <div className="flex items-start gap-3">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">
                    My Crew Compliance
                  </h3>
                  <span className="px-1.5 py-0.5 border border-slate-200 bg-slate-50 rounded text-[10px] font-mono uppercase tracking-wider text-slate-600">
                    Read-only · 180d scope
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  Operational accountability awareness for crews on your projects — training currency, PPE, corrective-action exposure, expirations.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-3" data-testid="pm-crew-compliance-card-tiles">
                  <div data-testid="pm-crew-card-tile-crew">
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold flex items-center gap-1">
                      <Users className="w-3 h-3" /> Crew (180d)
                    </div>
                    <div className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
                      {crewSummary?.crew_size ?? "—"}
                    </div>
                  </div>
                  <div data-testid="pm-crew-card-tile-expiring">
                    <div className={`font-mono text-[10px] uppercase tracking-[0.18em] font-bold flex items-center gap-1 ${crewSummary?.expiring_30d ? "text-amber-700" : "text-slate-500"}`}>
                      <AlertTriangle className="w-3 h-3" /> Expiring ≤30d
                    </div>
                    <div className={`font-display text-2xl font-black leading-none mt-1 ${crewSummary?.expiring_30d ? "text-amber-700" : "text-slate-900"}`}>
                      {crewSummary?.expiring_30d ?? "—"}
                    </div>
                  </div>
                  <div data-testid="pm-crew-card-tile-expired">
                    <div className={`font-mono text-[10px] uppercase tracking-[0.18em] font-bold flex items-center gap-1 ${crewSummary?.expired ? "text-rose-700" : "text-slate-500"}`}>
                      <CircleSlash className="w-3 h-3" /> Expired
                    </div>
                    <div className={`font-display text-2xl font-black leading-none mt-1 ${crewSummary?.expired ? "text-rose-700" : "text-slate-900"}`}>
                      {crewSummary?.expired ?? "—"}
                    </div>
                  </div>
                  <div data-testid="pm-crew-card-tile-capas">
                    <div className={`font-mono text-[10px] uppercase tracking-[0.18em] font-bold flex items-center gap-1 ${crewSummary?.open_capas ? "text-amber-700" : "text-slate-500"}`}>
                      <ClipboardCheck className="w-3 h-3" /> Open Corrective Actions
                    </div>
                    <div className={`font-display text-2xl font-black leading-none mt-1 ${crewSummary?.open_capas ? "text-amber-700" : "text-slate-900"}`}>
                      {crewSummary?.open_capas ?? "—"}
                    </div>
                  </div>
                </div>
              </div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold flex items-center gap-1 group-hover:gap-2 transition-all whitespace-nowrap">
                Open <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          </Link>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mt-5" data-testid="pm-tile-grid">
            {FORM_TILES.map((t) => (
              <PmTile
                key={t.to}
                to={t.to}
                icon={t.icon}
                title={t.title}
                count={t.countKey ? counts[t.countKey] : null}
                sub={t.sub}
                accent={t.accent}
                testId={`pm-tile-${t.to.split("/").pop()}`}
              />
            ))}
          </div>

          {/* iter409 · Phase 14.3 · PM Haul Activity production awareness */}
          <div className="mt-6" data-testid="pm-haul-activity-mount">
            <PmHaulActivityTile projectNumbers={pmProjectNumbers} />
          </div>

          {/* iter396 · DLS cross-portal convergence — read-only, project-scoped */}
          <div className="mt-6" data-testid="pm-dispatch-lifecycle-mount">
            <DispatchLifecycleTile
              scope="pm"
              projectNumbers={pmProjectNumbers}
              testId="pm-dispatch-lifecycle"
            />
          </div>
          </>
        )}
      </PmShell>
    </PortalShell>
  );
}
