import React from "react";
import { Link } from "react-router-dom";
import {
  HardHat,
  ClipboardList,
  Building2,
  Shield,
  Wrench,
  ClipboardCheck,
  GraduationCap,
  ArrowRight,
  MapPin,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

/**
 * MASCI Hub — top-level landing page.
 *
 * The app started as a Safety Hub and has grown into the full MASCI
 * operations platform. Sections:
 *
 *   🦺 Safety    — compliance forms (inspections, meetings, incidents, JHA, trench)
 *   👷 Field     — daily operational logs (daily reports, equipment pre-op)
 *   🏗️ Basecamp  — external link to the live MASCI Basecamp account
 *   📍 OnStation — external link to the OnStation field-staking app
 *   🗄️ Admin     — office console (dashboards, exports, backups, routing)
 *   🔧 Shop      — mechanic / fleet console
 *
 * The "Crew Hub" Basecamp-clone was scrapped 2026-04-28 in favor of linking
 * out to the real Basecamp + OnStation that the team already pays for.
 */

const SectionCard = ({ to, icon: Icon, eyebrow, title, desc, bullets, accent, testId, external, comingSoon }) => {
  const { t } = useT();
  // accent classes kept static so Tailwind keeps them in the build
  const styles = {
    red:   { bg: "bg-red-700",   bar: "border-red-700",   ring: "hover:border-red-700",   pill: "text-red-700 bg-red-50" },
    amber: { bg: "bg-amber-600", bar: "border-amber-600", ring: "hover:border-amber-600", pill: "text-amber-700 bg-amber-50" },
    slate: { bg: "bg-slate-900", bar: "border-slate-900", ring: "hover:border-slate-900", pill: "text-slate-800 bg-slate-100" },
    emerald:{ bg: "bg-emerald-700", bar: "border-emerald-700", ring: "hover:border-emerald-700", pill: "text-emerald-700 bg-emerald-50" },
    blue:  { bg: "bg-blue-700",  bar: "border-blue-700",  ring: "hover:border-blue-700",  pill: "text-blue-700 bg-blue-50" },
  };
  const s = styles[accent] || styles.red;

  // "Coming soon" tiles render as a non-clickable div with a wash-out look
  // so users can see what's planned without bumping into a dead link.
  if (comingSoon) {
    return (
      <div
        className="group relative bg-white border-2 border-dashed border-slate-300 rounded-md p-6 sm:p-8 flex flex-col opacity-90 cursor-not-allowed"
        data-testid={testId}
        aria-disabled="true"
      >
        <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${s.bg} opacity-60`} />
        <div className="flex items-start justify-between gap-3">
          <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${s.bg} text-white opacity-70`}>
            <Icon className="w-7 h-7" />
          </div>
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-900 text-amber-300 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
            {t("Coming Soon")}
          </span>
        </div>
        <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-700 mt-4">
          {title}
        </h3>
        <p className="text-slate-500 text-sm sm:text-base mt-2 leading-relaxed">{desc}</p>
        {bullets && (
          <ul className="mt-4 space-y-1.5 text-xs sm:text-sm text-slate-500">
            {bullets.map((b) => (
              <li key={b} className="flex items-start gap-2">
                <span className={`mt-1.5 w-1 h-1 rounded-full ${s.bg} shrink-0 opacity-60`} />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-6 pt-5 border-t-2 border-dashed border-slate-200 flex items-center justify-between">
          <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold text-slate-400">
            {t("In development")}
          </span>
        </div>
      </div>
    );
  }

  // External tiles (e.g., Basecamp) open in a new tab via <a target="_blank">
  // instead of react-router's <Link> (which only works for in-app routes).
  const isExternalUrl = typeof to === "string" && /^https?:\/\//i.test(to);
  if (isExternalUrl) {
    return (
      <a
        href={to}
        target="_blank"
        rel="noopener noreferrer"
        className={`group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 transition-all duration-150 hover:-translate-y-0.5 ${s.ring} flex flex-col`}
        data-testid={testId}
      >
        <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${s.bg}`} />
        <div className="flex items-start justify-between gap-3">
          <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${s.bg} text-white`}>
            <Icon className="w-7 h-7" />
          </div>
          {eyebrow && (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded ${s.pill} font-mono text-[10px] uppercase tracking-[0.2em] font-bold`}>
              {eyebrow}
            </span>
          )}
        </div>
        <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
          {title}
        </h3>
        <p className="text-slate-600 text-sm sm:text-base mt-2 leading-relaxed">{desc}</p>
        {bullets && (
          <ul className="mt-4 space-y-1.5 text-xs sm:text-sm text-slate-700">
            {bullets.map((b) => (
              <li key={b} className="flex items-start gap-2">
                <span className={`mt-1.5 w-1 h-1 rounded-full ${s.bg} shrink-0`} />
                <span>{b}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-6 pt-5 border-t-2 border-slate-100 flex items-center justify-between">
          <span className={`font-mono text-xs uppercase tracking-[0.2em] font-bold ${accent === "slate" ? "text-slate-800" : accent === "amber" ? "text-amber-700" : accent === "emerald" ? "text-emerald-700" : "text-red-700"}`}>
            {t("Open in new tab ↗")}
          </span>
          <ArrowRight className={`w-5 h-5 transition-transform duration-150 group-hover:translate-x-1 ${accent === "slate" ? "text-slate-800" : accent === "amber" ? "text-amber-600" : accent === "emerald" ? "text-emerald-700" : "text-red-700"}`} />
        </div>
      </a>
    );
  }

  return (
    <Link
      to={to}
      className={`group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 transition-all duration-150 hover:-translate-y-0.5 ${s.ring} flex flex-col`}
      data-testid={testId}
    >
      <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${s.bg}`} />
      <div className="flex items-start justify-between gap-3">
        <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${s.bg} text-white`}>
          <Icon className="w-7 h-7" />
        </div>
        {eyebrow && (
          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded ${s.pill} font-mono text-[10px] uppercase tracking-[0.2em] font-bold`}>
            {eyebrow}
          </span>
        )}
      </div>
      <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
        {title}
      </h3>
      <p className="text-slate-600 text-sm sm:text-base mt-2 leading-relaxed">{desc}</p>
      {bullets && (
        <ul className="mt-4 space-y-1.5 text-xs sm:text-sm text-slate-700">
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-2">
              <span className={`mt-1.5 w-1 h-1 rounded-full ${s.bg} shrink-0`} />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-6 pt-5 border-t-2 border-slate-100 flex items-center justify-between">
        <span className={`font-mono text-xs uppercase tracking-[0.2em] font-bold ${accent === "slate" ? "text-slate-800" : accent === "amber" ? "text-amber-700" : accent === "emerald" ? "text-emerald-700" : "text-red-700"}`}>
          {external ? t("Open →") : t("Enter section →")}
        </span>
        <ArrowRight className={`w-5 h-5 transition-transform duration-150 group-hover:translate-x-1 ${accent === "slate" ? "text-slate-800" : accent === "amber" ? "text-amber-600" : accent === "emerald" ? "text-emerald-700" : "text-red-700"}`} />
      </div>
    </Link>
  );
};

/**
 * ProjectsCard — single Hub tile that links out to the two external project
 * apps the team actually uses. NOT clickable as a whole; user picks one of
 * the two stacked buttons (Basecamp or OnStation).
 */
const ProjectsCard = ({ t, testId }) => (
  <div
    className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 flex flex-col"
    data-testid={testId}
  >
    <div className="absolute top-0 left-0 right-0 h-1.5 rounded-t bg-emerald-700" />
    <div className="flex items-start justify-between gap-3">
      <div className="inline-flex items-center justify-center w-14 h-14 rounded-md bg-emerald-700 text-white">
        <Building2 className="w-7 h-7" />
      </div>
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-emerald-700 bg-emerald-50 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
        {t("Project Workspaces")}
      </span>
    </div>
    <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
      {t("Projects")}
    </h3>
    <p className="text-slate-600 text-sm sm:text-base mt-2 leading-relaxed">
      {t("Project messages, to-dos, schedules, docs, and field staking all live in our two external apps. Pick one:")}
    </p>

    <div className="grid sm:grid-cols-2 gap-2.5 mt-5">
      <a
        href="https://3.basecamp.com/5958093/projects"
        target="_blank"
        rel="noopener noreferrer"
        className="group/btn relative bg-emerald-700 hover:bg-emerald-800 text-white rounded-md p-3 sm:p-4 border-b-4 border-emerald-900 transition-colors flex items-center gap-3 min-w-0"
        data-testid="hub-projects-basecamp-btn"
      >
        <Building2 className="w-6 h-6 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-display text-lg sm:text-xl font-black leading-tight">Basecamp</div>
          <div className="text-[11px] font-mono uppercase tracking-wide opacity-80 truncate">
            {t("Messages · To-dos · Schedule · Docs")}
          </div>
        </div>
        <ArrowRight className="w-4 h-4 shrink-0 transition-transform group-hover/btn:translate-x-1" />
      </a>
      <a
        href="https://app.onstation.us/login"
        target="_blank"
        rel="noopener noreferrer"
        className="group/btn relative bg-blue-700 hover:bg-blue-800 text-white rounded-md p-3 sm:p-4 border-b-4 border-blue-900 transition-colors flex items-center gap-3 min-w-0"
        data-testid="hub-projects-onstation-btn"
      >
        <MapPin className="w-6 h-6 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-display text-lg sm:text-xl font-black leading-tight">OnStation</div>
          <div className="text-[11px] font-mono uppercase tracking-wide opacity-80 truncate">
            {t("Field staking · Station mapping · GPS")}
          </div>
        </div>
        <ArrowRight className="w-4 h-4 shrink-0 transition-transform group-hover/btn:translate-x-1" />
      </a>
    </div>

    <p className="text-[11px] text-slate-500 mt-4 leading-relaxed">
      {t("Both open in a new tab. Sign in with your Basecamp / OnStation credentials.")}
    </p>
  </div>
);

export default function Hub() {
  const { t, lang } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-5 sm:py-7 flex items-center justify-between">
          <MasciLogo variant="lockup" size="4xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="lockup" size="xl" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10 sm:mb-14">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            {t("MASCI Hub")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-2">
            {lang === "es" ? (
              <>
                {"Un solo lugar para cada trabajo de "}
                <span className="text-red-700">MASCI</span>
                <span className="text-red-700">.</span>
              </>
            ) : (
              <>
                {"One place for every "}
                <span className="text-red-700">MASCI</span>
                {" job"}
                <span className="text-red-700">.</span>
              </>
            )}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            {t("Safety forms, field reports, project workspaces, and the office console — all under one roof.")}
          </p>
          <div className="mt-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] flex-wrap">
            <span className="text-red-700 font-bold">{t("Accountability")}</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span className="text-red-700 font-bold">{t("Adapt")}</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span className="text-red-700 font-bold">{t("Overcome")}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6 mb-10">
          <SectionCard
            to="/field"
            icon={HardHat}
            eyebrow={t("Daily Ops")}
            title={t("Field")}
            desc={t("End-of-day reports and equipment walk-arounds for the crew on the ground.")}
            bullets={[
              t("Daily Reports — what the crew did today"),
              t("Equipment Pre-Op — OSHA walk-around with pass / fail"),
            ]}
            accent="amber"
            testId="hub-section-field"
          />
          <SectionCard
            to="/safety"
            icon={Shield}
            eyebrow={t("Compliance")}
            title={t("Safety")}
            desc={t("Inspections, toolbox talks, incident reports, JHAs, and trench-box guidance — if safety is on your mind, it lives here.")}
            bullets={[
              t("Site Inspections · Safety Meetings · Incidents"),
              t("Job Hazard Plans · Trench Box Reference"),
            ]}
            accent="red"
            testId="hub-section-safety"
          />
          <ProjectsCard
            t={t}
            testId="hub-section-projects"
          />
          <SectionCard
            icon={ClipboardCheck}
            title={t("QA / QC")}
            desc={t("Quality Assurance and Quality Control workflows for the field team — pour cards, density logs, and inspection forms ready to fill out and turn in. More forms rolling out soon.")}
            bullets={[
              t("Asphalt density · core samples · roadway reports"),
              t("Rebar inspections · concrete form inspections"),
              t("Daily QA / QC submittals · field-team turn-ins"),
            ]}
            accent="blue"
            testId="hub-section-qc"
            comingSoon
          />
          <SectionCard
            to="/pm/login"
            icon={ClipboardList}
            eyebrow={t("Project Management")}
            title={t("PM Portal")}
            desc={t("The day-to-day project-management workspace — every job, every record, every master list, in one place.")}
            bullets={[
              t("Active jobs · email routing · site posters"),
              t("Equipment fleet · employees · suppliers"),
            ]}
            accent="amber"
            testId="hub-section-pm"
            external
          />
          <SectionCard
            to="/shop/login"
            icon={Wrench}
            eyebrow={t("Mechanics & Shop")}
            title={t("Shop")}
            desc={t("The mechanic's console for the MASCI equipment fleet. Sign off failed Pre-Ops, clear units back to service, and stay on top of open items.")}
            bullets={[
              t("Open Out-of-Service · Needs-Attention queue"),
              t("Recent inspections · full equipment list"),
            ]}
            accent="amber"
            testId="hub-section-shop"
            external
          />
          <SectionCard
            to="/training"
            icon={GraduationCap}
            eyebrow={t("Training")}
            title={t("Training Hub")}
            desc={t("Short lessons, printable cheat sheets, and video walk-throughs for Field, Shop, PMs, and Admins. New hires up to speed in an afternoon.")}
            bullets={[
              t("Field Crew · Shop · PM · Admin tracks"),
              t("Written guides + video slots + print-friendly"),
            ]}
            accent="blue"
            testId="hub-section-training"
          />
          <SectionCard
            to="/admin/login"
            icon={ClipboardList}
            eyebrow={t("Office Console")}
            title={t("Admin")}
            desc={t("The full office console. Dashboards, master records, and the back-office tools for the whole platform.")}
            bullets={[
              t("Records · master lists · compliance exports"),
              t("Office staff only"),
            ]}
            accent="slate"
            testId="hub-section-admin"
            external
          />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 border-t-2 border-slate-200">
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          {t("MASCI · Operations Platform")}
        </span>
        <div className="flex items-center gap-3">
          <Link
            to="/cheatsheet"
            className="inline-flex items-center gap-2 h-10 px-3 rounded-md border-2 border-slate-300 text-slate-700 hover:border-red-700 hover:text-red-700 font-mono text-xs uppercase tracking-[0.2em] font-bold transition-colors"
            data-testid="hub-cheatsheet-link"
          >
            {t("Cheat Sheet")}
          </Link>
        </div>
      </footer>

      {/* Vendor-internal access — intentionally low-contrast and small.
          Links to The Judd Group LLC developer portal (Ops Manual). */}
      <div className="max-w-6xl mx-auto px-5 sm:px-8 pb-6 -mt-2 flex justify-center">
        <Link
          to="/dev/login"
          className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-300 hover:text-slate-500 transition-colors"
          data-testid="hub-dev-link"
        >
          Developer
        </Link>
      </div>
    </div>
  );
}
