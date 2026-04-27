import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  MessageSquare,
  ListChecks,
  Calendar,
  FolderOpen,
  TrendingUp,
  Users as UsersIcon,
  Building2,
  Home,
  Loader2,
  MapPin,
  Hammer,
} from "lucide-react";
import { api } from "@/lib/api";

/**
 * ProjectHome — landing page inside one project. Shows the 5 Basecamp-style
 * tool tiles (Message Board, To-dos, Schedule, Docs, Hill Charts) plus a
 * Members tile. The tools themselves ship in Phase 2/3 — for now each tile
 * links to a "coming soon" placeholder so the navigation is real.
 */
export default function ProjectHome() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    setProject(null);
    setError(null);
    (async () => {
      try {
        const [p, m] = await Promise.all([
          api.get(`/projects/${projectId}`),
          api.get(`/projects/${projectId}/members`),
        ]);
        if (alive) {
          setProject(p.data);
          setMembers(m.data || []);
        }
      } catch (err) {
        if (alive) setError(err?.response?.data?.detail || "Project not found");
      }
    })();
    return () => {
      alive = false;
    };
  }, [projectId]);

  if (error) {
    return (
      <div className="p-10">
        <div className="bg-red-50 border-2 border-red-300 rounded-md p-6 max-w-xl">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Error</div>
          <div className="text-red-900 text-sm mt-1">{String(error)}</div>
          <Link to="/app" className="inline-block mt-3 text-xs font-mono uppercase tracking-[0.2em] text-red-700 hover:text-red-900 font-bold">
            ← Back to projects
          </Link>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-red-700" />
      </div>
    );
  }

  const tools = [
    { id: "messages", label: "Message Board", desc: "Announcements, discussion, photos.", Icon: MessageSquare, to: `/app/projects/${project.id}/messages`, accent: "red" },
    { id: "todos", label: "To-dos", desc: "Lists, assignees, due dates.", Icon: ListChecks, to: `/app/projects/${project.id}/todos`, accent: "amber" },
    { id: "schedule", label: "Schedule", desc: "Inspections, meetings, deliveries.", Icon: Calendar, to: `/app/projects/${project.id}/schedule`, accent: "emerald" },
    { id: "docs", label: "Docs & Files", desc: "Submittals, specs, RFIs.", Icon: FolderOpen, to: `/app/projects/${project.id}/docs`, accent: "blue" },
    { id: "hills", label: "Hill Charts", desc: "Visual progress tracking.", Icon: TrendingUp, to: `/app/projects/${project.id}/hills`, accent: "slate" },
    { id: "members", label: "Members", desc: `${members.length} ${members.length === 1 ? "person" : "people"} on this project.`, Icon: UsersIcon, to: `/app/projects/${project.id}/members`, accent: "slate" },
  ];

  const accentCls = (a) => ({
    red: "bg-red-700 text-white",
    amber: "bg-amber-500 text-white",
    emerald: "bg-emerald-600 text-white",
    blue: "bg-blue-600 text-white",
    slate: "bg-slate-800 text-white",
  }[a] || "bg-slate-800 text-white");

  return (
    <div className="p-8 sm:p-10 max-w-6xl" data-testid="project-home">
      {/* Project header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-md flex items-center justify-center shrink-0 ${project.is_hq ? "bg-red-700 text-white" : "bg-slate-900 text-white"}`}>
            {project.is_hq ? <Home className="w-6 h-6" /> : <Building2 className="w-6 h-6" />}
          </div>
          <div className="min-w-0">
            {project.project_number && (
              <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">
                {project.project_number}
              </div>
            )}
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 leading-tight mt-0.5">
              {project.name}
            </h1>
            {project.location && (
              <div className="flex items-center gap-1 text-xs text-slate-500 mt-1">
                <MapPin className="w-3 h-3" />
                <span>{project.location}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tool tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="tool-tiles">
        {tools.map((t) => (
          <Link
            key={t.id}
            to={t.to}
            className="group bg-white border-2 border-slate-200 hover:border-red-700 rounded-md p-5 transition-all shadow-sm hover:shadow-md"
            data-testid={`tool-tile-${t.id}`}
          >
            <div className={`w-11 h-11 rounded-md flex items-center justify-center ${accentCls(t.accent)}`}>
              <t.Icon className="w-5 h-5" />
            </div>
            <div className="font-display text-lg font-black text-slate-900 tracking-tight mt-3">{t.label}</div>
            <div className="text-sm text-slate-600 mt-1 leading-snug">{t.desc}</div>
          </Link>
        ))}
      </div>

      <div className="mt-10 bg-amber-50 border-2 border-amber-300 rounded-md p-5 flex items-start gap-3" data-testid="phase-2-notice">
        <Hammer className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-bold">Phase 1 complete · Phase 2 next</div>
          <div className="text-sm text-amber-900 mt-1 leading-relaxed">
            Message Board and To-dos ship in the next build. For now, tool tiles route to a placeholder — use them to show your team the shape of the workspace.
          </div>
        </div>
      </div>
    </div>
  );
}
