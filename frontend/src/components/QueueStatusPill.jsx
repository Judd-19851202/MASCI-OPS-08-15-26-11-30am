// R-BL-3 · Queue Visibility — global pill + drawer.
//
// VISIBILITY ONLY. Reads from the existing resiliency queue exports:
//   onQueueChange(cb)   subscribe to live updates
//   getQueueItems()     read current items
//   drainQueue()        manual retry trigger
//
// NEVER mutates queue state. NEVER duplicates persistence. NEVER alters
// retry logic / MAX_TRIES / backoff. Pure presentation layer.
//
// Doctrine: DR_BLOCKER_001B_QUEUED_SUBMISSION_TRUST_FIX_CERTIFICATION.md
//           (this sprint extends queued/failed trust visibility platform-wide)

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { CheckCircle2, CloudUpload, AlertTriangle, RefreshCw, X } from "lucide-react";
import {
  onQueueChange,
  getQueueItems,
  drainQueue,
  retryAllFailed,
} from "@/lib/resiliency/resiliencyQueue";
import { useT } from "@/lib/i18n";

const LAST_SYNC_KEY = "masci.last_successful_sync.v1";

function _readLastSync() {
  try {
    const v = localStorage.getItem(LAST_SYNC_KEY);
    return v ? new Date(v) : null;
  } catch {
    return null;
  }
}

function _writeLastSync(d) {
  try { localStorage.setItem(LAST_SYNC_KEY, d.toISOString()); } catch {/* */}
}

function _formatTime(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch { return String(iso); }
}

function _formatLong(d) {
  if (!d) return "—";
  try {
    return d.toLocaleString([], {
      month: "short", day: "numeric", year: "numeric",
      hour: "numeric", minute: "2-digit",
    });
  } catch { return String(d); }
}

const FORM_TYPE_FROM_KEY = {
  "daily-report-new": "Daily Report",
  "incident-new": "Incident Report",
  "inspection-new": "Inspection",
  "meeting-new": "Site Safety Meeting",
  "equipment-issuance": "Equipment Issuance",
  "equipment-pre-op": "Equipment Pre-Op",
  "jha-new": "JHA",
  "dvir-new": "DVIR",
};

function _formTypeOf(item) {
  return FORM_TYPE_FROM_KEY[item?.formKey] || "Submission";
}

function _projectOf(item) {
  const b = item?.body || {};
  return b.project_name || b.projectName || b.project || "—";
}

export default function QueueStatusPill() {
  const { t } = useT();
  const [items, setItems] = useState(() => getQueueItems());
  const [lastSync, setLastSync] = useState(_readLastSync);
  const [open, setOpen] = useState(false);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    const unsub = onQueueChange((next) => {
      setItems((prev) => {
        // Detect a successful drain: depth decreased.
        if ((prev?.length || 0) > (next?.length || 0)) {
          const now = new Date();
          _writeLastSync(now);
          setLastSync(now);
        }
        return next || [];
      });
    });
    return unsub;
  }, []);

  const stats = useMemo(() => {
    const total = items.length;
    const failed = items.filter((i) => i.status === "failed").length;
    const pending = total - failed;
    return { total, failed, pending };
  }, [items]);

  const state = stats.failed > 0
    ? "failed"
    : stats.total > 0
      ? "queued"
      : "synced";

  const VARIANTS = {
    synced: {
      bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-800",
      Icon: CheckCircle2, label: t("All Reports Synced"),
    },
    queued: {
      bg: "bg-amber-50", border: "border-amber-400", text: "text-amber-900",
      Icon: CloudUpload, label: `${t("Pending Uploads")}: ${stats.pending}`,
    },
    failed: {
      bg: "bg-red-50", border: "border-red-500", text: "text-red-900",
      Icon: AlertTriangle, label: t("Attention Required"),
    },
  };
  const v = VARIANTS[state];
  const Icon = v.Icon;

  const onRetry = useCallback(async () => {
    setRetrying(true);
    try {
      // DR-QUEUE-RETRY-001 · Manual "Retry All" is the ONLY path that
      // re-arms `failed` items (resets status→pending, tries→0,
      // lastError→null) before draining. Background drains continue
      // to skip failed items unchanged.
      if (stats.failed > 0) {
        await retryAllFailed();
      } else {
        await drainQueue();
      }
    } catch {/* */}
    setTimeout(() => setRetrying(false), 1500);
  }, [stats.failed]);

  // Suppress entirely on synced + no last-sync (i.e., quiet for fresh app loads).
  if (state === "synced" && !lastSync) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={state === "synced"}
        aria-label={v.label}
        data-testid={`queue-status-pill-${state}`}
        className={
          "fixed z-40 bottom-3 right-3 sm:bottom-4 sm:right-4 " +
          "flex items-center gap-2 px-3 py-2 rounded-full border-2 shadow-md " +
          "font-mono text-xs uppercase tracking-wider font-bold " +
          "transition-colors " +
          v.bg + " " + v.border + " " + v.text +
          (state === "synced" ? " opacity-90 cursor-default" : " cursor-pointer hover:shadow-lg")
        }
      >
        <Icon className={`w-4 h-4 ${state === "queued" && stats.pending > 0 ? "animate-pulse" : ""}`} />
        <span className="hidden sm:inline">{v.label}</span>
        <span className="sm:hidden">{state === "synced" ? "✓" : `${stats.total}`}</span>
      </button>

      {open && state !== "synced" && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/40 flex items-end sm:items-center sm:justify-end"
          onClick={() => setOpen(false)}
          data-testid="queue-status-drawer-backdrop"
        >
          <div
            className="bg-white w-full sm:max-w-md sm:mr-4 sm:rounded-md max-h-[85vh] overflow-y-auto border-2 border-slate-300 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            data-testid="queue-status-drawer"
          >
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-400 font-bold">
                  {t("Submission Queue")}
                </div>
                <div className="text-lg font-black mt-0.5">
                  {state === "failed" ? t("Attention Required") : t("Pending Uploads")}
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 hover:bg-white/10 rounded"
                data-testid="queue-drawer-close"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="px-5 py-3 bg-slate-50 border-b border-slate-200 text-xs flex justify-between items-center">
              <div className="font-mono uppercase tracking-wider text-slate-600">
                {t("Last Successful Sync")}
              </div>
              <div className="font-bold text-slate-800" data-testid="queue-last-sync">
                {lastSync ? _formatLong(lastSync) : t("Never Synced")}
              </div>
            </div>

            <ul className="divide-y divide-slate-100" data-testid="queue-items">
              {items.map((it) => {
                const isFailed = it.status === "failed";
                return (
                  <li key={it.id} className="px-5 py-3" data-testid={`queue-item-${it.id}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="font-bold text-sm text-slate-900 truncate">
                          {_formTypeOf(it)}
                        </div>
                        <div className="text-xs text-slate-600 truncate">{_projectOf(it)}</div>
                        <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mt-1">
                          {t("Queued")} {_formatTime(it.enqueuedAt)} ·{" "}
                          {t("Retry")} {it.tries || 0} {t("of")} 5
                        </div>
                      </div>
                      <div
                        className={
                          "px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-widest font-bold shrink-0 " +
                          (isFailed
                            ? "bg-red-100 text-red-800 border border-red-300"
                            : "bg-amber-100 text-amber-800 border border-amber-300")
                        }
                      >
                        {isFailed ? t("Needs Attention") : t("Pending")}
                      </div>
                    </div>
                    {isFailed && (
                      <div className="mt-2 text-xs text-slate-600 italic">
                        {t("This submission could not be delivered automatically.")}
                      </div>
                    )}
                    {it.lastError && (
                      <div className="mt-1 text-[11px] font-mono text-slate-500 truncate">
                        {it.lastError}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>

            <div className="px-5 py-4 border-t border-slate-200 bg-slate-50 flex gap-3">
              <button
                onClick={onRetry}
                disabled={retrying || items.length === 0}
                className={
                  "flex-1 h-10 rounded font-bold uppercase tracking-wide text-sm flex items-center justify-center gap-2 " +
                  "border-b-2 transition-colors " +
                  (state === "failed"
                    ? "bg-red-700 hover:bg-red-800 text-white border-red-900"
                    : "bg-amber-600 hover:bg-amber-700 text-white border-amber-800")
                }
                data-testid="queue-drawer-retry-all"
              >
                <RefreshCw className={`w-4 h-4 ${retrying ? "animate-spin" : ""}`} />
                {retrying ? t("Retrying...") : t("Retry All")}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
