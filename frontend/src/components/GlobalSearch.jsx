// GlobalSearch.jsx — Iter155 (Phase G). Shared, permission-safe
// global typeahead.
//
//   * Trigger:  Cmd/Ctrl+K (desktop) OR tap search icon (mobile)
//   * Behavior: debounced (260ms), grouped results by kind,
//               deep-links per row, recent searches (per-actor)
//   * Mobile:   full-screen sheet via inset utility (no clipped
//               dropdowns, no keyboard-overlap)
//   * Safety:   results are scoped server-side by portal token.
//               Anonymous users get nothing (no token → 401).
//
// Reusable across portals — drop into ANY shell header. Same testIds
// resolve everywhere so tests don't need per-portal forks.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search, Loader2, X, ArrowRight, History, ChevronRight, AlertCircle,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { globalSearch, hasAnyPortalToken } from "@/lib/searchApi";

const DEBOUNCE_MS = 260;
const RECENT_KEY_PREFIX = "masci.search.recent.v1.";
const MAX_RECENT = 8;

// Per-kind chip color hints (keeps the surface readable without
// dragging in a heavy theme system).
const KIND_TINT = {
  tasks:               "bg-blue-50 text-blue-800 border-blue-200",
  notifications:       "bg-amber-50 text-amber-800 border-amber-200",
  employees:           "bg-purple-50 text-purple-800 border-purple-200",
  equipment:           "bg-orange-50 text-orange-800 border-orange-200",
  projects:            "bg-emerald-50 text-emerald-800 border-emerald-200",
  po_requests:         "bg-indigo-50 text-indigo-800 border-indigo-200",
  incidents:           "bg-rose-50 text-rose-800 border-rose-200",
  corrective_actions:  "bg-cyan-50 text-cyan-800 border-cyan-200",
  fire_extinguishers:  "bg-red-50 text-red-800 border-red-200",
  safety_documents:    "bg-slate-100 text-slate-700 border-slate-300",
  safety_training:     "bg-violet-50 text-violet-800 border-violet-200",
  document_expirations:"bg-amber-50 text-amber-900 border-amber-300",
  operations_events:   "bg-sky-50 text-sky-800 border-sky-200",
  field_leadership:    "bg-stone-100 text-stone-800 border-stone-300",
  // Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE
  staffing:            "bg-amber-50 text-amber-900 border-amber-300",
};

function recentKey() {
  // Tie recents to whichever portal token is live so users in different
  // portals don't see each other's history. We deliberately use a coarse
  // bucket (the first 8 chars of whichever token wins) — not a hash —
  // because this is purely a UX nicety, not a security boundary.
  const candidates = [
    "masci.admin.token", "masci.safety.token", "masci.hr.token",
    "masci.pm.token", "masci.shop.token", "masci.dispatch.token",
    "masci.leadership.token",
  ];
  for (const k of candidates) {
    let v = null;
    try { v = localStorage.getItem(k) || sessionStorage.getItem(k); } catch {}
    if (v) return RECENT_KEY_PREFIX + v.slice(0, 8);
  }
  return RECENT_KEY_PREFIX + "anon";
}

function readRecents() {
  try {
    const raw = localStorage.getItem(recentKey());
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr.slice(0, MAX_RECENT) : [];
  } catch { return []; }
}

function pushRecent(q) {
  const t = (q || "").trim();
  if (t.length < 2) return;
  try {
    const cur = readRecents().filter((s) => s.toLowerCase() !== t.toLowerCase());
    cur.unshift(t);
    localStorage.setItem(recentKey(), JSON.stringify(cur.slice(0, MAX_RECENT)));
  } catch {}
}

function clearRecents() {
  try { localStorage.removeItem(recentKey()); } catch {}
}

export default function GlobalSearch({
  accent = "dark", // "dark" (slate header) | "light" (white header)
  placeholder = "Search platform — tasks, employees, equipment, POs…",
  className = "",
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [recents, setRecents] = useState([]);
  const [highlight, setHighlight] = useState(0);

  const inputRef = useRef(null);
  const abortRef = useRef(null);
  const navigate = useNavigate();

  const flat = useMemo(() => {
    if (!data?.groups) return [];
    return data.groups.flatMap((g) => g.rows.map((r) => ({ ...r, _group: g.label })));
  }, [data]);

  const closeOverlay = useCallback(() => {
    setOpen(false);
    setQ("");
    setData(null);
    setErr(null);
    setHighlight(0);
    if (abortRef.current) { try { abortRef.current.abort(); } catch {} }
  }, []);

  const openOverlay = useCallback(() => {
    if (!hasAnyPortalToken()) {
      setOpen(true);
      setErr("AUTH_REQUIRED");
      return;
    }
    setOpen(true);
    setRecents(readRecents());
    setErr(null);
    // focus on next paint
    setTimeout(() => inputRef.current && inputRef.current.focus(), 30);
  }, []);

  // Cmd/Ctrl+K to toggle. Esc to close.
  useEffect(() => {
    const onKey = (e) => {
      const isK = e.key === "k" || e.key === "K";
      if ((e.metaKey || e.ctrlKey) && isK) {
        e.preventDefault();
        open ? closeOverlay() : openOverlay();
      } else if (e.key === "Escape" && open) {
        e.preventDefault();
        closeOverlay();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, openOverlay, closeOverlay]);

  // Debounced fetch
  useEffect(() => {
    if (!open) return;
    const term = q.trim();
    if (term.length < 2) { setData(null); setErr(null); return; }
    setLoading(true);
    setErr(null);
    if (abortRef.current) { try { abortRef.current.abort(); } catch {} }
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    const id = setTimeout(async () => {
      try {
        const res = await globalSearch(term, { limit: 6, signal: ctrl.signal });
        setData(res);
        setHighlight(0);
      } catch (e) {
        if (e?.name === "CanceledError" || e?.code === "ERR_CANCELED") return;
        const code = e?.response?.status;
        if (code === 401) setErr("AUTH_REQUIRED");
        else setErr("FAIL");
        setData(null);
      } finally { setLoading(false); }
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [q, open]);

  const selectRow = (row) => {
    if (!row) return;
    pushRecent(q);
    closeOverlay();
    if (row.url) navigate(row.url);
  };

  const onKeyDownInput = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, Math.max(flat.length - 1, 0)));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (flat[highlight]) selectRow(flat[highlight]);
    }
  };

  const triggerBase = accent === "dark"
    ? "bg-slate-800 hover:bg-slate-700 border-slate-700 text-white placeholder:text-slate-400"
    : "bg-white hover:bg-slate-50 border-slate-300 text-slate-800 placeholder:text-slate-400";

  return (
    <>
      <button
        type="button"
        onClick={openOverlay}
        className={`inline-flex items-center gap-2 h-9 px-3 rounded-md border-2 text-sm font-medium transition-colors ${triggerBase} ${className}`}
        data-testid="global-search-trigger"
        title="Search platform (Cmd+K)"
      >
        <Search className="w-4 h-4 shrink-0" />
        <span className="hidden md:inline text-xs uppercase font-mono tracking-[0.16em]">Search</span>
        <span className="hidden md:inline ml-1 text-[10px] font-mono opacity-70 border rounded px-1 py-0.5">
          ⌘K
        </span>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-[80] flex items-start justify-center bg-slate-950/70 backdrop-blur-sm"
          data-testid="global-search-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Global Search"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeOverlay();
          }}
        >
          <div
            className="mt-4 sm:mt-24 w-full sm:max-w-2xl mx-2 sm:mx-4 bg-white rounded-lg shadow-2xl border border-slate-200 max-h-[90vh] flex flex-col overflow-hidden"
            data-testid="global-search-panel"
          >
            <div className="flex items-center gap-2 px-3 py-2 border-b-2 border-slate-200">
              <Search className="w-4 h-4 text-slate-500 shrink-0" />
              <Input
                ref={inputRef}
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={onKeyDownInput}
                placeholder={placeholder}
                className="flex-1 border-0 focus-visible:ring-0 text-sm h-9 px-1"
                data-testid="global-search-input"
                autoComplete="off"
                inputMode="search"
              />
              {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-500 shrink-0" data-testid="global-search-spinner" />}
              <Button
                size="sm"
                variant="ghost"
                onClick={closeOverlay}
                className="h-8 px-2"
                data-testid="global-search-close"
                aria-label="Close search"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {/* Auth required */}
              {err === "AUTH_REQUIRED" && (
                <div
                  className="p-6 text-center text-sm text-slate-700"
                  data-testid="global-search-auth-required"
                >
                  <AlertCircle className="w-5 h-5 mx-auto mb-2 text-amber-600" />
                  <div className="font-bold mb-1">Sign in to search</div>
                  <div className="text-xs text-slate-500">
                    Global search requires an active portal session.
                  </div>
                </div>
              )}

              {/* Generic failure */}
              {err === "FAIL" && (
                <div
                  className="p-4 text-sm text-rose-700 bg-rose-50 border-t border-rose-200"
                  data-testid="global-search-error"
                >
                  Could not load search results. Try again.
                </div>
              )}

              {/* Recents (when query is empty) */}
              {!err && q.trim().length < 2 && recents.length > 0 && (
                <div className="p-3" data-testid="global-search-recents">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500 font-bold flex items-center gap-1">
                      <History className="w-3.5 h-3.5" /> Recent
                    </div>
                    <button
                      className="text-[10px] text-slate-500 hover:text-slate-800 underline"
                      onClick={() => { clearRecents(); setRecents([]); }}
                      data-testid="global-search-recents-clear"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {recents.map((r) => (
                      <button
                        key={r}
                        className="text-xs px-2 py-1 rounded border border-slate-300 bg-slate-50 hover:bg-slate-100"
                        onClick={() => setQ(r)}
                        data-testid={`global-search-recent-${r}`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty / hint */}
              {!err && q.trim().length < 2 && recents.length === 0 && (
                <div
                  className="p-6 text-center text-xs text-slate-500"
                  data-testid="global-search-hint"
                >
                  Type at least 2 characters to search.
                </div>
              )}

              {/* No results */}
              {!err && !loading && q.trim().length >= 2 && data && (data.total || 0) === 0 && (
                <div
                  className="p-6 text-center text-sm text-slate-600"
                  data-testid="global-search-empty"
                >
                  No matches for <span className="font-mono">&ldquo;{q.trim()}&rdquo;</span>.
                </div>
              )}

              {/* Grouped results */}
              {!err && data?.groups?.length > 0 && (
                <div className="divide-y divide-slate-100">
                  {data.groups.map((g) => (
                    <section
                      key={g.kind}
                      data-testid={`global-search-group-${g.kind}`}
                    >
                      <div className="flex items-center justify-between px-3 py-2 bg-slate-50 sticky top-0">
                        <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold">
                          {g.label}
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">
                          {g.count}
                        </span>
                      </div>
                      <ul className="divide-y divide-slate-100">
                        {g.rows.map((row) => {
                          const idx = flat.findIndex((f) => f.kind === row.kind && f.id === row.id);
                          const active = idx === highlight;
                          return (
                            <li key={`${row.kind}|${row.id}`}>
                              <button
                                type="button"
                                onClick={() => selectRow(row)}
                                onMouseEnter={() => setHighlight(idx)}
                                className={`w-full text-left px-3 py-2.5 flex items-center gap-3 hover:bg-slate-50 focus:bg-slate-50 focus:outline-none ${active ? "bg-slate-50" : ""}`}
                                data-testid={`global-search-row-${row.kind}-${row.id}`}
                              >
                                <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-mono uppercase tracking-wider border shrink-0 ${KIND_TINT[row.kind] || "bg-slate-100 text-slate-700 border-slate-300"}`}>
                                  {row.kind.replace(/_/g, " ")}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-slate-900 truncate">
                                    {row.title}
                                  </div>
                                  {row.subtitle && (
                                    <div className="text-xs text-slate-500 truncate">
                                      {row.subtitle}
                                    </div>
                                  )}
                                </div>
                                {row.status && (
                                  <span className="text-[10px] font-mono uppercase text-slate-600 hidden sm:inline">
                                    {row.status}
                                  </span>
                                )}
                                <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  ))}
                </div>
              )}
            </div>

            {/* Footer hint */}
            <div className="px-3 py-2 border-t border-slate-200 bg-slate-50 text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500 flex items-center justify-between">
              <span data-testid="global-search-scope">
                {data?.role ? `Scope · ${data.role}` : "Scoped to your role"}
              </span>
              <span className="hidden sm:inline">
                ↑↓ navigate · <span className="px-1 border rounded">↵</span> open · <span className="px-1 border rounded">esc</span> close
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
