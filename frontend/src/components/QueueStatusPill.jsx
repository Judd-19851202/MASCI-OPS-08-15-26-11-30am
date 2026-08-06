// R-BL-3 · Queue Visibility — global pill + drawer.
//
// VISIBILITY + DISCARD. Reads from the existing resiliency queue exports:
//   onQueueChange(cb)       subscribe to live updates
//   getQueueItems()         read current items
//   drainQueue()            manual retry trigger
//   retryAllFailed()        re-arm failed items, then drain
//   discardQueueItem(id)    OFFLINE-UPLOAD-001 — operator discard
//
// NEVER mutates retry state. NEVER duplicates persistence. NEVER alters
// retry logic / MAX_TRIES / backoff. Pure presentation + operator
// recovery layer.
//
// Doctrine: DR_BLOCKER_001B_QUEUED_SUBMISSION_TRUST_FIX_CERTIFICATION.md
//           OFFLINE-UPLOAD-001 (hardens drawer against malformed items)

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { CheckCircle2, CloudUpload, AlertTriangle, RefreshCw, X, Trash2 } from "lucide-react";
import {
  onQueueChange,
  getQueueItems,
  drainQueue,
  retryAllFailed,
  discardQueueItem,
  clearQueue,
} from "@/lib/resiliency/resiliencyQueue";
import { useT } from "@/lib/i18n";
// TRACK 27.03 · Phase 3 · Canonical local-time formatters.
import { formatPlatformTime, formatPlatformTimeOnly } from "@/lib/platformTime";

const LAST_SYNC_KEY = "masci.last_successful_sync.v1";
const FLOATING_BOTTOM_OFFSET = "calc(var(--masci-form-shell-footer-height, 0px) + max(0.75rem, env(safe-area-inset-bottom)) + 0.5rem)";

function _readLastSync() {
  try {
    const v = localStorage.getItem(LAST_SYNC_KEY);
    return v ? new Date(v) : null;
  } catch {
    return null;
  }
}

function _writeLastSync(d) {
  try { localStorage.setItem(LAST_SYNC_KEY, d.toISOString()); } catch {/* */}  // TRACK-27.03-EXEMPT: localStorage serialization (machine value, not rendered)
}

function _formatTime(iso) {
  if (iso === null || iso === undefined) return "—";
  return formatPlatformTimeOnly(iso);
}

function _formatLong(d) {
  if (!d) return "—";
  return formatPlatformTime(d);
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

// Field-Leadership uses dynamic formKeys of shape `fl-<kind>-new`
// (kind ∈ equipment_checkout, write_up, crew_eval, verbal_coaching,
// attendance, recognition, new_employee_eval,
// promotion_recommendation, training_deficiency, supervisor_notes).
// Render a human label without enumerating every kind.
function _humanizeFlKind(kind) {
  if (!kind || typeof kind !== "string") return "";
  return kind
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function _formTypeOf(item) {
  const k = item && typeof item.formKey === "string" ? item.formKey : null;
  if (!k) return "Submission";
  if (FORM_TYPE_FROM_KEY[k]) return FORM_TYPE_FROM_KEY[k];
  // Field Leadership pattern: fl-<kind>-new
  const flMatch = /^fl-(.+)-new$/.exec(k);
  if (flMatch) {
    const label = _humanizeFlKind(flMatch[1]);
    return label ? `Field Leadership · ${label}` : "Field Leadership";
  }
  return "Submission";
}

function _projectOf(item) {
  try {
    const b = (item && typeof item.body === "object" && item.body) || {};
    const v = b.project_name || b.projectName || b.project;
    return typeof v === "string" && v.length > 0 ? v : "—";
  } catch { return "—"; }
}

// OFFLINE-UPLOAD-001 · Coerce any lastError shape (string | object |
// Error | axios-like) to a renderable string. Legacy IDB entries from
// earlier schema may have stored objects here, which would crash React
// when rendered directly as a child.
function _errorTextOf(item) {
  const e = item && item.lastError;
  if (e === null || e === undefined) return "";
  if (typeof e === "string") return e;
  if (typeof e === "number" || typeof e === "boolean") return String(e);
  if (typeof e === "object") {
    try {
      const msg = e.message || e.detail || (e.response && (e.response.data?.detail || e.response.statusText));
      if (typeof msg === "string" && msg.length > 0) return msg.slice(0, 240);
      return JSON.stringify(e).slice(0, 240);
    } catch { return "error"; }
  }
  return String(e);
}

function _safeId(item, index) {
  if (item && typeof item.id === "string" && item.id.length > 0) return item.id;
  if (item && typeof item.idempotencyKey === "string" && item.idempotencyKey.length > 0) {
    return item.idempotencyKey;
  }
  return `legacy-${index}`;
}

function _safeTries(item) {
  const n = item && item.tries;
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

// OFFLINE-UPLOAD-001 · Local ErrorBoundary so a single malformed item
// can never blank the entire app. Falls back to a discard-only view.
class DrawerErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error) {
    try {
      console.error("[QueueStatusPill] drawer render crash:", error);
    } catch { /* */ }
  }
  render() {
    if (this.state.error) {
      return (
        <div className="px-5 py-6 text-sm text-slate-700" data-testid="queue-drawer-error">
          <div className="font-bold text-red-700 mb-2">
            The submission queue couldn’t be rendered.
          </div>
          <div className="text-xs text-slate-600 mb-4">
            One or more queued items appear to be corrupted. Use the button
            below to clear them so you can keep working.
          </div>
          <button
            type="button"
            onClick={this.props.onClearAll}
            className="px-3 py-2 bg-red-700 hover:bg-red-800 text-white rounded font-bold text-xs uppercase tracking-wider"
            data-testid="queue-drawer-clear-corrupted"
          >
            Clear corrupted items
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function QueueItemRow({ item, index, t, onDiscard, confirming, setConfirming }) {
  const safeId = _safeId(item, index);
  const isFailed = item && item.status === "failed";
  const tries = _safeTries(item);
  const errText = _errorTextOf(item);
  const isConfirming = confirming === safeId;

  return (
    <li className="px-5 py-3" data-testid={`queue-item-${safeId}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="font-bold text-sm text-slate-900 truncate">
            {_formTypeOf(item)}
          </div>
          <div className="text-xs text-slate-600 truncate">{_projectOf(item)}</div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mt-1">
            {t("Queued")} {_formatTime(item && item.enqueuedAt)} ·{" "}
            {t("Retry")} {tries} {t("of")} 5
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div
            className={
              "px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-widest font-bold " +
              (isFailed
                ? "bg-red-100 text-red-800 border border-red-300"
                : "bg-amber-100 text-amber-800 border border-amber-300")
            }
          >
            {isFailed ? t("Needs Attention") : t("Pending")}
          </div>
          {!isConfirming && (
            <button
              type="button"
              onClick={() => setConfirming(safeId)}
              className="p-1.5 rounded hover:bg-slate-100 text-slate-500 hover:text-red-700 transition-colors"
              aria-label={t("Discard")}
              title={t("Discard")}
              data-testid={`queue-item-discard-${safeId}`}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
      {isFailed && (
        <div className="mt-2 text-xs text-slate-600 italic">
          {t("This submission could not be delivered automatically.")}
        </div>
      )}
      {errText && (
        <div className="mt-1 text-[11px] font-mono text-slate-500 truncate">
          {errText}
        </div>
      )}
      {isConfirming && (
        <div
          className="mt-3 flex items-center justify-between gap-2 rounded border border-red-300 bg-red-50 px-3 py-2"
          data-testid={`queue-item-confirm-${safeId}`}
        >
          <div className="text-xs text-red-900 font-semibold">
            {t("Discard this submission? This cannot be undone.")}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setConfirming(null)}
              className="px-2 py-1 text-xs font-bold uppercase tracking-wider text-slate-700 hover:bg-white rounded"
              data-testid={`queue-item-discard-cancel-${safeId}`}
            >
              {t("Cancel")}
            </button>
            <button
              type="button"
              onClick={() => onDiscard(safeId)}
              className="px-2 py-1 text-xs font-bold uppercase tracking-wider bg-red-700 hover:bg-red-800 text-white rounded"
              data-testid={`queue-item-discard-confirm-${safeId}`}
            >
              {t("Discard")}
            </button>
          </div>
        </div>
      )}
    </li>
  );
}

export default function QueueStatusPill() {
  const { t } = useT();
  const [items, setItems] = useState(() => getQueueItems());
  const [lastSync, setLastSync] = useState(_readLastSync);
  const [open, setOpen] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [confirmingId, setConfirmingId] = useState(null);

  useEffect(() => {
    const unsub = onQueueChange((next) => {
      setItems((prev) => {
        // Detect a successful drain: depth decreased.
        if ((prev?.length || 0) > (next?.length || 0)) {
          const now = new Date();
          _writeLastSync(now);
          setLastSync(now);
        }
        return Array.isArray(next) ? next : [];
      });
    });
    return unsub;
  }, []);

  // Reset inline confirm when drawer closes — handled by closeDrawer below.
  const closeDrawer = useCallback(() => {
    setOpen(false);
    setConfirmingId(null);
  }, []);

  const stats = useMemo(() => {
    const total = items.length;
    const failed = items.filter((i) => i && i.status === "failed").length;
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

  const onDiscard = useCallback(async (id) => {
    setConfirmingId(null);
    try {
      await discardQueueItem(id);
    } catch {/* */}
  }, []);

  // OFFLINE-UPLOAD-001 · Last-resort fallback when items can't be
  // rendered at all (ErrorBoundary path). Wipes the entire persisted
  // queue so the user is never stuck — per-item discard cannot be
  // trusted here because some items may lack a real id.
  const onClearAll = useCallback(async () => {
    try {
      await clearQueue();
    } catch {/* */}
  }, []);

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
        style={{ bottom: FLOATING_BOTTOM_OFFSET }}
        className={
          "fixed z-40 right-3 sm:right-4 " +
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
          onClick={closeDrawer}
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
                onClick={closeDrawer}
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

            <DrawerErrorBoundary onClearAll={onClearAll}>
              <ul className="divide-y divide-slate-100" data-testid="queue-items">
                {items.map((it, idx) => (
                  <QueueItemRow
                    key={_safeId(it, idx)}
                    item={it}
                    index={idx}
                    t={t}
                    onDiscard={onDiscard}
                    confirming={confirmingId}
                    setConfirming={setConfirmingId}
                  />
                ))}
              </ul>
            </DrawerErrorBoundary>

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
