import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Search as SearchIcon, Loader2, MessageSquare, ListChecks, FileText, Calendar, X } from "lucide-react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";

/**
 * ProjectSearch — per-project instant search across messages, to-dos,
 * docs, events. Dropdown results. Backend: /api/projects/{id}/search?q=...
 */
export function ProjectSearch({ projectId }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (q.trim().length < 2) {
      setResults(null);
      return;
    }
    setLoading(true);
    timerRef.current = setTimeout(async () => {
      try {
        const r = await api.get(`/projects/${projectId}/search`, { params: { q: q.trim() } });
        setResults(r.data);
      } catch {
        setResults({ messages: [], todos: [], docs: [], events: [] });
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => timerRef.current && clearTimeout(timerRef.current);
  }, [q, projectId]);

  const totalCount = results
    ? results.messages.length + results.todos.length + results.docs.length + results.events.length
    : 0;
  const base = `/app/projects/${projectId}`;

  return (
    <div className="relative w-full max-w-sm" data-testid="project-search">
      <div className="relative">
        <SearchIcon className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Search this project…"
          className="pl-9 pr-9 h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
          data-testid="project-search-input"
        />
        {q && (
          <button
            onClick={() => { setQ(""); setResults(null); }}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
            aria-label="Clear search"
            data-testid="project-search-clear"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {open && q.trim().length >= 2 && (
        <div
          className="absolute z-40 mt-2 w-full max-h-96 overflow-y-auto bg-white border-2 border-slate-200 rounded-md shadow-xl"
          data-testid="project-search-results"
        >
          {loading && (
            <div className="flex items-center gap-2 p-3 text-sm text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Searching…
            </div>
          )}
          {!loading && results && totalCount === 0 && (
            <div className="p-3 text-sm text-slate-500" data-testid="project-search-empty">
              No matches for "{q}".
            </div>
          )}
          {!loading && results && totalCount > 0 && (
            <>
              <ResultGroup label="Messages" Icon={MessageSquare} items={results.messages}
                render={(m) => (
                  <Link key={m.id} to={`${base}/messages`} className="block px-3 py-2 hover:bg-slate-50" data-testid={`search-msg-${m.id}`}>
                    <div className="font-bold text-sm text-slate-900 truncate">{m.title}</div>
                    <div className="text-xs text-slate-600 line-clamp-1">{m.body}</div>
                  </Link>
                )}
              />
              <ResultGroup label="To-dos" Icon={ListChecks} items={results.todos}
                render={(t) => (
                  <Link key={t.id} to={`${base}/todos`} className="block px-3 py-2 hover:bg-slate-50" data-testid={`search-todo-${t.id}`}>
                    <div className={`text-sm ${t.completed_at ? "line-through text-slate-500" : "text-slate-900"}`}>{t.title}</div>
                  </Link>
                )}
              />
              <ResultGroup label="Docs" Icon={FileText} items={results.docs}
                render={(d) => (
                  <Link key={d.id} to={`${base}/docs`} className="block px-3 py-2 hover:bg-slate-50" data-testid={`search-doc-${d.id}`}>
                    <div className="font-bold text-sm text-slate-900 truncate">{d.filename}</div>
                    <div className="text-xs text-slate-500 font-mono uppercase tracking-[0.1em]">{d.category}</div>
                  </Link>
                )}
              />
              <ResultGroup label="Events" Icon={Calendar} items={results.events}
                render={(e) => (
                  <Link key={e.id} to={`${base}/schedule`} className="block px-3 py-2 hover:bg-slate-50" data-testid={`search-event-${e.id}`}>
                    <div className="font-bold text-sm text-slate-900 truncate">{e.title}</div>
                    <div className="text-xs text-slate-500">{new Date(e.starts_at).toLocaleString()}</div>
                  </Link>
                )}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
}

function ResultGroup({ label, Icon, items, render }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="border-b border-slate-100 last:border-0">
      <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 border-b border-slate-100">
        <Icon className="w-3 h-3 text-slate-500" />
        <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500 font-bold">
          {label} · {items.length}
        </span>
      </div>
      {items.map(render)}
    </div>
  );
}
