import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Inbox, Bell, ListChecks, Loader2, CheckCheck, Calendar,
  Activity,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { relativeTime, apiErr } from "@/lib/crewHubUi";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ActivityFeed } from "@/components/ActivityFeed";
import { toast } from "sonner";

/**
 * MyStuff — "Hey!" inbox aggregating the signed-in user's @-mentions,
 * assigned open todos, and cross-project activity. Basecamp's "Hey!" UI.
 *
 * Routes: /app/me
 */
export default function MyStuff() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState(null);
  const [todos, setTodos] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const [n, t] = await Promise.all([
        api.get("/me/notifications"),
        api.get("/me/todos"),
      ]);
      setNotifications(n.data || []);
      setTodos(t.data || []);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load inbox"));
    }
  };

  useEffect(() => { load(); }, []);

  const markAll = async () => {
    setBusy(true);
    try {
      await api.post("/me/notifications/mark-all-read");
      await load();
      toast.success("All caught up");
    } catch {
      toast.error("Could not mark all read");
    } finally {
      setBusy(false);
    }
  };

  const markOne = async (id) => {
    try {
      await api.post(`/me/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => n.id === id
        ? { ...n, read_at: new Date().toISOString() }
        : n));
    } catch { /* ignore */ }
  };

  const toggleTodo = async (t) => {
    try {
      const r = await api.put(`/todos/${t.id}`, { completed: !t.completed_at });
      setTodos((prev) => (r.data.completed_at
        ? prev.filter((x) => x.id !== t.id)
        : prev.map((x) => x.id === t.id ? r.data : x)
      ));
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Could not update"));
    }
  };

  const unreadCount = (notifications || []).filter((n) => !n.read_at).length;

  return (
    <div className="p-8 sm:p-10 max-w-4xl" data-testid="my-stuff-page">
      <div className="mb-6">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold flex items-center gap-1.5">
          <Inbox className="w-3 h-3" /> My Stuff
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
          Hey, {user?.name?.split(" ")[0] || "there"}
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Everything pointed at you — @mentions, assigned to-dos, and recent activity across your projects.
        </p>
      </div>

      <Tabs defaultValue="mentions">
        <TabsList className="bg-white border-2 border-slate-200 p-0 h-auto">
          <TabsTrigger
            value="mentions"
            className="h-12 px-4 data-[state=active]:bg-red-700 data-[state=active]:text-white data-[state=active]:shadow-none rounded-none gap-2 font-bold uppercase tracking-wide text-xs"
            data-testid="tab-mentions"
          >
            <Bell className="w-3.5 h-3.5" /> @ Mentions
            {unreadCount > 0 && (
              <span className="ml-1 px-1.5 rounded-full bg-white text-red-700 text-[10px] font-black leading-4">
                {unreadCount}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger
            value="todos"
            className="h-12 px-4 data-[state=active]:bg-amber-500 data-[state=active]:text-white data-[state=active]:shadow-none rounded-none gap-2 font-bold uppercase tracking-wide text-xs"
            data-testid="tab-todos"
          >
            <ListChecks className="w-3.5 h-3.5" /> My to-dos
            {todos && todos.length > 0 && (
              <span className="ml-1 px-1.5 rounded-full bg-white text-amber-600 text-[10px] font-black leading-4">
                {todos.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger
            value="activity"
            className="h-12 px-4 data-[state=active]:bg-slate-900 data-[state=active]:text-white data-[state=active]:shadow-none rounded-none gap-2 font-bold uppercase tracking-wide text-xs"
            data-testid="tab-activity"
          >
            <Activity className="w-3.5 h-3.5" /> Activity
          </TabsTrigger>
        </TabsList>

        {/* Mentions / notifications */}
        <TabsContent value="mentions" className="mt-4">
          <div className="bg-white border-2 border-slate-200 rounded-md overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b-2 border-slate-100">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
                {unreadCount > 0 ? `${unreadCount} unread` : "All read"}
              </div>
              {unreadCount > 0 && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={markAll}
                  disabled={busy}
                  className="h-8 text-xs font-bold uppercase tracking-wide border-2"
                  data-testid="mark-all-read-btn"
                >
                  {busy ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <CheckCheck className="w-3 h-3 mr-1" />}
                  Mark all read
                </Button>
              )}
            </div>
            {notifications === null ? (
              <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>
            ) : notifications.length === 0 ? (
              <div className="p-10 text-center" data-testid="notifications-empty">
                <Bell className="w-8 h-8 mx-auto text-slate-300" />
                <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">
                  No notifications
                </div>
                <p className="text-slate-600 text-sm mt-1">When someone @-mentions you, you'll see it here.</p>
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {notifications.map((n) => (
                  <li key={n.id} className={`px-4 py-3 ${!n.read_at ? "bg-red-50/40" : ""}`} data-testid={`mystuff-notif-${n.id}`}>
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-red-700 text-white text-xs font-display font-black flex items-center justify-center shrink-0">
                        {(n.actor_name || "?").charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm leading-tight">
                          <span className="font-bold text-slate-900">{n.actor_name}</span>{" "}
                          <span className="text-slate-600">mentioned you in</span>{" "}
                          <span className="font-semibold text-slate-900">{n.target_label}</span>
                        </div>
                        {n.preview && (
                          <div className="text-sm text-slate-700 mt-1 bg-slate-50 border-l-2 border-slate-300 pl-3 py-1 whitespace-pre-wrap">
                            {n.preview}
                          </div>
                        )}
                        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.15em] text-slate-400 mt-2">
                          <span>{n.project_name}</span>
                          <span>·</span>
                          <span>{relativeTime(n.created_at)}</span>
                          {!n.read_at && (
                            <button
                              onClick={() => markOne(n.id)}
                              className="ml-auto text-red-700 hover:text-red-900 font-bold"
                              data-testid={`mystuff-notif-read-${n.id}`}
                            >
                              Mark read
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </TabsContent>

        {/* My assigned todos */}
        <TabsContent value="todos" className="mt-4">
          <div className="bg-white border-2 border-slate-200 rounded-md overflow-hidden">
            {todos === null ? (
              <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-amber-500" /></div>
            ) : todos.length === 0 ? (
              <div className="p-10 text-center" data-testid="mystuff-todos-empty">
                <ListChecks className="w-8 h-8 mx-auto text-slate-300" />
                <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">
                  Nothing on your plate
                </div>
                <p className="text-slate-600 text-sm mt-1">You have zero open to-dos assigned. Good work.</p>
              </div>
            ) : (
              <ul className="divide-y divide-slate-100" data-testid="mystuff-todos">
                {todos.map((t) => (
                  <li key={t.id} className="px-4 py-3 flex items-start gap-3" data-testid={`mystuff-todo-${t.id}`}>
                    <button
                      onClick={() => toggleTodo(t)}
                      className="mt-0.5 w-5 h-5 border-2 border-slate-300 rounded hover:border-amber-500 shrink-0"
                      aria-label="Mark complete"
                      data-testid={`mystuff-todo-check-${t.id}`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-slate-900 font-semibold">{t.title}</div>
                      <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 mt-1">
                        <Link to={`/app/projects/${t.project_id}/todos`} className="text-red-700 font-bold hover:text-red-900">
                          Open list
                        </Link>
                        {t.due_date && (
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="w-3 h-3" /> Due {t.due_date}
                          </span>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </TabsContent>

        {/* Activity feed across all my projects */}
        <TabsContent value="activity" className="mt-4">
          <div className="bg-white border-2 border-slate-200 rounded-md p-4">
            <ActivityFeed scope="me" limit={25} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
