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
import { Link } from "react-router-dom";
import {
  HardHat, ClipboardList, Building2, Shield, Wrench, ClipboardCheck,
  GraduationCap, UserCheck, Users, ArrowRight, MapPin, Lock, Phone,
  BookOpen, LogOut, ShieldAlert, Truck,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { getPmToken, clearPmToken } from "@/lib/pmAuth";
import { getShopToken, clearShopToken } from "@/lib/shopAuth";
import { getDispatchToken, clearDispatchToken, getDispatchUser } from "@/lib/dispatchAuth";
import { getHrToken, getHrUser, clearHrToken } from "@/lib/hrAuth";
import { getSafetyToken, getSafetyUser, clearSafetyToken } from "@/lib/safetyAuth";
import { isLeadershipAuthed, clearLeadershipToken } from "@/lib/leadershipAuth";
import { paletteFor, heroPaletteFor } from "@/lib/portalPalette";
import { authorizedPortals, isSignedInAnywhere } from "@/lib/permissions";

// ─── Shared tile component ──────────────────────────────────────────────

/**
 * BigTile — full color, photo-style. Used in TODAY IN THE FIELD row.
 * 3 across on desktop, stacked on mobile.
 */
const BigTile = ({ to, icon: Icon, title, desc, bullets, accent, testId }) => {
  const { t } = useT();
  const palette = {
    amber:   { bg: "bg-amber-600",   bar: "bg-amber-600",   pill: "text-amber-700 bg-amber-50",   cta: "text-amber-700" },
    emerald: { bg: "bg-emerald-700", bar: "bg-emerald-700", pill: "text-emerald-700 bg-emerald-50", cta: "text-emerald-700" },
    red:     { bg: "bg-red-700",     bar: "bg-red-700",     pill: "text-red-700 bg-red-50",       cta: "text-red-700" },
  }[accent] || { bg: "bg-slate-900", bar: "bg-slate-900", pill: "text-slate-700 bg-slate-100", cta: "text-slate-700" };
  return (
    <Link
      to={to}
      className="group relative bg-white border border-slate-200 rounded-md p-5 sm:p-7 transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md flex flex-col h-full"
      data-testid={testId}
    >
      <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${palette.bar}`} />
      <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${palette.bg} text-white`}>
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
        {title}
      </h3>
      <p className="text-slate-600 text-sm sm:text-base mt-2 leading-relaxed">{desc}</p>
      {bullets && (
        <ul className="mt-4 space-y-1.5 text-xs sm:text-sm text-slate-700">
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-2">
              <span className={`mt-1.5 w-1 h-1 rounded-full ${palette.bg} shrink-0`} />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-auto pt-5 border-t-2 border-slate-100 flex items-center justify-between">
        <span className={`font-mono text-xs uppercase tracking-[0.2em] font-bold ${palette.cta}`}>
          {t("Enter →")}
        </span>
        <ArrowRight className={`w-5 h-5 transition-transform duration-150 group-hover:translate-x-1 ${palette.cta}`} />
      </div>
    </Link>
  );
};

/**
 * MediumTile — used in LEADERSHIP TOOLS row. Half-height visual
 * weight, still informative.
 */
const MediumTile = ({ to, icon: Icon, title, desc, accent, testId, kicker }) => {
  const { t } = useT();
  const palette = {
    slate: { bg: "bg-slate-700", pill: "text-slate-700 bg-slate-100", cta: "text-slate-800" },
    yellow: { bg: "bg-yellow-500", pill: "text-yellow-800 bg-yellow-100", cta: "text-yellow-800" },
  }[accent] || { bg: "bg-slate-700", pill: "text-slate-700 bg-slate-100", cta: "text-slate-800" };
  return (
    <Link
      to={to}
      className="group relative bg-white border border-slate-200 rounded-md p-5 transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md flex items-start gap-4"
      data-testid={testId}
    >
      <div className={`inline-flex items-center justify-center w-12 h-12 rounded-md ${palette.bg} text-white shrink-0`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="flex-1 min-w-0">
        {kicker && (
          <span className={`inline-block px-2 py-0.5 rounded ${palette.pill} font-mono text-[10px] uppercase tracking-[0.2em] font-bold mb-1`}>
            {kicker}
          </span>
        )}
        <h3 className="font-display text-xl font-black tracking-tight text-slate-900">{title}</h3>
        <p className="text-slate-600 text-sm mt-1 leading-snug">{desc}</p>
      </div>
      <ArrowRight className={`w-5 h-5 mt-2 transition-transform duration-150 group-hover:translate-x-1 ${palette.cta} shrink-0`} />
    </Link>
  );
};

/**
 * PortalPill — compact card used in OFFICE PORTALS row. No feature
 * bullets — just title, one neutral sentence, sign-in CTA, lock icon.
 * Reinforces "restricted area" without being cold.
 *
 * iter143 — `kind` accepts a portal name ("pm"/"hr"/"safety"/…) and
 * the palette is resolved from the shared portalPalette table. No
 * visual change vs. the previous inline color tables.
 */
const PortalPill = ({ to, icon: Icon, title, desc, kind, testId, signedIn, signedInLabel, external }) => {
  const { t } = useT();
  const palette = paletteFor(kind);

  const inner = (
    <>
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${palette.bg} text-white shrink-0`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <h3 className="font-display text-base font-black tracking-tight text-slate-900 truncate">{title}</h3>
          {!signedIn && <Lock className="w-3 h-3 text-slate-400 shrink-0" />}
        </div>
        <p className="text-slate-600 text-xs mt-0.5 leading-snug line-clamp-2">{desc}</p>
        <div className={`font-mono text-[10px] uppercase tracking-[0.18em] font-bold mt-1.5 ${palette.cta}`}>
          {signedIn ? `${signedInLabel || t("Open")} →` : `${t("Sign in")} →`}
        </div>
      </div>
    </>
  );

  return (
    <Link
      to={to}
      className={`group bg-white border ${signedIn ? "border-slate-300" : "border-slate-200"} rounded-md p-3.5 transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md flex items-start gap-3`}
      data-testid={testId}
    >
      {inner}
    </Link>
  );
};

/**
 * WelcomeBackHero — promoted card at the very top when an active
 * session is detected. Lets a returning user one-tap back into their
 * home portal, and gives a friendly sign-out link for shared devices.
 *
 * iter143 — palette resolved from `session.kind` via portalPalette.
 */
function WelcomeBackHero({ session }) {
  const { t } = useT();
  const palette = heroPaletteFor(session.kind);
  return (
    <div
      className={`relative ${palette.bg} ${palette.onColor} rounded-md p-5 sm:p-6 mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-4`}
      data-testid="hub-welcome-back"
    >
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] opacity-70 font-bold">
          {t("Welcome back")} · {t(session.scopeLabel)}
        </div>
        <h3 className="font-display text-xl sm:text-2xl font-black mt-1">
          {session.name || t("Signed in")}
        </h3>
        <p className="text-sm opacity-80 mt-1">
          {t("Tap to jump back into your")} {t(session.scopeLabel)} {t("dashboard")}.
        </p>
      </div>
      <div className="flex items-center gap-2 self-stretch sm:self-auto">
        <Link
          to={session.to}
          className={`inline-flex items-center gap-2 h-10 px-4 rounded-md font-bold uppercase tracking-wide text-xs ${palette.btnInverse}`}
          data-testid="hub-welcome-back-open"
        >
          {t("Open")} <ArrowRight className="w-4 h-4" />
        </Link>
        <button
          onClick={session.signOut}
          className="inline-flex items-center gap-1 h-10 px-3 rounded-md border border-white/30 hover:bg-white/10 font-mono text-[10px] uppercase tracking-[0.2em] font-bold"
          data-testid="hub-welcome-back-signout"
          title={t("Sign out")}
        >
          <LogOut className="w-3.5 h-3.5" /> {t("Sign out")}
        </button>
      </div>
    </div>
  );
}

// ─── Page ───────────────────────────────────────────────────────────────

export default function Hub() {
  const { t, lang } = useT();
  // Re-render cue: signing out updates this counter to recompute the
  // detected session (it reads localStorage synchronously, so a state
  // bump is enough — no listener needed).
  const [renderTick, force] = useState(0);

  const session = useMemo(
    () => detectActiveSession(t, () => force((n) => n + 1)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, renderTick],
  );

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-5 sm:py-7 flex items-center justify-between">
          <MasciLogo variant="mark" size="2xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <Link
              to="/sign-in"
              className="hidden sm:inline-flex items-center h-9 px-3 rounded-md bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-bold uppercase tracking-wide transition-colors"
              data-testid="hub-sign-in-link"
              title="Multi-portal sign-in for managers, admins, and HR with cross-portal access"
            >
              {t("Sign in")}
            </Link>
            <LangToggle />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">

        {/* Hero headline */}
        <div className="mb-8 sm:mb-12">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            {t("MASCI Operations Platform")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-2">
            {lang === "es" ? (
              <>
                {"Cada trabajo bajo control. Cada detalle dirigido. "}
                <span className="text-red-700">Todo</span>{" protegido."}
              </>
            ) : (
              <>
                {"Run Every Job. Control Every Detail. Protect "}
                <span className="text-red-700">Everything</span>{"."}
              </>
            )}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            {t("End-of-day reports, safety enforcement, equipment tracking, quality control, and complete documentation — captured in the field, routed automatically, and stored in one operational system.")}
          </p>
        </div>

        {/* Welcome back strip (only when an active session is detected) */}
        {session && <WelcomeBackHero session={session} />}

        {/* iter218 · Day-1 "Start Here" entry — visible only when NO
            session is detected, so it stays out of the way for crews
            who already know the platform. Surfaced for new hires
            arriving from QR posters at the yard. */}
        {!session && (
          <Link
            to="/guidance/role-new-employee"
            data-testid="hub-day-one-start-here"
            className="group flex items-center gap-3 bg-amber-50 hover:bg-amber-100 border border-amber-300 border-l-4 border-l-amber-600 hover:border-l-amber-700 rounded-md px-4 py-3 mb-8 transition-all"
          >
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
              <MapPin className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-900 font-bold">
                {t("New here?")}
              </div>
              <div className="font-display text-base sm:text-lg font-black text-slate-900">
                {t("First week on the platform — start here")}
              </div>
              <div className="text-slate-700 text-xs mt-0.5 leading-snug">
                {t("A 5-minute walkthrough for new hires: what to fill out, where, and why.")}
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-amber-700 group-hover:translate-x-1 transition-transform shrink-0" />
          </Link>
        )}

        {/* SECTION 1 — Today in the Field */}
        <SectionHeader kicker="01" title={t("Today in the Field")} subtitle={t("What every crew on site does today.")} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4 sm:gap-5 mb-10">
          <BigTile
            to="/field"
            icon={HardHat}
            title={t("Field")}
            desc={t("File end-of-day reports, log equipment walk-arounds, and capture crew, weather, and production from the job site.")}
            accent="amber"
            testId="hub-section-field"
          />
          <BigTile
            to="/qaqc"
            icon={ClipboardCheck}
            title={t("QA / QC")}
            desc={t("Run quality inspections on concrete, asphalt, rebar, and subcontractor work — signed, photographed, routed, and archived.")}
            accent="emerald"
            testId="hub-section-qc"
          />
          <BigTile
            to="/safety"
            icon={Shield}
            title={t("Safety")}
            desc={t("File toolbox talks, JHAs, incident reports, and trench-box plans — directly from the truck or trailer.")}
            accent="red"
            testId="hub-section-safety"
          />
        </div>

        {/* SECTION 2 — Leadership Tools */}
        <SectionHeader kicker="02" title={t("Leadership Tools")} subtitle={t("For foremen, supervisors, and superintendents running the work.")} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 sm:gap-5 mb-10">
          <MediumTile
            to="/leadership"
            icon={UserCheck}
            kicker={t("MASCI Field Leadership")}
            title={t("Field Leadership")}
            desc={t("Track crew accountability, employee documentation, equipment custody, recognition, and workforce decisions.")}
            accent="slate"
            testId="hub-section-leadership"
          />
          <ProjectsCard testId="hub-section-projects" />
        </div>

        {/* SECTION 3 — Office Portals (compact, sign-in required) */}
        {(() => {
          // Iter149: when a user is signed in, separate the portals they
          // can actually use from the ones they can't — reduces visual
          // overwhelm and prevents the "click the locked tile" frustration.
          // Anonymous visitors keep the full 6-portal grid (it's the
          // public front door).
          const authed = isSignedInAnywhere() ? authorizedPortals() : null;
          const portalDefs = [
            { kind: "pm", to: "/pm/login", icon: ClipboardList, title: t("PM Portal"),
              desc: t("Manage jobs, PO requests, daily reports, inspections, photos, and project compliance."),
              testId: "hub-section-pm", signedInLabel: t("Open Portal") },
            { kind: "shop", to: "/shop/login", icon: Wrench, title: t("Shop"),
              desc: t("Run the mechanic queue — repairs, parts, PMs, and fleet readiness."),
              testId: "hub-section-shop", signedInLabel: t("Open Console") },
            { kind: "hr", to: "/hr/login", icon: Users, title: t("HR Portal"),
              desc: t("Employee records, onboarding, payroll cross-checks, and workforce documentation."),
              testId: "hub-section-hr", signedInLabel: t("Open Portal") },
            { kind: "safety", to: session?.kind === "safety" ? "/safety-portal" : "/safety-portal/login", icon: ShieldAlert, title: t("Safety Portal"),
              desc: t("Incidents, audits, inspections, PPE accountability, training, and corrective actions."),
              testId: "hub-section-safety-portal", signedInLabel: t("Open Portal") },
            { kind: "dispatch", to: session?.kind === "dispatch" ? "/dispatch-portal" : "/dispatch-portal/login", icon: Truck, title: t("Dispatch"),
              desc: t("Equipment movement, DVIRs, transfers, utilization, and operational readiness."),
              testId: "hub-section-dispatch-portal", signedInLabel: t("Open Portal") },
            { kind: "admin", to: "/admin/login", icon: ClipboardList, title: t("Admin"),
              desc: t("System administration — users, roles, integrations, audit logs, and exports."),
              testId: "hub-section-admin", signedInLabel: t("Open Console") },
          ];
          const yours = authed ? portalDefs.filter((p) => authed.includes(p.kind)) : portalDefs;
          const others = authed ? portalDefs.filter((p) => !authed.includes(p.kind)) : [];

          return (
            <>
              <SectionHeader
                kicker="03"
                title={authed ? t("Your Portals") : t("Office Portals")}
                subtitle={authed ? t("Sign-in required. Showing the portals you're authorized for.") : t("Sign-in required. Office, mechanic, HR, Safety, Dispatch, and Admin operations.")}
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 sm:gap-4 mb-6">
                {yours.map((p) => (
                  <PortalPill
                    key={p.kind}
                    to={p.to}
                    icon={p.icon}
                    title={p.title}
                    desc={p.desc}
                    kind={p.kind}
                    testId={p.testId}
                    signedIn={session?.kind === p.kind}
                    signedInLabel={p.signedInLabel}
                  />
                ))}
              </div>

              {others.length > 0 && (
                <div className="mb-10" data-testid="hub-other-portals">
                  <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-400 font-bold mb-2.5 flex items-center gap-2">
                    <Lock className="w-3 h-3" /> {t("Other Portals")} · {t("not in your access set")}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {others.map((p) => (
                      <span
                        key={p.kind}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-100 text-slate-500 text-[11px] font-bold uppercase tracking-wide"
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
        <SectionHeader kicker="04" title={t("Reference")} subtitle={t("Operator guides, training, and contact info — always available, no sign-in required.")} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4 sm:gap-4 mb-6">
          <CompanyInfoDialog
            trigger={(
              <button
                type="button"
                className="group flex items-start gap-3 bg-white border border-slate-200 hover:border-slate-400 hover:shadow-md rounded-md p-4 transition-all duration-150 hover:-translate-y-0.5 text-left w-full"
                data-testid="hub-need-help"
              >
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-200 text-slate-800 shrink-0">
                  <Phone className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-display text-base font-black tracking-tight text-slate-900">{t("Need Help?")}</h3>
                  <p className="text-slate-600 text-xs mt-1 leading-snug">{t("Office phone, address, and after-hours operations contact.")}</p>
                </div>
                <ArrowRight className="w-5 h-5 mt-2 text-slate-700 group-hover:translate-x-1 transition-transform shrink-0" />
              </button>
            )}
          />
          <ReferenceLink
            to="/guidance"
            icon={GraduationCap}
            title={t("Operational Guidance Center")}
            desc={t("Role-based operator playbooks, portal walk-throughs, and field cheat references.")}
            testId="hub-section-training"
          />
          <ReferenceLink
            to="/cheatsheet"
            icon={BookOpen}
            title={t("Cheat Sheet")}
            desc={t("The one-page operations summary pinned in every site trailer.")}
            testId="hub-cheatsheet-link"
          />
        </div>
      </main>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────

function SectionHeader({ kicker, title, subtitle }) {
  return (
    <div className="flex items-baseline gap-3 mb-4 sm:mb-5">
      <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-black">{kicker}</span>
      <span className="h-px flex-1 bg-slate-300 max-w-6" />
      <div className="flex-1 min-w-0">
        <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">{title}</h2>
        {subtitle && <p className="text-xs sm:text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function ReferenceLink({ to, icon: Icon, title, desc, testId }) {
  return (
    <Link
      to={to}
      className="group flex items-start gap-3 bg-white border border-slate-200 hover:border-slate-400 hover:shadow-md rounded-md p-4 transition-all duration-150 hover:-translate-y-0.5"
      data-testid={testId}
    >
      <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-200 text-slate-800 shrink-0">
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="font-display text-base font-black tracking-tight text-slate-900">{title}</h3>
        <p className="text-slate-600 text-xs mt-1 leading-snug">{desc}</p>
      </div>
      <ArrowRight className="w-5 h-5 mt-2 text-slate-700 group-hover:translate-x-1 transition-transform shrink-0" />
    </Link>
  );
}

/**
 * Reads localStorage for any active portal token and returns the first
 * one detected. Admin > HR > PM > Shop > Leadership. If multiple are
 * present (rare, dev sessions), admin wins because admin is the only
 * scope that can see everything.
 */
function detectActiveSession(t, rerender) {
  const onSignOut = (clearFn) => () => {
    try { clearFn(); } catch { /* noop */ }
    rerender?.();
  };
  if (getAdminToken()) {
    return { kind: "admin", scopeLabel: "Admin Console", name: "Admin", to: "/admin",
             signOut: onSignOut(clearAdminToken) };
  }
  if (getHrToken()) {
    const u = getHrUser() || {};
    return { kind: "hr", scopeLabel: "HR Portal", name: u.name || u.email || "HR", to: "/hr",
             signOut: onSignOut(clearHrToken) };
  }
  if (getSafetyToken()) {
    const u = getSafetyUser() || {};
    return { kind: "safety", scopeLabel: "Safety Portal", name: u.name || u.email || "Safety", to: "/safety-portal",
             signOut: onSignOut(clearSafetyToken) };
  }
  if (getPmToken()) {
    return { kind: "pm", scopeLabel: "PM Portal", name: "Project Manager", to: "/pm",
             signOut: onSignOut(clearPmToken) };
  }
  if (getShopToken()) {
    return { kind: "shop", scopeLabel: "Shop Console", name: "Shop", to: "/shop",
             signOut: onSignOut(clearShopToken) };
  }
  if (getDispatchToken()) {
    const u = getDispatchUser() || {};
    return { kind: "dispatch", scopeLabel: "Dispatch Portal", name: u.name || u.email || "Dispatcher", to: "/dispatch-portal",
             signOut: onSignOut(clearDispatchToken) };
  }
  if (isLeadershipAuthed()) {
    return { kind: "leadership", scopeLabel: "Field Leadership", name: "Field Leadership", to: "/leadership",
             signOut: onSignOut(clearLeadershipToken) };
  }
  return null;
}

/**
 * ProjectsCard — Basecamp / OnStation external links (kept as a tile
 * because they don't have a single canonical URL).
 */
function ProjectsCard({ testId }) {
  const { t } = useT();
  return (
    <div
      className="group relative bg-white border border-slate-200 rounded-md p-5 flex items-start gap-4"
      data-testid={testId}
    >
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-yellow-500 text-slate-900 shrink-0">
        <Building2 className="w-6 h-6" />
      </div>
      <div className="flex-1 min-w-0">
        <span className="inline-block px-2 py-0.5 rounded text-yellow-800 bg-yellow-100 font-mono text-[10px] uppercase tracking-[0.2em] font-bold mb-1">
          {t("Project Workspaces")}
        </span>
        <h3 className="font-display text-xl font-black tracking-tight text-slate-900">{t("Projects")}</h3>
        <p className="text-slate-600 text-sm mt-1 leading-snug">
          {t("Messages, to-dos, schedules, docs, and field staking.")}
        </p>
        <div className="flex flex-wrap gap-2 mt-3">
          <a
            href="https://3.basecamp.com/5958093/projects"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold uppercase tracking-wide"
            data-testid="hub-projects-basecamp-btn"
          >
            <Building2 className="w-3.5 h-3.5" /> Basecamp <ArrowRight className="w-3.5 h-3.5" />
          </a>
          <a
            href="https://app.onstation.us/login"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold uppercase tracking-wide"
            data-testid="hub-projects-onstation-btn"
          >
            <MapPin className="w-3.5 h-3.5" /> OnStation <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
