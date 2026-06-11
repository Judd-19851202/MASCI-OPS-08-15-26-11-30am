// SupportIdAffordance.jsx — TRUST-1 · TF-022 · 2026-05-27.
//
// Calm, field-friendly "Support ID" affordance for the autosave pill.
// Operators who call the office about a daily report can read their
// device's Support ID to the office; the admin then types it into the
// Draft Health tile's per-device filter to triage.
//
// Doctrine
// --------
//   * Hidden by default behind a calm icon button. Long-press OR tap
//     opens a tiny popover. Never visible in a "scary debug bar".
//   * Wording is operator-language only:
//       "Support ID"          ← preferred top label
//       "If the office asks…"  ← reassuring sub-line
//     NEVER: "Fingerprint", "Tracking ID", "Device UUID", "Debug ID".
//   * Tap to copy → toast "Support ID copied".
//   * One short tone — slate, not amber, not red. No urgency.
//   * NOT a feature flag — the affordance is always available, just
//     visually quiet.

import React, { useEffect, useRef, useState } from "react";
import { LifeBuoy, Copy, Check } from "lucide-react";
import { getDeviceId } from "@/lib/resiliency";
import { toast } from "sonner";

function _shortId(deviceId) {
  // Operator-readable form: keep the "d." prefix + first 8 hex chars
  // so the value is easy to read aloud over the phone but still
  // unique enough to find on the admin side.
  if (!deviceId) return "—";
  const s = String(deviceId);
  if (s.length <= 12) return s;
  return `${s.slice(0, 10)}…`;
}

export default function SupportIdAffordance({ testId = "support-id-affordance" }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deviceId, setDeviceId] = useState("");
  const popRef = useRef(null);
  const btnRef = useRef(null);

  useEffect(() => {
    try { setDeviceId(getDeviceId()); } catch { /* ignore */ }
  }, []);

  // Close on outside tap.
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (popRef.current && popRef.current.contains(e.target)) return;
      if (btnRef.current && btnRef.current.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("touchstart", onDown);
    };
  }, [open]);

  const onCopy = async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(deviceId || "");
      } else {
        // Fallback for older Safari: hidden input + execCommand.
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
    <div className="relative inline-block">
      <button
        ref={btnRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center justify-center min-w-[32px] min-h-[32px] rounded-full text-white/70 hover:text-white hover:bg-slate-800/40 transition-colors"
        title="Support ID"
        aria-label="Show Support ID"
        aria-expanded={open}
        data-testid={testId}
      >
        <LifeBuoy className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
      {open ? (
        <div
          ref={popRef}
          role="dialog"
          aria-label="Support ID"
          data-testid={`${testId}-popover`}
          className="absolute right-0 mt-1 z-50 w-64 rounded-md border border-slate-300 bg-white text-slate-800 shadow-md p-3"
        >
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
              Support ID
            </span>
            <span className="font-mono text-[10px] text-slate-400">
              {_shortId(deviceId)}
            </span>
          </div>
          <button
            type="button"
            onClick={onCopy}
            className="w-full inline-flex items-center justify-between gap-2 px-2 py-1.5 rounded border border-slate-200 hover:border-slate-400 hover:bg-slate-50 font-mono text-[11px] text-slate-700"
            data-testid={`${testId}-copy`}
            aria-label="Copy Support ID"
          >
            <span className="truncate text-left" data-testid={`${testId}-value`}>
              {deviceId || "—"}
            </span>
            {copied ? (
              <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" aria-hidden="true" />
            ) : (
              <Copy className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" aria-hidden="true" />
            )}
          </button>
          <p className="text-[11px] text-slate-600 leading-snug mt-2">
            If the office asks about your daily report, share this ID
            so they can find it on their end.
          </p>
        </div>
      ) : null}
    </div>
  );
}
