/**
 * DispatchHub.jsx · iter441 · OMEGA Polish Sprint · Command Center Mode
 *
 * Polish-only refactor (no new features, no new backend):
 *   - Operational Attention is the FIRST operational surface visible.
 *   - Decorative read-only surfaces (PasskeyEnrollPrompt, FieldMemoryGlance,
 *     LastActivityLine) sit BELOW operational content (P0 hierarchy rule).
 *   - Coaching is collapsed by default for returning users (localStorage),
 *     expanded by default on first visit.
 *   - Guide tiles consolidated into a single "Dispatch Resources" CTA.
 *   - Section padding reduced from p-5 → p-4, vertical rhythm space-y-6 → space-y-4.
 *   - Local footer removed (duplicate of <GlobalFooter /> mounted in App.js).
 *   - Every route, test-id, capability, and backend call PRESERVED.
 *
 * Visual doctrine: Command center — live signals first, instruction last.
 */
import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Truck, Send, ShieldAlert, Activity, LogOut, Clock, Home, ArrowLeft,
  Plug, BookOpen, ShieldCheck, AlertTriangle, Wrench, Droplet, ArrowRight,
  Package, Compass, ListChecks, ChevronDown, ChevronUp,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import PortalSwitcher from "@/components/PortalSwitcher";
import NotificationBell from "@/components/NotificationBell";
import GlobalSearch from "@/components/GlobalSearch";
import { OfflineIndicator } from "@/lib/resiliency";
import {
  DispatchOverviewTab, DispatchUtilizationTab, DispatchIdleAlertsTab,
  DispatchTransfersTab, DispatchHoldsTab,
} from "@/pages/admin/AdminDispatch";
import DispatchIntegrationsTab from "@/components/DispatchIntegrationsTab";
import AssignmentCreateDrawer from "@/components/dispatch/AssignmentCreateDrawer";
import { clearDispatchToken, getDispatchUser, getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { paletteFor } from "@/lib/portalPalette";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";
import DispatchSideNavV2, { useDispatchSidebarV2Enabled } from "@/components/dispatch/sidebar/DispatchSideNavV2";
import { FieldMemoryGlance } from "@/components/field_memory/FieldMemoryGlance";
import DispatchEquipmentMaintenanceIndicator from "@/components/dispatch/DispatchEquipmentMaintenanceIndicator";
import LastActivityLine from "@/components/admin/LastActivityLine";

const API = process.env.REACT_APP_BACKEND_URL;
const DISPATCH_PAL = paletteFor("dispatch");
const COACH_LS_KEY = "masci.dispatch.coaching.collapsed";

function authHeaders() {
  const headers = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const d = getDispatchToken();
  if (a) headers["X-Admin-Token"] = a;
  if (d) headers["X-Dispatch-Token"] = d;
  return headers;
}

// Coaching collapse state (per-device, localStorage).
// iter504 · OMEGA Dispatch Production Readiness Sprint:
// COLLAPSED BY DEFAULT for every user — operators should not see training
// material at every visit. The block surfaces a counter and an expand affordance.
// Operator can persist their preference via toggling (stored in localStorage).
function useCoachingCollapsed() {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      const v = localStorage.getItem(COACH_LS_KEY);
      // null (first visit) → collapsed; "0" → expanded; "1" → collapsed
      return v === null ? true : v === "1";
    } catch { return true; }
  });
  const set = (v) => {
    setCollapsed(v);
    try { localStorage.setItem(COACH_LS_KEY, v ? "1" : "0"); }
    catch { /* noop */ }
  };
  return [collapsed, set];
}

export default function DispatchHub() {
  usePageTitle("Dispatch Command · MASCI");
  const { t } = useT();
  const nav = useNavigate();
  const user = getDispatchUser() || {};
  const sidebarV2 = useDispatchSidebarV2Enabled();

  const [createOpen, setCreateOpen] = useState(false);
  const [createHaulType, setCreateHaulType] = useState("Material");
  const [coachCollapsed, setCoachCollapsed] = useCoachingCollapsed();

  const [attention, setAttention] = useState({ findings: [], loading: true, error: false });

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(`${API}/api/dispatch/governance/findings`, { headers: authHeaders() });
        const j = await r.json().catch(() => ({}));
        if (cancelled) return;
        setAttention({
          findings: Array.isArray(j.findings) ? j.findings : [],
          loading: false,
          error: !r.ok,
        });
      } catch {
        if (!cancelled) setAttention((s) => ({ ...s, loading: false, error: true }));
      }
    };
    load();
    const id = setInterval(load, 60000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const findingCounts = React.useMemo(() => {
    const out = { stuck: 0, breakdown: 0, longWait: 0, total: 0 };
    for (const f of attention.findings) {
      out.total += 1;
      if (f.kind === "STUCK_IN_STATE") out.stuck += 1;
      if (f.kind === "BREAKDOWN_ACTIVE") out.breakdown += 1;
      if (f.kind === "LONG_WAIT") out.longWait += 1;
    }
    return out;
  }, [attention.findings]);

  const issueWork = (haulType) => {
    setCreateHaulType(haulType);
    setCreateOpen(true);
  };

  const logout = async () => {
    await clearAllSessions();
    nav("/dispatch-portal/login", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col" data-testid="dispatch-hub">
      <div className="caution-stripe" />

      {/* ── Top nav · ORIENTATION ONLY ─────────────────────────── */}
      <header className={`bg-slate-900 text-white border-b-4 ${DISPATCH_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-3 flex items-center gap-3">
          <Link
            to="/"
            className={`inline-flex items-center text-white ${DISPATCH_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="dispatch-nav-home"
            title="Public Hub"
          >
            <Home className="w-4 h-4 sm:mr-1" />
            <span className="hidden sm:inline">{t("Home")}</span>
          </Link>
          <button
            onClick={() => nav(-1)}
            className={`inline-flex items-center text-white ${DISPATCH_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="dispatch-nav-back"
            title="Back"
          >
            <ArrowLeft className="w-4 h-4 sm:mr-1" />
            <span className="hidden sm:inline">{t("Back")}</span>
          </button>
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <div className="flex-1 min-w-0">
            <div className={`font-mono text-[10px] uppercase tracking-[0.22em] ${DISPATCH_PAL.hubKickerStatic} font-bold`}>
              {t("Dispatch")}
            </div>
            <div className="font-display text-lg sm:text-xl font-black leading-tight truncate">
              {user.name || t("Dispatcher")}
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2">
            <PortalSwitcher current="dispatch" />
            <GlobalSearch accent="dark" />
          </div>
          <NotificationBell accent="white" />
          <OfflineIndicator />
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="bg-transparent text-white border-white/30 hover:bg-white/10"
            data-testid="dispatch-logout"
          >
            <LogOut className="w-3.5 h-3.5 sm:mr-1" />
            <span className="hidden sm:inline">{t("Sign out")}</span>
          </Button>
        </div>
      </header>

      <div className={sidebarV2 ? "max-w-7xl mx-auto flex w-full" : ""}>
        {sidebarV2 && (
          <DispatchSideNavV2 className="hidden lg:block w-64 flex-shrink-0 min-h-[calc(100vh-200px)]" />
        )}
        <main className={sidebarV2
          ? "flex-1 px-5 sm:px-8 py-4 space-y-4 w-full"
          : "max-w-6xl mx-auto px-5 sm:px-8 py-4 space-y-4 flex-1 w-full"}>

        {/* iter511 · MaintainX maintenance indicator (calm, count-only) */}
        <DispatchEquipmentMaintenanceIndicator />

        {/* ── 1 · OPERATIONAL ATTENTION · what matters now ───────── */}
        <Section
          testId="ds-section-attention"
          accent="rose"
          icon={AlertTriangle}
          kicker={t("Right now")}
          title={t("Operational Attention")}
          subtitle={t("Items most likely to slow work today.")}
          dense
        >
          {attention.loading ? (
            <div className="text-sm text-slate-500 py-1" data-testid="ds-attention-loading">
              {t("Reading signals…")}
            </div>
          ) : findingCounts.total === 0 ? (
            <div className="text-sm text-slate-500 italic py-1" data-testid="ds-attention-empty">
              {t("All hauls are flowing. Nothing requires dispatch attention right now.")}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" data-testid="ds-attention-cards">
              <AttentionCard
                testId="ds-attention-breakdown"
                icon={Wrench}
                tone="danger"
                count={findingCounts.breakdown}
                label={t("Trucks in breakdown")}
                hint={t("Shop sees these too. Decide reassign vs hold.")}
              />
              <AttentionCard
                testId="ds-attention-stuck"
                icon={Clock}
                tone="warn"
                count={findingCounts.stuck}
                label={t("Stuck > 30 min")}
                hint={t("Lifecycle stalled. Tap the row on the board for context.")}
              />
              <AttentionCard
                testId="ds-attention-longwait"
                icon={Clock}
                tone="warn"
                count={findingCounts.longWait}
                label={t("Extended wait")}
                hint={t("Driver waiting too long. Confirm the wait reason still applies.")}
              />
            </div>
          )}
          <div className="mt-3 flex items-center gap-4 flex-wrap">
            <Link
              to="/dispatch-portal/board"
              data-testid="ds-attention-open-board"
              className="inline-flex items-center text-xs font-bold uppercase tracking-wide text-orange-700 hover:text-orange-800"
            >
              {t("Open the operational board")} <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
            <HelpLink
              testId="ds-attention-help"
              to="/guidance/dls-operational-attention"
              label={t("What requires dispatch attention")}
            />
          </div>
        </Section>

        {/* ── 2 · ISSUE WORK · primary actions ───────────────────── */}
        <Section
          testId="ds-section-issue"
          accent="orange"
          icon={Send}
          kicker={t("Primary actions")}
          title={t("Issue Work")}
          subtitle={t("Create assignment once · downstream signals fan out automatically.")}
          dense
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2" data-testid="ds-issue-grid">
            <IssueButton
              testId="ds-issue-material"
              icon={Truck}
              title={t("Create Assignment")}
              sub={t("Material haul")}
              onClick={() => issueWork("Material")}
            />
            <IssueButton
              testId="ds-issue-equipment-move"
              icon={Wrench}
              title={t("Start Equipment Move")}
              sub={t("Lowboy / equipment haul")}
              onClick={() => issueWork("Equipment Move")}
            />
            <IssueButton
              testId="ds-issue-tanker"
              icon={Droplet}
              title={t("Tanker / Liquid Asphalt")}
              sub={t("Asphalt oil · binder · fuel")}
              onClick={() => issueWork("Tanker / Liquid Asphalt")}
            />
            <IssueButton
              testId="ds-issue-support"
              icon={Package}
              title={t("Support / Misc Haul")}
              sub={t("Spoils · support · misc")}
              onClick={() => issueWork("Support / Misc")}
            />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1">
            <HelpLink
              testId="ds-issue-help-issuance"
              to="/guidance/dls-assignment-issuance"
              label={t("How assignment issuance works")}
            />
            <HelpLink
              testId="ds-issue-help-haul-types"
              to="/guidance/dls-haul-types"
              label={t("How the 5 haul types flow")}
            />
          </div>
        </Section>

        {/* ── 3 · LIVE OPERATIONAL BOARD · deep link ─────────────── */}
        <Section
          testId="ds-section-live"
          accent="orange"
          icon={Activity}
          kicker={t("Watch movement")}
          title={t("Live Operational Board")}
          subtitle={t("Active assignments, waiting trucks, breakdowns, haul movement.")}
          dense
        >
          <Link
            to="/dispatch-portal/board"
            data-testid="dispatch-board-link"
            className="inline-flex items-center min-h-[48px] px-5 rounded-md bg-orange-600 hover:bg-orange-500 text-white font-black tracking-wide"
          >
            <Activity className="w-5 h-5 mr-2" />
            {t("Open Operational Board")}
          </Link>
        </Section>

        {/* ── 4 · FOLLOW-THROUGH · transfers + holds ─────────────── */}
        <Section
          testId="ds-section-follow"
          accent="amber"
          icon={ListChecks}
          kicker={t("Resolve before tomorrow")}
          title={t("Follow-Through")}
          subtitle={t("Decisions, handoffs, and corrections that stop tomorrow's problems.")}
          dense
        >
          <Tabs defaultValue="transfers" className="mt-1">
            <TabsList className="flex-wrap h-auto">
              <TabsTrigger value="transfers" data-testid="dh-tab-transfers">
                <Send className="w-3.5 h-3.5 mr-1" /> {t("Equipment moves")}
              </TabsTrigger>
              <TabsTrigger value="holds" data-testid="dh-tab-holds">
                <ShieldAlert className="w-3.5 h-3.5 mr-1" /> {t("Holds")}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="transfers"><DispatchTransfersTab /></TabsContent>
            <TabsContent value="holds"><DispatchHoldsTab /></TabsContent>
          </Tabs>
        </Section>

        {/* ── 5 · SECONDARY OPERATIONS ───────────────────────────── */}
        <Section
          testId="ds-section-secondary"
          accent="slate"
          icon={Truck}
          kicker={t("Secondary operations")}
          title={t("Fleet, utilization, and integrations")}
          subtitle={t("Lower-priority context. Open only when needed.")}
          dense
        >
          <Tabs defaultValue="overview" className="mt-1">
            <TabsList className="flex-wrap h-auto">
              <TabsTrigger value="overview" data-testid="dh-tab-overview">
                <Activity className="w-3.5 h-3.5 mr-1" /> {t("Overview")}
              </TabsTrigger>
              <TabsTrigger value="utilization" data-testid="dh-tab-utilization">
                <Activity className="w-3.5 h-3.5 mr-1" /> {t("What's moving vs sitting")}
              </TabsTrigger>
              <TabsTrigger value="idle" data-testid="dh-tab-idle">
                <Clock className="w-3.5 h-3.5 mr-1" /> {t("Trucks sitting too long")}
              </TabsTrigger>
              <TabsTrigger value="integrations" data-testid="dh-tab-integrations">
                <Plug className="w-3.5 h-3.5 mr-1" /> {t("Systems that validate operations")}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="overview"><DispatchOverviewTab /></TabsContent>
            <TabsContent value="utilization"><DispatchUtilizationTab /></TabsContent>
            <TabsContent value="idle"><DispatchIdleAlertsTab /></TabsContent>
            <TabsContent value="integrations"><DispatchIntegrationsTab /></TabsContent>
          </Tabs>

          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-100" data-testid="ds-secondary-links">
            <Link
              to="/dispatch-portal/fleet"
              className="inline-flex items-center min-h-[36px] px-3 rounded-md border border-slate-300 hover:border-orange-400 hover:bg-orange-50 text-sm font-bold text-slate-700"
              data-testid="dispatch-fleet-link"
            >
              <Truck className="w-4 h-4 mr-1.5" />
              {t("Fleet")}
            </Link>
            <Link
              to="/dispatch-portal/driver-qualification"
              className="inline-flex items-center min-h-[36px] px-3 rounded-md border border-slate-300 hover:border-orange-400 hover:bg-orange-50 text-sm font-bold text-slate-700"
              data-testid="dispatch-driver-qual-link"
            >
              <ShieldCheck className="w-4 h-4 mr-1.5" />
              {t("Approved drivers")}
            </Link>
            <Link
              to="/asset-transfers"
              className="inline-flex items-center min-h-[36px] px-3 rounded-md border border-slate-300 hover:border-orange-400 hover:bg-orange-50 text-sm font-bold text-slate-700"
              data-testid="dispatch-asset-transfers-link"
            >
              <Truck className="w-4 h-4 mr-1.5" />
              {t("Equipment moves (all-time)")}
            </Link>
          </div>
        </Section>

        {/* ── 6 · DISPATCH COMMAND · collapsed coaching + utility pill ─── */}
        {/* iter504 · OMEGA Dispatch Production Readiness Sprint:
            Coaching collapsed by default · Dispatch Resources converted from
            full operational panel to a compact inline guide button. */}
        <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center" data-testid="ds-utility-row">
          <div className="flex-1 min-w-0">
            <CoachingBlock
              collapsed={coachCollapsed}
              onToggle={() => setCoachCollapsed(!coachCollapsed)}
              t={t}
            />
          </div>
          <Link
            to="/guidance?from=dispatch"
            data-testid="dispatch-training-link"
            className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700 font-mono text-[11px] uppercase tracking-[0.18em] font-bold whitespace-nowrap"
            title={t("Open the operational guidance center")}
          >
            <BookOpen className="w-3.5 h-3.5" />
            {t("Guides")}
          </Link>
        </div>

        {/* ── 7 · CALM PERIPHERAL · below operational content ──── */}
        <div className="space-y-3 pt-2 border-t border-slate-200" data-testid="ds-peripheral">
          <PasskeyEnrollPrompt />
          <FieldMemoryGlance />
          <LastActivityLine portal="dispatch" />
        </div>
      </main>
      </div>

      {/* Local footer removed — GlobalFooter mounted in App.js renders the
          single, app-wide attribution strip on every route. */}

      <AssignmentCreateDrawer
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => setCreateOpen(false)}
        initialHaulType={createHaulType}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Section · platform-family contract (white card + colored left stripe)
// `dense` reduces padding from p-5 → p-4 for command-center density.
// ─────────────────────────────────────────────────────────────────────
function Section({ testId, accent = "slate", icon: Icon, kicker, title, subtitle, children, dense = false }) {
  const stripe =
    accent === "orange" ? "border-l-orange-500"
    : accent === "rose"   ? "border-l-rose-700"
    : accent === "amber"  ? "border-l-amber-600"
    : "border-l-slate-700";
  const kickerCls =
    accent === "orange" ? "text-orange-700"
    : accent === "rose"   ? "text-rose-700"
    : accent === "amber"  ? "text-amber-700"
    : "text-slate-600";
  const padding = dense ? "p-4" : "p-5";
  return (
    <section
      className={`bg-white border border-slate-200 border-l-4 ${stripe} rounded-md ${padding}`}
      data-testid={testId}
    >
      <div className="flex items-start gap-3">
        {Icon ? (
          <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-slate-900 text-white shrink-0">
            <Icon className="w-5 h-5" />
          </div>
        ) : null}
        <div className="flex-1 min-w-0">
          <div className={`font-mono text-[10px] uppercase tracking-[0.22em] ${kickerCls} font-bold`}>
            {kicker}
          </div>
          <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900 mt-0.5">
            {title}
          </h2>
          {subtitle ? (
            <p className="text-sm text-slate-600 mt-0.5 max-w-2xl">{subtitle}</p>
          ) : null}
        </div>
      </div>
      <div className="mt-3">{children}</div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────
// CoachingBlock · collapsible Dispatch Command coaching.
// iter504 · Collapsed-by-default · production-density.
// When collapsed: single compact line — "6 coaching tips available".
// When expanded: full Dispatch Command content.
// ─────────────────────────────────────────────────────────────────────
function CoachingBlock({ collapsed, onToggle, t }) {
  // Canonical bullet count — kept in sync with the <CoachLi> entries below.
  const TIP_COUNT = 6;
  if (collapsed) {
    return (
      <button
        type="button"
        onClick={onToggle}
        data-testid="ds-section-command"
        aria-expanded="false"
        className="w-full bg-white border border-slate-200 rounded-md px-4 py-2 flex items-center gap-3 hover:bg-slate-50 transition-colors"
      >
        <Compass className="w-4 h-4 text-slate-500 shrink-0" />
        <span
          className="flex-1 text-left font-mono text-[11px] uppercase tracking-[0.18em] text-slate-600"
          data-testid="ds-coaching-counter"
        >
          {TIP_COUNT} {t("coaching tips available · tap to expand")}
        </span>
        <ChevronDown className="w-4 h-4 text-slate-400" data-testid="ds-coaching-icon-down" />
      </button>
    );
  }
  return (
    <section
      className="bg-white border border-slate-200 border-l-4 border-l-slate-400 rounded-md p-4"
      data-testid="ds-section-command"
    >
      <button
        type="button"
        onClick={onToggle}
        data-testid="ds-coaching-toggle"
        className="w-full flex items-center gap-3 text-left"
        aria-expanded="true"
      >
        <div className="inline-flex items-center justify-center w-9 h-9 rounded-md bg-slate-900 text-white shrink-0">
          <Compass className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-600 font-bold">
            {t("Need help?")}
          </div>
          <div className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900 mt-0.5">
            {t("Dispatch Command")}
          </div>
        </div>
        <ChevronUp className="w-5 h-5 text-slate-500" data-testid="ds-coaching-icon-up" />
      </button>
      <div className="mt-3" data-testid="ds-coaching-body">
        <p className="text-sm text-slate-600 mb-2 max-w-2xl">
          {t("Issue work, watch movement, resolve delays, and keep trucks flowing.")}
        </p>
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-4 gap-y-1.5 text-sm text-slate-700">
          <CoachLi>{t("Start with anything needing attention.")}</CoachLi>
          <CoachLi>{t("Issue assignments before reviewing history.")}</CoachLi>
          <CoachLi>{t("Driver taps are the source of operational truth.")}</CoachLi>
          <CoachLi>{t("PMs see production awareness only.")}</CoachLi>
          <CoachLi>{t("Shop sees breakdown continuity only.")}</CoachLi>
          <CoachLi>{t("Motive validates later — it does not replace the driver.")}</CoachLi>
        </ul>
      </div>
    </section>
  );
}

function CoachLi({ children }) {
  return (
    <li className="flex items-start gap-2 text-sm text-slate-700">
      <span className="text-orange-600 font-bold leading-none mt-0.5">·</span>
      <span>{children}</span>
    </li>
  );
}

function AttentionCard({ testId, icon: Icon, tone = "calm", count = 0, label, hint }) {
  const isLive = (count || 0) > 0;
  const wrap = isLive
    ? (tone === "danger" ? "border-rose-300 bg-rose-50" : "border-amber-300 bg-amber-50")
    : "border-slate-200 bg-white";
  const num = isLive
    ? (tone === "danger" ? "text-rose-700" : "text-amber-700")
    : "text-slate-400";
  return (
    <div
      data-testid={testId}
      className={`border ${wrap} rounded-md p-3 flex flex-col gap-1 ${isLive ? "ring-1 ring-inset" : ""} ${isLive && tone === "danger" ? "ring-rose-200" : ""} ${isLive && tone !== "danger" ? "ring-amber-200" : ""}`}
    >
      <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-slate-600 font-bold">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <div className={`font-display text-3xl font-black leading-none ${num}`}>
        {count}
      </div>
      <div className="text-[11px] text-slate-500 leading-tight">{hint}</div>
    </div>
  );
}

function IssueButton({ testId, icon: Icon, title, sub, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      className="min-h-[76px] rounded-md border-2 border-slate-200 hover:border-orange-400 hover:bg-orange-50 bg-white p-3 text-left flex items-start gap-3 transition-all"
    >
      <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-orange-600 text-white shrink-0">
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-display text-sm font-black text-slate-900 leading-tight break-words hyphens-auto">{title}</div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500 mt-0.5 break-words">{sub}</div>
      </div>
    </button>
  );
}

/**
 * HelpLink · iter414 · Phase 18.1 · in-flow operational coaching.
 *
 * Calm, slate, low-visual-weight link to the Operational Guidance Center
 * article for the surrounding operational area.
 */
function HelpLink({ testId, to, label }) {
  return (
    <Link
      to={to}
      data-testid={testId}
      className="inline-flex items-center text-xs text-slate-500 hover:text-slate-800 underline decoration-slate-300 hover:decoration-slate-600 underline-offset-2"
    >
      {label}
      <ArrowRight className="w-3 h-3 ml-1 opacity-70" />
    </Link>
  );
}
