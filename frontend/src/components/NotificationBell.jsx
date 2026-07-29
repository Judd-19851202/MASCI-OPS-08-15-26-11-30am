// NotificationBell.jsx — Iter150 (Phase A) + Track 14.0-UXS-NOTIFY (2026-06-14).
// Global notification bell shown in every protected portal header.
// Click → drawer with the current user's notification feed.
//
// Phase J addition (iter166): renders a small amber "upload queued"
// badge underneath the bell when the resiliency queue has pending
// items. Subtle — no banner, no toast, no sound.
//
// UXS-NOTIFY (2026-06-14):
//   • Audible chime when the unread count increases (Web Audio API
//     synth — no asset, no network).
//   • Operator-controlled Mute / 1h snooze / 8h snooze in the drawer
//     header. Persisted to localStorage so a single tap survives
//     reloads.
//   • Local-time timestamps only (toLocaleString respects device tz).
//   • Empty state, role-filtered, no fake notifications — backend
//     enforces recipient_role scoping (admin sees all, others see
//     only their role).
//   • Click-through: rows now follow `link_url` when present, else
//     fall back to /tasks?id=<linked_task_id>.

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Bell, CheckCheck, ExternalLink, AlertOctagon, Info, AlertTriangle, Upload, BellOff, BellRing, VolumeX } from "lucide-react";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  listNotifications, markRead, markAllRead, getUnreadCount,
} from "@/lib/tasksApi";
import { activePortals, isSignedInAnywhere } from "@/lib/permissions";
import { onQueueChange } from "@/lib/resiliency";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const SEV_ICON = {
  Info: Info,
  Warning: AlertTriangle,
  Critical: AlertOctagon,
};
const SEV_CLR = {
  Info: "text-slate-500",
  Warning: "text-amber-600",
  Critical: "text-red-700",
};

// TRACK 15.40 · Notification Completion — humanize the canonical
// `linked_source_module` keys into operator-readable traceability
// chips. Adding a new module key here is the ONLY operator-facing
// change required for a new producer.
const SOURCE_MODULE_LABEL = {
  team_assignment: "Team Assignment",
  "safety.incidents": "Safety Incident",
  "safety.meeting": "Safety Meeting",
  "safety.jha": "JHA",
  "safety.inspections": "Safety Inspection",
  "safety.fire_extinguishers": "Fire Extinguisher",
  "safety.form.issuance": "Equipment Issuance",
  "safety.form.return": "Equipment Return",
  "safety.form.training": "Equipment Training",
  daily_reports: "Daily Report",
  "qaqc.inspections": "QA/QC",
  "field_leadership.records": "Field Leadership",
  "po.requests": "PO Request",
  "po.receipts": "PO Receipt",
  "equipment.preop": "Pre-Op",
  "fleet.dvir": "DVIR",
  "fleet.defect.assignment": "Fleet Defect",
  "fuel_lube_visit.issue": "Fuel/Lube Issue",
  "asset.transfer": "Asset Transfer",
  "documents.expiration": "Document Expiration",
  "hr.payroll_variance": "Payroll Variance",
  "trench_safety:reinspection_requested": "Trench Re-inspection",
};

// TRACK 15.46 · FR-03 · Notification action label specificity.
// The raw `type` token (e.g. `project_team_assignment`,
// `daily_report.pending_review`) is technical and tells the operator
// nothing about WHAT action to take. This map translates it into an
// action-oriented verb chip ("Review", "Approve", "Open", "Submit")
// so a PM scanning the bell list knows in 0.5s whether the item
// requires a decision or is purely informational.
//
// Pattern: every label MUST start with an imperative verb
// (Review · Approve · Open · Submit · Acknowledge · Verify) so the
// operator's brain doesn't have to translate "X happened" → "what do
// I do about X". Honest field-real verbs only — no marketing copy.
const TYPE_ACTION_LABEL = {
  // Team / assignment
  project_team_assignment: "Review team change",
  // Tasks
  "task.assigned": "Action assigned task",
  "task.closed": "Acknowledge closed task",
  // Daily reports
  "daily_report.pending_review": "Review daily report",
  "daily_reports.submitted": "Review daily report",
  // Safety incidents / inspections
  "safety.incident.opened": "Review incident",
  "incident.opened": "Review incident",
  "inspection.deficiency": "Review deficiency",
  "inspection.stop_work": "Action stop-work",
  // Pre-Op
  "preop.failed": "Review failed Pre-Op",
  // PO
  "po.approval_visibility": "Review PO request",
  "po.receipt_received": "Acknowledge receipt",
  // Asset transfers
  "asset_transfer.requested": "Review transfer request",
  "asset_transfer.approved": "Acknowledge transfer",
  "asset_transfer.dispatch_pickup": "Dispatch pickup",
  "asset_transfer.in_transit": "Track in-transit",
  "asset_transfer.received": "Acknowledge received",
  "asset_transfer.rejected": "Review rejection",
  // Fuel/Lube
  "fuel_lube.issue_reported": "Review fuel/lube issue",
  "fuel_lube.issue_reported.dispatch": "Action fuel/lube issue",
  // Fire ext / fleet
  "fire_ext.deficiency": "Review extinguisher deficiency",
  "dvir.defect.oos": "Review OOS defect",
  "shop_assignment": "Review shop assignment",
  // Safety forms
  "safety_form.issuance.submitted": "Acknowledge issuance",
  "safety_form.return.submitted": "Acknowledge return",
  "safety_form.training.submitted": "Acknowledge training",
  // Documents
  "document.expired": "Renew expired document",
  "document.expiring": "Renew expiring document",
  // Payroll
  "payroll_variance.manual_run": "Review payroll variance",
  // Trench safety
  "trench_safety.hold_opened": "Review trench hold",
  "trench_safety.hold_cleared": "Acknowledge hold cleared",
  "trench_safety.inspection_failed": "Review failed inspection",
  "trench_safety.damage_report": "Review damage report",
  "trench_safety.cert_expired": "Renew expired certification",
  "trench_safety.cert_due_soon_7": "Renew certification (≤ 7d)",
  "trench_safety.cert_due_soon_14": "Renew certification (≤ 14d)",
  "trench_safety.cert_due_soon_30": "Renew certification (≤ 30d)",
  "trench_safety.reinspection_requested": "Schedule re-inspection",
  "trench_safety.repair_awaiting_safety": "Verify repair",
  "trench_safety.asset_returned_to_service": "Acknowledge return",
  // Operations Actions
  "oa_assignment": "Action assigned item",
  // System
  "system": "Review notification",
};

// Resolve an `n.type` token to an action-verb label. Falls back to a
// humanized version of the raw type so unmapped events still read
// reasonably (e.g. `fleet.defect.assignment` → "Fleet · Defect ·
// Assignment").
function actionLabelFor(rawType) {
  if (!rawType) return "Review notification";
  if (TYPE_ACTION_LABEL[rawType]) return TYPE_ACTION_LABEL[rawType];
  // Prefix match for namespaced events with dynamic suffixes.
  for (const key of Object.keys(TYPE_ACTION_LABEL)) {
    if (rawType.startsWith(key + ".") || rawType.startsWith(key + "_")) {
      return TYPE_ACTION_LABEL[key];
    }
  }
  // Humanize fallback: snake/dot/colon → Title · Case
  return String(rawType)
    .replace(/[._:]+/g, " · ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// TRACK 15.40 · 5-minute "recently read" window per operator approval.
const RECENT_READ_MS = 5 * 60 * 1000;

const MUTE_KEY = "masci.notifications.mute_until";
const LAST_COUNT_KEY = "masci.notifications.last_count";

function readMuteUntil() {
  try {
    const raw = localStorage.getItem(MUTE_KEY);
    if (!raw) return 0;
    const n = parseInt(raw, 10);
    return Number.isFinite(n) ? n : 0;
  } catch { return 0; }
}
function writeMuteUntil(ts) {
  try { localStorage.setItem(MUTE_KEY, String(ts || 0)); } catch { /* noop */ }
}

// Minimal two-tone chime via Web Audio — no asset download, no
// autoplay-policy issue because every call is gated by a previous
// user click (the bell or sign-in).
function playChime() {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const now = ctx.currentTime;
    const ring = (freq, start, dur) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.setValueAtTime(freq, now + start);
      g.gain.setValueAtTime(0.0001, now + start);
      g.gain.exponentialRampToValueAtTime(0.18, now + start + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
      o.connect(g).connect(ctx.destination);
      o.start(now + start);
      o.stop(now + start + dur + 0.05);
    };
    ring(880, 0, 0.18);
    ring(660, 0.16, 0.22);
    setTimeout(() => { try { ctx.close(); } catch { /* noop */ } }, 700);
  } catch { /* silent */ }
}

export default function NotificationBell({ accent = "slate" }) {
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [queueDepth, setQueueDepth] = useState(0);
  const [muteUntil, setMuteUntil] = useState(() => readMuteUntil());
  const lastCountRef = useRef(parseInt(sessionStorage.getItem(LAST_COUNT_KEY) || "0", 10) || 0);
  const navigate = useNavigate();

  const muted = muteUntil > Date.now();
  const hasLivePortalSession = activePortals().length > 0;

  const refreshCount = useCallback(async () => {
    if (!hasLivePortalSession) return;
    const n = await getUnreadCount();
    setUnread(n);
    // Audible cue only when count strictly increases AND not muted
    // AND user has interacted (audio context only works post-gesture
    // — which any signed-in user has done at the login screen).
    if (n > lastCountRef.current && readMuteUntil() <= Date.now()) {
      playChime();
    }
    lastCountRef.current = n;
    try { sessionStorage.setItem(LAST_COUNT_KEY, String(n)); } catch { /* noop */ }
  }, [hasLivePortalSession]);

  // Light polling — 60s. Pauses when tab is hidden.
  useEffect(() => {
    refreshCount();
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") refreshCount();
    }, 60000);
    const onVis = () => { if (document.visibilityState === "visible") refreshCount(); };
    document.addEventListener("visibilitychange", onVis);
    return () => { clearInterval(interval); document.removeEventListener("visibilitychange", onVis); };
  }, [refreshCount]);

  // Phase J — subscribe to the resiliency upload queue.
  useEffect(() => {
    const unsub = onQueueChange((q) => {
      const pending = (q || []).filter((it) => it.status !== "failed").length;
      setQueueDepth(pending);
    });
    return () => { try { unsub && unsub(); } catch { /* ignore */ } };
  }, []);

  // TRACK 15.40 · 5-minute "recently read" persistence.
  // We persist a small `{id → readTimestampMs}` map to localStorage
  // so the amber pulse survives drawer close+open AND hard reloads
  // within the 5-min window. Pruned on every read so the map never
  // grows beyond the active window.
  const RECENT_READ_LS_KEY = "masci.notif.recentReadStamps";

  const readRecentMap = useCallback(() => {
    try {
      const raw = localStorage.getItem(RECENT_READ_LS_KEY);
      if (!raw) return {};
      const map = JSON.parse(raw);
      const now = Date.now();
      let mutated = false;
      for (const k of Object.keys(map)) {
        if (typeof map[k] !== "number" || now - map[k] > RECENT_READ_MS) {
          delete map[k];
          mutated = true;
        }
      }
      if (mutated) {
        try { localStorage.setItem(RECENT_READ_LS_KEY, JSON.stringify(map)); } catch { /* quota */ }
      }
      return map;
    } catch {
      return {};
    }
  }, []);

  const writeRecentRead = useCallback((id, ts) => {
    try {
      const map = readRecentMap();
      map[id] = ts;
      localStorage.setItem(RECENT_READ_LS_KEY, JSON.stringify(map));
    } catch { /* quota */ }
  }, [readRecentMap]);

  const fetchItems = useCallback(async () => {
    if (!hasLivePortalSession) {
      setItems([]);
      return;
    }
    setLoading(true);
    try {
      const r = await listNotifications({ limit: 30 });
      const recent = readRecentMap();
      // TRACK 15.40 · merge stale-but-still-recent stamps onto the
      // fresh server payload so the amber pulse persists across
      // drawer reopens and reloads.
      setItems((r.items || []).map((n) => (
        recent[n.id] ? { ...n, _recently_read_at: recent[n.id] } : n
      )));
    } finally {
      setLoading(false);
    }
  }, [hasLivePortalSession, readRecentMap]);

  const handleOpenChange = (v) => {
    setOpen(v);
    if (v) fetchItems();
    else refreshCount();
  };

  const onItemClick = async (n) => {
    if (!n.is_read) {
      try { await markRead(n.id); } catch { /* silent */ }
      // TRACK 15.40 · stamp `_recently_read_at` locally (state + ls)
      // so the row shows the amber "recently read" pulse for the next
      // 5 minutes. No schema change; client-only ephemeral state.
      const stamp = Date.now();
      writeRecentRead(n.id, stamp);
      setItems((prev) => prev.map((x) => x.id === n.id ? { ...x, is_read: true, _recently_read_at: stamp } : x));
    }
    // Click-through routing — prefer explicit link_url, then linked task.
    const target = n.link_url || n.url || (n.linked_task_id ? `/tasks?id=${n.linked_task_id}` : null);
    if (target) {
      setOpen(false);
      navigate(target);
    }
  };

  const onMarkAll = async () => {
    try { await markAllRead(); } catch { /* silent */ }
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    setUnread(0);
  };

  const applyMute = (hours) => {
    const next = hours > 0 ? Date.now() + hours * 60 * 60 * 1000 : 0;
    writeMuteUntil(next);
    setMuteUntil(next);
  };

  // Don't render anything when fully signed-out.
  if (!isSignedInAnywhere() || !hasLivePortalSession) return null;

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetTrigger asChild>
        <button
          type="button"
          className={`relative inline-flex items-center justify-center w-10 h-10 rounded-sm border ${accent === "white" ? "border-white/20 text-white hover:bg-white/10" : "border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50"} transition-colors wp16-focus-ring`}
          title={muted ? "Notifications · sound muted" : "Notifications"}
          data-testid="notification-bell"
          aria-label="Notifications"
        >
          {muted ? <BellOff className="w-5 h-5 opacity-80" /> : <Bell className="w-5 h-5" />}
          {unread > 0 && (
            <span
              className="absolute -top-1 -right-1 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-red-600 text-white text-[10px] font-black border-2 border-white"
              data-testid="notification-bell-badge"
            >
              {unread > 99 ? "99+" : unread}
            </span>
          )}
          {queueDepth > 0 && (
            <span
              className="absolute -bottom-1 -right-1 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-amber-500 text-white text-[10px] font-black border-2 border-white"
              data-testid="notification-bell-queue-badge"
              title={`${queueDepth} upload${queueDepth === 1 ? "" : "s"} queued`}
            >
              <Upload className="w-2.5 h-2.5" />
            </span>
          )}
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-md p-0 flex flex-col bg-white" data-testid="notification-drawer">
        <SheetHeader className="px-5 pt-5 pb-3 border-b-2 border-zinc-900 bg-zinc-50">
          {/* Track 15.1 (2026-06-16) — Defect 3 iPad layout fix:
              pr-12 reserves space for the Shadcn close X (absolute
              right-4 top-4); flex-wrap on the sound row prevents
              cramped overflow on iPad portrait widths. */}
          <div className="flex items-center justify-between gap-3 pr-12">
            <SheetTitle className="font-display text-lg">Notifications</SheetTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={onMarkAll}
              disabled={items.every((x) => x.is_read)}
              className="text-xs whitespace-nowrap"
              data-testid="notification-mark-all-read"
            >
              <CheckCheck className="w-3.5 h-3.5 mr-1" /> Mark all read
            </Button>
          </div>
          <div className="flex items-center gap-2 mt-3 flex-wrap" data-testid="notification-sound-controls">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500 shrink-0">Sound</span>
            <Button
              type="button"
              size="sm"
              variant={muted ? "outline" : "default"}
              onClick={() => applyMute(0)}
              className="h-8 px-2.5 text-[11px]"
              data-testid="notification-sound-on"
              aria-pressed={!muted}
            >
              <BellRing className="w-3 h-3 mr-1" /> On
            </Button>
            <Button
              type="button"
              size="sm"
              variant={muted && muteUntil - Date.now() <= 3600 * 1000 + 1000 ? "default" : "outline"}
              onClick={() => applyMute(1)}
              className="h-8 px-2.5 text-[11px]"
              data-testid="notification-snooze-1h"
            >
              Snooze 1h
            </Button>
            <Button
              type="button"
              size="sm"
              variant={muted && muteUntil - Date.now() > 3600 * 1000 + 1000 ? "default" : "outline"}
              onClick={() => applyMute(8)}
              className="h-8 px-2.5 text-[11px]"
              data-testid="notification-snooze-8h"
            >
              Snooze 8h
            </Button>
            <Button
              type="button"
              size="sm"
              variant={muted ? "default" : "outline"}
              onClick={() => applyMute(24 * 365)}
              className="h-8 px-2.5 text-[11px]"
              data-testid="notification-mute"
              title="Mute notification sounds on this device"
            >
              <VolumeX className="w-3 h-3 mr-1" /> Mute
            </Button>
          </div>
          {muted && (
            <p className="text-[10px] text-zinc-500 mt-1" data-testid="notification-mute-status">
              Sound muted until {formatPlatformTime(muteUntil)}. Notifications still arrive silently.
            </p>
          )}
        </SheetHeader>
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="text-center text-zinc-500 py-10 text-sm">Loading…</div>
          ) : items.length === 0 ? (
            <div className="text-center text-zinc-500 py-10 text-sm" data-testid="notification-empty">
              You&apos;re all caught up.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {items.map((n) => {
                const SevIcon = SEV_ICON[n.severity] || Info;
                const localTime = n.created_at ? formatPlatformTime(n.created_at) : "";
                // TRACK 15.40 · "recently read" = read within the last
                // 5 minutes. Drives the amber pulse below.
                const recentlyRead = n.is_read && n._recently_read_at && (Date.now() - n._recently_read_at) < RECENT_READ_MS;
                const sourceLabel = SOURCE_MODULE_LABEL[n.linked_source_module] || n.linked_source_module || null;
                return (
                  <li
                    key={n.id}
                    onClick={() => onItemClick(n)}
                    className={`px-5 py-3.5 cursor-pointer hover:bg-zinc-50 transition-colors ${n.is_read ? "" : "bg-blue-50/50"}`}
                    data-testid={`notification-item-${n.id}`}
                    data-read={n.is_read ? "true" : "false"}
                    data-recently-read={recentlyRead ? "true" : "false"}
                  >
                    <div className="flex items-start gap-3">
                      <SevIcon className={`w-4 h-4 mt-0.5 shrink-0 ${SEV_CLR[n.severity] || "text-slate-500"}`} />
                      <div className="flex-1 min-w-0">
                        <div className="font-bold text-sm text-slate-900 truncate">{n.title}</div>
                        {n.message && (
                          <div className="text-xs text-slate-600 mt-0.5 line-clamp-2">{n.message}</div>
                        )}
                        {/* TRACK 15.40 · traceability chip row.
                            Type · source-module · created-at — all
                            sourced from canonical notification fields,
                            no schema change. */}
                        <div className="flex items-center gap-1.5 mt-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-500 flex-wrap">
                          <span
                            className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200"
                            data-testid={`notification-type-${n.id}`}
                            title={`Action · ${n.type}`}
                          >
                            {actionLabelFor(n.type)}
                          </span>
                          {sourceLabel && (
                            <span
                              className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200"
                              data-testid={`notification-source-${n.id}`}
                              title={`Source module · ${n.linked_source_module}`}
                            >
                              {sourceLabel}
                            </span>
                          )}
                          <span
                            className="text-slate-400 normal-case tracking-normal"
                            title="Local device time"
                            data-testid={`notification-time-${n.id}`}
                          >
                            {localTime}
                          </span>
                          {n.linked_task_id && (
                            <Link
                              to={`/tasks?id=${n.linked_task_id}`}
                              className="inline-flex items-center gap-0.5 text-slate-600 hover:text-slate-900 normal-case tracking-normal"
                              onClick={(e) => e.stopPropagation()}
                              data-testid={`notification-task-link-${n.id}`}
                            >
                              Task <ExternalLink className="w-2.5 h-2.5" />
                            </Link>
                          )}
                        </div>
                      </div>
                      {/* TRACK 15.40 · unread state (solid blue) OR
                          recently-read state (soft amber w/ pulse).
                          After 5 minutes the indicator goes away
                          entirely so the row reads as normal. */}
                      {!n.is_read ? (
                        <span
                          className="inline-block w-2 h-2 rounded-full bg-blue-600 mt-1.5 shrink-0"
                          data-testid={`notification-unread-dot-${n.id}`}
                        />
                      ) : recentlyRead ? (
                        <span
                          className="inline-block w-2 h-2 rounded-full bg-amber-400 mt-1.5 shrink-0 animate-pulse"
                          data-testid={`notification-recent-dot-${n.id}`}
                          title="Recently read"
                        />
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
        <div className="border-t border-zinc-200 px-5 py-3 flex items-center justify-between bg-zinc-50">
          <Link
            to="/tasks"
            className="inline-flex items-center text-xs font-bold uppercase tracking-wide text-zinc-700 hover:text-zinc-900"
            onClick={() => setOpen(false)}
            data-testid="notification-tasks-link"
          >
            View all tasks →
          </Link>
        </div>
      </SheetContent>
    </Sheet>
  );
}
