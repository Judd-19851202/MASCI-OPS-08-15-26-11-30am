/**
 * TRACK 18.00 · Phase A · Transportation Operations universal shell.
 *
 * Provides the standardized layout every workspace inside
 * Transportation Operations renders inside:
 *
 *   ┌────────────────────────────────────────────────────────┐
 *   │ TxOpsHeader (workspace title · context · actions)      │
 *   ├──────────────────────────────────────┬─────────────────┤
 *   │ BODY (workspace-specific content)    │ RIGHT RAIL      │
 *   │                                      │  · Recent       │
 *   │                                      │  · Timeline     │
 *   │                                      │  · Related      │
 *   │                                      │  · Open Actions │
 *   │                                      │  · Audit        │
 *   └──────────────────────────────────────┴─────────────────┘
 *
 * Phase A delivers the SHELL ONLY — the right-rail sections are
 * intentionally rendered as scaffolded placeholders that wire up
 * to real data sources in Phase D. The header + body slot are
 * fully functional from day one.
 *
 * Doctrine:
 *   - One card, one chip, one header library.
 *   - No new backend.
 *   - No new collections.
 *   - No new scoring.
 *   - No URL break — every existing transportation route still resolves.
 */
import React from "react";
import { Link } from "react-router-dom";
import {
  Activity, History, Inbox, Link2, Sparkles,
} from "lucide-react";

/* ─────────────────────────────────────────────────────────────────
 * One shared header. Every workspace uses this — never custom.
 * ────────────────────────────────────────────────────────────── */
export function TxOpsHeader({
  workspace,           // operational group label (e.g. "People")
  title,               // workspace title (e.g. "Drivers")
  subtitle,            // optional one-liner
  rightSlot,           // primary actions (chips, buttons)
  testid,
}) {
  return (
    <header
      data-testid={testid || "txops-header"}
      className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-3 mb-4"
    >
      <div className="min-w-0">
        {workspace ? (
          <div
            data-testid="txops-header-group"
            className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold"
          >
            {workspace}
          </div>
        ) : null}
        <h1
          data-testid="txops-header-title"
          className="text-2xl font-semibold text-slate-900 leading-tight"
        >
          {title}
        </h1>
        {subtitle ? (
          <p className="text-sm text-slate-600 mt-1 max-w-2xl">{subtitle}</p>
        ) : null}
      </div>
      {rightSlot ? (
        <div
          data-testid="txops-header-actions"
          className="flex items-center gap-2 flex-shrink-0"
        >
          {rightSlot}
        </div>
      ) : null}
    </header>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * Universal right-rail · 5 sections.
 *
 * Phase A renders calm "wired in Phase D" placeholders. The
 * structure + testids are locked here so later phases just fill
 * the slots without changing the chrome.
 * ────────────────────────────────────────────────────────────── */
function RailSection({ icon: Icon, title, testid, children }) {
  return (
    <section
      data-testid={testid}
      className="rounded-md border border-slate-200 bg-white"
    >
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-100">
        {Icon ? <Icon className="h-3.5 w-3.5 text-slate-500" /> : null}
        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-700">
          {title}
        </div>
      </div>
      <div className="p-3 text-xs text-slate-600">
        {children}
      </div>
    </section>
  );
}

export function TxOpsRightRail({
  entityContext,       // { type, id } when on an entity workspace
  recentActivity,      // optional override for Phase D
  timeline,            // optional override
  relatedRecords,      // optional override
  openActions,         // optional override
  auditHref,           // link to admin audit timeline
  testid,
}) {
  const calmPlaceholder = (
    <div className="text-[11px] text-slate-400 italic">
      Wired in Phase D — universal right-rail data.
    </div>
  );

  return (
    <aside
      data-testid={testid || "txops-right-rail"}
      className="hidden xl:flex flex-col gap-3 w-72 shrink-0"
    >
      <RailSection
        icon={Activity}
        title="Recent Activity"
        testid="txops-rail-recent-activity"
      >
        {recentActivity || calmPlaceholder}
      </RailSection>

      <RailSection
        icon={History}
        title="Timeline"
        testid="txops-rail-timeline"
      >
        {timeline || (entityContext ? (
          <div className="text-[11px] text-slate-500">
            Entity: <span className="font-mono">{entityContext.type}:{entityContext.id}</span>
          </div>
        ) : calmPlaceholder)}
      </RailSection>

      <RailSection
        icon={Link2}
        title="Related Records"
        testid="txops-rail-related"
      >
        {relatedRecords || calmPlaceholder}
      </RailSection>

      <RailSection
        icon={Inbox}
        title="Open Actions"
        testid="txops-rail-open-actions"
      >
        {openActions || calmPlaceholder}
      </RailSection>

      <RailSection
        icon={Sparkles}
        title="Audit"
        testid="txops-rail-audit"
      >
        <Link
          to={auditHref || "/admin/transportation/administration/audit"}
          data-testid="txops-rail-audit-link"
          className="text-amber-700 hover:text-amber-900 underline-offset-2 hover:underline"
        >
          Open the full audit timeline →
        </Link>
      </RailSection>
    </aside>
  );
}

/* ─────────────────────────────────────────────────────────────────
 * The universal shell. Wraps every workspace inside Transportation
 * Operations with a consistent layout.
 *
 * Usage:
 *   <TransportationWorkspaceShell
 *     workspace="People"
 *     title="Drivers"
 *     subtitle="Driver master, eligibility, intelligence"
 *     rightSlot={<MyActions />}
 *     entityContext={{ type: "driver", id }}
 *   >
 *     {body}
 *   </TransportationWorkspaceShell>
 * ────────────────────────────────────────────────────────────── */
export default function TransportationWorkspaceShell({
  workspace,
  title,
  subtitle,
  rightSlot,
  entityContext,
  hideRightRail = false,
  children,
}) {
  return (
    <div
      data-testid="txops-workspace-shell"
      className="space-y-3"
    >
      <TxOpsHeader
        workspace={workspace}
        title={title}
        subtitle={subtitle}
        rightSlot={rightSlot}
      />
      <div className="flex gap-6">
        <main
          data-testid="txops-workspace-body"
          className="flex-1 min-w-0 space-y-4"
        >
          {children}
        </main>
        {hideRightRail ? null : (
          <TxOpsRightRail entityContext={entityContext} />
        )}
      </div>
    </div>
  );
}
