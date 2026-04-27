import React, { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import {
  Home,
  LogOut,
  Users as UsersIcon,
  Building2,
  ChevronRight,
  Loader2,
  Shield,
  Inbox,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { MasciLogo } from "@/components/MasciLogo";
import { NotificationBell } from "@/components/NotificationBell";
import { toast } from "sonner";

/**
 * AppLayout — persistent sidebar for the /app section.
 * Left: MASCI HQ + pinned project list. Right: outlet.
 */
export default function AppLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const { projectId } = useParams();
  const [projects, setProjects] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/projects");
        if (alive) setProjects(r.data || []);
      } catch {
        if (alive) setProjects([]);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const isAdmin = user?.role === "owner" || user?.role === "admin";
  const hq = (projects || []).find((p) => p.is_hq);
  const regular = (projects || []).filter((p) => !p.is_hq);

  return (
    <div className="h-screen flex bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-slate-900 text-white flex flex-col border-r-4 border-red-700 h-screen">
        <div className="p-5 border-b border-slate-800">
          <MasciLogo variant="lockup" size="lg" homeLink="/app" />
          <div className="font-mono text-[9px] uppercase tracking-[0.3em] text-red-400 font-bold mt-2">
            Crew Hub
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          <SidebarLink to="/app" end icon={Home} label="Home" testId="sidebar-home" />
          <SidebarLink to="/app/me" icon={Inbox} label="My Stuff" testId="sidebar-my-stuff" />
          {hq && (
            <SidebarLink
              to={`/app/projects/${hq.id}`}
              icon={Building2}
              label="MASCI HQ"
              accent="red"
              testId="sidebar-hq"
            />
          )}

          {projects === null && (
            <div className="flex justify-center py-6">
              <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
            </div>
          )}

          {regular.length > 0 && (
            <div className="pt-4">
              <div className="font-mono text-[9px] uppercase tracking-[0.3em] text-slate-500 font-bold px-3 pb-2">
                Projects · {regular.length}
              </div>
              <div className="space-y-0.5">
                {regular.map((p) => (
                  <SidebarLink
                    key={p.id}
                    to={`/app/projects/${p.id}`}
                    icon={null}
                    label={
                      <span className="truncate block">
                        <span className="font-mono text-[10px] text-slate-400">{p.project_number}</span>
                        {"  "}
                        <span className="text-slate-200">{shortName(p.name, p.project_number)}</span>
                      </span>
                    }
                    testId={`sidebar-project-${p.id}`}
                    compact
                  />
                ))}
              </div>
            </div>
          )}

          {isAdmin && (
            <div className="pt-4">
              <div className="font-mono text-[9px] uppercase tracking-[0.3em] text-slate-500 font-bold px-3 pb-2">
                Admin
              </div>
              <SidebarLink to="/app/users" icon={UsersIcon} label="Users" testId="sidebar-users" />
              <SidebarLink to="/admin" icon={Shield} label="Safety Admin" testId="sidebar-safety-admin" external />
            </div>
          )}
        </nav>

        {/* User footer */}
        <div className="border-t border-slate-800 p-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 shrink-0 rounded-full bg-red-700 flex items-center justify-center font-display font-black text-sm">
              {(user?.name || user?.email || "?").charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold text-white truncate">{user?.name || user?.email}</div>
              <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-400 truncate">
                {user?.role}
              </div>
            </div>
            <NotificationBell />
            <button
              onClick={async () => {
                await logout();
                toast.success("Signed out");
                nav("/app/login", { replace: true });
              }}
              className="p-2 rounded hover:bg-slate-800 text-slate-400 hover:text-red-400 transition-colors"
              title="Sign out"
              data-testid="sidebar-logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main outlet */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden">
        <Outlet key={projectId || "home"} />
      </main>
    </div>
  );
}

function SidebarLink({ to, icon: Icon, label, testId, compact, accent, external, end }) {
  const base = "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors";
  const activeCls = accent === "red"
    ? "bg-red-700 text-white font-bold"
    : "bg-slate-800 text-white font-bold";
  const idleCls = "text-slate-300 hover:bg-slate-800 hover:text-white";

  if (external) {
    return (
      <a href={to} className={`${base} ${idleCls}`} data-testid={testId}>
        {Icon && <Icon className="w-4 h-4 shrink-0" />}
        <span className="truncate">{label}</span>
        <ChevronRight className="w-3 h-3 ml-auto opacity-50" />
      </a>
    );
  }
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => `${base} ${compact ? "py-1.5 pl-6" : ""} ${isActive ? activeCls : idleCls}`}
      data-testid={testId}
    >
      {Icon && <Icon className="w-4 h-4 shrink-0" />}
      <span className="flex-1 truncate">{label}</span>
    </NavLink>
  );
}

function shortName(name, projectNumber) {
  if (!name) return "";
  // Strip the T-code + project number prefix if it's in the name already
  const prefixes = [projectNumber, "T", "E", "SJR", "CC", "G2"];
  for (const p of prefixes) {
    if (name.startsWith(`${p}5`) || name.startsWith(`${p} `)) {
      // take everything after first " - " or first space block
      const dash = name.indexOf(" - ");
      if (dash > 0) return name.slice(dash + 3);
      const space = name.indexOf(" ");
      return name.slice(space + 1);
    }
  }
  return name;
}
