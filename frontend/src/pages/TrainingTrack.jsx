import React, { useEffect, useState } from "react";
import { useParams, Link, Navigate } from "react-router-dom";
import { ArrowLeft, Printer, ExternalLink, CheckCircle2, AlertCircle, FileDown } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { TRACKS, lessonsForTrack } from "@/data/training";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";

// Convert any common training-video URL into an embeddable iframe `src`.
// Supports: YouTube (watch?v=, youtu.be, /embed/), Loom (/share/), Vimeo
// (vimeo.com/123), Wistia. Falls back to the raw URL if we can't parse it
// (user can still click through).
function toEmbedUrl(raw) {
  if (!raw) return null;
  const url = raw.trim();
  try {
    // YouTube
    const yt = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{6,})/);
    if (yt) return { kind: "iframe", src: `https://www.youtube.com/embed/${yt[1]}` };
    // Loom
    const loom = url.match(/loom\.com\/(?:share|embed)\/([\w-]+)/);
    if (loom) return { kind: "iframe", src: `https://www.loom.com/embed/${loom[1]}` };
    // Vimeo
    const vim = url.match(/vimeo\.com\/(\d+)/);
    if (vim) return { kind: "iframe", src: `https://player.vimeo.com/video/${vim[1]}` };
    // Direct file — .mp4, .webm, .mov etc. → render with native <video>
    // so field crews get real playback controls + captions on mobile.
    if (/\.(mp4|webm|ogv|mov|m4v)(\?|$)/i.test(url)) {
      return { kind: "file", src: url };
    }
  } catch {
    /* noop */
  }
  return { kind: "iframe", src: url };
}

export default function TrainingTrack() {
  const { t, lang } = useT();
  const { track: trackSlug } = useParams();
  const track = TRACKS[trackSlug];
  const [videoMap, setVideoMap] = useState({});
  const [loadingVideos, setLoadingVideos] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await api.get("/training/videos");
        if (mounted) setVideoMap(res?.data?.videos || {});
      } catch {
        /* fall back to empty map */
      } finally {
        if (mounted) setLoadingVideos(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  if (!track) return <Navigate to="/training" replace />;

  // Gate non-public tracks
  const audience = track.audience;
  let allowed = true;
  if (audience === "admin") allowed = isAdmin();
  else if (audience === "pm") allowed = isAdmin() || isPm();
  else if (audience === "shop") allowed = isAdmin() || isShop();
  // field is public — no gate

  if (!allowed) {
    return <AccessDenied trackSlug={trackSlug} track={track} t={t} lang={lang} />;
  }

  // Per-lesson field picker — prefer *_es when the UI is Spanish and the
  // translation exists. Falls back to English seamlessly.
  const pick = (l, key) => {
    if (lang === "es" && l[`${key}_es`] != null) return l[`${key}_es`];
    return l[key];
  };

  const lessons = lessonsForTrack(trackSlug);
  const title = lang === "es" && track.title_es ? track.title_es : track.title;
  const blurb = lang === "es" && track.blurb_es ? track.blurb_es : track.blurb;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe print:hidden" />
      <header className="bg-slate-900 border-b-4 border-red-700 print:hidden">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/training"
            className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide"
            data-testid="training-back-all"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("All Tracks")}
          </Link>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-8 sm:mb-10 print:mb-4">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            {t("Training Track")}
          </span>
          <h1 className="font-display text-3xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2">
            {title}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 leading-relaxed max-w-2xl">
            {blurb}
          </p>
          <div className="mt-4 flex items-center gap-2 text-xs text-slate-500 font-mono uppercase tracking-[0.2em] print:hidden flex-wrap">
            <span>{lessons.length} {t("lessons")}</span>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-slate-300 text-slate-700 hover:border-red-700 hover:text-red-700 font-bold transition-colors"
              data-testid="training-print-all"
            >
              <Printer className="w-3.5 h-3.5" /> {t("Print all cheat sheets")}
            </button>
            <a
              href={track.audience === "public"
                ? `${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${track.slug}&lang=en`
                : `/training/${track.slug}/packet?lang=en`}
              target={track.audience === "public" ? "_blank" : undefined}
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-slate-300 text-slate-700 hover:border-red-700 hover:text-red-700 font-bold transition-colors"
              data-testid={`training-pdf-${track.slug}-en`}
            >
              <FileDown className="w-3.5 h-3.5" /> PDF · EN
            </a>
            <a
              href={track.audience === "public"
                ? `${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${track.slug}&lang=es`
                : `/training/${track.slug}/packet?lang=es`}
              target={track.audience === "public" ? "_blank" : undefined}
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-slate-300 text-slate-700 hover:border-red-700 hover:text-red-700 font-bold transition-colors"
              data-testid={`training-pdf-${track.slug}-es`}
            >
              <FileDown className="w-3.5 h-3.5" /> PDF · ES
            </a>
            <a
              href={track.audience === "public"
                ? `${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${track.slug}&lang=bi`
                : `/training/${track.slug}/packet?lang=bi`}
              target={track.audience === "public" ? "_blank" : undefined}
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-red-700 bg-red-700 text-white hover:bg-red-800 hover:border-red-800 font-bold transition-colors"
              data-testid={`training-pdf-${track.slug}-bi`}
            >
              <FileDown className="w-3.5 h-3.5" /> PDF · EN + ES
            </a>
          </div>
        </div>

        <div className="space-y-6 sm:space-y-8">
          {lessons.map((l) => (
            <LessonCard
              key={l.slug}
              lesson={l}
              videoUrl={videoMap[l.slug]}
              loadingVideo={loadingVideos}
              t={t}
              pick={pick}
            />
          ))}
        </div>
      </main>
    </div>
  );
}

function AccessDenied({ track, t, lang }) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link to="/training" className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide">
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("All Tracks")}
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center px-5 py-12">
        <div className="max-w-md w-full bg-white border-2 border-slate-300 rounded-md p-8 text-center">
          <AlertCircle className="w-10 h-10 text-amber-600 mx-auto mb-3" />
          <h2 className="font-display text-2xl font-black text-slate-900">
            {t("This track is password-protected")}
          </h2>
          <p className="text-slate-600 text-sm mt-3">
            {lang === "es"
              ? `Inicie sesión como ${track.audience === "admin" ? "Administrador" : track.audience === "pm" ? "Gerente de Proyecto" : "Taller"} para ver esta capacitación.`
              : `Sign in as ${track.audience === "admin" ? "Admin" : track.audience === "pm" ? "Project Manager" : "Shop"} to view this training.`}
          </p>
          <div className="mt-6 flex flex-col gap-2">
            <Link
              to={track.audience === "admin" ? "/admin/login" : track.audience === "pm" ? "/pm/login" : "/shop/login"}
              className="inline-flex items-center justify-center h-11 rounded-md bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
            >
              {t("Sign In")}
            </Link>
            <Link
              to="/training"
              className="inline-flex items-center justify-center h-11 rounded-md border-2 border-slate-300 text-slate-700 hover:border-slate-500 font-bold uppercase tracking-wide text-sm"
            >
              {t("Back to Training Hub")}
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

function LessonCard({ lesson, videoUrl, loadingVideo, t, pick }) {
  const embedSrc = toEmbedUrl(videoUrl);
  const title = pick(lesson, "title");
  const why = pick(lesson, "why");
  const steps = pick(lesson, "steps") || [];
  const tips = pick(lesson, "tips") || [];
  const cheatSheet = pick(lesson, "cheatSheet") || [];
  return (
    <article
      className="bg-white border-2 border-slate-300 rounded-md overflow-hidden print:break-inside-avoid print:border-slate-400"
      data-testid={`lesson-${lesson.slug}`}
    >
      <div className="px-5 sm:px-7 pt-5 sm:pt-7 pb-3">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 flex-1">
            {title}
          </h2>
          {lesson.duration && (
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold shrink-0">
              {lesson.duration}
            </span>
          )}
        </div>
      </div>

      {/* Video embed slot — shown above the walk-through when a URL is saved.
          MP4 URLs use native <video> so field crews get proper mobile
          playback controls; YouTube / Loom / Vimeo URLs use an iframe. */}
      <div className="px-5 sm:px-7 print:hidden">
        {loadingVideo ? null : embedSrc ? (
          <div className="relative w-full rounded-md overflow-hidden border-2 border-slate-200 bg-black" style={{ paddingBottom: "56.25%" }}>
            {embedSrc.kind === "file" ? (
              <video
                src={embedSrc.src}
                className="absolute inset-0 w-full h-full"
                controls
                playsInline
                preload="metadata"
                data-testid="lesson-video-file"
              />
            ) : (
              <iframe
                src={embedSrc.src}
                title={title}
                className="absolute inset-0 w-full h-full"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                data-testid="lesson-video-iframe"
              />
            )}
          </div>
        ) : (
          <div className="rounded-md border-2 border-dashed border-slate-300 bg-slate-50 p-4 text-center text-xs text-slate-500 font-mono uppercase tracking-[0.15em]">
            {t("Video tutorial coming soon")}
          </div>
        )}
      </div>

      <div className="px-5 sm:px-7 py-5 sm:py-6 space-y-5">
        <div className="rounded-md border-l-4 border-red-700 bg-red-50 px-4 py-3">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold mb-1">
            {t("Why this matters")}
          </div>
          <p className="text-slate-800 text-sm leading-relaxed">{why}</p>
        </div>

        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold mb-2">
            {t("Step-by-step")}
          </div>
          <ol className="space-y-2.5">
            {steps.map((step, i) => (
              <li key={i} className="flex gap-3">
                <span className="shrink-0 inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-900 text-white text-xs font-bold font-mono">
                  {i + 1}
                </span>
                <span className="text-slate-800 text-sm leading-relaxed flex-1 pt-0.5">
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </div>

        {tips.length > 0 && (
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-emerald-700 font-bold mb-2">
              {t("Tips")}
            </div>
            <ul className="space-y-1.5">
              {tips.map((tip, i) => (
                <li key={i} className="flex gap-2 text-sm text-slate-700">
                  <span className="shrink-0 text-emerald-700 mt-0.5">✓</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {cheatSheet.length > 0 && (
          <div className="rounded-md bg-slate-900 text-white px-4 py-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-400 font-bold mb-2">
              {t("Cheat Sheet")}
            </div>
            <ul className="space-y-1">
              {cheatSheet.map((b, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="px-5 sm:px-7 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-2 print:hidden">
        {videoUrl && (
          <a
            href={videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-[0.2em] font-bold text-slate-700 hover:text-red-700"
          >
            <ExternalLink className="w-3.5 h-3.5" /> {t("Open video")}
          </a>
        )}
      </div>
    </article>
  );
}
