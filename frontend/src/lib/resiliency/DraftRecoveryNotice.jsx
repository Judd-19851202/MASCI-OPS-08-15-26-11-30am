// DraftRecoveryNotice.jsx — TRUST-1 · TF-016 · 2026-05-27.
//
// Calm, reassuring recovery affordance for a draft that was previously
// SOFT-DELETED (via the Discard button on DraftRestorePrompt). The
// draft remains in the IDB archive store for 24h. This banner is the
// ONLY operator-visible path back to that work — without it, recovery
// requires developer tools.
//
// Doctrine
// --------
//   * Hidden by default — only renders when an archive entry exists
//     AND no live draft is present.
//   * Tone: slate / reassuring, NEVER amber/red. "your work is safe".
//   * Wording: "Recover a draft you discarded earlier?" · operator
//     language. Avoid "deleted", "lost", "missing", "abandoned",
//     "orphan", "panic", "recovery operation".
//   * Two actions only: Recover · Dismiss. Dismiss hides the banner
//     for this mount (does NOT delete the archive).
//   * One small line below: "Saved {ago} · discarded {ago}". Calm
//     factual timestamp, no spinner, no progress, no alarm.

import React, { useEffect, useState } from "react";
import { LifeBuoy, X } from "lucide-react";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

function _fmtRelative(ts) {
  if (!ts) return "earlier";
  const secs = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return formatPlatformTime(ts);
}

export default function DraftRecoveryNotice({
  archive,
  onRecover,
  onDismiss,
  testId = "draft-recovery-notice",
}) {
  const [hidden, setHidden] = useState(false);
  useEffect(() => { setHidden(false); }, [archive]);

  if (!archive || hidden) return null;
  const savedAt = archive.savedAt || 0;
  const deletedAt = archive.deletedAt || 0;

  return (
    <section
      data-testid={testId}
      className="rounded-md border border-slate-300 bg-slate-50 text-slate-800 px-4 py-3 flex items-start gap-3"
    >
      <LifeBuoy
        className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
          Recover a draft you discarded earlier?
        </div>
        <p className="text-sm leading-snug mt-1">
          Your work is still here for 24 hours after a discard. You can
          bring it back if it was tapped by mistake.
        </p>
        <div className="font-mono text-[10px] text-slate-500 mt-1">
          {savedAt ? `Saved ${_fmtRelative(savedAt)}` : ""}
          {savedAt && deletedAt ? " · " : ""}
          {deletedAt ? `Discarded ${_fmtRelative(deletedAt)}` : ""}
        </div>
        <div className="mt-2 flex items-center gap-2">
          <button
            type="button"
            onClick={onRecover}
            data-testid={`${testId}-recover`}
            className="inline-flex items-center px-3 py-1.5 rounded border border-slate-700 bg-slate-900 text-white font-mono text-[11px] uppercase tracking-wider hover:bg-slate-800"
          >
            Bring it back
          </button>
          <button
            type="button"
            onClick={() => {
              setHidden(true);
              try { onDismiss && onDismiss(); } catch { /* ignore */ }
            }}
            data-testid={`${testId}-dismiss`}
            className="inline-flex items-center gap-1 px-2 py-1.5 rounded text-slate-500 hover:text-slate-700 font-mono text-[11px] uppercase tracking-wider"
          >
            <X className="w-3 h-3" aria-hidden="true" /> Not now
          </button>
        </div>
      </div>
    </section>
  );
}
