import React from "react";
import { Link } from "react-router-dom";
import juddLogo from "@/assets/judd-group-logo.png";

/**
 * JuddGroupAttribution — three render modes for vendor attribution.
 *
 * MASCI HUB is the customer-branded deployment of the underlying Platform,
 * which is owned and operated by The Judd Group LLC. Same model as Microsoft
 * owning Word: Judd owns the Platform IP / code / infrastructure / domain;
 * MASCI is the customer that uses it and owns their own data.
 *
 *   • global   — every-page footer: © {year} The Judd Group LLC · MASCI HUB
 *                · Terms · Privacy
 *   • login    — "Powered by [logo] The Judd Group LLC" under login form
 *                (correct: they ARE the Platform vendor)
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
        <span>Powered by</span>
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
            Platform Owned &amp; Operated
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
      © {YEAR} The Judd Group LLC · MASCI HUB™ ·{" "}
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
