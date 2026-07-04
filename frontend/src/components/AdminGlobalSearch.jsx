// AdminGlobalSearch.jsx — Iter130. Debounced typeahead in the admin
// top bar. Calls /api/admin/search?q=... and groups results by
// category with quick-link navigation.
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Loader2, ArrowRight, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const DEBOUNCE_MS = 280;

export default function AdminGlobalSearch() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const navigate = useNavigate();
  const containerRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Debounced fetch
  useEffect(() => {
    if (q.trim().length < 2) { setData(null); return; }
    setLoading(true);
    const id = setTimeout(async () => {
      try {
        const r = await api.get(`/admin/search?q=${encodeURIComponent(q.trim())}&limit=6`);
        setData(r.data);
        setOpen(true);
      } catch {
        setData({ q, groups: [] });
      } finally { setLoading(false); }
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [q]);

  const onSelect = (link) => {
    setOpen(false);
    setQ("");
    if (link) navigate(link);
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-sm" data-testid="admin-global-search">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-slate-400 pointer-events-none" />
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => { if (data) setOpen(true); }}
          placeholder="Search assets, employees, events…"
          className="pl-8 pr-8 h-9 bg-slate-800 border-slate-700 text-white placeholder:text-slate-400 focus-visible:ring-red-700"
          data-testid="admin-search-input"
        />
        {q && (
          <button
            onClick={() => { setQ(""); setOpen(false); }}
            className="absolute right-2 top-2 text-slate-400 hover:text-white"
            data-testid="admin-search-clear"
            aria-label="Clear"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {open && (
        <div
          className="absolute right-0 mt-1 w-[28rem] max-w-[92vw] bg-white border border-slate-200 rounded-md shadow-xl z-50 max-h-[70vh] overflow-y-auto"
          data-testid="admin-search-dropdown"
        >
          {loading ? (
            <div className="p-6 text-center text-slate-500"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>
          ) : (data?.groups || []).length === 0 ? (
            <p className="p-5 text-sm text-slate-500 italic text-center" data-testid="admin-search-empty">
              No matches for <strong>&quot;{q}&quot;</strong>
            </p>
          ) : (
            <div data-testid="admin-search-groups">
              {data.groups.map((g) => (
                <div key={g.label} className="border-b border-slate-100 last:border-b-0">
                  <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500 font-bold bg-slate-50 sticky top-0">
                    {g.label} <span className="text-slate-400 font-normal">({g.count})</span>
                  </div>
                  <ul>
                    {g.rows.map((r) => (
                      <li key={r.id}>
                        <button
                          onClick={() => onSelect(r.link)}
                          className="w-full text-left px-3 py-2 hover:bg-slate-100 flex items-center gap-2 group"
                          data-testid={`admin-search-result-${r.id}`}
                        >
                          <div className="flex-1 min-w-0">
                            <div className="font-bold text-sm truncate text-slate-900">{r.title}</div>
                            {r.subtitle && (
                              <div className="text-[11px] text-slate-500 truncate font-mono">{r.subtitle}</div>
                            )}
                            {(r.linked_equipment_label || r.linked_employee_label) && (
                              <div className="flex flex-wrap gap-1 mt-1" data-testid={`admin-search-links-${r.id}`}>
                                {r.linked_equipment_label && (
                                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-cyan-50 border border-cyan-300 text-cyan-900 text-[10px] font-mono">
                                    <span className="font-bold tracking-wider">EQ</span>
                                    <span className="truncate max-w-[10rem]">{r.linked_equipment_label}</span>
                                  </span>
                                )}
                                {r.linked_employee_label && (
                                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-purple-50 border border-purple-300 text-purple-900 text-[10px] font-mono">
                                    <span className="font-bold tracking-wider">EMP</span>
                                    <span className="truncate max-w-[10rem]">{r.linked_employee_label}</span>
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                          {r.status && (
                            <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 text-[9px] font-mono uppercase tracking-[0.15em]">
                              {r.status}
                            </span>
                          )}
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 shrink-0" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
