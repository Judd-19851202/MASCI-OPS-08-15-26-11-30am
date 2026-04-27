import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Building2, MapPin, Loader2, ArrowRight, Home } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";

/**
 * AppHome — /app landing page. Grid of cards for every project the
 * signed-in user has access to, with HQ pinned first.
 */
export default function AppHome() {
  const { user } = useAuth();
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

  return (
    <div className="p-8 sm:p-10 max-w-6xl">
      <div className="mb-8">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">
          Welcome, {user?.name?.split(" ")[0] || "there"}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
          What are you working on today?
        </h1>
        <p className="text-slate-600 mt-2 text-sm max-w-2xl">
          Every MASCI job has its own workspace here — message board, to-dos, schedule, docs, and progress tracking. Pick a project to jump in.
        </p>
      </div>

      {projects === null && (
        <div className="flex items-center gap-2 text-slate-500 py-16 justify-center">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading projects…
        </div>
      )}

      {projects !== null && projects.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold">No projects yet</div>
          <p className="text-slate-600 mt-2 text-sm">
            An owner will add you to projects shortly. You still have MASCI HQ below for company-wide announcements.
          </p>
        </div>
      )}

      {projects !== null && projects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="project-grid">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/app/projects/${p.id}`}
              className="group bg-white border-2 border-slate-200 hover:border-red-700 rounded-md p-5 transition-all shadow-sm hover:shadow-md"
              data-testid={`project-card-${p.id}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className={`w-10 h-10 rounded-md flex items-center justify-center shrink-0 ${p.is_hq ? "bg-red-700 text-white" : "bg-slate-100 text-slate-700"}`}>
                  {p.is_hq ? <Home className="w-5 h-5" /> : <Building2 className="w-5 h-5" />}
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-red-700 group-hover:translate-x-1 transition-all" />
              </div>
              <div className="mt-3">
                {p.project_number && (
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold">
                    {p.project_number}
                  </div>
                )}
                <div className="font-display text-base font-black text-slate-900 leading-tight mt-1 line-clamp-2 min-h-[2.5rem]">
                  {p.name}
                </div>
                {p.location && (
                  <div className="flex items-center gap-1 text-xs text-slate-500 mt-2">
                    <MapPin className="w-3 h-3" />
                    <span className="truncate">{p.location}</span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
