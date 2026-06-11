// DraftStatusPill.jsx — iter440 · P0 field-incident remediation.
// iter-RC1-FH · M-18 · Spanish localization closure.
//
// What changed at iter440
// -----------------------
// The pill used to show ONLY "saving" or "saved" — and the "saved"
// state was driven by the side-effect of `setDraftStatus("saved")`
// AFTER the IDB write, **regardless** of whether the write actually
// succeeded. With `saveDraft()` swallowing every exception, the
// pill was effectively lying every time the iOS quota was exceeded.
//
// iter440 introduces:
//   - `"failed"` state (rose-tinted, with the real reason).
//   - `lastSavedAt` prop → renders "Saved 12s ago" / "Saved 4m ago".
//   - Pill no longer auto-collapses to "idle" — it shows the
//     relative timestamp continuously so the operator can verify
//     the work is safe BEFORE backgrounding the tab.
//
// iter-RC1-FH adds bilingual labels (ES bleed-through was breaking
// the EN/ES contract on /daily/new, /jha, /sign-in, every drafted
// form). All visible strings now route through useT().

import React, { useEffect, useState } from "react";
import { CloudUpload, Check, AlertTriangle } from "lucide-react";
import { useT } from "@/lib/i18n";

function _formatRelative(ts, t) {
  if (!ts) return "";
  const secs = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (secs < 5) return t("just now");
  if (secs < 60) return `${secs}${t("s ago")}`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}${t("m ago")}`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}${t("h ago")}`;
  return new Date(ts).toLocaleString();
}

function _failedReason(err, t) {
  if (!err) return t("Save failed");
  if (err.name === "QuotaExceededError" || /quota/i.test(err.message || "")) {
    return t("Save failed — storage full");
  }
  if (err.name === "InvalidStateError") {
    return t("Save failed — storage disabled");
  }
  return `${t("Save failed")} — ${err.name || t("unknown")}`;
}

export default function DraftStatusPill({
  status,
  lastSavedAt,
  lastError,
  testId = "draft-status-pill",
}) {
  const { t } = useT();
  // Re-render every 5 s so the "Saved Ns ago" text stays fresh.
  const [, setTick] = useState(0);
  useEffect(() => {
    if (!lastSavedAt && status !== "saved") return undefined;
    const tick = setInterval(() => setTick((x) => x + 1), 5_000);
    return () => clearInterval(tick);
  }, [lastSavedAt, status]);

  if (status === "failed") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 text-[10px] font-mono uppercase tracking-wider border border-rose-200"
        data-testid={testId}
        data-state="failed"
      >
        <AlertTriangle className="w-3 h-3" /> {_failedReason(lastError, t)}
      </span>
    );
  }

  if (status === "saving") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-mono uppercase tracking-wider"
        data-testid={testId}
        data-state="saving"
      >
        <CloudUpload className="w-3 h-3" /> {t("Saving draft…")}
      </span>
    );
  }

  if (status === "saved" || (status === "idle" && lastSavedAt)) {
    const label = lastSavedAt
      ? `${t("Saved")} ${_formatRelative(lastSavedAt, t)}`
      : t("Saved");
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono uppercase tracking-wider"
        data-testid={testId}
        data-state={status}
        data-saved-at={lastSavedAt || ""}
      >
        <Check className="w-3 h-3" /> {label}
      </span>
    );
  }

  return null;
}
