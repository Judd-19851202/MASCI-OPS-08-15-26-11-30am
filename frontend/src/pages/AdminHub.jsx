// AdminHub.jsx — /admin Overview page (iter83 redesign)
//
// The dashboard glance: top-line KPIs + always-visible Doc-ID search +
// 8 tile-style entry points into each admin section. Every panel that
// used to live on this page has been moved to one of /admin/{section}
// pages — nothing was removed, just reorganized.

import React from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import AdminShell, { SECTIONS } from "@/components/AdminShell";
import AdminDocIdSearch from "@/components/AdminDocIdSearch";
import AdminKpiStrip from "@/components/AdminKpiStrip";
import IntegrationHealthCard from "@/components/IntegrationHealthCard";
import OperationsCenter from "@/components/OperationsCenter";
import MotiveOpsIntelPanel from "@/components/MotiveOpsIntelPanel";
import { getAdminToken } from "@/lib/adminAuth";
import { usePageTitle } from "@/lib/usePageTitle";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";
import GovernanceHealthChip from "@/components/GovernanceHealthChip";
import { setPortalContext } from "@/lib/portalContext";

// iter326 · platform-wide calm convergence — AdminHub SectionTile
// migrated from the legacy hot-chrome pattern (border-2 +
// hover:border-red-700) to the calm family contract (border +
// border-l-4 red-700 accent stripe + slate-200 borders + slate-300
// hover). Same visual identity as SafetyHub, HrHub, FieldHub, etc.
function SectionTile({ to, icon: Icon, label, desc, testId }) {
  return (
    <Link
      to={to}
      className="group bg-white border border-slate-200 border-l-4 border-l-red-700 hover:shadow-md hover:border-slate-300 rounded-md p-5 transition-all duration-150 hover:-translate-y-0.5 flex items-start gap-3"
      data-testid={testId}
    >
      <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-slate-900 text-white shrink-0">
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="font-display text-base font-black tracking-tight text-slate-900 leading-tight">
          {label}
        </h3>
        <p className="text-slate-600 text-xs mt-1.5 leading-snug">{desc}</p>
      </div>
      <ChevronRight className="w-5 h-5 mt-2 text-slate-400 group-hover:text-slate-700 group-hover:translate-x-0.5 transition-all shrink-0" />
    </Link>
  );
}

export default function AdminHub() {
  usePageTitle("Admin Console · MASCI");
  // TRUST-PO-1 · 2026-05-28 — declare portal context on mount so shared
  // pages (e.g., /po-requests) know the operator is in the Admin context.
  React.useEffect(() => {
    try { setPortalContext("admin"); } catch { /* noop */ }
  }, []);
  // The Overview tile excludes itself.
  const tiles = SECTIONS.filter((s) => s.key !== "overview");

  return (
    <AdminShell
      title="Overview"
      section="overview"
      intro={
        <p className="text-sm text-slate-600 leading-relaxed">
          Welcome to the MASCI Admin Console. Every administrative tool on the platform lives one
          click away in the navigation on the left (or hamburger on mobile). Below is a high-level
          snapshot of today's activity — plus a Doc-ID search if you're hunting a specific record.
        </p>
      }
    >
      <div className="space-y-5">
        {/* iter437 IV-BETA.5A-P1A · governance health chip (quiet) */}
        <GovernanceHealthChip portal="admin" />

        {/* iter422 · Phase 24 · Optional device sign-in enrollment (self-gated · dismissible · single-card) */}
        <PasskeyEnrollPrompt />

        {/* Operations Center — real-time aggregated operational visibility */}
        <OperationsCenter />

        {/* OIS-1E · Motive Operations Intelligence (single-pane fleet/driver/safety snapshot) */}
        <MotiveOpsIntelPanel />

        {/* Records-on-file count strip — at-a-glance KPIs */}
        <AdminKpiStrip />

        {/* Frequently-used: Doc-ID search */}
        <AdminDocIdSearch />

        {/* iter445 · F-003 fix — surface scheduler/digest execution history
           inside the platform (was email-only). Operators can answer
           "Why did this digest send · which pod · when · who received it
           · was a duplicate prevented" without admin DB access. */}
        <Link
          to="/admin/scheduler-runs"
          data-testid="admin-tile-scheduler-runs"
          className="block bg-white border border-slate-200 border-l-4 border-l-amber-600 hover:shadow-md hover:border-slate-300 rounded-md p-4 transition-all duration-150"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-700 font-bold">audit · iter445</p>
              <h3 className="font-display text-sm font-black tracking-tight text-slate-900 mt-0.5">Scheduler Runs · Digest History</h3>
              <p className="text-xs text-slate-600 mt-1">Every Monday PO / safety / operator digest fire — recipient count, pod, dedup attempts. Read-only.</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400 shrink-0" />
          </div>
        </Link>

        {/* Integration framework health (Motive + MaintainX) */}
        <IntegrationHealthCard
          tokenHeader={{ "X-Admin-Token": getAdminToken() || "" }}
          showAdminLink={false}
          accent="slate"
        />

        {/* Section tiles — 7 entries (Overview itself excluded) */}
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2 mt-2">
            Jump to a section
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {tiles.map((s) => (
              <SectionTile
                key={s.key}
                to={s.to}
                icon={s.icon}
                label={s.label}
                desc={s.desc}
                testId={`admin-tile-${s.key}`}
              />
            ))}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
