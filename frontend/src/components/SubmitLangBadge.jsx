import React from "react";
import { Languages } from "lucide-react";

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
      className={
        "inline-flex items-center gap-1 px-2 py-0.5 rounded " +
        "bg-amber-100 text-amber-900 border border-amber-300 " +
        "font-mono text-[10px] font-bold uppercase tracking-[0.15em] " +
        className
      }
      title="Originally entered in Spanish by the field crew. The record below was auto-translated to English at submit time."
    >
      <Languages className="w-3 h-3" />
      Originally entered in Spanish
    </span>
  );
}

export default SubmitLangBadge;
