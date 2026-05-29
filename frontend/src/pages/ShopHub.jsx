/**
 * ShopHub.jsx · iter423 · Phase 25 · Shop Operational Cognition Convergence
 * ─────────────────────────────────────────────────────────────────────────
 * The Shop Portal is NOT maintenance software.
 * The Shop Portal IS  operational recovery continuity.
 *
 * Information architecture (replaces the prior 7-tab ERP layout):
 *   1. Equipment Needing Attention      (FAIL DVIR + BREAKDOWN lifecycle)
 *   2. Active Recovery Work             (iter420 sub-state: acknowledged →
 *                                        diagnosing → repair_active →
 *                                        operational_test)
 *   3. Waiting / Delays                 (recovery_state = waiting_on_parts)
 *   4. Returned to Service              (last 7 days · read-only tail)
 *   5. Operational Continuity History   (iter419 dispatch_continuity_events ·
 *                                        read-only chronology · NOT activity)
 *
 * Demoted to a calm "More" footer (still reachable · never first-screen):
 *   Trends · Recent inspections · Activity · Equipment list · Parts ·
 *   Integrations · MASCI Fleet view
 *
 * Doctrine guards locked:
 *   • NO charts · NO scoring · NO KPIs · NO utilization
 *   • Read-only sections except where iter420 already authorised writes
 *   • Coaching pause-points are single-line · calm · embedded
 *   • Mobile-first 390px vertical rhythm · 44px touch targets
 *   • Wording: operational recovery (NOT fleet repair queue)
 */
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Wrench, LogOut, KeyRound, BookOpen, ChevronRight,
  AlertOctagon, CheckCircle2, Clock, Stethoscope, PackageOpen,
  Cog, ClipboardList, History, Loader2, Truck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import OpenItemsPanel from "@/components/OpenItemsPanel";
import DispatchLifecycleTile from "@/components/dispatch/DispatchLifecycleTile";
import { RecoveryActionRow } from "@/components/shop/RecoveryActionRow";
import { LangToggle } from "@/components/LangToggle";
import PortalSwitcher from "@/components/PortalSwitcher";
import NotificationBell from "@/components/NotificationBell";
import GlobalSearch from "@/components/GlobalSearch";
import { OfflineIndicator } from "@/lib/resiliency";
import { api } from "@/lib/api";
import { clearAllSessions } from "@/lib/sessionReset";
import { useT } from "@/lib/i18n";
import { paletteFor } from "@/lib/portalPalette";
import { usePageTitle } from "@/lib/usePageTitle";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";
import { FieldMemoryGlance } from "@/components/field_memory/FieldMemoryGlance";
import LastActivityLine from "@/components/admin/LastActivityLine";

const SHOP_PAL = paletteFor("shop");

// ────────────────────────────────────────────────────────────────────
// Small calm helpers
// ────────────────────────────────────────────────────────────────────
function relTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  } catch {
    return "";
  }
}

const SectionHeader = ({ icon: Icon, kicker, title, count, coaching, testIdRoot }) => {
  const { t } = useT();
  return (
    <div className="mb-3" data-testid={`${testIdRoot}-header`}>
      <div className="flex items-baseline gap-3">
        <div className="shrink-0 w-9 h-9 rounded-md bg-slate-900 text-amber-400 flex items-center justify-center">
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-700 font-bold">
            {t(kicker)}
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-tight">
            {t(title)}
            {typeof count === "number" ? (
              <span className="ml-2 inline-flex items-center justify-center min-w-[1.75rem] h-6 px-2 rounded-full bg-slate-100 text-slate-700 font-mono text-xs font-bold align-middle">
                {count}
              </span>
            ) : null}
          </h2>
        </div>
      </div>
      {coaching ? (
        <p className="mt-2 ml-12 text-xs text-slate-500 italic max-w-2xl leading-snug" data-testid={`${testIdRoot}-coaching`}>
          {t(coaching)}
        </p>
      ) : null}
    </div>
  );
};

const RecoveryCard = ({ row, stateLabel, testIdRoot, onUpdated, enableActions = true }) => {
  const { t } = useT();
  const impact = useMemo(() => {
    // Tiny secondary operational-impact line · field-driven phrasing.
    const parts = [];
    if (row.truck_id) parts.push(`${t("Truck")} ${row.truck_id}`);
    if (row.driver_name) parts.push(`${t("Driver")}: ${row.driver_name}`);
    if (row.project_number) parts.push(`#${row.project_number}`);
    return parts.join(" · ");
  }, [row, t]);
  return (
    <li
      className="bg-white border border-slate-200 border-l-4 border-l-amber-500 rounded-md p-4 hover:border-slate-300 transition-colors"
      data-testid={`${testIdRoot}-card-${row.assignment_id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="font-display text-base font-black text-slate-900 truncate">
            {row.truck_id || t("Equipment")} <span className="text-slate-400">·</span> {row.material || row.current_state || ""}
          </div>
          {impact ? (
            <div className="mt-1 text-xs text-slate-600 truncate" data-testid={`${testIdRoot}-impact-${row.assignment_id}`}>
              {impact}
            </div>
          ) : null}
          {row.last_recovery_note ? (
            <div className="mt-2 text-xs text-slate-700 italic line-clamp-2">
              “{row.last_recovery_note}”
            </div>
          ) : null}
        </div>
        <div className="shrink-0 text-right">
          <span className="inline-flex items-center px-2 py-1 rounded bg-slate-100 text-slate-700 font-mono text-[10px] uppercase tracking-wider font-bold">
            {stateLabel}
          </span>
          <div className="mt-1 font-mono text-[10px] uppercase tracking-wider text-slate-500">
            {relTime(row.last_recovery_at) || ""}
          </div>
        </div>
      </div>
      {enableActions ? (
        <RecoveryActionRow
          assignmentId={row.assignment_id}
          currentState={row.recovery_state}
          onSaved={onUpdated}
          testIdPrefix={`${testIdRoot}-action-${row.assignment_id}`}
        />
      ) : null}
    </li>
  );
};

const EmptyHint = ({ children, testId }) => (
  <div className="text-sm text-slate-500 italic py-3 px-4 bg-slate-50 border border-dashed border-slate-200 rounded-md" data-testid={testId}>
    {children}
  </div>
);

// ────────────────────────────────────────────────────────────────────
// ShopHub · main component
// ────────────────────────────────────────────────────────────────────
export default function ShopHub() {
  usePageTitle("Shop Recovery · MASCI");
  const { t } = useT();
  const navigate = useNavigate();
  const [me, setMe] = useState(null);
  const [recovery, setRecovery] = useState({
    buckets: { reported: [], acknowledged: [], diagnosing: [], waiting_on_parts: [], repair_active: [], operational_test: [] },
    restored_recent: [],
    summary: { total_active: 0, waiting_on_parts: 0, returned_today: 0 },
  });
  const [recoveryLoading, setRecoveryLoading] = useState(true);
  const [showMore, setShowMore] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/shop/me");
        if (!alive) return;
        if (r.data?.user?.id) setMe(r.data.user);
      } catch { /* hidden */ }
    })();
    return () => { alive = false; };
  }, []);

  const loadRecovery = async () => {
    setRecoveryLoading(true);
    try {
      const r = await api.get("/dispatch/recovery/by-shop");
      setRecovery(r.data || recovery);
    } catch {
      // Non-fatal — empty buckets retain calm shape
    } finally {
      setRecoveryLoading(false);
    }
  };
  useEffect(() => { loadRecovery(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const onLogout = async () => {
    await clearAllSessions();
    navigate("/");
  };

  const activeBuckets = {
    acknowledged: recovery.buckets.acknowledged || [],
    diagnosing: recovery.buckets.diagnosing || [],
    repair_active: recovery.buckets.repair_active || [],
    operational_test: recovery.buckets.operational_test || [],
  };
  const activeTotal =
    activeBuckets.acknowledged.length + activeBuckets.diagnosing.length +
    activeBuckets.repair_active.length + activeBuckets.operational_test.length;
  const waiting = recovery.buckets.waiting_on_parts || [];
  const restored = recovery.restored_recent || [];

  // Calm one-line status strip · operational language only · NO KPIs.
  const statusLine = useMemo(() => {
    const parts = [];
    if (activeTotal > 0) {
      parts.push(t("{n} pieces of equipment currently in operational recovery.").replace("{n}", activeTotal));
    }
    if (waiting.length > 0) {
      parts.push(t("{n} operational interruption waiting on parts.").replace("{n}", waiting.length));
    }
    if (recovery.summary.returned_today > 0) {
      parts.push(t("{n} pieces of equipment returned to service today.").replace("{n}", recovery.summary.returned_today));
    }
    if (parts.length === 0) {
      return t("No equipment in operational recovery right now.");
    }
    return parts.join("  ");
  }, [activeTotal, waiting.length, recovery.summary.returned_today, t]);

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className={`bg-slate-900 border-b-4 ${SHOP_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link to="/" className={`inline-flex items-center text-white ${SHOP_PAL.hubLinkHover} text-sm font-bold uppercase tracking-wide`} data-testid="shop-nav-home">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex items-center gap-1 sm:gap-2">
            <div className="hidden sm:flex items-center gap-2">
              <PortalSwitcher current="shop" />
              <GlobalSearch accent="dark" />
            </div>
            <NotificationBell accent="white" />
            <OfflineIndicator />
            <LangToggle />
            <Link
              to="/guidance?from=shop"
              className="hidden sm:inline-flex items-center h-10 px-3 rounded-md border-2 border-amber-400 text-amber-400 hover:bg-amber-500 hover:text-white bg-transparent font-bold uppercase tracking-wide text-xs"
              data-testid="shop-training-link"
            >
              <BookOpen className="w-4 h-4 sm:mr-1" />
              <span className="hidden sm:inline">{t("Guides")}</span>
            </Link>
            {me ? (
              <Button
                onClick={() => navigate("/shop/change-password")}
                variant="outline"
                className="h-10 px-3 border-2 border-amber-400 text-amber-400 hover:bg-amber-500 hover:text-white bg-transparent font-bold uppercase tracking-wide text-xs hidden sm:inline-flex"
                title={`Signed in as ${me.email}`}
                data-testid="shop-change-pw-link"
              >
                <KeyRound className="w-4 h-4 mr-1" /> {t("Change password")}
              </Button>
            ) : null}
            <Button
              onClick={onLogout}
              variant="outline"
              className="h-10 px-2 sm:px-3 border-2 border-amber-400 text-amber-400 hover:bg-amber-500 hover:text-white bg-transparent font-bold uppercase tracking-wide text-xs"
              data-testid="shop-logout-btn"
              title="Sign out"
            >
              <LogOut className="w-4 h-4 sm:mr-1" /> <span className="hidden sm:inline">{t("Sign out")}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 space-y-10">
        {/* iter429 · Phase 28 · Optional device sign-in enrollment ·
            self-gated · dismissible · single-card · NEVER nags */}
        <PasskeyEnrollPrompt />

        {/* iter432 · Phase 30 · Part 6 · Option iii · ONE calm additive
            operational-attention surface — read-only Field Memory glance. */}
        <FieldMemoryGlance />

        {/* iter440 · calm one-line "Last activity" trace per portal ·
            quiet proof the platform is being USED, not just UP. */}
        <LastActivityLine portal="shop" />

        {/* Calm operational kicker · iter423 wording: recovery, not maintenance */}
        <div>
          <span className={`font-mono text-xs uppercase tracking-[0.22em] ${SHOP_PAL.hubKicker} font-bold`}>
            {t("Shop Console")}
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("Shop Recovery")}
          </h1>
          <p className="text-slate-600 text-base mt-2 max-w-2xl" data-testid="shop-status-line">
            {recoveryLoading ? (
              <span className="inline-flex items-center text-slate-400"><Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Loading operational recovery…")}</span>
            ) : statusLine}
          </p>
        </div>

        {/* ═════════ 1 · EQUIPMENT NEEDING ATTENTION ════════════════════ */}
        <section data-testid="shop-section-attention">
          <SectionHeader
            icon={AlertOctagon}
            kicker="Operational Recovery"
            title="Equipment Needing Attention"
            coaching="Operational interruptions that need Shop awareness right now. Sign off when the unit is back in field service."
            testIdRoot="shop-attention"
          />
          <div className="space-y-4">
            <DispatchLifecycleTile scope="shop" testId="shop-dispatch-lifecycle" />
            <OpenItemsPanel baseHref="/shop/equipment" testIdPrefix="shop-open" />
          </div>
        </section>

        {/* ═════════ 2 · ACTIVE RECOVERY WORK ═══════════════════════════ */}
        <section data-testid="shop-section-active">
          <SectionHeader
            icon={Cog}
            kicker="Operational Recovery"
            title="Active Recovery Work"
            count={activeTotal}
            coaching="Active recovery work means equipment is being restored to field service."
            testIdRoot="shop-active"
          />
          {recoveryLoading ? (
            <div className="text-sm text-slate-500 py-4"><Loader2 className="w-4 h-4 animate-spin inline mr-2" /> {t("Loading…")}</div>
          ) : activeTotal === 0 ? (
            <EmptyHint testId="shop-active-empty">
              {t("No active recovery work right now. Equipment is in field service or waiting on parts.")}
            </EmptyHint>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <ActiveBucket label={t("Acknowledged")} icon={CheckCircle2} rows={activeBuckets.acknowledged} testIdRoot="shop-active-acknowledged" onUpdated={loadRecovery} />
              <ActiveBucket label={t("Diagnosing")} icon={Stethoscope} rows={activeBuckets.diagnosing} testIdRoot="shop-active-diagnosing" onUpdated={loadRecovery} />
              <ActiveBucket label={t("Repair Active")} icon={Wrench} rows={activeBuckets.repair_active} testIdRoot="shop-active-repair_active" onUpdated={loadRecovery} />
              <ActiveBucket label={t("Operational Test")} icon={ClipboardList} rows={activeBuckets.operational_test} testIdRoot="shop-active-operational_test" onUpdated={loadRecovery} />
            </div>
          )}
        </section>

        {/* ═════════ 3 · WAITING / DELAYS ═══════════════════════════════ */}
        <section data-testid="shop-section-waiting">
          <SectionHeader
            icon={PackageOpen}
            kicker="Operational Recovery"
            title="Waiting / Delays"
            count={waiting.length}
            coaching="Waiting on parts pauses operational recovery until components arrive."
            testIdRoot="shop-waiting"
          />
          {recoveryLoading ? (
            <div className="text-sm text-slate-500 py-4"><Loader2 className="w-4 h-4 animate-spin inline mr-2" /> {t("Loading…")}</div>
          ) : waiting.length === 0 ? (
            <EmptyHint testId="shop-waiting-empty">
              {t("No equipment is currently held by an operational interruption.")}
            </EmptyHint>
          ) : (
            <ul className="space-y-2" data-testid="shop-waiting-list">
              {waiting.map((row) => (
                <RecoveryCard key={row.assignment_id} row={row} stateLabel={t("Waiting on parts")} testIdRoot="shop-waiting" onUpdated={loadRecovery} />
              ))}
            </ul>
          )}
        </section>

        {/* ═════════ 4 · RETURNED TO SERVICE ════════════════════════════ */}
        <section data-testid="shop-section-restored">
          <SectionHeader
            icon={CheckCircle2}
            kicker="Operational Recovery"
            title="Returned to Service"
            count={restored.length}
            coaching="Returned to service means the equipment is operationally ready for field continuity again."
            testIdRoot="shop-restored"
          />
          {recoveryLoading ? (
            <div className="text-sm text-slate-500 py-4"><Loader2 className="w-4 h-4 animate-spin inline mr-2" /> {t("Loading…")}</div>
          ) : restored.length === 0 ? (
            <EmptyHint testId="shop-restored-empty">
              {t("No equipment has been returned to service in the last 7 days.")}
            </EmptyHint>
          ) : (
            <ul className="space-y-2" data-testid="shop-restored-list">
              {restored.map((row) => (
                <li
                  key={row.assignment_id}
                  className="bg-white border border-slate-200 border-l-4 border-l-emerald-500 rounded-md p-4"
                  data-testid={`shop-restored-card-${row.assignment_id}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="font-display text-base font-black text-slate-900 truncate">
                        {row.truck_id || t("Equipment")}
                        {row.project_number ? <span className="text-slate-400 font-normal"> · #{row.project_number}</span> : null}
                      </div>
                      <div className="mt-0.5 text-xs text-emerald-700 font-bold uppercase tracking-wider">
                        ✓ {t("Operational continuity restored.")}
                      </div>
                      {row.note ? (
                        <div className="mt-2 text-xs text-slate-700 italic line-clamp-2">“{row.note}”</div>
                      ) : null}
                    </div>
                    <div className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-slate-500 text-right">
                      {relTime(row.returned_at)}
                      {row.returned_by ? <div className="mt-0.5">{row.returned_by}</div> : null}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ═════════ 5 · OPERATIONAL CONTINUITY HISTORY ═════════════════ */}
        <OperationalContinuityHistory />

        {/* ═════════ MORE · demoted secondary surfaces ══════════════════ */}
        <section data-testid="shop-section-more">
          <button
            type="button"
            onClick={() => setShowMore((v) => !v)}
            className="inline-flex items-center text-xs font-mono uppercase tracking-[0.22em] font-bold text-slate-500 hover:text-slate-800"
            data-testid="shop-more-toggle"
          >
            <ChevronRight className={`w-4 h-4 mr-1 transition-transform ${showMore ? "rotate-90" : ""}`} />
            {t("More")} · {t("Trends · Equipment · Parts · Integrations · Activity")}
          </button>
          {showMore ? (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4" data-testid="shop-more-grid">
              <MoreLink to="/shop/fleet" icon={Truck} label="MASCI Fleet · DVIR queue" testId="shop-more-fleet" />
              <MoreLink to="?legacy=recent" icon={ClipboardList} label="Recent Pre-Op Inspections" testId="shop-more-recent" disabled />
              <MoreLink to="?legacy=trends" icon={History} label="Equipment Trends" testId="shop-more-trends" disabled />
              <MoreLink to="?legacy=activity" icon={Clock} label="Shop Activity" testId="shop-more-activity" disabled />
              <MoreLink to="?legacy=equipment" icon={Truck} label="Equipment List" testId="shop-more-equipment" disabled />
              <MoreLink to="?legacy=parts" icon={Wrench} label="Parts Catalog" testId="shop-more-parts" disabled />
            </div>
          ) : null}
          <p className="mt-2 text-[11px] text-slate-400 italic max-w-xl">
            {t("These views remain accessible but stay out of first-screen cognition.")}
          </p>
        </section>
      </main>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────
// Sub-components
// ────────────────────────────────────────────────────────────────────
const ActiveBucket = ({ label, icon: Icon, rows, testIdRoot, onUpdated }) => {
  const { t } = useT();
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3" data-testid={`${testIdRoot}-bucket`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-amber-700" />
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
          {label}
        </span>
        <span className="ml-auto inline-flex items-center justify-center min-w-[1.5rem] h-5 px-2 rounded bg-slate-100 text-slate-700 font-mono text-[10px] font-bold">
          {rows.length}
        </span>
      </div>
      {rows.length === 0 ? (
        <div className="text-xs text-slate-400 italic px-1 py-2">{t("None.")}</div>
      ) : (
        <ul className="space-y-2" data-testid={`${testIdRoot}-list`}>
          {rows.map((row) => (
            <RecoveryCard key={row.assignment_id} row={row} stateLabel={label} testIdRoot={testIdRoot} onUpdated={onUpdated} />
          ))}
        </ul>
      )}
    </div>
  );
};

const MoreLink = ({ to, icon: Icon, label, testId, disabled }) => {
  const { t } = useT();
  const className = "inline-flex items-center gap-2 px-3 py-2 rounded-md border border-slate-200 bg-white text-sm text-slate-700 hover:border-slate-300 hover:text-slate-900";
  if (disabled) {
    return (
      <span className={`${className} opacity-60 cursor-not-allowed`} data-testid={testId} title={t("Reachable via direct URL · kept out of first-screen cognition")}>
        <Icon className="w-4 h-4" /> {t(label)}
      </span>
    );
  }
  return (
    <Link to={to} className={className} data-testid={testId}>
      <Icon className="w-4 h-4" /> {t(label)}
    </Link>
  );
};

// ────────────────────────────────────────────────────────────────────
// Operational Continuity History · read-only chronology (iter419 events)
// ────────────────────────────────────────────────────────────────────
const OperationalContinuityHistory = () => {
  const { t } = useT();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        // Pull recent continuity events platform-wide (no per-assignment filter).
        // Endpoint hits the existing /by-assignment list pattern via a tiny
        // wrapper — until that ships we render an empty calm hint, NOT an error.
        const r = await api.get("/dispatch/continuity-events/recent").catch(() => null);
        if (!alive) return;
        if (r && Array.isArray(r.data?.events)) {
          setEvents(r.data.events);
        } else {
          setEvents([]);
        }
      } catch {
        if (alive) setError(true);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  return (
    <section data-testid="shop-section-history">
      <SectionHeader
        icon={History}
        kicker="Operational Recovery"
        title="Operational Continuity History"
        coaching="Operational chronology · breakdown continuity, reassignments, and recovery moments across the platform."
        testIdRoot="shop-history"
      />
      {loading ? (
        <div className="text-sm text-slate-500 py-4"><Loader2 className="w-4 h-4 animate-spin inline mr-2" /> {t("Loading…")}</div>
      ) : error || events.length === 0 ? (
        <EmptyHint testId="shop-history-empty">
          {t("No operational continuity events recorded yet. Recent breakdowns, reassignments, and recovery moments will appear here as they happen.")}
        </EmptyHint>
      ) : (
        <ul className="space-y-2" data-testid="shop-history-list">
          {events.slice(0, 25).map((e) => (
            <li
              key={e.id}
              className="bg-white border border-slate-200 border-l-4 border-l-slate-400 rounded-md p-3"
              data-testid={`shop-history-event-${e.id}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">
                    {t(e.kind || "Event")}
                  </div>
                  {e.narrative ? (
                    <div className="mt-1 text-sm text-slate-800 line-clamp-2">{e.narrative}</div>
                  ) : null}
                  <div className="mt-1 text-[11px] text-slate-500">
                    {e.captured_by || ""} {e.captured_role ? `· ${e.captured_role}` : ""}
                  </div>
                </div>
                <div className="shrink-0 font-mono text-[10px] uppercase tracking-wider text-slate-500">
                  {relTime(e.created_at)}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};
