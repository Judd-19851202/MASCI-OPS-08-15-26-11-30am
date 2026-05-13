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
  BookOpen, LogOut,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { getPmToken, clearPmToken } from "@/lib/pmAuth";
import { getShopToken, clearShopToken } from "@/lib/shopAuth";
import { getHrToken, getHrUser, clearHrToken } from "@/lib/hrAuth";
import { isLeadershipAuthed, clearLeadershipToken } from "@/lib/leadershipAuth";

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
      className="group relative bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md flex flex-col h-full"
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
      className="group relative bg-white border-2 border-slate-300 rounded-md p-5 transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md flex items-start gap-4"
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
 */
const PortalPill = ({ to, icon: Icon, title, desc, accent, testId, signedIn, signedInLabel, external }) => {
  const { t } = useT();
  const palette = {
    purple: { bg: "bg-purple-700", border: "border-purple-200", cta: "text-purple-700" },
    orange: { bg: "bg-orange-600", border: "border-orange-200", cta: "text-orange-700" },
    indigo: { bg: "bg-indigo-700", border: "border-indigo-200", cta: "text-indigo-700" },
    slate:  { bg: "bg-slate-900",  border: "border-slate-200",  cta: "text-slate-800" },
  }[accent] || { bg: "bg-slate-900", border: "border-slate-200", cta: "text-slate-800" };

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
      className={`group bg-white border-2 ${signedIn ? "border-slate-400" : "border-slate-200"} rounded-md p-3.5 transition-all duration-150 hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-md flex items-start gap-3`}
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
 */
function WelcomeBackHero({ session }) {
  const { t } = useT();
  const palette = {
    admin:  { bg: "bg-slate-900",  text: "text-slate-100", btn: "bg-white text-slate-900 hover:bg-slate-100" },
    pm:     { bg: "bg-indigo-700", text: "text-indigo-50", btn: "bg-white text-indigo-700 hover:bg-indigo-50" },
    shop:   { bg: "bg-orange-700", text: "text-orange-50", btn: "bg-white text-orange-700 hover:bg-orange-50" },
    hr:     { bg: "bg-purple-700", text: "text-purple-50", btn: "bg-white text-purple-700 hover:bg-purple-50" },
    leadership: { bg: "bg-slate-700", text: "text-slate-100", btn: "bg-white text-slate-900 hover:bg-slate-100" },
  }[session.kind];
  return (
    <div
      className={`relative ${palette.bg} ${palette.text} rounded-md p-5 sm:p-6 mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-4`}
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
          className={`inline-flex items-center gap-2 h-10 px-4 rounded-md font-bold uppercase tracking-wide text-xs ${palette.btn}`}
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
          <MasciLogo variant="lockup" size="4xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="lockup" size="xl" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">

        {/* Hero headline */}
        <div className="mb-8 sm:mb-12">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            {t("MASCI Hub")}
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
            {t("Daily reports, safety enforcement, equipment tracking, training, and complete documentation — automatically captured, routed, and stored in one system.")}
          </p>
        </div>

        {/* Welcome back strip (only when an active session is detected) */}
        {session && <WelcomeBackHero session={session} />}

        {/* SECTION 1 — Today in the Field */}
        <SectionHeader kicker="01" title={t("Today in the Field")} subtitle={t("Submissions every crew on site needs today.")} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5 mb-10">
          <BigTile
            to="/field"
            icon={HardHat}
            title={t("Field")}
            desc={t("End-of-day reports and equipment walk-arounds for the crew on the ground.")}
            bullets={[
              t("Daily Reports — what the crew did today"),
              t("Equipment Pre-Op — OSHA walk-around"),
            ]}
            accent="amber"
            testId="hub-section-field"
          />
          <BigTile
            to="/qaqc"
            icon={ClipboardCheck}
            title={t("QA / QC")}
            desc={t("Quality inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored.")}
            bullets={[
              t("Concrete Form · Rebar · Subcontractor Inspection"),
            ]}
            accent="emerald"
            testId="hub-section-qc"
          />
          <BigTile
            to="/safety"
            icon={Shield}
            title={t("Safety")}
            desc={t("Inspections, toolbox talks, incident reports, JHPs, and trench-box guidance — if safety is on your mind, it lives here.")}
            bullets={[
              t("Site Inspections · Toolbox Talks · Incidents"),
              t("Job Hazard Plans · Trench Box Reference"),
            ]}
            accent="red"
            testId="hub-section-safety"
          />
        </div>

        {/* SECTION 2 — Leadership Tools */}
        <SectionHeader kicker="02" title={t("Leadership Tools")} subtitle={t("For foremen, supervisors, and superintendents in the field.")} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-10">
          <MediumTile
            to="/leadership"
            icon={UserCheck}
            kicker={t("MASCI Field Leadership")}
            title={t("Field Leadership")}
            desc={t("Crew accountability, employee documentation, equipment responsibility, recognition, and workforce-management forms.")}
            accent="slate"
            testId="hub-section-leadership"
          />
          <ProjectsCard testId="hub-section-projects" />
        </div>

        {/* SECTION 3 — Office Portals (compact, sign-in required) */}
        <SectionHeader kicker="03" title={t("Office Portals")} subtitle={t("Sign-in required. For office staff, mechanics, and HR.")} />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-10">
          <PortalPill
            to="/pm/login"
            icon={ClipboardList}
            title={t("PM Portal")}
            desc={t("The project-management workspace for MASCI office staff.")}
            accent="indigo"
            testId="hub-section-pm"
            signedIn={session?.kind === "pm"}
            signedInLabel={t("Open Portal")}
          />
          <PortalPill
            to="/shop/login"
            icon={Wrench}
            title={t("Shop")}
            desc={t("The mechanic's console for the MASCI equipment fleet.")}
            accent="orange"
            testId="hub-section-shop"
            signedIn={session?.kind === "shop"}
            signedInLabel={t("Open Console")}
          />
          <PortalPill
            to="/hr/login"
            icon={Users}
            title={t("HR Portal")}
            desc={t("Employee records and payroll cross-check for MASCI HR.")}
            accent="purple"
            testId="hub-section-hr"
            signedIn={session?.kind === "hr"}
            signedInLabel={t("Open Portal")}
          />
          <PortalPill
            to="/admin/login"
            icon={ClipboardList}
            title={t("Admin")}
            desc={t("The MASCI office console.")}
            accent="slate"
            testId="hub-section-admin"
            signedIn={session?.kind === "admin"}
            signedInLabel={t("Open Console")}
          />
        </div>

        {/* SECTION 4 — Reference strip */}
        <SectionHeader kicker="04" title={t("Reference")} subtitle={t("Always available — no sign-in needed.")} />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6">
          <ReferenceLink
            to="/training"
            icon={GraduationCap}
            title={t("Training Hub")}
            desc={t("Short bilingual lessons for every role.")}
            testId="hub-section-training"
          />
          <ReferenceLink
            to="/cheatsheet"
            icon={BookOpen}
            title={t("Cheat Sheet")}
            desc={t("The one-pager pinned in every site trailer.")}
            testId="hub-cheatsheet-link"
          />
          <CompanyInfoDialog
            trigger={(
              <button
                type="button"
                className="group flex items-start gap-3 bg-white border-2 border-slate-200 hover:border-slate-400 hover:shadow-md rounded-md p-4 transition-all duration-150 hover:-translate-y-0.5 text-left w-full"
                data-testid="hub-need-help"
              >
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-200 text-slate-800 shrink-0">
                  <Phone className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-display text-base font-black tracking-tight text-slate-900">{t("Need Help?")}</h3>
                  <p className="text-slate-600 text-xs mt-1 leading-snug">{t("Office phone, address, and after-hours contact.")}</p>
                </div>
                <ArrowRight className="w-5 h-5 mt-2 text-slate-700 group-hover:translate-x-1 transition-transform shrink-0" />
              </button>
            )}
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
      className="group flex items-start gap-3 bg-white border-2 border-slate-200 hover:border-slate-400 hover:shadow-md rounded-md p-4 transition-all duration-150 hover:-translate-y-0.5"
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
  if (getPmToken()) {
    return { kind: "pm", scopeLabel: "PM Portal", name: "Project Manager", to: "/pm",
             signOut: onSignOut(clearPmToken) };
  }
  if (getShopToken()) {
    return { kind: "shop", scopeLabel: "Shop Console", name: "Shop", to: "/shop",
             signOut: onSignOut(clearShopToken) };
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
      className="group relative bg-white border-2 border-slate-300 rounded-md p-5 flex items-start gap-4"
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
