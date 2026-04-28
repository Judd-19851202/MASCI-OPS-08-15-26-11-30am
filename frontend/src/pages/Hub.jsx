import React from "react";
import { Link } from "react-router-dom";
import {
  HardHat,
  ClipboardList,
  Building2,
  Shield,
  ArrowRight,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";

/**
 * MASCI Hub — top-level landing page.
 *
 * The app started as a Safety Hub and has grown into the full MASCI
 * operations platform. Four sections:
 *
 *   🦺 Safety   — compliance forms (inspections, meetings, incidents, JHA, trench)
 *   👷 Field    — daily operational logs (daily reports, equipment pre-op)
 *   🏗️ Projects — Crew Hub (Basecamp-style project collaboration)
 *   🗄️ Admin    — office console (dashboards, exports, backups, routing)
 *
 * Each section leads to its own landing so the user always feels they're in
 * the "right neighborhood" for what they're doing.
 */

const SectionCard = ({ to, icon: Icon, eyebrow, title, desc, bullets, accent, testId, external }) => {
  // accent classes kept static so Tailwind keeps them in the build
  const styles = {
    red:   { bg: "bg-red-700",   bar: "border-red-700",   ring: "hover:border-red-700",   pill: "text-red-700 bg-red-50" },
    amber: { bg: "bg-amber-600", bar: "border-amber-600", ring: "hover:border-amber-600", pill: "text-amber-700 bg-amber-50" },
    slate: { bg: "bg-slate-900", bar: "border-slate-900", ring: "hover:border-slate-900", pill: "text-slate-800 bg-slate-100" },
    emerald:{ bg: "bg-emerald-700", bar: "border-emerald-700", ring: "hover:border-emerald-700", pill: "text-emerald-700 bg-emerald-50" },
  };
  const s = styles[accent] || styles.red;
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
          {external ? "Open →" : "Enter section →"}
        </span>
        <ArrowRight className={`w-5 h-5 transition-transform duration-150 group-hover:translate-x-1 ${accent === "slate" ? "text-slate-800" : accent === "amber" ? "text-amber-600" : accent === "emerald" ? "text-emerald-700" : "text-red-700"}`} />
      </div>
    </Link>
  );
};

export default function Hub() {
  const { t } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="2xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" homeLink="/" />
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
            {t("One place for every MASCI job.")}
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
            to="/safety"
            icon={Shield}
            eyebrow="Compliance"
            title={t("Safety")}
            desc={t("Every inspection, meeting, incident, JHA, and trench-box record in one place.")}
            bullets={[
              t("Site Inspections · Safety Meetings"),
              t("Incident Reports · JHA Plans · Trench Box Data"),
            ]}
            accent="red"
            testId="hub-section-safety"
          />
          <SectionCard
            to="/field"
            icon={HardHat}
            eyebrow="Daily Ops"
            title={t("Field")}
            desc={t("End-of-shift logs and pre-operational equipment checks for crews on the ground.")}
            bullets={[
              t("Daily Reports — crews, subs, visitors, equipment, materials"),
              t("Equipment Pre-Op — OSHA walk-arounds with pass/fail"),
            ]}
            accent="amber"
            testId="hub-section-field"
          />
          <SectionCard
            to="/app"
            icon={Building2}
            eyebrow="Project Workspaces"
            title={t("Projects")}
            desc={t("Project-by-project message boards, to-dos, schedules, docs, and hill charts. Sign in required.")}
            bullets={[
              t("Crew Hub — Basecamp-style per-job collaboration"),
              t("@mentions · My Stuff inbox · Activity feed"),
            ]}
            accent="emerald"
            testId="hub-section-projects"
            external
          />
          <SectionCard
            to="/admin/login"
            icon={ClipboardList}
            eyebrow="Office Console"
            title={t("Admin")}
            desc={t("Dashboards, PDF exports, compliance CSVs, PM email routing, full backups & restore.")}
            bullets={[
              t("Password-gated · view / print / delete any record"),
              t("Backup · Restore · Auto-email routing · Posters"),
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
    </div>
  );
}
