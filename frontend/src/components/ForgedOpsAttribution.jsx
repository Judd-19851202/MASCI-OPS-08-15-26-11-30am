import React from "react";
import { Link } from "react-router-dom";
import forgedOpsLogo from "@/assets/forgedops-logo.png";
import { BUILD_VERSION, BUILT_AT_ISO } from "@/buildVersion.generated";

/**
 * ForgedOpsAttribution — platform-owner branding line, three render modes.
 *
 * mascidocs.com is a customer-branded deployment of an enterprise
 * operations platform. The branding standard is:
 *
 *   MASCI     = operational environment / client platform
 *   ForgedOps = underlying operations technology platform
 *
 * UI surfaces use "ForgedOps™" (trademark, no "LLC"). The "LLC" legal
 * name is reserved for terms, privacy, contracts, and other legal
 * documents — never for UI chrome.
 *
 * Variants:
 *   • global — every-page footer. Single clean stack:
 *              ┌─────────────────────────────────────┐
 *              │  MASCI Operations Platform          │  primary
 *              │  Powered by ForgedOps™              │  secondary
 *              │  Terms · Privacy · vYYYY.MM.DD-hash │  legal/version
 *              └─────────────────────────────────────┘
 *   • login  — subtle "Powered by ForgedOps™" line beneath the login
 *              form, with the small ForgedOps mark.
 *   • admin  — slightly stronger "MASCI Operations Platform · Powered
 *              by ForgedOps™" for admin chrome.
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
        <span>Powered by ForgedOps™</span>
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
          MASCI Operations Platform{" "}
          <span className="text-slate-400 font-normal mx-1.5">·</span>{" "}
          Powered by ForgedOps™
        </div>
      </div>
    );
  }

  // global — every-page footer.
  return (
    <div
      className={`text-center ${className}`}
      data-testid="forgedops-attr-global"
    >
      <div
        className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.25em] text-slate-800 font-bold"
        data-testid="footer-primary"
      >
        MASCI Operations Platform
      </div>
      <div
        className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500"
        data-testid="footer-secondary"
      >
        Powered by ForgedOps™
      </div>
      <div className="mt-2 font-mono text-[9px] uppercase tracking-[0.2em] text-slate-400">
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
