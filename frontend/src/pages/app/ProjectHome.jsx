import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  MessageSquare, ListChecks, Calendar, FolderOpen, TrendingUp, Users as UsersIcon,
  Building2, Home, Loader2, MapPin, ArrowRight, Plus, FileText, Clock, Check,
} from "lucide-react";
import { api } from "@/lib/api";
import { UserAvatar, relativeTime, apiErr } from "@/lib/crewHubUi";
import { toast } from "sonner";

/**
 * ProjectHome — scorecard layout inspired by Basecamp's per-project view.
 * Loads project + members + scorecard aggregate (single endpoint, 1 round
 * trip) then renders 6 tiles in a 3-column grid: Message Board, To-dos,
 * Schedule, Docs, Hill Charts, Members. Each tile shows a snapshot of the
 * latest content so PMs see everything at a glance.
 */
export default function ProjectHome() {
  const { projectId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    setError(null);
    (async () => {
      try {
        const [p, m, s] = await Promise.all([
          api.get(`/projects/${projectId}`),
          api.get(`/projects/${projectId}/members`),
          api.get(`/projects/${projectId}/scorecard`),
        ]);
        if (alive) setData({ project: p.data, members: m.data, scorecard: s.data });
      } catch (err) {
        if (alive) setError(apiErr(err?.response?.data?.detail, "Project not found"));
      }
    })();
    return () => { alive = false; };
  }, [projectId]);

  if (error) {
    return (
      <div className="p-10">
        <div className="bg-red-50 border-2 border-red-300 rounded-md p-6 max-w-xl">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Error</div>
          <div className="text-red-900 text-sm mt-1">{error}</div>
          <Link to="/app" className="inline-block mt-3 text-xs font-mono uppercase tracking-[0.2em] text-red-700 hover:text-red-900 font-bold">
            ← Back to projects
          </Link>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-red-700" />
      </div>
    );
  }

  const { project, members, scorecard } = data;
  const base = `/app/projects/${project.id}`;

  return (
    <div className="p-6 sm:p-8 max-w-6xl" data-testid="project-home">
      {/* Project header */}
      <div className="mb-6">
        <div className="flex items-start gap-3 flex-wrap">
          <div className={`w-12 h-12 rounded-md flex items-center justify-center shrink-0 ${project.is_hq ? "bg-red-700 text-white" : "bg-slate-900 text-white"}`}>
            {project.is_hq ? <Home className="w-6 h-6" /> : <Building2 className="w-6 h-6" />}
          </div>
          <div className="flex-1 min-w-0">
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
          {/* Member avatar stack */}
          <Link
            to={`${base}/members`}
            className="flex -space-x-2 hover:opacity-80 transition-opacity"
            title={`${members.length} ${members.length === 1 ? "person" : "people"}`}
            data-testid="members-avatar-stack"
          >
            {members.slice(0, 5).map((m) => (
              <div key={m.user_id} className="ring-2 ring-white rounded-full">
                <UserAvatar name={m.name} userId={m.user_id} size="sm" />
              </div>
            ))}
            {members.length > 5 && (
              <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 text-[10px] font-mono font-black flex items-center justify-center ring-2 ring-white">
                +{members.length - 5}
              </div>
            )}
          </Link>
        </div>
      </div>

      {/* Hill Chart snapshot at top (like Basecamp IMG_4413) */}
      {scorecard.hill_scopes.length > 0 && (
        <HillSnapshot scopes={scorecard.hill_scopes} to={`${base}/hills`} />
      )}

      {/* Scorecard grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="scorecard-grid">
        <MessageBoardCard scorecard={scorecard} to={`${base}/messages`} />
        <TodosCard scorecard={scorecard} to={`${base}/todos`} />
        <ScheduleCard scorecard={scorecard} to={`${base}/schedule`} />
        <DocsCard scorecard={scorecard} to={`${base}/docs`} />
      </div>

      {/* Secondary tiles row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <SmallTile
          to={`${base}/hills`}
          icon={TrendingUp}
          label="Hill Charts"
          badge={`${scorecard.hill_scopes.length} scopes`}
          accent="slate"
        />
        <SmallTile
          to={`${base}/members`}
          icon={UsersIcon}
          label="Members"
          badge={`${members.length} ${members.length === 1 ? "person" : "people"}`}
          accent="slate"
        />
      </div>
    </div>
  );
}

// ------------------------- Cards -------------------------
function Card({ to, title, icon: Icon, accent, action, children, empty, testId }) {
  const accentBar = {
    red: "border-t-red-700",
    amber: "border-t-amber-500",
    emerald: "border-t-emerald-600",
    blue: "border-t-blue-600",
    slate: "border-t-slate-800",
  }[accent] || "border-t-slate-800";
  return (
    <div className={`bg-white border-2 border-slate-200 ${accentBar} border-t-4 rounded-md p-5 flex flex-col`} data-testid={testId}>
      <div className="flex items-center justify-between mb-3">
        <Link to={to} className="flex items-center gap-2 group">
          <Icon className="w-4 h-4 text-slate-700" />
          <span className="font-display font-black text-slate-900 text-base group-hover:text-red-700 transition-colors">{title}</span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-red-700 group-hover:translate-x-0.5 transition-all" />
        </Link>
        {action && (
          <Link
            to={action.to}
            className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.15em] font-bold text-slate-500 hover:text-red-700"
          >
            <Plus className="w-3 h-3" /> {action.label}
          </Link>
        )}
      </div>
      <div className="flex-1">
        {empty ? (
          <div className="text-sm text-slate-400 italic py-4">{empty}</div>
        ) : children}
      </div>
    </div>
  );
}

function MessageBoardCard({ scorecard, to }) {
  const msgs = scorecard.messages;
  return (
    <Card
      to={to}
      title="Message Board"
      icon={MessageSquare}
      accent="red"
      testId="scorecard-messages"
      empty={msgs.length === 0 ? "No posts yet — start the first discussion." : null}
    >
      <div className="space-y-3">
        {msgs.map((m) => (
          <Link
            key={m.id}
            to={to}
            className="flex items-start gap-2.5 -mx-2 px-2 py-1.5 rounded hover:bg-slate-50 transition-colors"
          >
            <UserAvatar name={m.author_name} userId={m.author_id} size="sm" />
            <div className="flex-1 min-w-0">
              <div className="font-display font-bold text-slate-900 text-sm truncate">{m.title}</div>
              <div className="text-xs text-slate-600 line-clamp-1">{m.body_preview}</div>
              <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.1em] text-slate-500 mt-0.5">
                <span className="font-bold">{m.author_name.split(" ")[0]}</span>
                <span>·</span>
                <span>{relativeTime(m.created_at)}</span>
                {m.comment_count > 0 && (
                  <>
                    <span>·</span>
                    <span className="inline-flex items-center gap-0.5"><MessageSquare className="w-3 h-3" /> {m.comment_count}</span>
                  </>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function TodosCard({ scorecard, to }) {
  const { open, done, total } = scorecard.todos;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return (
    <Card
      to={to}
      title="To-dos"
      icon={ListChecks}
      accent="amber"
      testId="scorecard-todos"
      empty={total === 0 ? "No lists yet — start with a punch list." : null}
    >
      {total > 0 && (
        <>
          <div className="flex items-baseline gap-2">
            <span className="font-display text-3xl font-black text-slate-900">{open}</span>
            <span className="text-sm text-slate-600">open</span>
            <span className="text-xs font-mono uppercase tracking-[0.15em] text-slate-400 ml-auto">
              {done} of {total} done
            </span>
          </div>
          <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="text-xs text-slate-600 mt-2">
            {pct}% complete across this project.
          </div>
        </>
      )}
    </Card>
  );
}

function ScheduleCard({ scorecard, to }) {
  const events = scorecard.events;
  const fmtDay = (iso) => {
    const d = new Date(iso.length > 10 ? iso : iso + "T12:00:00");
    return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  };
  const fmtTime = (iso) => new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return (
    <Card
      to={to}
      title="Schedule"
      icon={Calendar}
      accent="emerald"
      testId="scorecard-schedule"
      empty={events.length === 0 ? "Nothing scheduled." : null}
    >
      <div className="space-y-2.5">
        {events.map((e) => (
          <Link
            key={e.id}
            to={to}
            className="flex items-start gap-3 -mx-2 px-2 py-1.5 rounded hover:bg-slate-50 transition-colors"
          >
            <div className="w-10 h-10 rounded-md bg-emerald-50 border border-emerald-200 flex flex-col items-center justify-center shrink-0">
              <div className="font-mono text-[8px] uppercase tracking-[0.1em] text-emerald-700 font-black leading-none">
                {fmtDay(e.starts_at).split(" ")[1]}
              </div>
              <div className="font-display font-black text-emerald-900 text-sm leading-none mt-0.5">
                {fmtDay(e.starts_at).split(" ")[2]}
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-display font-bold text-slate-900 text-sm truncate">{e.title}</div>
              <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.1em] text-slate-500 mt-0.5">
                <Clock className="w-3 h-3" />
                {e.all_day ? "All day" : fmtTime(e.starts_at)}
                {e.location && <><span>·</span><span className="truncate">{e.location}</span></>}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function DocsCard({ scorecard, to }) {
  const docs = scorecard.docs;
  return (
    <Card
      to={to}
      title="Docs & Files"
      icon={FolderOpen}
      accent="blue"
      testId="scorecard-docs"
      empty={docs.length === 0 ? "No files uploaded yet." : null}
    >
      <div className="space-y-2">
        {docs.map((d) => (
          <Link
            key={d.id}
            to={to}
            className="flex items-center gap-2.5 -mx-2 px-2 py-1.5 rounded hover:bg-slate-50 transition-colors"
          >
            <div className="w-9 h-9 rounded-md bg-blue-600 text-white flex items-center justify-center shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-display font-bold text-slate-900 text-sm truncate">{d.filename}</div>
              <div className="text-[10px] font-mono uppercase tracking-[0.1em] text-slate-500 mt-0.5 truncate">
                {d.category} · {d.uploaded_by_name.split(" ")[0]} · {relativeTime(d.uploaded_at)}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function HillSnapshot({ scopes, to }) {
  // Inline mini SVG with just the first few scopes rendered non-interactive
  const W = 800, H = 120, margin = 20;
  const curveW = W - margin * 2;
  const hillY = (pos) => Math.round(-Math.sin((pos / 100) * Math.PI) * 40);
  const pathPts = [];
  for (let i = 0; i <= 50; i++) {
    const pos = i * 2;
    const x = margin + (pos / 100) * curveW;
    const y = H - 20 + hillY(pos);
    pathPts.push(`${i === 0 ? "M" : "L"}${x},${y}`);
  }
  const scopeColor = (id) => {
    const palette = ["#b91c1c", "#d97706", "#059669", "#2563eb", "#7c3aed", "#db2777", "#334155", "#ea580c"];
    const h = (id || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0);
    return palette[h % palette.length];
  };

  return (
    <Link
      to={to}
      className="block bg-white border-2 border-slate-200 border-t-4 border-t-slate-800 rounded-md p-5 mb-4 hover:border-red-700 transition-colors"
      data-testid="scorecard-hill-snapshot"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-slate-700" />
          <span className="font-display font-black text-slate-900 text-base">Hill Chart</span>
          <span className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 font-bold">
            · {scopes.length} scope{scopes.length === 1 ? "" : "s"}
          </span>
        </div>
        <span className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 font-bold">
          View chart →
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 140 }}>
        <line x1={W/2} y1={10} x2={W/2} y2={H-10} stroke="#cbd5e1" strokeWidth="1" strokeDasharray="3 3" />
        <path d={pathPts.join(" ")} fill="none" stroke="#334155" strokeWidth="2" strokeLinecap="round" />
        {scopes.map((s) => {
          const cx = margin + (s.position / 100) * curveW;
          const cy = H - 20 + hillY(s.position);
          return (
            <circle key={s.id} cx={cx} cy={cy} r="7" fill={scopeColor(s.id)} stroke="white" strokeWidth="2" />
          );
        })}
      </svg>
      <div className="flex flex-wrap gap-2 mt-3">
        {scopes.map((s) => (
          <span
            key={s.id}
            className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono uppercase tracking-[0.1em] font-bold bg-slate-100 text-slate-700"
          >
            <span className="w-2 h-2 rounded-full" style={{ background: scopeColor(s.id) }} />
            {s.title.length > 20 ? s.title.slice(0, 18) + "…" : s.title}
            <span className="text-slate-400">· {s.position}%</span>
          </span>
        ))}
      </div>
    </Link>
  );
}

function SmallTile({ to, icon: Icon, label, badge, accent }) {
  const accentCls = {
    slate: "bg-slate-800 text-white",
    red: "bg-red-700 text-white",
  }[accent] || "bg-slate-800 text-white";
  return (
    <Link
      to={to}
      className="bg-white border-2 border-slate-200 hover:border-red-700 rounded-md p-4 flex items-center gap-3 transition-colors"
    >
      <div className={`w-10 h-10 rounded-md flex items-center justify-center ${accentCls}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1">
        <div className="font-display font-black text-slate-900">{label}</div>
        <div className="text-xs font-mono uppercase tracking-[0.15em] text-slate-500 font-bold mt-0.5">{badge}</div>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-300" />
    </Link>
  );
}
