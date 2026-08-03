/**
 * PmCommandCenter.jsx · FORGEDOPS PM Command Center · Phase 4B.
 *
 * Route: /pm/command-center (RequirePm — admin tokens also accepted).
 * Query: ?project_number=<canonical> to filter every section to one
 *        project. Omit for "all my projects".
 *
 * One page · six operational sections · top KPI strip · honest empty
 * states · no fake green status · iPad-friendly · 5:30 AM test.
 *
 * Powered exclusively by Phase 4A endpoints
 * (/api/pm/command-center/{overview,resources,hauls,materials,
 * shop-impact,safety-impact,timeline}). No new backend route, no
 * duplicate PM project page, no map, no analytics.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  LayoutDashboard, Truck, Boxes, Wrench, ShieldAlert,
  Activity, ArrowLeft,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePageTitle } from "@/lib/usePageTitle";
import { PortalShell } from "@/design-system";
import PmSideNavV2 from "@/components/pm/sidebar/SideNavV2";
import PmCommandStrip from "@/components/pm/command/PmCommandStrip";
import PmResourcesBoard from "@/components/pm/command/PmResourcesBoard";
import PmHaulsBoard from "@/components/pm/command/PmHaulsBoard";
import PmMaterialsBoard from "@/components/pm/command/PmMaterialsBoard";
import PmShopImpactBoard from "@/components/pm/command/PmShopImpactBoard";
import PmSafetyImpactBoard from "@/components/pm/command/PmSafetyImpactBoard";
import PmTimelineBoard from "@/components/pm/command/PmTimelineBoard";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import PmProjectFirstHome from "@/components/pm/command/PmProjectFirstHome";
import JobTeamRosterPanel from "@/components/team/JobTeamRosterPanel";
import { pmCommandApi } from "@/components/pm/command/pmCommandApi";
import { Users } from "lucide-react";
import { OperationsTransportationHealthWidget } from "@/components/operations_transportation_integration";
import OiAttentionStrip from "@/components/operational_intelligence/OiAttentionStrip";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
import { sanitizeOperatorProjectNumber } from "@/lib/operatorLanguage";

const OVERVIEW_POLL_MS = 45000;

export default function PmCommandCenter() {
  usePageTitle("PM Command Center · MASCI");
  const [searchParams, setSearchParams] = useSearchParams();

  const projectNumber = searchParams.get("project_number") || null;
  const initialKind = searchParams.get("kind") || "all";

  const [tab, setTab] = useState("overview");
  // Track 13 · §6 — default view is project-first; tabs are the
  // "detailed operational view" reachable via the support-resources
  // section footer. The tab view still works exactly as before.
  const [viewMode, setViewMode] = useState("projects");
  const [overview, setOverview] = useState(null);
  const [loadingOverview, setLoadingOverview] = useState(true);
  const [resourceKindFilter, setResourceKindFilter] = useState(initialKind);

  const loadOverview = useCallback(async () => {
    try {
      const d = await pmCommandApi.overview(projectNumber);
      setOverview(d);
    } catch (_e) {
      // SessionStatusOverlay handles auth/network errors globally.
    } finally {
      setLoadingOverview(false);
    }
  }, [projectNumber]);
  useEffect(() => {
    loadOverview();
    const id = setInterval(loadOverview, OVERVIEW_POLL_MS);
    return () => clearInterval(id);
  }, [loadOverview]);
  const setProjectNumber = useCallback((pn) => {
    const next = new URLSearchParams(searchParams);
    if (pn) next.set("project_number", pn);
    else next.delete("project_number");
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  const jumpTo = useCallback((section) => {
    setTab(section);
    setResourceKindFilter("all");
  }, []);

  const jumpToWithFilter = useCallback((section, filterKind) => {
    setTab(section);
    setResourceKindFilter(filterKind || "all");
  }, []);

  const headerSubtitle = useMemo(() => {
    if (projectNumber) return `Project · ${sanitizeOperatorProjectNumber(projectNumber, "Operations support")}`;
    return "Projects assigned to you";
  }, [projectNumber]);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Project Management"
      pageTitle="Project Management Center"
      subtitle={headerSubtitle}
      showBack
      backHref="/pm"
      portalSwitcherCurrent="pm"
      sideNav={<PmSideNavV2 />}
      primaryActions={
        <div className="flex items-center gap-3">
          {/* RC1-PORTAL-NAV-001 · Dispatch shortcut removed —
              clicking it sent PM users to /dispatch-portal/command
              and returned 403. Dispatch surface is not part of the
              PM portal scope. */}
          <Link
            to="/pm"
            className="text-xs text-slate-600 hover:text-slate-900 font-mono uppercase tracking-widest"
            data-testid="pm-cc-back-hub"
          >
            PM Home
          </Link>
        </div>
      }
      lastActivity={
        overview?.as_of
          ? `Updated ${formatPlatformTimeOnly(overview.as_of)}`
          : overview ? "Updated just now" : null
      }
    >
      <div data-testid="pm-command-center" className="space-y-4">
        {/* Track 19.52 · P1 #3 — OI Attention Strip.
           project_intelligence signal at the very top of the PM
           Command Center. Zero-drift: no new backend, no new score. */}
        <OiAttentionStrip
          portal="pm"
          productIds={["project_intelligence"]}
          title="Project Intelligence · attention now"
          testId="pm-cc-oi-strip"
        />

        <div className="flex flex-wrap items-center justify-between gap-3">
          <PmProjectSelector value={projectNumber} onChange={setProjectNumber} />
          {overview ? (
            <div className="text-[10.5px] font-mono uppercase tracking-widest text-slate-500" data-testid="pm-cc-as-of">
              {overview.as_of
                ? `Updated ${formatPlatformTimeOnly(overview.as_of)}`
                : "Updated just now"}
            </div>
          ) : null}
        </div>

        <PmCommandStrip
          overview={overview}
          loading={loadingOverview}
          onJumpTo={jumpTo}
          onJumpToWithFilter={jumpToWithFilter}
          hidden={viewMode === "projects"}
        />

        {viewMode === "projects" ? (
          /* Track 13 · §6 PM Portal Rebuild — project-first home.
             Replaces the 12-tile fleet strip + 7-tab resource-typed
             layout as the default first screen. The detailed tab view
             is one click away via the support-resources footer. */
          <PmProjectFirstHome
            overview={overview}
            loading={loadingOverview}
            onOpenDetailedView={() => setViewMode("detailed")}
          />
        ) : (
        <>
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setViewMode("projects")}
            data-testid="pm-cc-back-to-projects"
            className="inline-flex items-center min-h-[44px] px-3 -ml-1 text-xs font-mono uppercase tracking-widest text-slate-600 hover:text-slate-900"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to project view
          </button>
        </div>

        <Tabs value={tab} onValueChange={setTab} className="space-y-4">
          <TabsList
            className="w-full h-auto flex flex-wrap justify-start bg-white border border-slate-200 p-1 rounded-md gap-1"
            data-testid="pm-cc-tabs"
          >
            <TabsTrigger value="overview" data-testid="pm-cc-tab-overview" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <LayoutDashboard className="w-3.5 h-3.5 mr-1.5" /> Overview
            </TabsTrigger>
            <TabsTrigger value="resources" data-testid="pm-cc-tab-resources" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Truck className="w-3.5 h-3.5 mr-1.5" /> Resources
            </TabsTrigger>
            <TabsTrigger value="hauls" data-testid="pm-cc-tab-hauls" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Activity className="w-3.5 h-3.5 mr-1.5" /> Hauls
            </TabsTrigger>
            <TabsTrigger value="materials" data-testid="pm-cc-tab-materials" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Boxes className="w-3.5 h-3.5 mr-1.5" /> Materials
            </TabsTrigger>
            <TabsTrigger value="shop" data-testid="pm-cc-tab-shop" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Wrench className="w-3.5 h-3.5 mr-1.5" /> Shop
            </TabsTrigger>
            <TabsTrigger value="safety" data-testid="pm-cc-tab-safety" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <ShieldAlert className="w-3.5 h-3.5 mr-1.5" /> Safety
            </TabsTrigger>
            <TabsTrigger value="team" data-testid="pm-cc-tab-team" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Users className="w-3.5 h-3.5 mr-1.5" /> Team
            </TabsTrigger>
            <TabsTrigger value="timeline" data-testid="pm-cc-tab-timeline" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Activity className="w-3.5 h-3.5 mr-1.5" /> Timeline
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" data-testid="pm-cc-tab-content-overview">
            {/* TRACK 16.16 · Transportation Health widget — same
                consumer envelope used on OperationsCenterCommand.
                One glance · one click · no duplicate dashboard. */}
            <div className="mb-4">
              <OperationsTransportationHealthWidget />
            </div>
            <PmOverviewPane overview={overview} loading={loadingOverview} onJumpTo={jumpTo} />
          </TabsContent>
          <TabsContent value="resources" data-testid="pm-cc-tab-content-resources">
            <PmResourcesBoard projectNumber={projectNumber} initialKind={resourceKindFilter} />
          </TabsContent>
          <TabsContent value="hauls" data-testid="pm-cc-tab-content-hauls">
            <PmHaulsBoard projectNumber={projectNumber} />
          </TabsContent>
          <TabsContent value="materials" data-testid="pm-cc-tab-content-materials">
            <PmMaterialsBoard projectNumber={projectNumber} />
          </TabsContent>
          <TabsContent value="shop" data-testid="pm-cc-tab-content-shop">
            <PmShopImpactBoard projectNumber={projectNumber} />
          </TabsContent>
          <TabsContent value="safety" data-testid="pm-cc-tab-content-safety">
            <PmSafetyImpactBoard projectNumber={projectNumber} />
          </TabsContent>
          <TabsContent value="team" data-testid="pm-cc-tab-content-team">
            {/* Track 14.0-PM-STAFFING-COMPLETION · always-visible
                Team Card. Shows the 17-role project roster inline so
                PMs never need to navigate to /pm/job/:pn/team. */}
            {projectNumber ? (
              <div data-testid="pm-cc-team-card" className="bg-white border border-slate-200 rounded-md p-4">
                <JobTeamRosterPanel projectNumber={projectNumber} scope="pm" />
              </div>
            ) : (
              <div
                data-testid="pm-cc-team-card-empty"
                className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-md p-4"
              >
                Pick a project from the selector above to see and manage its team.
              </div>
            )}
          </TabsContent>
          <TabsContent value="timeline" data-testid="pm-cc-tab-content-timeline">
            <PmTimelineBoard projectNumber={projectNumber} />
          </TabsContent>
        </Tabs>
        </>
        )}
      </div>
    </PortalShell>
  );
}

/* ────────────────────────────────────────────────────────────────── */
function OvRow({ k, v, mono = true, testId }) {
  return (
    <div
      className="flex justify-between text-xs sm:text-sm py-1.5 border-b border-slate-100 last:border-b-0"
      data-testid={testId}
    >
      <span className="text-slate-600">{k}</span>
      <span className={`text-slate-900 font-bold ${mono ? "font-mono" : ""}`}>{v ?? "—"}</span>
    </div>
  );
}

function PmOverviewPane({ overview, loading, onJumpTo }) {
  const counts = overview?.counts || {};
  const ir = overview?.integration_readiness || {};

  if (loading && !overview) {
    return (
      <div className="space-y-2" data-testid="pm-cc-overview-skeleton">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-12 bg-slate-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4" data-testid="pm-cc-overview-pane">
      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="pm-cc-overview-resources-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Resources</span>
          <button
            className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900"
            onClick={() => onJumpTo("resources")}
            data-testid="pm-cc-overview-resources-open"
          >Open →</button>
        </h3>
        <OvRow k="Equipment assigned" v={counts.equipment_assigned} testId="pm-cc-ov-equipment" />
        <OvRow k="Trucks assigned" v={counts.trucks_assigned} testId="pm-cc-ov-trucks" />
        <OvRow k="Trailers assigned" v={counts.trailers_assigned} testId="pm-cc-ov-trailers" />
        <OvRow k="Road plates assigned" v={counts.road_plates_assigned} testId="pm-cc-ov-road-plates" />
        <OvRow k="Drivers assigned" v={counts.drivers_assigned} testId="pm-cc-ov-drivers" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="pm-cc-overview-hauls-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Hauls</span>
          <button
            className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900"
            onClick={() => onJumpTo("hauls")}
            data-testid="pm-cc-overview-hauls-open"
          >Open →</button>
        </h3>
        <OvRow k="Active assignments" v={counts.active_assignments} testId="pm-cc-ov-assignments" />
        <OvRow k="Active hauls" v={counts.active_hauls} testId="pm-cc-ov-active-hauls" />
        <OvRow k="Loads today" v={counts.loads_today} testId="pm-cc-ov-loads-today" />
        <OvRow k="Materials in today" v={counts.materials_in_today} testId="pm-cc-ov-mat-in" />
        <OvRow k="Materials out today" v={counts.materials_out_today} testId="pm-cc-ov-mat-out" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="pm-cc-overview-impact-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Impact</span>
          <button
            className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900"
            onClick={() => onJumpTo("shop")}
            data-testid="pm-cc-overview-impact-open"
          >Open →</button>
        </h3>
        <OvRow k="Open defects" v={counts.defects_open} testId="pm-cc-ov-defects" />
        <OvRow k="Open incidents" v={counts.incidents_open} testId="pm-cc-ov-incidents" />
        <OvRow k="Open CAPAs" v={counts.capas_open} testId="pm-cc-ov-capas" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="pm-cc-overview-integration-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5">Integrations</h3>
        <OvRow
          k="FleetWatcher"
          v={ir.fleetwatcher === "not_connected" ? "Pending Integration" : (ir.fleetwatcher || "—")}
          mono={false}
          testId="pm-cc-ov-fleetwatcher"
        />
        <OvRow
          k="MaintainX"
          v={ir.maintainx === "not_connected" ? "Pending Integration" : (ir.maintainx || "—")}
          mono={false}
          testId="pm-cc-ov-maintainx"
        />
      </div>
    </div>
  );
}
