import React from "react";
import { SemanticIcon } from "@/components/icons/AppIcon";

/**
 * SubmitLangBadge — tiny chip rendered on admin-facing record views (and
 * PDF covers) that marks which records were originally filled out in
 * Spanish by the field crew. The record itself is stored in English (the
 * submit flow auto-translates), so this badge is the only trace of the
 * original language. Renders nothing when the record was filed in English
 * (no visual noise on the happy path).
 *
 * Usage:
 *   <SubmitLangBadge lang={doc.submit_language} />
 */
export function SubmitLangBadge({ lang, className = "" }) {
  if (!lang || lang === "en") return null;
  return (
    <span
      data-testid="submit-lang-badge"
      className={`wp17-status-badge wp17-tone--amber ${className}`}
      title="Originally entered in Spanish by the field crew. The record below was auto-translated to English at submit time."
    >
      <SemanticIcon name="language" size="xs" />
      Originally entered in Spanish
    </span>
  );
}

export default SubmitLangBadge;
