// PriorUsageBanner.jsx — TRUST-1 · TF-001 · 2026-05-27.
//
// Calm, reassuring soft banner shown when:
//   1. There is no live draft on offer (useFormDraft.pendingDraft is null)
//   2. There is no archived (soft-deleted) draft to recover (TF-016 absent)
//   3. BUT the prior-usage beacon shows this device HAS previously saved
//      on this form (so the operator is a returning user, not first-timer)
//   4. AND the beacon's `last` timestamp is at least 24h old — long
//      enough that Safari ITP / storage-sweep could have plausibly
//      cleared the IDB store between sessions.
//
// Operator-first wording (user-approved):
//   "We couldn't find recent local draft data on this iPad."
//   "If work seems missing, contact support and provide your Support ID."
//
// Doctrine
// --------
//   * Calm slate tone. NOT amber. NOT red. NO pulse.
//   * Reassuring, not alarming. Operator's work is presumed safe.
//   * No "browser storage", "corruption", "purge", "ITP", "quota" wording.
//   * Includes a Support ID copy button (mirrors the iter442 affordance).
//   * Lightweight "Learn more" disclosure for operators who want context.
//   * Dismiss action hides for this mount only (does NOT wipe the beacon).
//   * One-time telemetry: emits `draft.recovery.absent` per mount.

import React, { useEffect, useState } from "react";
import { LifeBuoy, Copy, Check, ChevronDown, ChevronUp, X } from "lucide-react";
import { getDeviceId, emitDraftEvent } from "@/lib/resiliency";
import { toast } from "sonner";

function _shortId(deviceId) {
  if (!deviceId) return "—";
  const s = String(deviceId);
  return s.length > 12 ? `${s.slice(0, 10)}…` : s;
}

function _fmtRelative(ts) {
  if (!ts) return "earlier";
  const secs = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  const hrs = Math.floor(secs / 3600);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
  return new Date(ts).toLocaleDateString();
}

export default function PriorUsageBanner({
  formKey,
  priorUsage,
  onDismiss,
  testId = "prior-usage-banner",
}) {
  const [hidden, setHidden] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deviceId, setDeviceId] = useState("");

  useEffect(() => { setHidden(false); }, [priorUsage]);

  useEffect(() => {
    try { setDeviceId(getDeviceId()); } catch { /* ignore */ }
  }, []);

  // One-time telemetry on mount. NEVER sends form content.
  useEffect(() => {
    if (!priorUsage) return;
    try {
      emitDraftEvent("draft.recovery.absent", {
        formKey: formKey || "unknown",
        lastUsedAt: priorUsage.last || 0,
        priorCount: priorUsage.count || 0,
      });
    } catch { /* never throw from telemetry */ }
  }, [formKey, priorUsage]);

  if (!priorUsage || hidden) return null;

  const onCopy = async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(deviceId || "");
      } else {
        const ta = document.createElement("textarea");
        ta.value = deviceId || "";
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); } catch { /* ignore */ }
        document.body.removeChild(ta);
      }
      setCopied(true);
      toast.success("Support ID copied");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.message("Couldn't copy — read it to the office instead.");
    }
  };

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
          Welcome back · returning device
        </div>
        <p className="text-sm leading-snug mt-1">
          We couldn't find recent local draft data on this iPad.
        </p>
        <p className="text-sm leading-snug mt-1 text-slate-700">
          If work seems missing, contact support and provide your Support ID
          so they can look it up on their end. Otherwise, start a new
          report — anything you submitted before is safe on the server.
        </p>

        {/* Support ID row · calm copy affordance */}
        <div className="mt-2 flex items-center gap-2">
          <button
            type="button"
            onClick={onCopy}
            data-testid={`${testId}-copy-support-id`}
            className="inline-flex items-center gap-2 px-2 py-1.5 rounded border border-slate-300 hover:border-slate-500 bg-white font-mono text-[11px] text-slate-700"
            aria-label="Copy Support ID"
          >
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
              Support&nbsp;ID
            </span>
            <span className="truncate" data-testid={`${testId}-support-id-value`}>
              {_shortId(deviceId)}
            </span>
            {copied ? (
              <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" aria-hidden="true" />
            ) : (
              <Copy className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" aria-hidden="true" />
            )}
          </button>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            data-testid={`${testId}-learn-more`}
            className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-700 font-mono text-[11px] uppercase tracking-wider"
            aria-expanded={expanded}
          >
            Learn more
            {expanded ? (
              <ChevronUp className="w-3 h-3" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-3 h-3" aria-hidden="true" />
            )}
          </button>
          <button
            type="button"
            onClick={() => {
              setHidden(true);
              try { onDismiss && onDismiss(); } catch { /* ignore */ }
            }}
            data-testid={`${testId}-dismiss`}
            className="ml-auto inline-flex items-center gap-1 text-slate-400 hover:text-slate-700 font-mono text-[11px] uppercase tracking-wider"
            aria-label="Dismiss"
          >
            <X className="w-3 h-3" aria-hidden="true" />
          </button>
        </div>

        {expanded ? (
          <div
            data-testid={`${testId}-detail`}
            className="mt-2 rounded border border-slate-200 bg-white p-3 text-[12px] leading-snug text-slate-600 space-y-1.5"
          >
            <p>
              Your device last used this form about {_fmtRelative(priorUsage.last)}.
              Some iPads clear local app data after long idle periods.
              That doesn't affect anything you already submitted to the office.
            </p>
            <p>
              If a specific report seems missing, share the Support ID
              above with the office. They can find this iPad's history
              and confirm what was received.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
