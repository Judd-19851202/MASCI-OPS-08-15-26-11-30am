import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  GraduationCap,
  HardHat,
  Wrench,
  Briefcase,
  ShieldCheck,
  FileDown,
  UserPlus,
  Printer,
  QrCode,
  Lock,
  BookOpen,
  ChevronRight,
} from "lucide-react";
import { PortalShell } from "@/design-system";
import { renderAdminRouteSideNav } from "@/components/admin/AdminRouteShell";
import { useT } from "@/lib/i18n";
import { TRACKS, lessonsForTrack } from "@/data/training";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import { isHr } from "@/lib/hrAuth";

const ICONS = { HardHat, Wrench, Briefcase, ShieldCheck };

const ACCENTS = {
  amber: "border-amber-600 hover:border-amber-700 bg-amber-600",
  red: "border-red-700 hover:border-red-800 bg-red-700",
  slate: "border-slate-700 hover:border-slate-800 bg-slate-700",
  orange: "border-orange-600 hover:border-orange-700 bg-orange-600",
  purple: "border-purple-700 hover:border-purple-800 bg-purple-700",
  lime: "border-lime-600 hover:border-lime-700 bg-lime-600",
  emerald: "border-emerald-700 hover:border-emerald-800 bg-emerald-700",
};

// Tracks are gated by the same passwords as the rest of the app. Labor
// crews have no business reading the PM/Admin workflows — this function
// returns whether the current user is allowed to see the preview of a
// given track's lessons. `track.audience === "public"` (the Field track)
// is always visible. Shop requires Shop/PM/Admin. PM requires PM/Admin.
// Admin requires Admin.
function trackUnlocked(track) {
  if (!track) return false;
  if (track.audience === "public") return true;
  if (isAdmin()) return true;
  if (track.audience === "pm") return isPm();
  if (track.audience === "shop") return isShop() || isPm();
  if (track.audience === "leadership") return isLeadershipAuthed();
  if (track.audience === "hr") return isHr();
  return false;
}

function loginPathFor(audience) {
  if (audience === "admin") return "/admin/login";
  if (audience === "pm") return "/pm/login";
  if (audience === "shop") return "/shop/login";
  if (audience === "leadership") return "/leadership";
  if (audience === "hr") return "/hr/login";
  return "/";
}

function loginLabelFor(audience, lang) {
  const en = { admin: "Admin", pm: "Project Manager", shop: "Shop", leadership: "Field Leadership", hr: "HR Manager" };
  const es = { admin: "Administrador", pm: "Gerente de Proyecto", shop: "Taller", leadership: "Liderazgo de Campo", hr: "Gerente RRHH" };
  return (lang === "es" ? es : en)[audience] || audience;
}

export default function TrainingHub() {
  const { t, lang } = useT();

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Admin · Training"
      pageTitle={t("MASCI Training")}
      subtitle={t("Learn the Hub in minutes, not days.")}
      sideNav={renderAdminRouteSideNav()}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-6 sm:py-8" data-testid="training-hub-page">
        <section className="wp17-mission-banner mb-8" data-testid="training-hub-mission-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">Portal mission</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">Teach the platform once so every operator understands the next task everywhere.</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                Training, guides, and packets now live in one shared system and route users to the right role-specific material without feeling like a separate site.
              </p>
            </div>
          </div>
        </section>

        <div className="mb-10 max-w-3xl">
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
            {t("Short, focused lessons for every role — field crews, shop, project managers, and admins. Use written walk-throughs, printable cheat sheets, and video tutorials to get the job done faster.")}
          </p>

          {/* iter190 — Operational Guidance Center entry banner.
              Wraps and absorbs this Training Hub without breaking
              existing role-track URLs (/training/<slug> still works). */}
          <Link
            to="/guidance"
            className="mt-5 flex items-center gap-3 bg-amber-50 border border-amber-300 border-l-4 border-l-amber-600 rounded-md p-4 hover:bg-amber-100 hover:border-l-amber-700 transition-colors group"
            data-testid="training-hub-guidance-banner"
          >
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white shrink-0">
              <BookOpen className="w-6 h-6" />
            </div>
            <div className="flex-1 text-left">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-700 font-bold">
                {t("Operational Guidance Center")}
              </div>
              <div className="font-display text-lg font-black text-slate-900">
                {t("How to run MASCI operations")}
              </div>
              <div className="text-[13px] text-slate-600 mt-0.5">
                {t("Role-based training, task-based help, and troubleshooting. Filtered to your portal access.")}
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-amber-700 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6 mb-10">
          {Object.values(TRACKS).map((track) => {
            const Icon = ICONS[track.icon] || GraduationCap;
            const lessons = lessonsForTrack(track.slug);
            const accent = ACCENTS[track.accent] || ACCENTS.red;
            const unlocked = trackUnlocked(track);
            const destination = unlocked
              ? `/training/${track.slug}`
              : loginPathFor(track.audience);
            return (
              <Link
                key={track.slug}
                to={destination}
                state={unlocked ? undefined : { from: `/training/${track.slug}` }}
                className={`group relative bg-white border border-slate-200 rounded-md p-6 sm:p-8 transition-all duration-150 hover:-translate-y-0.5 ${accent.split(" ")[1]} flex flex-col`}
                data-testid={`training-track-${track.slug}`}
              >
                <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${accent.split(" ")[2]}`} />
                <div className="flex items-start justify-between gap-3">
                  <div className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accent.split(" ")[2]} text-white`}>
                    <Icon className="w-7 h-7" />
                  </div>
                  {unlocked ? (
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-100 text-slate-700 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
                      {lessons.length} {t("lessons")}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-amber-100 text-amber-800 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
                      <Lock className="w-3 h-3" /> {t("Password required")}
                    </span>
                  )}
                </div>
                <h3 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-4">
                  {lang === "es" && track.title_es ? track.title_es : track.title}
                </h3>

                {unlocked ? (
                  <>
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
                  </>
                ) : (
                  <p className="text-slate-500 text-sm mt-3 leading-relaxed italic">
                    {t("This track is for office teams. Sign in as")}{" "}
                    <strong className="not-italic text-slate-700">
                      {loginLabelFor(track.audience, lang)}
                    </strong>{" "}
                    {t("to see the lessons and packets.")}
                  </p>
                )}
                <div className="mt-6 pt-5 border-t-2 border-slate-100 flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold text-slate-700">
                    {unlocked ? t("Open track →") : t("Sign in →")}
                  </span>
                  {unlocked ? (
                    <ArrowRight className="w-5 h-5 text-slate-700 transition-transform duration-150 group-hover:translate-x-1" />
                  ) : (
                    <Lock className="w-5 h-5 text-amber-700" />
                  )}
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-6 rounded-md border-2 border-slate-900 bg-slate-900 text-white p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-400 font-bold mb-1 flex items-center gap-2">
                <FileDown className="w-3.5 h-3.5" /> {t("Downloadable packets")}
              </div>
              <h3 className="font-display text-lg font-black text-white">
                {t("PDF training packets")}
              </h3>
              <p className="text-slate-300 text-sm mt-1 leading-relaxed max-w-2xl">
                {t("The Field Crew packet is public for onboarding and outside partners. Shop, PM, and admin packets stay behind the matching sign-in.")}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-2 mt-4 max-w-md">
            {Object.values(TRACKS).filter((tr) => tr.audience === "public").map((tr) => {
              const isPublic = tr.audience === "public";
              const unlocked = trackUnlocked(tr);
              // For PUBLIC tracks the buttons hit the PDF endpoint directly
              // (anyone can pull). For GATED tracks they ALWAYS go through
              // the auth-aware route — even when an admin is currently
              // logged in — so the lock icon and the "Sign-in required"
              // chip stay visible regardless of session state. (Otherwise
              // admins testing the page see all 4 rows identical and
              // think the gating is broken.)
              const link = (lng) =>
                isPublic
                  ? `${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${tr.slug}&lang=${lng}`
                  : `/training/${tr.slug}/packet?lang=${lng}`;
              const target = isPublic ? "_blank" : undefined;
              const tierLabel = isPublic
                ? t("Public")
                : tr.audience === "shop"
                ? t("Shop sign-in")
                : tr.audience === "pm"
                ? t("PM sign-in")
                : t("Admin sign-in");
              return (
                <div key={tr.slug} className="bg-slate-800 rounded p-3 flex flex-col gap-2 text-xs" data-testid={`training-landing-tile-${tr.slug}`}>
                  <div className="flex items-center justify-between gap-2 min-w-0">
                    <span className="font-bold truncate flex items-center gap-1.5 min-w-0">
                      {!isPublic && <Lock className="w-3 h-3 text-amber-400 shrink-0" />}
                      <span className="truncate">{lang === "es" && tr.title_es ? tr.title_es : tr.title}</span>
                    </span>
                    <span
                      className={`shrink-0 inline-flex items-center px-1.5 py-0.5 rounded font-mono text-[9px] tracking-[0.15em] uppercase ${
                        isPublic
                          ? "bg-emerald-700/30 text-emerald-300 border border-emerald-700/40"
                          : unlocked
                          ? "bg-amber-700/30 text-amber-300 border border-amber-700/40"
                          : "bg-slate-700 text-slate-300 border border-slate-600"
                      }`}
                      data-testid={`training-landing-tier-${tr.slug}`}
                    >
                      {tierLabel}
                    </span>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <a
                      href={link("en")}
                      target={target}
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-amber-500 hover:text-slate-900 font-mono font-bold uppercase tracking-wide transition-colors"
                      data-testid={`training-landing-pdf-${tr.slug}-en`}
                    >
                      EN
                    </a>
                    <a
                      href={link("es")}
                      target={target}
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-amber-500 hover:text-slate-900 font-mono font-bold uppercase tracking-wide transition-colors"
                      data-testid={`training-landing-pdf-${tr.slug}-es`}
                    >
                      ES
                    </a>
                    <a
                      href={link("bi")}
                      target={target}
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-700 hover:bg-red-600 font-mono font-bold uppercase tracking-wide transition-colors"
                      data-testid={`training-landing-pdf-${tr.slug}-bi`}
                      title="Bilingual · side-by-side"
                    >
                      EN+ES
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Scan-&-Go QR Posters — one per track, prints a 1-page letter
            poster with 3 QR codes (EN / ES / EN+ES) so crews can scan
            straight into the packet from the job trailer. */}
        <div className="mt-6 rounded-md border-2 border-amber-600 bg-amber-50 p-5 sm:p-6">
          <div className="flex items-start gap-4 flex-wrap">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white shrink-0">
              <QrCode className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-bold flex items-center gap-2">
                {t("Scan-&-Go Posters")}
              </div>
              <h3 className="font-display text-lg font-black text-slate-900 mt-1">
                {t("1-page QR poster per track · tape in every trailer")}
              </h3>
              <p className="text-slate-700 text-sm mt-1 leading-relaxed">
                {t("Three QR codes per poster — EN, ES, and EN+ES side-by-side. Print, tape, done. No typing URLs on phones.")}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-2 mt-4 max-w-md">
            {Object.values(TRACKS).filter((tr) => tr.audience === "public").map((tr) => {
              const isPublic = tr.audience === "public";
              const unlocked = trackUnlocked(tr);
              const viewPath = unlocked
                ? `/training/${tr.slug}/poster`
                : loginPathFor(tr.audience);
              const printPath = unlocked
                ? `/training/${tr.slug}/poster?autoprint=1`
                : loginPathFor(tr.audience);
              const linkState = unlocked
                ? undefined
                : { from: `/training/${tr.slug}/poster` };
              const tierLabel = isPublic
                ? t("Public")
                : tr.audience === "shop"
                ? t("Shop sign-in")
                : tr.audience === "pm"
                ? t("PM sign-in")
                : t("Admin sign-in");
              return (
                <div key={tr.slug} className="bg-white border-2 border-amber-600 rounded p-3 flex flex-col gap-2 text-xs" data-testid={`training-qr-tile-${tr.slug}`}>
                  <div className="flex items-center justify-between gap-2 min-w-0">
                    <span className="font-bold truncate text-slate-900 flex items-center gap-1.5 min-w-0">
                      {!isPublic && <Lock className="w-3 h-3 text-amber-700 shrink-0" />}
                      <span className="truncate">{lang === "es" && tr.title_es ? tr.title_es : tr.title}</span>
                    </span>
                    <span
                      className={`shrink-0 inline-flex items-center px-1.5 py-0.5 rounded font-mono text-[9px] tracking-[0.15em] uppercase border ${
                        isPublic
                          ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                          : "bg-amber-100 text-amber-800 border-amber-300"
                      }`}
                      data-testid={`training-qr-tier-${tr.slug}`}
                    >
                      {tierLabel}
                    </span>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <Link
                      to={viewPath}
                      state={linkState}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-white font-mono font-bold uppercase tracking-wide transition-colors"
                      data-testid={`training-qr-poster-${tr.slug}`}
                    >
                      {unlocked ? t("View") : t("Sign In")}
                    </Link>
                    {unlocked && (
                      <Link
                        to={printPath}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white font-mono font-bold uppercase tracking-wide transition-colors"
                        data-testid={`training-qr-poster-print-${tr.slug}`}
                      >
                        <Printer className="w-3 h-3" />
                        {t("Print")}
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* New Hire Onboarding — coming-soon placeholder so the team knows
            it's on the roadmap and can pressure-test the concept. */}
        <div className="mt-6 rounded-md border-2 border-dashed border-slate-400 bg-slate-50 p-5 sm:p-6">
          <div className="flex items-start gap-4 flex-wrap">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-300 text-slate-700 shrink-0">
              <UserPlus className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold flex items-center gap-2">
                {t("Coming soon")}
              </div>
              <h3 className="font-display text-lg font-black text-slate-700 mt-1">
                {t("New Hire Onboarding")}
              </h3>
              <p className="text-slate-600 text-sm mt-1 leading-relaxed max-w-2xl">
                {t("A guided first-day checklist for every new MASCI hire: watch the core Field lessons, take a short quiz, sign an acknowledgement, and you're cleared for the site. HR gets a paper trail, the new hire gets confidence, insurance gets peace of mind.")}
              </p>
              <ul className="mt-3 space-y-1 text-xs text-slate-600">
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                  {t("Required lesson tracking per employee")}
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                  {t("5-question quiz + pass/fail threshold")}
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                  {t("Digital signed acknowledgement stored on the employee record")}
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1.5 w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                  {t("Admin dashboard: who's onboarded, who's outstanding, who's expired")}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
