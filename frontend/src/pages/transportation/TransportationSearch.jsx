/**
 * TRACK 18.00 · Phase C · RBAC-aware Universal Search.
 *
 * Single search bar mounted at the top of every Transportation
 * Operations workspace. Consumes `GET /api/admin/transportation/search`
 * (the Phase C composer) which returns only the result types the
 * calling portal token is allowed to see.
 *
 * Doctrine:
 *   - 300ms debounce.
 *   - Limit 20 results.
 *   - `/` keyboard shortcut focuses the input.
 *   - Results grouped by type; only groups with results render.
 *   - Click a result → navigate to its existing route (deep link).
 *   - No dead results. No "coming soon".
 */
import React, { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Loader2, X } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { STATE_LABEL, useTxPathPrefix } from "./_shared";

const ENDPOINT = "/admin/transportation/search";
const DEBOUNCE_MS = 300;

const GROUP_LABELS = {
  drivers:     "Drivers",
  carriers:    "Carriers",
  trucks:      "Trucks / Fleet",
  dispatch:    "Dispatch",
  projects:    "Projects",
  documents:   "Documents",
  orientation: "Orientation",
  actions:     "Actions",
  intelligence: "Intelligence / Cleanup",
  timeline:    "Timeline",
};

const STATUS_PALETTE = {
  eligible:        "bg-emerald-100 text-emerald-800",
  active:          "bg-emerald-100 text-emerald-800",
  approved:        "bg-emerald-100 text-emerald-800",
  pending_review:  "bg-amber-100 text-amber-900",
  open:            "bg-amber-100 text-amber-900",
  needs_correction:"bg-rose-100 text-rose-800",
  suspended:       "bg-rose-100 text-rose-800",
  not_dispatchable:"bg-rose-100 text-rose-800",
  expired:         "bg-rose-100 text-rose-800",
};

function groupResults(results) {
  const buckets = {};
  for (const r of results || []) {
    const g = r.group || "other";
    if (!buckets[g]) buckets[g] = [];
    buckets[g].push(r);
  }
  return buckets;
}

export default function TransportationSearch() {
  const { t } = useT();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const debounceRef = useRef(null);
  const inputRef = useRef(null);
  const containerRef = useRef(null);
  const navigate = useNavigate();
  const prefix = useTxPathPrefix();

  // Keyboard shortcut: "/" focuses search when not already in an input.
  useEffect(() => {
    const onKey = (e) => {
      const tag = (e.target?.tagName || "").toLowerCase();
      if (e.key === "/" && tag !== "input" && tag !== "textarea") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Close drawer on outside click.
  useEffect(() => {
    const onClick = (e) => {
      if (!containerRef.current?.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Debounced search.
  const runSearch = useCallback((query) => {
    if (!query || query.trim().length < 1) {
      setResults([]); setLoading(false); setError(null);
      return;
    }
    setLoading(true); setError(null);
    api.get(ENDPOINT, { params: { q: query, limit: 20 } })
      .then((r) => {
        setResults(r.data?.results || []);
        setLoading(false);
      })
      .catch((e) => {
        setError(e?.response?.data?.detail || e.message);
        setLoading(false);
        setResults([]);
      });
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(q), DEBOUNCE_MS);
    return () => debounceRef.current && clearTimeout(debounceRef.current);
  }, [q, runSearch]);

  const onPickResult = (route) => {
    setOpen(false);
    setQ("");
    setResults([]);
    if (!route) return;
    // TRACK 18.12 · Rewrite backend-emitted /admin/transportation
    // routes to the active prefix so dispatch users stay inside
    // /transportation-operations on every search result deep-link.
    let target = route;
    if (typeof target === "string" && target.startsWith("/admin/transportation")) {
      target = prefix + target.slice("/admin/transportation".length);
    }
    navigate(target);
  };

  const buckets = groupResults(results);
  const hasResults = results.length > 0;
  const showDrawer = open && (q.trim().length >= 1);

  return (
    <div
      ref={containerRef}
      data-testid="txops-search"
      className="relative w-full max-w-xl"
    >
      <div className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-2 py-1.5 focus-within:border-amber-400">
        <Search className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
        <input
          ref={inputRef}
          data-testid="txops-search-input"
          type="text"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          placeholder={t("Search drivers, trucks, carriers, projects… (press /)")}
          className="flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
        />
        {loading ? (
          <Loader2
            data-testid="txops-search-loading"
            className="h-3.5 w-3.5 text-slate-400 animate-spin"
          />
        ) : q ? (
          <button
            type="button"
            data-testid="txops-search-clear"
            onClick={() => { setQ(""); setResults([]); }}
            className="text-slate-400 hover:text-slate-700"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : (
          <span
            data-testid="txops-search-shortcut-hint"
            className="text-[10px] uppercase tracking-wide text-slate-400 border border-slate-200 rounded px-1"
          >
            /
          </span>
        )}
      </div>

      {showDrawer ? (
        <div
          data-testid="txops-search-drawer"
          className="absolute z-40 mt-1 w-full bg-white border border-slate-200 rounded-md shadow-lg max-h-[60vh] overflow-y-auto"
        >
          {error ? (
            <div
              data-testid="txops-search-error"
              className="p-3 text-xs text-rose-700"
            >
              {t("Search unavailable right now.")}{error ? ` ${error}` : ""}
            </div>
          ) : !hasResults && !loading ? (
            <div
              data-testid="txops-search-empty"
              className="p-3 text-xs text-slate-500"
            >
              {t("No results for “{q}”. Try a unit number, name, project number, or DOT/MC.").replace("{q}", q)}
            </div>
          ) : (
            Object.entries(buckets).map(([group, rows]) => (
              <section
                key={group}
                data-testid={`txops-search-group-${group}`}
                className="border-b border-slate-100 last:border-0"
              >
                <div className="px-3 py-1 text-[10px] uppercase tracking-wider text-slate-500 font-semibold bg-slate-50">
                  {t(GROUP_LABELS[group] || group)}
                </div>
                <ul>
                  {rows.map((r, i) => (
                    <li
                      key={`${group}-${i}`}
                      data-testid={`txops-search-result-${group}-${i}`}
                    >
                      <button
                        type="button"
                        onClick={() => onPickResult(r.route)}
                        data-testid={`txops-search-result-action-${group}-${i}`}
                        className="w-full text-left px-3 py-2 hover:bg-amber-50 flex items-center gap-2"
                      >
                        <span className="flex-1 min-w-0">
                          <span className="block text-sm font-medium text-slate-900 truncate">
                            {r.title}
                          </span>
                          {r.subtitle ? (
                            <span className="block text-[11px] text-slate-500 truncate">
                              {r.subtitle}
                            </span>
                          ) : null}
                          <span className="block text-[10px] text-slate-400 italic truncate">
                            {r.reason}
                          </span>
                        </span>
                        {r.status ? (
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                              STATUS_PALETTE[r.status] || "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {t(STATE_LABEL[r.status] || String(r.status).replace(/_/g, " "))}
                          </span>
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
