import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  GraduationCap,
  HardHat,
  Wrench,
  Briefcase,
  ShieldCheck,
  FileDown,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { TRACKS, lessonsForTrack } from "@/data/training";

const ICONS = { HardHat, Wrench, Briefcase, ShieldCheck };

const ACCENTS = {
  amber: "border-amber-600 hover:border-amber-700 bg-amber-600",
  red: "border-red-700 hover:border-red-800 bg-red-700",
  slate: "border-slate-900 hover:border-slate-950 bg-slate-900",
  emerald: "border-emerald-700 hover:border-emerald-800 bg-emerald-700",
};

export default function TrainingHub() {
  const { t, lang } = useT();

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide"
            data-testid="training-back-hub"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Hub")}
          </Link>
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10 sm:mb-14 max-w-3xl">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold flex items-center gap-2">
            <GraduationCap className="w-4 h-4" /> {t("MASCI Training")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-3">
            {lang === "es" ? (
              <>
                {"Aprenda el Hub en "}
                <span className="text-red-700">minutos</span>
                {", no días."}
              </>
            ) : (
              <>
                {"Learn the Hub in "}
                <span className="text-red-700">minutes</span>
                {", not days."}
              </>
            )}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-4 leading-relaxed">
            {t("Short, focused lessons for every role — Field Crews, Shop, Project Managers, and Admins. Written walk-throughs, printable cheat sheets, and video tutorials. Pick your track.")}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6 mb-10">
          {Object.values(TRACKS).map((track) => {
            const Icon = ICONS[track.icon] || GraduationCap;
            const lessons = lessonsForTrack(track.slug);
            const accent = ACCENTS[track.accent] || ACCENTS.red;
            return (
              <Link
                key={track.slug}
                to={`/training/${track.slug}`}
                className={`group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 transition-all duration-150 hover:-translate-y-0.5 ${accent.split(" ")[1]} flex flex-col`}
                data-testid={`training-track-${track.slug}`}
              >
                <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${accent.split(" ")[2]}`} />
                <div className="flex items-start justify-between gap-3">
                  <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accent.split(" ")[2]} text-white`}>
                    <Icon className="w-7 h-7" />
                  </div>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-100 text-slate-700 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
                    {lessons.length} {t("lessons")}
                  </span>
                </div>
                <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
                  {lang === "es" && track.title_es ? track.title_es : track.title}
                </h3>
                <p className="text-slate-600 text-sm sm:text-base mt-2 leading-relaxed">
                  {lang === "es" && track.blurb_es ? track.blurb_es : track.blurb}
                </p>
                <ul className="mt-4 space-y-1 text-xs sm:text-sm text-slate-700">
                  {lessons.slice(0, 3).map((l) => (
                    <li key={l.slug} className="flex items-start gap-2">
                      <span className={`mt-1.5 w-1 h-1 rounded-full ${accent.split(" ")[2]} shrink-0`} />
                      <span>{l.title.replace(/^Lesson \d+ — /, "")}</span>
                    </li>
                  ))}
                  {lessons.length > 3 && (
                    <li className="text-slate-400 text-xs pl-3 italic">
                      + {lessons.length - 3} {t("more…")}
                    </li>
                  )}
                </ul>
                <div className="mt-6 pt-5 border-t-2 border-slate-100 flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold text-slate-700">
                    {t("Open track →")}
                  </span>
                  <ArrowRight className="w-5 h-5 text-slate-700 transition-transform duration-150 group-hover:translate-x-1" />
                </div>
              </Link>
            );
          })}
        </div>

        <div className="rounded-md border-2 border-slate-200 bg-slate-50 p-5 sm:p-6 text-sm text-slate-700 leading-relaxed">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold mb-2">
            {t("Admin note")}
          </div>
          <p>
            {t("Shop / PM / Admin tracks require their respective passwords. The Field Crew track is public — no login needed. Each lesson has a video slot; admins can paste YouTube / Loom / Vimeo URLs via the Admin console → Training Videos panel.")}
          </p>
        </div>

        <div className="mt-6 rounded-md border-2 border-slate-900 bg-slate-900 text-white p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-400 font-bold mb-1 flex items-center gap-2">
                <FileDown className="w-3.5 h-3.5" /> {t("Downloadable packets")}
              </div>
              <h3 className="font-display text-lg font-black text-white">
                {t("PDF training packets · no login required")}
              </h3>
              <p className="text-slate-300 text-sm mt-1 leading-relaxed max-w-2xl">
                {t("Share these links with insurance, auditors, or new-hire onboarding. Cover, table of contents, and every lesson in one file — in English or Spanish.")}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 mt-4">
            {Object.values(TRACKS).map((tr) => (
              <div key={tr.slug} className="bg-slate-800 rounded p-3 flex items-center justify-between gap-2 text-xs">
                <span className="font-bold truncate">{lang === "es" && tr.title_es ? tr.title_es : tr.title}</span>
                <div className="flex gap-1 shrink-0">
                  <a
                    href={`${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${tr.slug}&lang=en`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-amber-500 hover:text-slate-900 font-mono font-bold uppercase tracking-wide transition-colors"
                    data-testid={`training-landing-pdf-${tr.slug}-en`}
                  >
                    EN
                  </a>
                  <a
                    href={`${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${tr.slug}&lang=es`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-amber-500 hover:text-slate-900 font-mono font-bold uppercase tracking-wide transition-colors"
                    data-testid={`training-landing-pdf-${tr.slug}-es`}
                  >
                    ES
                  </a>
                  <a
                    href={`${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${tr.slug}&lang=bi`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-700 hover:bg-red-600 font-mono font-bold uppercase tracking-wide transition-colors"
                    data-testid={`training-landing-pdf-${tr.slug}-bi`}
                    title="Bilingual · side-by-side"
                  >
                    EN+ES
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
