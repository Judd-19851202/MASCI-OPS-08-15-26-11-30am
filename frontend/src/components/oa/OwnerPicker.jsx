/**
 * OA-1 · OwnerPicker.jsx
 * Cross-directory typeahead. Returns a structured owner ref:
 *   { directory, id, name, email }
 * No free-text owners allowed.
 */
import React, { useEffect, useRef, useState } from "react";
import { Search, Loader2, X, User } from "lucide-react";
import { useT } from "@/lib/i18n";
import { oaApi } from "@/lib/oa";

const DIR_LABEL = {
  user_directory: "Admin",
  project_managers: "PM",
  dispatch_users: "Dispatch",
  hr_users: "HR",
  safety_users: "Safety",
  field_leadership_users: "Field Leadership",
  shop_users: "Shop",
};
const DIR_TONE = {
  user_directory: "bg-slate-100 text-slate-700 border-slate-300",
  project_managers: "bg-indigo-100 text-indigo-900 border-indigo-300",
  dispatch_users: "bg-sky-100 text-sky-900 border-sky-300",
  hr_users: "bg-violet-100 text-violet-900 border-violet-300",
  safety_users: "bg-cyan-100 text-cyan-900 border-cyan-300",
  field_leadership_users: "bg-rose-100 text-rose-900 border-rose-300",
  shop_users: "bg-amber-100 text-amber-900 border-amber-300",
};

export default function OwnerPicker({ value, onChange, autoFocus = false }) {
  const { t } = useT();
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => {
    const query = q.trim();
    if (!query) {
      // eslint-disable-next-line
      setResults([]);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await oaApi.ownerSearch(query, 25);
        setResults(r.data?.results || []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);
  }, [q]);

  useEffect(() => {
    function clickAway(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", clickAway);
    return () => document.removeEventListener("mousedown", clickAway);
  }, []);

  const clear = () => {
    onChange?.(null);
    setQ("");
    setResults([]);
    setOpen(false);
  };

  return (
    <div ref={boxRef} className="relative" data-testid="oa-owner-picker">
      {value ? (
        <div
          className="flex items-center justify-between gap-2 px-2 py-1.5 rounded border border-slate-300 bg-white"
          data-testid="oa-owner-picked"
        >
          <div className="flex items-center gap-2 min-w-0">
            <User className="w-4 h-4 text-slate-600 shrink-0" />
            <div className="min-w-0">
              <div className="text-sm font-bold text-slate-900 truncate">{value.name || value.email || value.id}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`inline-block px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-wider font-bold ${DIR_TONE[value.directory] || "bg-slate-100 border-slate-300"}`}>
                  {DIR_LABEL[value.directory] || value.directory}
                </span>
                {value.email ? <span className="text-[10px] text-slate-500 truncate">{value.email}</span> : null}
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={clear}
            className="text-slate-500 hover:text-rose-700 p-1"
            data-testid="oa-owner-clear"
            aria-label="Clear owner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <>
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={q}
              onChange={(e) => { setQ(e.target.value); setOpen(true); }}
              onFocus={() => setOpen(true)}
              placeholder={t("Search owner…")}
              autoFocus={autoFocus}
              data-testid="oa-owner-search-input"
              className="w-full pl-8 pr-3 py-2 border border-slate-300 rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            {loading ? (
              <Loader2 className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
            ) : null}
          </div>
          {open && results.length > 0 ? (
            <ul
              className="absolute z-10 mt-1 w-full bg-white border border-slate-300 rounded-md shadow-md max-h-64 overflow-auto"
              data-testid="oa-owner-results"
            >
              {results.map((r) => (
                <li
                  key={`${r.directory}-${r.id}`}
                  data-testid={`oa-owner-result-${r.id}`}
                  className="px-2 py-1.5 hover:bg-slate-50 cursor-pointer text-sm"
                  onClick={() => {
                    onChange?.({ directory: r.directory, id: r.id, name: r.name, email: r.email });
                    setQ("");
                    setResults([]);
                    setOpen(false);
                  }}
                >
                  <div className="flex items-center gap-2 justify-between">
                    <div className="min-w-0">
                      <div className="font-bold text-slate-900 truncate">{r.name || r.email || r.id}</div>
                      <div className="text-[10px] text-slate-500 truncate">{r.email || ""}</div>
                    </div>
                    <span className={`shrink-0 inline-block px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-wider font-bold ${DIR_TONE[r.directory] || "bg-slate-100 border-slate-300"}`}>
                      {DIR_LABEL[r.directory] || r.directory}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </>
      )}
    </div>
  );
}
