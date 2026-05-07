import React from "react";
import { Link } from "react-router-dom";
import forgedOpsLogo from "@/assets/forgedops-logo.png";
import { BUILD_VERSION, BUILT_AT_ISO } from "@/buildVersion.generated";

/**
 * ForgedOpsAttribution — platform-owner branding line, three render modes.
 *
 * mascidocs.com is a customer-branded deployment of an enterprise
 * operational platform developed and maintained by ForgedOps LLC. MASCI
 * is the operational brand the field crews interact with every day;
 * ForgedOps is the platform-technology owner — present subtly so
 * ownership is clear without overpowering MASCI's identity.
 *
 * Variants:
 *   • global — every-page footer. Two-row layout:
 *              ┌───────────────────────────────────────────────────────┐
 *              │ POWERED BY FORGEDOPS LLC ·                           │
 *              │ BUILDING SAFER JOBS | POWERING PERFORMANCE           │  (dominant)
 *              │ Terms · Privacy · v2026.MM.DD-hash                   │  (subtle)
 *              └───────────────────────────────────────────────────────┘
 *   • login  — subtle "Powered by ForgedOps LLC" line beneath the
 *              login form, with the ForgedOps mark.
 *   • admin  — slightly stronger "Platform developed & maintained by
 *              ForgedOps LLC" — admin-area only.
 *
 * Per owner brand guidelines: MASCI HUB branding remains dominant;
 * ForgedOps attribution is present but professional and subtle.
 */

export function ForgedOpsAttribution({ variant = "global", className = "" }) {
  if (variant === "login") {
    return (
      <div
        className={`flex items-center justify-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 ${className}`}
        data-testid="forgedops-attr-login"
      >
        <img
          src={forgedOpsLogo}
          alt="ForgedOps"
          className="h-5 w-auto opacity-80"
        />
        <span>Powered by ForgedOps LLC</span>
      </div>
    );
  }

  if (variant === "admin") {
    return (
      <div
        className={`flex flex-col sm:flex-row items-center justify-center gap-3 ${className}`}
        data-testid="forgedops-attr-admin"
      >
        <img
          src={forgedOpsLogo}
          alt="ForgedOps"
          className="h-7 w-auto opacity-90"
        />
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
          Platform developed &amp; maintained by ForgedOps LLC
        </div>
      </div>
    );
  }

  // global — every-page footer. Two-row: dominant brand stamp + subtle utility line.
  return (
    <div
      className={`text-center ${className}`}
      data-testid="forgedops-attr-global"
    >
      <div className="font-mono text-[10px] sm:text-[11px] uppercase tracking-[0.2em] text-slate-700 font-bold leading-relaxed px-2 break-words">
        Powered by ForgedOps LLC{" "}
        <span className="text-slate-400 font-normal mx-1">·</span>{" "}
        Building Safer Jobs <span className="text-slate-400 mx-1">|</span>{" "}
        Powering Performance
      </div>
      <div className="mt-1 font-mono text-[9px] uppercase tracking-[0.2em] text-slate-400">
        <Link
          to="/legal/terms"
          className="hover:text-slate-700 underline-offset-2 hover:underline"
          data-testid="footer-terms-link"
        >
          Terms
        </Link>{" "}
        ·{" "}
        <Link
          to="/legal/privacy"
          className="hover:text-slate-700 underline-offset-2 hover:underline"
          data-testid="footer-privacy-link"
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
    </div>
  );
}

export default ForgedOpsAttribution;
