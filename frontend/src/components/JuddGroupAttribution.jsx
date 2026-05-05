import React from "react";
import { Link } from "react-router-dom";
import juddLogo from "@/assets/judd-group-logo.png";
import { BUILD_VERSION, BUILT_AT_ISO } from "@/buildVersion.generated";

/**
 * JuddGroupAttribution — platform ownership line, three render modes.
 *
 * mascidocs.com is a customer-branded deployment of a platform developed
 * by The Judd Group LLC. MASCI is the operational brand the field crews
 * interact with every day; The Judd Group is named subtly so ownership is
 * clear without overpowering MASCI's identity.
 *
 * Variants (use exactly one of the three strings — never both):
 *   • global — every-page footer, small subtle gray text:
 *              "Platform developed by The Judd Group LLC · Terms · Privacy"
 *   • login  — subtle "Platform developed by The Judd Group LLC" line
 *              beneath the login form
 *   • admin  — slightly stronger "System developed & maintained by
 *              The Judd Group LLC" — admin-panel only, never on
 *              field/shop/safety surfaces
 *
 * Per owner brand guidelines: MASCI branding remains dominant; the
 * Judd Group attribution is present but subtle and professional.
 */

export function JuddGroupAttribution({ variant = "global", className = "" }) {
  if (variant === "login") {
    return (
      <div
        className={`flex items-center justify-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 ${className}`}
        data-testid="judd-attr-login"
      >
        <img
          src={juddLogo}
          alt="The Judd Group"
          className="h-5 w-auto opacity-80"
        />
        <span>Platform developed by The Judd Group LLC</span>
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
          className="h-7 w-auto opacity-90"
        />
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
          System developed &amp; maintained by The Judd Group LLC
        </div>
      </div>
    );
  }

  // global — single subtle line used on every page. No "© MASCI" prefix
  // here (MASCI branding lives in the main lockup / page chrome);
  // this line is strictly the platform-ownership clarifier + legal links.
  return (
    <div
      className={`text-center font-mono text-[9px] uppercase tracking-[0.2em] text-slate-400 ${className}`}
      data-testid="judd-attr-global"
    >
      Platform developed by The Judd Group LLC ·{" "}
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
      </Link>{" "}
      ·{" "}
      <span
        title={`Built ${BUILT_AT_ISO}`}
        data-testid="build-version-stamp"
        className="cursor-help select-all"
      >
        {BUILD_VERSION}
      </span>
    </div>
  );
}

export default JuddGroupAttribution;
