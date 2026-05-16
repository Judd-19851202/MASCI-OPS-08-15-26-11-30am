// NotificationBell.jsx — Iter150 (Phase A). Global notification bell
// shown in every protected portal header. Click → drawer with the
// current user's notification feed.
//
// Design notes:
//   * Polls /api/notifications/unread-count every 60s while the tab
//     is foregrounded — light enough to never hit rate limits.
//   * The bell is invisible (no DOM) when the user is fully signed-out.
//   * Mark-as-read happens on drawer close so opening the drawer
//     doesn't immediately reset the badge (gives the user time to
//     read the items first).

import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Bell, CheckCheck, ExternalLink, AlertOctagon, Info, AlertTriangle, Upload } from "lucide-react";
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

export default function NotificationBell({ accent = "slate" }) {
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const refreshCount = useCallback(async () => {
    if (!isSignedInAnywhere()) return;
    const n = await getUnreadCount();
    setUnread(n);
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
  };

  const onMarkAll = async () => {
    try { await markAllRead(); } catch { /* silent */ }
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    setUnread(0);
  };

  // Don't render anything when fully signed-out.
  if (!isSignedInAnywhere()) return null;

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetTrigger asChild>
        <button
          type="button"
          className={`relative inline-flex items-center justify-center w-9 h-9 rounded-md ${accent === "white" ? "text-white hover:bg-white/10" : "text-slate-700 hover:bg-slate-100"} transition-colors`}
          title="Notifications"
          data-testid="notification-bell"
        >
          <Bell className="w-5 h-5" />
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
          <div className="flex items-center justify-between gap-3">
            <SheetTitle className="font-display text-lg">Notifications</SheetTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={onMarkAll}
              disabled={items.every((x) => x.is_read)}
              className="text-xs"
              data-testid="notification-mark-all-read"
            >
              <CheckCheck className="w-3.5 h-3.5 mr-1" /> Mark all read
            </Button>
          </div>
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
                          <span>{new Date(n.created_at).toLocaleString()}</span>
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
slate-700 hover:text-slate-900"
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
