// OdrTrustBanner.jsx — Phase V.1 · M0.3.
//
// Doctrine: /app/memory/ODR_TRUST_BANNER_DOCTRINE.md
//
// Quiet, calm, neutral. Never red. Never legal language. Never
// modal. Single line. Dismissible per-session.

import React from "react";

export default function OdrTrustBanner({ dataTestId = "odr-trust-banner" }) {
  const [dismissed, setDismissed] = React.useState(() => {
    try {
      return window.sessionStorage.getItem("odr_trust_banner_dismissed") === "1";
    } catch { return false; }
  });
  if (dismissed) return null;

  const dismiss = () => {
    try { window.sessionStorage.setItem("odr_trust_banner_dismissed", "1"); } catch { /* noop */ }
    setDismissed(true);
  };

  return (
    <div
      role="note"
      data-testid={dataTestId}
      className="flex items-center gap-3 text-xs text-slate-500 border border-slate-200 bg-slate-50 rounded-md px-3 py-2"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="h-3.5 w-3.5 text-slate-400 shrink-0"
      >
        <path d="M12 3l8 4v5c0 4.5-3 8.5-8 9-5-.5-8-4.5-8-9V7l8-4z" />
      </svg>
      <span className="flex-1">
        Operational Record · Audit history protected · Amendments tracked.
      </span>
      <button
        type="button"
        onClick={dismiss}
        data-testid={`${dataTestId}-dismiss`}
        className="text-slate-400 hover:text-slate-600 text-[10px] uppercase tracking-wider"
      >
        Dismiss
      </button>
    </div>
  );
}
