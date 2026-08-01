// MASCI Hub — top-level landing page.
//
// Iter73 layout: audience-grouped sections.
//
//   1. Hero headline + tagline.
//   2. "Welcome back" auto-personalization strip (only if a portal
//      token is present in this browser) — promotes the user's home
//      portal to a single big call-out card.
//   3. TODAY IN THE FIELD — Field, QA/QC, Safety (3 large tiles).
//   4. LEADERSHIP TOOLS — Field Leadership + Projects (2 medium).
//   5. OFFICE PORTALS — PM, Shop, HR, Admin (4 compact, sign-in).
//   6. REFERENCE — Training Hub · Cheat Sheet · Need Help (text strip).
//
// Verbiage rule (Phase D — hybrid): public destinations keep warm
// descriptive copy; restricted tiles show one neutral line + 🔒 + a
// "Sign in to continue" CTA. No feature bullets are exposed on
// restricted tiles to avoid telegraphing internal structure to
// unauthorized viewers.

import React, { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HardHat, ClipboardList, Building2, Shield, Wrench, ClipboardCheck,
  GraduationCap, UserCheck, Users, ArrowRight, MapPin, Lock, Phone,
  BookOpen, LogOut, ShieldAlert, ShieldCheck, Truck, ExternalLink,
} from "lucide-react";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { CanonicalHeader } from "@/components/CanonicalHeader";
import { CanonicalCard } from "@/components/CanonicalCard";
import { SectionHeading } from "@/components/SectionHeading";
import { useT } from "@/lib/i18n";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { getPmToken, clearPmToken } from "@/lib/pmAuth";
import { getShopToken, clearShopToken } from "@/lib/shopAuth";
import { getDispatchToken, clearDispatchToken, getDispatchUser } from "@/lib/dispatchAuth";
import { getHrToken, getHrUser, clearHrToken } from "@/lib/hrAuth";
import { getSafetyToken, getSafetyUser, clearSafetyToken } from "@/lib/safetyAuth";
import { isLeadershipAuthed, clearLeadershipToken } from "@/lib/leadershipAuth";
import { tileAccentFor } from "@/lib/portalPalette";
import { authorizedPortals, isSignedInAnywhere } from "@/lib/permissions";
import { clearAllSessions } from "@/lib/sessionReset";
function WelcomeBackHero({ session }) {
  const { t } = useT();
  return (
    <CanonicalCard
      tone={tileAccentFor(session.kind)}
      appearance="solid"
      title={session.name || t("Signed in")}
      description={`${t("Tap to jump back into your")} ${t(session.scopeLabel)} ${t("dashboard")}.`}
      eyebrow={`${t("Welcome back")} · ${t(session.scopeLabel)}`}
      testId="hub-welcome-back"
      className="mb-6"
      footerSlot={(
        <div className="flex flex-wrap items-center gap-2 w-full">
          <Link
            to={session.to}
            className="wp17-cta wp17-cta--outline wp17-cta--sm !text-slate-900"
            data-testid="hub-welcome-back-open"
          >
            {t("Open")}
            <ArrowRight className="w-4 h-4" />
          </Link>
          <button
            onClick={session.signOut}
            className="wp17-cta wp17-cta--ghost wp17-cta--sm !text-white hover:!bg-white/10 hover:!border-white/15"
            data-testid="hub-welcome-back-signout"
            title={t("Sign out")}
            type="button"
          >
            <LogOut className="w-3.5 h-3.5" />
            {t("Sign out")}
          </button>
        </div>
      )}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] opacity-70 font-bold" data-testid="hub-welcome-back-label">
          {t("Welcome back")} · {t(session.scopeLabel)}
      </div>
    </CanonicalCard>
  );
}

const FIELD_ENTRY_CARDS = [
  {
    to: "/field",
    icon: HardHat,
    title: "Field",
    description: "File end-of-day reports, log equipment walk-arounds, and capture crew, weather, and production from the job site.",
    tone: "amber",
    testId: "hub-section-field",
  },
  {
    to: "/qaqc",
    icon: ClipboardCheck,
    title: "QA / QC",
    description: "Run quality inspections on concrete, asphalt, rebar, and subcontractor work — signed, photographed, routed, and archived.",
    tone: "emerald",
    testId: "hub-section-qc",
  },
  {
    to: "/safety",
    icon: Shield,
    title: "Safety",
    description: "File toolbox talks, JHAs, incident reports, and trench-box plans — directly from the truck or trailer.",
    tone: "red",
    testId: "hub-section-safety",
  },
];

// ─── Page ───────────────────────────────────────────────────────────────

export default function Hub() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  // Re-render cue: signing out updates this counter to recompute the
  // detected session (it reads localStorage synchronously, so a state
  // bump is enough — no listener needed).
  const [renderTick, force] = useState(0);

  const handleSignOut = async () => {
    await clearAllSessions();
    force((n) => n + 1);
    navigate("/sign-in", { replace: true });
  };

  const session = useMemo(
    () => detectActiveSession(t, handleSignOut, renderTick),
    [t, renderTick],
  );

  const headerAction = session ? (
    <Link
      to={session.to}
      className="inline-flex items-center h-10 rounded-full border border-white/12 bg-white/10 px-3.5 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white hover:bg-white/18"
      data-testid="hub-resume-link"
      title={t(`Open ${session.scopeLabel}`)}
    >
      {t("Resume")}
    </Link>
  ) : (
    <Link
      to="/sign-in"
      className="inline-flex items-center h-10 rounded-full border border-white/12 bg-white/10 px-3.5 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-white hover:bg-white/18"
      data-testid="hub-sign-in-link"
      title="Multi-portal sign-in for managers, admins, and HR with cross-portal access"
    >
      {t("Sign in")}
    </Link>
  );

  return (
    <div className="wp17-public-shell">
      <div className="caution-stripe" />
      <CanonicalHeader
        variant="home"
        accent="red"
        homeTo="/"
        showHomeLink={false}
        showLangToggle
        testIdPrefix="hub-home"
        containerClassName="max-w-6xl"
        postControlsSlot={headerAction}
      />

      <main className="wp17-public-main py-8 sm:py-12">

        {/* Hero headline */}
        <div className="wp17-public-hero mb-8 sm:mb-12" data-testid="hub-entry-architecture">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr),320px] lg:items-start">
            <div>
              <span className="wp17-kicker text-red-700">{t("Operational command center")}</span>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
                {lang === "es" ? (
                  <>
                    {"Un Solo Sistema. Cada Cuadrilla. "}
                    <span className="text-red-700">Cada Trabajo</span>{"."}
                  </>
                ) : (
                  <>
                    {"One System. Every Crew. "}
                    <span className="text-red-700">Every Job</span>{"."}
                  </>
                )}
              </h1>
              <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-3xl">
                {t("Choose the workflow you need, jump into the right workspace, and keep crews, field reports, safety, quality, and operations moving from one command center.")}
              </p>
              <div className="wp17-chip-row mt-6" data-testid="hub-next-actions-row">
                <Link to="/field" className="wp17-chip !bg-slate-900 !text-white !border-slate-900/20" data-testid="hub-next-field-chip">{t("Start field reporting")}</Link>
                <Link to="/guidance" className="wp17-chip !bg-white !text-slate-900 !border-slate-200" data-testid="hub-next-guidance-chip">{t("Open guidance")}</Link>
                <Link to="/cheatsheet" className="wp17-chip !bg-white !text-slate-900 !border-slate-200" data-testid="hub-next-cheatsheet-chip">{t("Open cheat sheet")}</Link>
              </div>
            </div>
            <div className="rounded-[1.6rem] border border-slate-900/75 bg-slate-950 px-5 py-5 text-white shadow-[0_24px_60px_rgba(15,23,42,0.22)]" data-testid="hub-attention-panel">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-white/55">{t("What needs attention now")}</div>
              <div className="mt-2 text-lg font-semibold leading-tight">{t("Pick the workflow that gets work moving in the next minute.")}</div>
              <p className="mt-2 text-sm leading-6 text-white/74">{t("Use field tools for live jobsite reporting, guidance for how-to answers, and your workspace when you need restricted operational data.")}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <OperationalStatusBadge tone="red" testId="hub-badge-public">{t("Public field entry")}</OperationalStatusBadge>
                <OperationalStatusBadge tone="cyan" testId="hub-badge-workspaces">{t("Portal workspaces")}</OperationalStatusBadge>
                <OperationalStatusBadge tone="amber" testId="hub-badge-help">{t("Help always available")}</OperationalStatusBadge>
              </div>
            </div>
          </div>
        </div>

        {/* Welcome back strip (only when an active session is detected) */}
        {session && <WelcomeBackHero session={session} />}

        {/* iter218 · Day-1 "Start Here" entry — visible only when NO
            session is detected, so it stays out of the way for crews
            who already know the platform. Surfaced for new hires
            arriving from QR posters at the yard. */}
        {!session && (
          <CanonicalCard
            to="/guidance/role-new-employee"
            icon={MapPin}
            tone="amber"
            size="compact"
            eyebrow={t("New here?")}
            title={t("First week on the platform — start here")}
            description={t("A 5-minute walkthrough for new hires: what to fill out, where, and why.")}
            ctaLabel={`${t("Start here")} →`}
            testId="hub-day-one-start-here"
            className="mb-8"
          >
          </CanonicalCard>
        )}

        {/* SECTION 1 — Today in the Field */}
        <SectionHeading
          index="01"
          title={t("Today in the Field")}
          subtitle={t("What every crew on site does today.")}
          testId="hub-field-heading"
        />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 sm:gap-5 mb-10">
          {FIELD_ENTRY_CARDS.map((card) => (
            <CanonicalCard
              key={card.testId}
              to={card.to}
              icon={card.icon}
              tone={card.tone}
              size="feature"
              title={t(card.title)}
              description={t(card.description)}
              ctaLabel={t("Enter →")}
              testId={card.testId}
            />
          ))}
        </div>

        {/* SECTION 2 — Leadership Tools */}
        <SectionHeading
          index="02"
          title={t("Leadership Tools")}
          subtitle={t("For foremen, supervisors, and superintendents running the work.")}
          testId="hub-leadership-heading"
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 sm:gap-5 mb-10">
          <FieldLeadershipCard testId="hub-section-leadership" />
          <ProjectsCard testId="hub-section-projects" />
        </div>

        {/* SECTION 3 — Operations (compact, sign-in required) */}
        {(() => {
          // Iter149 → 18.04: when a user is signed in, separate the
          // workspaces they can actually use from the ones they can't —
          // reduces visual overwhelm and prevents the "click the locked
          // tile" frustration. Anonymous visitors keep the full 6-tile
          // grid (it's the public front door).
          const authed = isSignedInAnywhere() ? authorizedPortals() : null;
          const portalDefs = [
            { kind: "pm", to: "/pm/login", icon: ClipboardList, title: t("Project Management"),
              desc: t("Project management, PO requests, subcontractor administration, and project oversight."),
              testId: "hub-section-pm", signedInLabel: t("Open Workspace") },
            { kind: "shop", to: "/shop/login", icon: Wrench, title: t("Shop Operations"),
              desc: t("Fleet maintenance, inspections, repairs, parts, and equipment readiness."),
              testId: "hub-section-shop", signedInLabel: t("Open Workspace") },
            { kind: "hr", to: "/hr/login", icon: Users, title: t("Human Resources"),
              desc: t("Employee records, onboarding, compliance, training, and workforce management."),
              testId: "hub-section-hr", signedInLabel: t("Open Workspace") },
            { kind: "safety", to: session?.kind === "safety" ? "/safety-portal" : "/safety-portal/login", icon: ShieldAlert, title: t("Safety Operations"),
              desc: t("Incidents, audits, inspections, JHPs, toolbox talks, and compliance workflows."),
              testId: "hub-section-safety-portal", signedInLabel: t("Open Workspace") },
            { kind: "dispatch", to: session?.kind === "dispatch" ? "/dispatch-portal" : "/dispatch-portal/login", icon: Truck, title: t("Transportation Operations"),
              desc: t("Dispatch, live map, fleet, drivers, carriers, compliance, orientation, cleanup, and transportation coordination."),
              testId: "hub-section-dispatch-portal", signedInLabel: t("Open Workspace") },
            { kind: "admin", to: "/admin/login", icon: ClipboardList, title: t("Administration"),
              desc: t("System administration, user management, platform configuration, and reporting."),
              testId: "hub-section-admin", signedInLabel: t("Open Workspace") },
          ];
          const yours = authed ? portalDefs.filter((p) => authed.includes(p.kind)) : portalDefs;
          const others = authed ? portalDefs.filter((p) => !authed.includes(p.kind)) : [];

          return (
            <>
              <SectionHeading
                index="03"
                title={authed ? t("Your Workspaces") : t("Operations")}
                subtitle={authed ? t("Sign-in required. Showing the workspaces you're authorized for.") : t("Sign-in required. Project management, shop operations, human resources, safety, transportation, and administration.")}
                testId="hub-operations-heading"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
                {yours.map((p) => (
                  <CanonicalCard
                    key={p.kind}
                    to={p.to}
                    icon={p.icon}
                    tone={tileAccentFor(p.kind)}
                    size="compact"
                    eyebrow={session?.kind === p.kind ? t("Active workspace") : t("Restricted workspace")}
                    title={p.title}
                    titleSuffix={!session?.kind || session.kind !== p.kind ? <Lock className="w-3.5 h-3.5 text-slate-400 shrink-0" data-testid={`${p.testId}-lock`} /> : null}
                    description={p.desc}
                    testId={p.testId}
                    ctaLabel={session?.kind === p.kind ? `${p.signedInLabel || t("Open")} →` : `${t("Sign in")} →`}
                  />
                ))}
              </div>

              {others.length > 0 && (
                <div className="mb-10" data-testid="hub-other-portals">
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400 font-bold mb-2.5 flex items-center gap-2">
                    <Lock className="w-3 h-3" /> {t("Other Workspaces")} · {t("not in your access set")}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {others.map((p) => (
                      <span
                        key={p.kind}
                        className="wp17-status-badge wp17-tone--slate"
                        data-testid={`hub-other-portal-${p.kind}`}
                      >
                        <p.icon className="w-3.5 h-3.5" /> {p.title}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          );
        })()}

        {/* SECTION 4 — Reference strip */}
        <SectionHeading
          index="04"
          title={t("Reference")}
          subtitle={t("Operator guides, training, and contact info — always available, no sign-in required.")}
          testId="hub-reference-heading"
        />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 sm:gap-4 mb-6">
          <CompanyInfoDialog
            trigger={(
              <CanonicalCard
                element="button"
                type="button"
                icon={Phone}
                tone="slate"
                size="compact"
                title={t("Need Help?")}
                description={t("Office phone, address, and after-hours operations contact.")}
                ctaLabel={`${t("Open contact details")} →`}
                testId="hub-need-help"
                className="w-full text-left"
              />
            )}
          />
          <CanonicalCard
            to="/guidance"
            icon={GraduationCap}
            tone="blue"
            size="compact"
            title={t("Operational Guidance Center")}
            description={t("Role-based operator playbooks, portal walk-throughs, and field cheat references.")}
            ctaLabel={`${t("Open guidance")} →`}
            testId="hub-section-training"
          />
          <CanonicalCard
            to="/cheatsheet"
            icon={BookOpen}
            tone="amber"
            size="compact"
            title={t("Cheat Sheet")}
            description={t("The one-page operations summary pinned in every site trailer.")}
            ctaLabel={`${t("Open cheat sheet")} →`}
            testId="hub-cheatsheet-link"
          />
        </div>
      </main>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────

/**
 * Reads localStorage for any active portal token and returns the first
 * one detected. Admin > HR > PM > Shop > Leadership. If multiple are
 * present (rare, dev sessions), admin wins because admin is the only
 * scope that can see everything.
 */
function detectActiveSession(t, signOut) {
  if (getAdminToken()) {
    return { kind: "admin", scopeLabel: "Admin Console", name: "Admin", to: "/admin",
             signOut };
  }
  if (getHrToken()) {
    const u = getHrUser() || {};
    return { kind: "hr", scopeLabel: "HR Portal", name: u.name || u.email || "HR", to: "/hr",
             signOut };
  }
  if (getSafetyToken()) {
    const u = getSafetyUser() || {};
    return { kind: "safety", scopeLabel: "Safety Portal", name: u.name || u.email || "Safety", to: "/safety-portal",
             signOut };
  }
  if (getPmToken()) {
    return { kind: "pm", scopeLabel: "PM Portal", name: "Project Manager", to: "/pm",
             signOut };
  }
  if (getShopToken()) {
    return { kind: "shop", scopeLabel: "Shop Console", name: "Shop", to: "/shop",
             signOut };
  }
  if (getDispatchToken()) {
    const u = getDispatchUser() || {};
    return { kind: "dispatch", scopeLabel: "Dispatch Portal", name: u.name || u.email || "Dispatcher", to: "/dispatch-portal",
             signOut };
  }
  if (isLeadershipAuthed()) {
    return { kind: "leadership", scopeLabel: "Field Leadership", name: "Field Leadership", to: "/leadership",
             signOut };
  }
  return null;
}

/**
 * FieldLeadershipCard — Track 15.4B (2026-06-16) public-safe correction.
 *
 * The 15.4A iteration exposed 4 internal workflow routes
 * (Recognition / Write-Up / Equipment Checkout / Records) on the
 * public homepage. That advertised internal gated process structure
 * and made the card read as a form menu rather than a leadership
 * system.
 *
 * 15.4B removes all internal launchers. The card is now a single
 * full-card click target routing to `/leadership` (the gated
 * Field Leadership entry point that already enforces auth and shows
 * the real workflow menu to authorized users). A non-clickable
 * capability list communicates scope in public-safe language
 * (capability labels, NOT form names).
 *
 * Visual density (vs the prior 4-launcher grid) comes from the
 * capability list rendered as small bordered rows with check icons,
 * so the card retains its equal-peer weight with Project Systems
 * without exposing internal workflow URLs.
 */
const FIELD_LEADERSHIP_CAPABILITIES = [
  "Workforce Accountability",
  "Employee Development",
  "Equipment Custody",
  "Recognition Programs",
];

function FieldLeadershipCard({ testId }) {
  const { t } = useT();
  return (
    <CanonicalCard
      to="/leadership"
      icon={UserCheck}
      tone="slate"
      title={t("Field Leadership")}
      description={t("Track workforce accountability, employee development, equipment custody, recognition, and leadership records across every project.")}
      eyebrow={t("Field leadership")}
      ctaLabel={t("Open Field Leadership")}
      testId={testId}
    >
      <ul
        className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2"
        data-testid="hub-field-leadership-capabilities"
        aria-label={t("Field Leadership capabilities")}
      >
          {FIELD_LEADERSHIP_CAPABILITIES.map((label) => (
            <li
              key={label}
              className="flex items-center gap-2.5 text-slate-700"
            >
              <ShieldCheck className="w-4 h-4 text-slate-500 shrink-0" />
              <span className="text-sm font-display font-bold tracking-tight text-slate-900">
                {t(label)}
              </span>
            </li>
          ))}
      </ul>
    </CanonicalCard>
  );
}

/**
 * ProjectSystemsCard — Track 15.3 (2026-06-16) replacement for the
 * legacy "Projects" tile. Three connected platform launchers:
 *   • Basecamp     — project communication / to-dos / docs
 *   • OnStation    — utility locating / field staking
 *   • ForgedOps Plans — construction plan viewer / takeoff
 *
 * Config-driven (PROJECT_SYSTEMS array) so future customers can swap
 * branding without re-engineering the tile. Logos render on dark
 * logo "chips" so the official black-background source assets
 * integrate cleanly with the surrounding card design (no clash with
 * the per-platform accent colors which live on the left edge stripe
 * and the label).
 */
const PROJECT_SYSTEMS = [
  {
    key: "basecamp",
    label: "Basecamp",
    url: "https://3.basecamp.com/5958093/projects",
    logo: "/brand-logos/basecamp.jpeg",
    // Basecamp brand green.
    accent: "#16a34a",
    accentHover: "#15803d",
    testid: "hub-projects-basecamp-btn",
    // Logo natively fills its frame (square icon) — standard max.
    logoMax: 52,
  },
  {
    key: "onstation",
    label: "OnStation",
    url: "https://app.onstation.us/login",
    logo: "/brand-logos/onstation.jpeg",
    // OnStation brand blue.
    accent: "#1d4ed8",
    accentHover: "#1e40af",
    testid: "hub-projects-onstation-btn",
    logoMax: 52,
  },
  {
    key: "forgedops-plans",
    label: "ForgedOps Plans",
    url: "https://forgedopsplans.com/login",
    logo: "/brand-logos/forgedops-plans.png",
    // ForgedOps signature orange (matches the molten-metal in the logotype).
    accent: "#ea580c",
    accentHover: "#c2410c",
    testid: "hub-projects-forgedops-plans-btn",
    // Track 15.4 (2026-06-16) — ForgedOps Plans logo has more
    // negative space in the source asset than Basecamp/OnStation, so
    // we render it ~23% larger inside the SAME chip footprint to
    // achieve equal perceived visual weight. Button height and chip
    // size remain identical across all three.
    logoMax: 64,
  },
];

function ProjectSystemsCard({ testId }) {
  const { t } = useT();
  return (
    <CanonicalCard
      icon={Building2}
      tone="amber"
      title={t("Project Systems")}
      description={t("Connected project platforms for communication, utility locating, and construction plans.")}
      eyebrow={t("Connected platforms")}
      testId={testId}
      footerSlot={<span className="wp17-card-surface__cta">{t("Open a connected platform")}</span>}
    >
      <div className="flex flex-wrap gap-3" data-testid="hub-project-systems-launchers">
          {PROJECT_SYSTEMS.map((sys) => (
            <a
              key={sys.key}
              href={sys.url}
              target="_blank"
              rel="noopener noreferrer"
              data-testid={sys.testid}
              aria-label={`Open ${sys.label} in a new tab`}
              className="group/sys relative flex items-center gap-3 min-h-[4.25rem] pl-0 pr-3.5 rounded-[1rem] bg-slate-950 hover:bg-slate-900 text-white transition-all duration-150 overflow-hidden shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 min-w-[200px] flex-1 basis-[200px]"
              style={{ borderLeft: `4px solid ${sys.accent}` }}
            >
              <span className="flex items-center justify-center w-[72px] h-full bg-black shrink-0">
                <img
                  src={sys.logo}
                  alt={`${sys.label} logo`}
                  className="object-contain"
                  style={{
                    maxWidth: `${sys.logoMax}px`,
                    maxHeight: `${sys.logoMax}px`,
                  }}
                  draggable={false}
                />
              </span>
              <span className="flex-1 min-w-0 flex flex-col">
                <span
                  className="text-[10px] font-mono uppercase tracking-[0.18em] font-bold leading-tight"
                  style={{ color: sys.accent }}
                >
                  Launch
                </span>
                <span className="text-sm font-display font-bold tracking-tight leading-tight whitespace-nowrap">
                  {sys.label}
                </span>
              </span>
              <ExternalLink className="w-4 h-4 shrink-0 opacity-60 group-hover/sys:opacity-100 transition-opacity" />
            </a>
          ))}
      </div>
    </CanonicalCard>
  );
}

/**
 * ProjectsCard — DEPRECATED, kept as alias for backward compatibility
 * with anything importing the old name. Renders the new
 * ProjectSystemsCard.
 */
function ProjectsCard({ testId }) {
  return <ProjectSystemsCard testId={testId} />;
}
