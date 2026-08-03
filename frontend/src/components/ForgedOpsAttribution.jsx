import React from "react";
import { Link } from "react-router-dom";
import { BUILD_SOURCE_HASH, BUILD_VERSION, BUILT_AT_ISO } from "@/buildVersion.generated";
import { useT } from "@/lib/i18n";
import { useBranding } from "@/lib/BrandingProvider";

/**
 * ForgedOpsAttribution — platform-owner branding line, three render modes.
 *
 * mascidocs.com is a customer-branded deployment of an enterprise
 * operations platform. The branding standard is:
 *
 *   MASCI = operational environment / client platform
 *
 * Variants keep MASCI as the operator-facing identity across the platform.
 */

export function ForgedOpsAttribution({ variant = "global", className = "" }) {
  const { t } = useT();
  const { platform_display_name } = useBranding();
  const platform = platform_display_name || "Operations Platform";
  if (variant === "login") {
    return (
      <div
        className={`flex items-center justify-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500 ${className}`}
        data-testid="forgedops-attr-login"
      >
        <span>{platform}</span>
      </div>
    );
  }

  if (variant === "admin") {
    return (
      <div
        className={`flex flex-col sm:flex-row items-center justify-center gap-3 ${className}`}
        data-testid="forgedops-attr-admin"
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-600 font-bold">
          {platform}
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
        {platform}
      </div>
      <div
        className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500"
        data-testid="footer-secondary"
      >
        Shared operations workspace
      </div>
      <div className="mt-2 font-mono text-[9px] uppercase tracking-[0.2em] text-slate-400">
        <Link
          to="/legal/terms"
          className="inline-flex items-center min-h-[44px] px-1 hover:text-slate-700 underline-offset-2 hover:underline"
          data-testid="footer-terms-link"
        >
          {t("Terms")}
        </Link>{" "}
        ·{" "}
        <Link
          to="/legal/privacy"
          className="inline-flex items-center min-h-[44px] px-1 hover:text-slate-700 underline-offset-2 hover:underline"
          data-testid="footer-privacy-link"
        >
          {t("Privacy")}
        </Link>{" "}
        ·{" "}
        <span
          title={`Built ${BUILT_AT_ISO}\nSource ${BUILD_SOURCE_HASH}`}
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
