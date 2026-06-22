// PromoHeroLoop.jsx — iter347 (Promo Asset Library · embed player)
//
// Optional homepage hero loop + click-to-open full film player.
// Strictly env-driven so it stays dark until MASCI is ready to publish:
//
//   REACT_APP_PROMO_HERO_LOOP_URL  · muted 8–12 sec autoplay loop
//   REACT_APP_PROMO_FULL_VIDEO_URL · full cinematic film (modal)
//   REACT_APP_PROMO_POSTER_URL     · poster image (mobile/JS-off fallback)
//
// If `REACT_APP_PROMO_HERO_LOOP_URL` is blank → component renders nothing.
// Safe to mount on Hub.jsx unconditionally — zero footprint until env
// is wired.
//
// Public-by-design:
//   - hero loop autoplays muted with `playsInline` (iOS-safe)
//   - click anywhere on the loop → opens modal with the full film
//   - modal closes on backdrop click / ESC / X
//   - keyboard accessible
//   - mobile-responsive (object-cover, no overflow)
//   - graceful fallback to poster if video fails
import React, { useEffect, useRef, useState } from "react";
import { Play, X } from "lucide-react";
import { useT } from "@/lib/i18n";
import { useBranding } from "@/lib/BrandingProvider";

const HERO_URL = process.env.REACT_APP_PROMO_HERO_LOOP_URL || "";
const FULL_URL = process.env.REACT_APP_PROMO_FULL_VIDEO_URL || "";
const POSTER_URL = process.env.REACT_APP_PROMO_POSTER_URL || "";

export function PromoHeroLoop({ className = "" }) {
  const { t } = useT();
  const branding = useBranding();
  const [open, setOpen] = useState(false);
  const heroRef = useRef(null);

  // Tap into muted-autoplay quirks: ensure the loop is actively trying
  // to play after mount (some browsers stall the first autoplay until
  // user interaction).
  useEffect(() => {
    const v = heroRef.current;
    if (!v) return;
    const p = v.play();
    if (p && typeof p.catch === "function") {
      p.catch(() => {
        // Autoplay blocked — the poster will be visible and the play
        // overlay click will recover playback.
      });
    }
  }, []);

  // ESC to close the modal.
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!HERO_URL) return null;

  return (
    <>
      <div
        className={`relative w-full bg-slate-900 overflow-hidden rounded-md cursor-pointer group ${className}`}
        onClick={() => FULL_URL && setOpen(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && FULL_URL) {
            e.preventDefault();
            setOpen(true);
          }
        }}
        data-testid="promo-hero-loop"
      >
        <video
          ref={heroRef}
          src={HERO_URL}
          poster={POSTER_URL || undefined}
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          className="w-full h-full object-cover aspect-video pointer-events-none"
          data-testid="promo-hero-loop-video"
        />
        {/* Calm overlay scrim + play hint */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
        {FULL_URL && (
          <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between gap-3 pointer-events-none">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-white/80">
                {branding.platform_display_name || t("MASCI Operations Platform")}
              </div>
              <div className="font-display text-base sm:text-lg font-black text-white leading-tight mt-1">
                {t("Watch The Platform In Action")}
              </div>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/90 text-slate-900 font-mono text-[10px] uppercase tracking-wider font-bold group-hover:bg-white transition-colors">
              <Play className="w-3 h-3" /> {t("Play")}
            </div>
          </div>
        )}
      </div>

      {open && FULL_URL && (
        <div
          className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 sm:p-8"
          onClick={() => setOpen(false)}
          data-testid="promo-hero-modal"
        >
          <div
            className="relative w-full max-w-5xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="absolute -top-10 right-0 text-white hover:text-slate-300 inline-flex items-center gap-1 font-mono text-xs uppercase tracking-wider"
              data-testid="promo-hero-modal-close"
              aria-label={t("Close")}
            >
              <X className="w-4 h-4" /> {t("Close")}
            </button>
            <video
              src={FULL_URL}
              poster={POSTER_URL || undefined}
              controls
              autoPlay
              playsInline
              className="w-full rounded-md bg-slate-900"
              data-testid="promo-hero-modal-video"
            />
          </div>
        </div>
      )}
    </>
  );
}

export default PromoHeroLoop;
