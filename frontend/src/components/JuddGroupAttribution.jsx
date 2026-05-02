import React from "react";
import { Link } from "react-router-dom";
import juddLogo from "@/assets/judd-group-logo.png";

/**
 * JuddGroupAttribution — three render modes for developer credit.
 *
 * MASCI HUB is owned and operated by MASCI. The Judd Group LLC is the
 * development contractor only. These renders give Judd Group a clean
 * developer credit without implying ownership, partnership, or
 * subsidiary status of any kind.
 *
 *   • global   — every-page footer: © MASCI · Developed by The Judd Group LLC
 *   • login    — "Developed by [logo] The Judd Group LLC" under login form
 *   • admin    — slightly larger logo + maintenance line, admin pages only
 *
 * Field-crew pages get ONLY the `global` variant. MASCI branding stays
 * dominant. Logo never appears on safety/field/shop forms.
 */

const YEAR = new Date().getFullYear();

export function JuddGroupAttribution({ variant = "global", className = "" }) {
  if (variant === "login") {
    return (
      <div
        className={`flex items-center justify-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 ${className}`}
        data-testid="judd-attr-login"
      >
        <span>Developed by</span>
        <img
          src={juddLogo}
          alt="The Judd Group"
          className="h-5 w-auto opacity-80"
        />
        <span className="hidden sm:inline">The Judd Group LLC</span>
      </div>
    );
  }

  if (variant === "admin") {
    return (
      <div
        className={`flex flex-col sm:flex-row items-center justify-center gap-3 ${className}`}
        data-testid="judd-attr-admin"
      >
        <img
          src={juddLogo}
          alt="The Judd Group"
          className="h-8 w-auto opacity-90"
        />
        <div className="text-center sm:text-left">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
            Platform Developed &amp; Maintained
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
            By The Judd Group LLC
          </div>
        </div>
      </div>
    );
  }

  // global — text-only, all pages
  return (
    <div
      className={`text-center font-mono text-[9px] uppercase tracking-[0.2em] text-slate-400 ${className}`}
      data-testid="judd-attr-global"
    >
      © {YEAR} MASCI · Platform developed by The Judd Group LLC ·{" "}
      <Link
        to="/legal/terms"
        className="hover:text-slate-700 underline-offset-2 hover:underline"
      >
        Terms
      </Link>{" "}
      ·{" "}
      <Link
        to="/legal/privacy"
        className="hover:text-slate-700 underline-offset-2 hover:underline"
      >
        Privacy
      </Link>
    </div>
  );
}

export default JuddGroupAttribution;
