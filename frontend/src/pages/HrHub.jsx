// HR Portal — main hub. 4 tiles: Field Leadership Records ·
// Employee Accountability · Time Verification · Training Records.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Users, Search, Clock, GraduationCap, LogOut, ShieldCheck, Calculator, CalendarOff, KeyRound, Home, ArrowLeft, BookOpen, Receipt, Truck, ClipboardList } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import PortalSwitcher from "@/components/PortalSwitcher";
import NotificationBell from "@/components/NotificationBell";
import GlobalSearch from "@/components/GlobalSearch";
import { OfflineIndicator } from "@/lib/resiliency";
import IntegrationHealthCard from "@/components/IntegrationHealthCard";
import IntegrationEventsCard from "@/components/IntegrationEventsCard";
import OperationsCenter from "@/components/OperationsCenter";
import { useT } from "@/lib/i18n";
import { clearHrToken, getHrUser, getHrToken } from "@/lib/hrAuth";
import { usePageTitle } from "@/lib/usePageTitle";
import { clearAllSessions } from "@/lib/sessionReset";
import { paletteFor } from "@/lib/portalPalette";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";

const HR_PAL = paletteFor("hr");

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// iter437 P1B · HR Calmness Tuning — 2026-02-27
//
// Tile palette consolidated from 9 hues to 5 (matching the 5-domain
// V2 sidebar map in `HR_INFORMATION_PRIORITY_MAP.json`). Every tile
// subline trimmed to ≤14 words sentence case, period-terminated, per
// `CROSS_PORTAL_COACHING_STANDARD.md §V`. Per-tile CTA buttons
// normalised to a single neutral slate-800 across the board — identity
// is carried by the left-edge stripe, not by the button.
//
// The 5-stripe / 5-domain map:
//   green-600  → People Operations
//   sky-600    → Time & Payroll
//   violet-600 → Compliance & Records
//   amber-700  → Access & Identity
//   slate-600  → Guidance
const TILE_DEFS = {
  // ── People Operations (green-600) ────────────────────────────
  employees: { to: "/hr/employees", icon: Users, label: "Employee Lifecycle",
    desc: "Add, status, offboarding, termination playbook.",
    stripe: "border-l-green-600", btn: "bg-slate-800 hover:bg-slate-900" },
  tasks: { to: "/tasks", icon: GraduationCap, label: "Tasks & Actions",
    desc: "Cross-portal accountability and follow-ups.",
    stripe: "border-l-green-600", btn: "bg-slate-800 hover:bg-slate-900" },
  accountability: { to: "/hr/employee-accountability", icon: Search, label: "Employee Accountability",
    desc: "Per-employee records, equipment, clearance.",
    stripe: "border-l-green-600", btn: "bg-slate-800 hover:bg-slate-900" },
  flRecords: { to: "/hr/field-leadership", icon: Users, label: "Field Leadership Records",
    desc: "Crew docs, coaching, recognition, evaluations.",
    stripe: "border-l-green-600", btn: "bg-slate-800 hover:bg-slate-900" },

  // ── Time & Payroll (sky-600) ─────────────────────────────────
  timeVerification: { to: "/hr/time-verification", icon: Clock, label: "Time Verification",
    desc: "Daily report labor and payroll cross-check.",
    stripe: "border-l-sky-600", btn: "bg-slate-800 hover:bg-slate-900" },
  payrollVariance: { to: "/hr/payroll-variance", icon: Calculator, label: "Payroll Variance",
    desc: "Reconcile Exact CSV against MASCI hours.",
    stripe: "border-l-sky-600", btn: "bg-slate-800 hover:bg-slate-900" },
  timeOff: { to: "/hr/time-off", icon: CalendarOff, label: "Time Off Requests",
    desc: "Vacation, sick, medical, bereavement approvals.",
    stripe: "border-l-sky-600", btn: "bg-slate-800 hover:bg-slate-900",
    badgeKey: "pending" },
  poRequests: { to: "/po-requests", icon: Receipt, label: "PO Requests & Receipts",
    desc: "Pending approvals, receipts, employee-linked spend.",
    stripe: "border-l-sky-600", btn: "bg-slate-800 hover:bg-slate-900" },

  // ── Compliance & Records (violet-600) ───────────────────────
  docExpirations: { to: "/document-expirations", icon: GraduationCap, label: "Document Expirations",
    desc: "OSHA, TWIC, CDL, training cert windows.",
    stripe: "border-l-violet-600", btn: "bg-slate-800 hover:bg-slate-900" },
  trainingRecords: { to: "/hr/training-records", icon: GraduationCap, label: "Training Records",
    desc: "Completed tracks and certification roster.",
    stripe: "border-l-violet-600", btn: "bg-slate-800 hover:bg-slate-900" },
  driverQual: { to: "/hr/driver-qualification", icon: Truck, label: "Driver Qualification",
    desc: "CDL holders, endorsements, tanker capability.",
    stripe: "border-l-violet-600", btn: "bg-slate-800 hover:bg-slate-900" },
  safetyRecords: { to: "/hr/safety-records", icon: ShieldCheck, label: "Safety Records",
    desc: "Read-only Safety library and per-employee training.",
    stripe: "border-l-violet-600", btn: "bg-slate-800 hover:bg-slate-900" },
  dailyReports: { to: "/hr/daily-reports", icon: ClipboardList, label: "Daily Reports Review",
    desc: "Read-only payroll cross-check context.",
    stripe: "border-l-violet-600", btn: "bg-slate-800 hover:bg-slate-900" },

  // ── Access & Identity (amber-700) ───────────────────────────
  flUsers: { to: "/hr/field-leadership-users", icon: KeyRound, label: "Field Leadership Portal Accounts",
    desc: "Issue, reset, deactivate Field Leadership logins.",
    stripe: "border-l-amber-700", btn: "bg-slate-800 hover:bg-slate-900" },

  // ── Guidance (slate-600) ────────────────────────────────────
  guidance: { to: "/guidance?from=hr", icon: BookOpen, label: "Training Center & Guides",
    desc: "Step-by-step HR operator guides.",
    stripe: "border-l-slate-600", btn: "bg-slate-800 hover:bg-slate-900" },
};

// iter437 P1B · Tile groups now mirror the 5-domain V2 sidebar map.
// `HR_INFORMATION_PRIORITY_MAP.json` is the canonical reference.
const TILE_GROUPS = [
  {
    key: "people-operations",
    heading: "People Operations",
    sub: "Day-to-day employee lifecycle and field accountability.",
    tiles: ["employees", "tasks", "accountability", "flRecords"],
  },
  {
    key: "time-payroll",
    heading: "Time & Payroll",
    sub: "Time verification, payroll variance, expense visibility.",
    tiles: ["timeVerification", "payrollVariance", "timeOff", "poRequests"],
  },
  {
    key: "compliance-records",
    heading: "Compliance & Records",
    sub: "Certifications, driver qualification, safety overlap.",
    tiles: ["docExpirations", "trainingRecords", "driverQual", "safetyRecords", "dailyReports"],
  },
  {
    key: "access-identity",
    heading: "Access & Identity",
    sub: "Field leadership accounts and sign-in management.",
    tiles: ["flUsers"],
  },
  {
    key: "guidance",
    heading: "Guidance",
    sub: "Operator guides and supporting documentation.",
    tiles: ["guidance"],
    muted: true,
  },
];

// Flat list for any consumer that still expects all tiles (regression
// safety net — preserves iter285+ test discoverability semantics if
// anything imports HrHub internals).
const TILES = TILE_GROUPS.flatMap((g) => g.tiles.map((k) => TILE_DEFS[k]));

export default function HrHub() {
  usePageTitle("HR · MASCI");
  const { t } = useT();
  const nav = useNavigate();
  const user = getHrUser();
  const [stats, setStats] = React.useState({});

  React.useEffect(() => {
    (async () => {
      try {
        const tok = getHrToken();
        if (!tok) return;
        const r = await fetch(`${API}/field-leadership/time-off/stats`, {
          headers: { "X-HR-Token": tok },
        });
        if (r.ok) setStats(await r.json());
      } catch (e) { /* silent */ }
    })();
  }, []);

  const signOut = async () => {
    // P0 (iter179): wipe every auth artifact, not just HR.
    await clearAllSessions();
    nav("/hr/login");
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className={`bg-slate-900 border-b-4 ${HR_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link to="/" className={`inline-flex items-center text-white ${HR_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`} data-testid="hr-nav-home" title="Home">
            <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
          </Link>
          <button onClick={() => nav(-1)} className={`inline-flex items-center text-white ${HR_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`} data-testid="hr-nav-back" title="Back">
            <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Back</span>
          </button>
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex-1" />
          {/* iter203 — Mobile header collapse */}
          <div className="flex items-center gap-1 sm:gap-2">
            <div className="hidden sm:flex items-center gap-2">
              <PortalSwitcher current="hr" />
              <GlobalSearch accent="dark" />
            </div>
            <NotificationBell accent="white" />
            <OfflineIndicator />
            <LangToggle />
            <div className="hidden sm:flex"><CompanyInfoDialog /></div>
            <Button variant="outline" size="sm" onClick={() => nav("/hr/change-password")} className="hidden sm:inline-flex text-xs bg-transparent text-white border-white/30 hover:bg-white/10" data-testid="hr-change-password">
              <KeyRound className="w-3.5 h-3.5 sm:mr-1" /><span className="hidden sm:inline">{t("Password")}</span>
            </Button>
            <Button variant="outline" size="sm" onClick={signOut} className="text-xs h-8 px-2 sm:px-2.5" data-testid="hr-sign-out" title="Sign out">
              <LogOut className="w-3.5 h-3.5 sm:mr-1" /><span className="hidden sm:inline">{t("Sign out")}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8">
        <div className={`font-mono text-xs uppercase tracking-[0.2em] ${HR_PAL.hubKicker}`}>
          <ShieldCheck className="w-3.5 h-3.5 inline mr-1" /> {t("HR Portal")} · {user?.name || ""}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1">{t("Employee Records & Accountability")}</h1>
        <p className="text-slate-600 mt-2 max-w-2xl">
          {t("Read-only HR access · field leadership records · accountability · payroll-time verification · training compliance.")}
        </p>

        <OperationsCenter compact className="mt-6" />

        {/* iter429 · Phase 28 · Optional device sign-in enrollment ·
            self-gated · dismissible · single-card · NEVER nags */}
        <div className="mt-6">
          <PasskeyEnrollPrompt />
        </div>

        <div className="mt-8 space-y-10">
          {TILE_GROUPS.map((group) => {
            const isMuted = !!group.muted;
            return (
              <section
                key={group.key}
                data-testid={`hr-group-${group.key}`}
                className={isMuted ? "pt-6 border-t border-slate-200" : ""}
              >
                <div className="mb-4 flex items-baseline gap-3 flex-wrap">
                  <h2
                    className={`font-mono text-xs uppercase tracking-[0.22em] ${
                      isMuted ? "text-slate-500" : "text-slate-700"
                    }`}
                    data-testid={`hr-group-heading-${group.key}`}
                  >
                    {t(group.heading)}
                  </h2>
                  <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
                  <span className="text-xs text-slate-500 italic">{t(group.sub)}</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {group.tiles.map((tileKey) => {
                    const tile = TILE_DEFS[tileKey];
                    const badge = tile.badgeKey ? stats[tile.badgeKey] : 0;
                    return (
                      <Link
                        key={tile.to}
                        to={tile.to}
                        className={`block rounded-lg border border-slate-200 border-l-4 ${tile.stripe} bg-white p-5 hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300 transition-all duration-150 relative`}
                        data-testid={`hr-tile-${tile.to.split('/').pop()}`}
                      >
                        {badge > 0 && (
                          <span
                            className="absolute top-3 right-3 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-full bg-red-600 text-white text-xs font-black border-2 border-white shadow"
                            data-testid={`hr-tile-badge-${tile.to.split('/').pop()}`}
                          >
                            {badge}
                          </span>
                        )}
                        <div className="flex items-start gap-3">
                          <tile.icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <h3 className="font-display text-lg font-black">{t(tile.label)}</h3>
                            <p className="text-sm text-slate-600 mt-1">{t(tile.desc)}</p>
                            <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${tile.btn} text-white font-bold uppercase tracking-wide text-xs`}>
                              {t("OPEN →")}
                            </span>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>

        {/* Cross-portal integration strip — Motive driver-safety roll-up
            for HR review. Lives inside the Integrations & Systems group
            visually (after the section divider above) to keep it from
            competing with the operational HR sections. Empty until
            Motive credentials land or Admin flips Demo mode. */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6" data-testid="hr-integrations-strip">
          <IntegrationHealthCard
            tokenHeader={{ "X-HR-Token": getHrToken() || "" }}
            accent="purple"
            showAdminLink={false}
          />
          <IntegrationEventsCard
            provider="motive"
            title={t("Driver Safety Events (HR Review)")}
            tokenHeader={{ "X-HR-Token": getHrToken() || "" }}
            accent="purple"
          />
        </div>
      </main>
    </div>
  );
}
