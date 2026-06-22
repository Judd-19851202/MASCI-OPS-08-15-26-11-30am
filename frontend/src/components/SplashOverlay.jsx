/**
 * SplashOverlay — one-time animated splash that runs on first cold load.
 *
 * Timeline (~1.7s total):
 *   0.0–0.5s : M-mark scales in from 60% → 100% (ease-out)
 *   0.4–0.8s : caution stripe slides in across the bottom
 *   0.6–1.1s : wordmark + tagline fade in below the M
 *   1.3–1.6s : overlay fades out (opacity 1 → 0)
 *   1.7s     : unmount
 *
 * Why not 5s? On mobile, 5s of a splash overlay feels like the app froze.
 * 1.7s is the standard "iOS app launch animation" feel — long enough to
 * register the brand, short enough that no one taps in frustration.
 *
 * Triggered ONCE per session (sessionStorage flag). Skipped if user has
 * already seen it during this browser session.
 */
import React, { useEffect, useState } from "react";
import { useBranding } from "@/lib/BrandingProvider";

const SEEN_KEY = "masci.splash.seen.2026";

export function SplashOverlay() {
  const branding = useBranding();
  const isMasci = !branding?.tenant_key || branding.tenant_key === "masci";
  const platformName = (branding.platform_display_name || "Operations Platform").toUpperCase();
  const tagline = isMasci
    ? "Run every job. Control every detail. Protect everything."
    : (branding.company_name ? `${branding.company_name} · Operations` : "Operations Platform");
  const logoSrc = isMasci ? "/icon-512.png" : (branding.logo_url || "");
  const primary = branding.primary_color || "#b91c1c";
  const monogramLetter = (branding.company_name || "C").trim().slice(0, 1).toUpperCase();

  const [visible, setVisible] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return !sessionStorage.getItem(SEEN_KEY);
    } catch {
      return false;
    }
  });
  const [fading, setFading] = useState(false);

  useEffect(() => {
    if (!visible) return undefined;
    try { sessionStorage.setItem(SEEN_KEY, "1"); } catch { /* noop */ }
    const fadeTimer = setTimeout(() => setFading(true), 1300);
    const doneTimer = setTimeout(() => setVisible(false), 1700);
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(doneTimer);
    };
  }, [visible]);

  if (!visible) return null;

  return (
    <div
      className={
        "fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900 " +
        "transition-opacity duration-[400ms] ease-out " +
        (fading ? "opacity-0 pointer-events-none" : "opacity-100")
      }
      data-testid="splash-overlay"
      aria-hidden="true"
    >
      {/* Subtle blueprint grid — purely decorative */}
      <div
        className="absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #60a5fa 1px, transparent 1px), " +
            "linear-gradient(to bottom, #60a5fa 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      {/* Center stack: tenant logo + platform name + tagline */}
      <div className="relative flex flex-col items-center px-6">
        {logoSrc ? (
          <img
            src={logoSrc}
            alt=""
            className="w-40 h-40 sm:w-48 sm:h-48 splash-m object-contain"
            draggable={false}
            data-testid="splash-logo"
            onError={(e) => { e.currentTarget.style.display = "none"; }}
          />
        ) : (
          <div
            className="w-40 h-40 sm:w-48 sm:h-48 splash-m rounded-2xl flex items-center justify-center font-display font-black text-white text-7xl sm:text-8xl"
            style={{ background: primary }}
            data-testid="splash-monogram"
          >
            {monogramLetter}
          </div>
        )}
        <div className="mt-6 sm:mt-8 splash-text">
          <h1 className="font-display text-2xl sm:text-3xl font-black text-white tracking-wider text-center">
            {platformName.replace(/ /g, "\u00a0")}
          </h1>
          <p className="mt-2 text-sm sm:text-base text-slate-300 text-center">
            {tagline}
          </p>
        </div>
      </div>

      {/* Caution-stripe band sliding across the bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-3 overflow-hidden">
        <div
          className="absolute inset-0 splash-stripe"
          style={{
            backgroundImage:
              `repeating-linear-gradient(135deg, ${primary} 0 18px, #0f172a 18px 36px)`,
          }}
        />
      </div>

      <style>{`
        @keyframes splash-m-in {
          0%   { transform: scale(0.6); opacity: 0; }
          60%  { transform: scale(1.04); opacity: 1; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes splash-text-in {
          0%   { transform: translateY(8px); opacity: 0; }
          100% { transform: translateY(0); opacity: 1; }
        }
        @keyframes splash-stripe-in {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(0); }
        }
        .splash-m     { animation: splash-m-in 0.55s ease-out both; }
        .splash-text  { animation: splash-text-in 0.50s ease-out both;
                        animation-delay: 0.55s; }
        .splash-stripe{ animation: splash-stripe-in 0.45s ease-out both;
                        animation-delay: 0.40s; }
      `}</style>
    </div>
  );
}

export default SplashOverlay;
