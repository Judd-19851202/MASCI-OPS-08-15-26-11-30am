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
// descriptive copy; restricted tiles show one neutral line plus a lock
// state and a direct access CTA. No feature bullets are exposed on
// restricted tiles to avoid telegraphing internal structure to
// unauthorized viewers.

import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HardHat, ClipboardList, Building2, Shield, Wrench, ClipboardCheck,
  GraduationCap, UserCheck, Users, MapPin, Lock, Phone,
  BookOpen, ShieldAlert, ShieldCheck, Truck, ExternalLink,
} from "lucide-react";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { CanonicalHeader } from "@/components/CanonicalHeader";
import { ActionCard, ExternalPlatformCard, InformationCard, ModuleCard, WorkflowCard } from "@/components/CanonicalCard";
import { SectionHeading } from "@/components/SectionHeading";
import { WorkspaceSessionControl } from "@/components/WorkspaceSessionControl";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";
import { usePageTitle } from "@/lib/usePageTitle";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { getPmToken, clearPmToken } from "@/lib/pmAuth";
import { getShopToken, clearShopToken } from "@/lib/shopAuth";
import { getDispatchToken, clearDispatchToken, getDispatchUser } from "@/lib/dispatchAuth";
import { getFlToken, getFlUser, clearFlToken } from "@/lib/flAuth";
import { getHrToken, getHrUser, clearHrToken } from "@/lib/hrAuth";
import { getSafetyToken, getSafetyUser, clearSafetyToken } from "@/lib/safetyAuth";
import { isLeadershipAuthed, clearLeadershipToken } from "@/lib/leadershipAuth";
import { tileAccentFor } from "@/lib/portalPalette";
import { authorizedPortals, isSignedInAnywhere } from "@/lib/permissions";
import { clearAllSessions, redirectToPublicHome } from "@/lib/sessionReset";
import { setPortalContext } from "@/lib/portalContext";

const FIELD_ENTRY_CARDS = [
  {
    to: "/field",
    icon: HardHat,
    title: "Field",
    description: "File end-of-day reports, log equipment walk-arounds, and capture crew, weather, and production from the job site.",
    tone: "field",
    testId: "hub-section-field",
  },
  {
    to: "/qaqc",
    icon: ClipboardCheck,
    title: "QA/QC",
    description: "Run quality inspections on concrete, asphalt, rebar, and subcontractor work — signed, photographed, routed, and archived.",
    tone: "qaqc",
    testId: "hub-section-qc",
  },
  {
    to: "/safety",
    icon: Shield,
    title: "Safety",
    description: "File toolbox talks, JHAs, incident reports, and trench-box plans — directly from the truck or trailer.",
    tone: "safety",
    testId: "hub-section-safety",
  },
];

// ─── Page ───────────────────────────────────────────────────────────────

export default function Hub() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  usePageTitle("Home · MASCI Operations Platform");
  // Re-render cue: signing out updates this counter to recompute the
  // detected session (it reads localStorage synchronously, so a state
  // bump is enough — no listener needed).
  const [renderTick, force] = useState(0);

  const handleSignOut = async () => {
    await clearAllSessions();
    force((n) => n + 1);
    redirectToPublicHome(navigate);
  };

  const session = useMemo(
    () => detectActiveSession(t, handleSignOut, renderTick),
    [t, renderTick],
  );

  useEffect(() => {
    if (!session) {
      try { setPortalContext("public"); } catch { /* noop */ }
    }
  }, [session]);

  const headerAction = session ? (
    <WorkspaceSessionControl session={session} onSignOut={handleSignOut} />
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
        headerControlsSlot={headerAction}
        testIdPrefix="hub-home"
        containerClassName="max-w-6xl"
      />

      <main className="wp17-public-main py-8 sm:py-12">

        {/* Hero headline */}
        <div className="wp17-public-hero mb-8 sm:mb-12" data-testid="hub-entry-architecture">
          <div className="max-w-4xl">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700" data-testid="hub-hero-kicker">
                {t("MASCI Operations Platform")}
              </div>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900">
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
              <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-3xl" data-testid="hub-hero-subheadline">
                {t("Start field work fast with field reporting, safety, quality, equipment, workforce accountability, transportation, and project operations in one trusted system built for heavy-civil operations.")}
              </p>
              <div className="mt-6 flex flex-wrap gap-3" data-testid="hub-next-actions-row">
                <Button asChild data-testid="hub-next-field-button">
                  <Link to="/field">{t("Start field reporting")}</Link>
                </Button>
                <Button asChild variant="outline" data-testid="hub-next-guidance-button">
                  <Link to="/guidance">{t("Open guidance")}</Link>
                </Button>
                <Button asChild variant="secondary" data-testid="hub-next-cheatsheet-button">
                  <Link to="/cheatsheet">{t("Open cheat sheet")}</Link>
                </Button>
              </div>
          </div>
        </div>

        {/* iter218 · Day-1 "Start Here" entry — visible only when NO
            session is detected, so it stays out of the way for crews
            who already know the platform. Surfaced for new hires
            arriving from QR posters at the yard. */}
        {!session && (
          <ActionCard
            to="/guidance/role-new-employee"
            icon={MapPin}
            tone="amber"
            eyebrow={t("New here?")}
            title={t("First week on the platform — start here")}
            description={t("A 5-minute walkthrough for new hires: what to fill out, where, and why.")}
            ctaLabel={t("Start here")}
            testId="hub-day-one-start-here"
            className="mb-8"
          />
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
            <ModuleCard
              key={card.testId}
              to={card.to}
              icon={card.icon}
              tone={card.tone}
              title={t(card.title)}
              description={t(card.description)}
              ctaLabel={t("Open")}
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
                subtitle={authed ? t("Showing the operations areas your account can open right now.") : t("Restricted operational areas for project management, shop operations, human resources, safety, transportation, and administration.")}
                testId="hub-operations-heading"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
                {yours.map((p) => (
                  <WorkflowCard
                    key={p.kind}
                    to={p.to}
                    icon={p.icon}
                    tone={tileAccentFor(p.kind)}
                    eyebrow={session?.kind === p.kind ? t("Active workspace") : t("Restricted workspace")}
                    title={p.title}
                    titleSuffix={!session?.kind || session.kind !== p.kind ? <Lock className="w-3.5 h-3.5 text-slate-400 shrink-0" data-testid={`${p.testId}-lock`} /> : null}
                    description={p.desc}
                    testId={p.testId}
                    ctaLabel={session?.kind === p.kind ? (p.signedInLabel || t("Open workspace")) : t("Open workspace")}
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
              <InformationCard
                element="button"
                type="button"
                icon={Phone}
                tone="slate"
                title={t("Need Help?")}
                description={t("Office phone, address, and after-hours operations contact.")}
                ctaLabel={t("Open contact details")}
                testId="hub-need-help"
                className="w-full text-left"
              />
            )}
          />
          <InformationCard
            to="/guidance"
            icon={GraduationCap}
            tone="blue"
            title={t("Operational Guidance Center")}
            description={t("Role-based operator playbooks, portal walk-throughs, and field cheat references.")}
            ctaLabel={t("Open guidance")}
            testId="hub-section-training"
          />
          <InformationCard
            to="/cheatsheet"
            icon={BookOpen}
            tone="amber"
            title={t("Cheat Sheet")}
            description={t("The one-page operations summary pinned in every site trailer.")}
            ctaLabel={t("Open cheat sheet")}
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
  if (getFlToken()) {
    const u = getFlUser() || {};
    return { kind: "leadership", scopeLabel: "Field Leadership", name: u.name || u.email || "Field Leadership", to: "/leadership",
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
    <WorkflowCard
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
    </WorkflowCard>
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
    <ExternalPlatformCard
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
    </ExternalPlatformCard>
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
