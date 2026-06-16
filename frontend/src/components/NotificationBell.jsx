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
import { isSignedInAnywhere } from "@/lib/permissions";
import { onQueueChange } from "@/lib/resiliency";

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

  const refreshCount = useCallback(async () => {
    if (!isSignedInAnywhere()) return;
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
  }, []);

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

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listNotifications({ limit: 30 });
      setItems(r.items || []);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleOpenChange = (v) => {
    setOpen(v);
    if (v) fetchItems();
    else refreshCount();
  };

  const onItemClick = async (n) => {
    if (!n.is_read) {
      try { await markRead(n.id); } catch { /* silent */ }
      setItems((prev) => prev.map((x) => x.id === n.id ? { ...x, is_read: true } : x));
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
  if (!isSignedInAnywhere()) return null;

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetTrigger asChild>
        <button
          type="button"
          className={`relative inline-flex items-center justify-center w-9 h-9 rounded-md ${accent === "white" ? "text-white hover:bg-white/10" : "text-slate-700 hover:bg-slate-100"} transition-colors`}
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
      <SheetContent side="right" className="w-full sm:max-w-md p-0 flex flex-col" data-testid="notification-drawer">
        <SheetHeader className="px-5 pt-5 pb-3 border-b border-slate-200">
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
            <p className="text-[10px] text-slate-500 mt-1" data-testid="notification-mute-status">
              Sound muted until {new Date(muteUntil).toLocaleString()}. Notifications still arrive silently.
            </p>
          )}
        </SheetHeader>
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="text-center text-slate-500 py-10 text-sm">Loading…</div>
          ) : items.length === 0 ? (
            <div className="text-center text-slate-500 py-10 text-sm" data-testid="notification-empty">
              You&apos;re all caught up.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {items.map((n) => {
                const SevIcon = SEV_ICON[n.severity] || Info;
                const localTime = n.created_at ? new Date(n.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" }) : "";
                return (
                  <li
                    key={n.id}
                    onClick={() => onItemClick(n)}
                    className={`px-5 py-3.5 cursor-pointer hover:bg-slate-50 transition-colors ${n.is_read ? "" : "bg-blue-50/50"}`}
                    data-testid={`notification-item-${n.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <SevIcon className={`w-4 h-4 mt-0.5 shrink-0 ${SEV_CLR[n.severity] || "text-slate-500"}`} />
                      <div className="flex-1 min-w-0">
                        <div className="font-bold text-sm text-slate-900 truncate">{n.title}</div>
                        {n.message && (
                          <div className="text-xs text-slate-600 mt-0.5 line-clamp-2">{n.message}</div>
                        )}
                        <div className="flex items-center gap-2 mt-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400">
                          <span>{n.type}</span>
                          <span>·</span>
                          <span title="Local device time">{localTime}</span>
                          {n.linked_task_id && (
                            <>
                              <span>·</span>
                              <Link
                                to={`/tasks?id=${n.linked_task_id}`}
                                className="inline-flex items-center gap-0.5 text-slate-600 hover:text-slate-900"
                                onClick={(e) => e.stopPropagation()}
                                data-testid={`notification-task-link-${n.id}`}
                              >
                                Task <ExternalLink className="w-2.5 h-2.5" />
                              </Link>
                            </>
                          )}
                        </div>
                      </div>
                      {!n.is_read && (
                        <span className="inline-block w-2 h-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
        <div className="border-t border-slate-200 px-5 py-3 flex items-center justify-between">
          <Link
            to="/tasks"
            className="inline-flex items-center text-xs font-bold uppercase tracking-wide text-slate-700 hover:text-slate-900"
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
