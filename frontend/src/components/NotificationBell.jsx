import React, { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { Bell, CheckCheck, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { relativeTime } from "@/lib/crewHubUi";
import { toast } from "sonner";

const POLL_MS = 60_000;

/**
 * NotificationBell — sidebar bell with unread count. Dropdown lists the
 * latest 10 notifications; clicking one marks it read; "Mark all read" CTA
 * at the bottom. Polls every 60s.
 */
export function NotificationBell() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);

  const load = async () => {
    try {
      const r = await api.get("/me/notifications");
      setItems(r.data || []);
    } catch {
      // silent — don't spam the sidebar with errors
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, []);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const onDown = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  const unread = items.filter((n) => !n.read_at);
  const unreadCount = unread.length;

  const markOne = async (id) => {
    try {
      await api.post(`/me/notifications/${id}/read`);
      setItems((prev) => prev.map((n) => n.id === id ? { ...n, read_at: new Date().toISOString() } : n));
    } catch { /* ignore */ }
  };

  const markAll = async () => {
    setLoading(true);
    try {
      await api.post("/me/notifications/mark-all-read");
      setItems((prev) => prev.map((n) => ({ ...n, read_at: n.read_at || new Date().toISOString() })));
      toast.success("All notifications marked read");
    } catch {
      toast.error("Could not mark all read");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
        title={unreadCount > 0 ? `${unreadCount} unread` : "Notifications"}
        data-testid="notification-bell"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 min-w-[16px] h-[16px] px-1 rounded-full bg-red-600 text-white text-[9px] font-black leading-[16px] text-center font-mono"
            data-testid="notification-badge"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute z-50 bottom-full right-0 mb-2 w-80 max-h-[26rem] overflow-y-auto bg-white text-slate-900 border-2 border-slate-200 rounded-md shadow-xl"
          data-testid="notification-dropdown"
        >
          <div className="flex items-center justify-between px-3 py-2 border-b-2 border-slate-100">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
              Notifications
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAll}
                disabled={loading}
                className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.1em] text-slate-500 hover:text-red-700 font-bold"
                data-testid="notification-mark-all-read"
              >
                {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCheck className="w-3 h-3" />}
                Mark all read
              </button>
            )}
          </div>
          {items.length === 0 ? (
            <div className="p-5 text-center text-sm text-slate-500" data-testid="notification-empty">
              You're all caught up.
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {items.slice(0, 15).map((n) => (
                <li key={n.id}>
                  <Link
                    to="/app/me"
                    onClick={() => markOne(n.id)}
                    className={`block px-3 py-2.5 hover:bg-slate-50 ${!n.read_at ? "bg-red-50/40" : ""}`}
                    data-testid={`notification-${n.id}`}
                  >
                    <div className="text-sm leading-tight">
                      <span className="font-bold">{n.actor_name}</span>{" "}
                      <span className="text-slate-600">mentioned you in</span>{" "}
                      <span className="font-semibold">{n.target_label}</span>
                    </div>
                    {n.preview && (
                      <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{n.preview}</div>
                    )}
                    <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.1em] text-slate-400 mt-1">
                      <span>{n.project_name}</span>
                      <span>·</span>
                      <span>{relativeTime(n.created_at)}</span>
                      {!n.read_at && (
                        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-red-600" title="Unread" />
                      )}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div className="border-t-2 border-slate-100 p-2">
            <Link
              to="/app/me"
              onClick={() => setOpen(false)}
              className="block text-center text-[10px] font-mono uppercase tracking-[0.2em] text-red-700 hover:text-red-900 font-bold py-1.5"
              data-testid="notification-open-inbox"
            >
              Open My Stuff →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
