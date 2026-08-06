// Shared source-truth picker for Shop forms. Wraps a debounced search
// input against a list endpoint (/api/shop/projects/list, /units/list)
// with honest empty/error states and an optional manual fallback.
//
// Usage:
//   <ShopSelector kind="project" value={value} onChange={onChange} />
//   <ShopSelector kind="unit"    value={value} onChange={onChange}
//                 filterFn={(u) => /truck/i.test(u.equipment_type)} />
//
// Renders an input + filterable dropdown. Selecting a row calls
// onChange with the full row object. Manual free-typing is allowed as
// a fallback (the typed value is passed through as { manual: true }).
import React, { useEffect, useMemo, useRef, useState } from "react";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

const KIND_CONFIG = {
  project: {
    endpoint: "/api/shop/projects/list",
    placeholder: "Search project number or name…",
    primaryKey: "project_number",
    primaryLabel: (row) => row.project_number,
    secondaryLabel: (row) => row.project_name,
    matches: (row, q) => {
      const qq = q.toLowerCase();
      return (row.project_number || "").toLowerCase().includes(qq)
          || (row.project_name   || "").toLowerCase().includes(qq);
    },
    emptyMsg: "No matching projects found.",
    errorMsg: "Project list unavailable. Type the project number manually below.",
  },
  unit: {
    endpoint: "/api/shop/units/list?limit=500",
    placeholder: "Search unit number or equipment name…",
    primaryKey: "unit_number",
    primaryLabel: (row) => row.unit_number,
    secondaryLabel: (row) => `${row.equipment_name || ""} · ${row.equipment_type || ""}`.replace(/^ · /, "").replace(/ · $/, ""),
    matches: (row, q) => {
      const qq = q.toLowerCase();
      return (row.unit_number || "").toLowerCase().includes(qq)
          || (row.equipment_name || "").toLowerCase().includes(qq)
          || (row.equipment_type || "").toLowerCase().includes(qq);
    },
    emptyMsg: "No matching units found.",
    errorMsg: "Unit list unavailable. Type the unit number manually below.",
  },
};

export default function ShopSelector({
  kind,
  value,        // current selected primary key string
  onChange,     // (row|null) => void
  filterFn,     // optional client-side filter (e.g. only service trucks)
  required = false,
  testIdPrefix = "shop-selector",
}) {
  const cfg = KIND_CONFIG[kind];
  if (!cfg) throw new Error(`Unknown selector kind: ${kind}`);

  const [items, setItems] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const wrapRef = useRef(null);

  // Load items on first focus to avoid hub-load fanout.
  async function ensureLoaded() {
    if (loaded || error) return;
    try {
      const r = await fetch(`${API}${cfg.endpoint}`, { headers: authHeaders() });
      const body = await r.json().catch(() => null);
      if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
      const all = body.items || [];
      const filtered = filterFn ? all.filter(filterFn) : all;
      setItems(filtered); setLoaded(true); setError("");
    } catch (e) {
      setError(e.message || cfg.errorMsg);
      setManualMode(true);
    }
  }

  // Click outside closes
  useEffect(() => {
    function onClick(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const filtered = useMemo(() => {
    if (!query) return items.slice(0, 25);
    return items.filter((r) => cfg.matches(r, query)).slice(0, 25);
  }, [items, query, cfg]);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [query, open]);

  function pick(row) {
    onChange?.(row || null);
    setQuery("");
    setOpen(false);
    setHighlightedIndex(0);
  }

  function onKeyDown(e) {
    if (manualMode) return;
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) {
        ensureLoaded();
        setOpen(true);
        return;
      }
      setHighlightedIndex((cur) => Math.min(cur + 1, Math.max(filtered.length - 1, 0)));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        ensureLoaded();
        setOpen(true);
        return;
      }
      setHighlightedIndex((cur) => Math.max(cur - 1, 0));
      return;
    }
    if (e.key === "Enter" && open && filtered.length > 0) {
      e.preventDefault();
      pick(filtered[Math.min(highlightedIndex, filtered.length - 1)]);
    }
  }

  return (
    <div ref={wrapRef} data-testid={`${testIdPrefix}-${kind}-root`}
         style={{ position: "relative", width: "100%" }}>
      {/* Selected pill / current value */}
      {value && !manualMode && (
        <div data-testid={`${testIdPrefix}-${kind}-current`}
             style={{ marginBottom: 6, display: "flex", alignItems: "center",
                      gap: 8, padding: "6px 10px", background: "#eef2ff",
                      border: "1px solid #c7d2fe", borderRadius: 4,
                      fontSize: 12, color: "#1e293b" }}>
          <strong>{value}</strong>
          <button type="button" onClick={() => pick(null)}
                  data-testid={`${testIdPrefix}-${kind}-clear`}
                  style={{ padding: "2px 8px", fontSize: 10, background: "#fff",
                           border: "1px solid #cbd5e1", borderRadius: 3, cursor: "pointer" }}>
            Clear
          </button>
        </div>
      )}
      {/* Search input */}
      {!manualMode && (
        <input data-testid={`${testIdPrefix}-${kind}-input`}
               type="text" value={query}
               required={required && !value}
               placeholder={cfg.placeholder}
               onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
               onFocus={() => { ensureLoaded(); setOpen(true); }}
               onKeyDown={onKeyDown}
               style={{ width: "100%", padding: 6, fontSize: 12 }} />
      )}
      {open && !manualMode && (
        <div data-testid={`${testIdPrefix}-${kind}-dropdown`}
             style={{ position: "absolute", top: "100%", left: 0, right: 0, zIndex: 30,
                      background: "var(--paper-card)", border: "1px solid var(--border-bold)",
                      borderRadius: "var(--radius-card)", maxHeight: 280, overflowY: "auto",
                      boxShadow: "0 4px 12px rgba(0,0,0,.08)" }}>
          {!loaded && !error && (
            <div style={{ padding: 10, fontSize: 12, color: "var(--ink-soft)" }}>Loading…</div>
          )}
          {error && (
            <div data-testid={`${testIdPrefix}-${kind}-error`}
                 style={{ padding: 10, fontSize: 12, color: "#7f1d1d", background: "#fee2e2" }}>
              {error}
            </div>
          )}
          {loaded && !error && filtered.length === 0 && (
            <div data-testid={`${testIdPrefix}-${kind}-empty`}
                 style={{ padding: 10, fontSize: 12, color: "var(--ink-soft)" }}>
              {cfg.emptyMsg}
            </div>
          )}
          {loaded && !error && filtered.map((row, index) => {
            const pk = row[cfg.primaryKey];
            const highlighted = index === highlightedIndex;
            return (
              <button key={pk} type="button"
                      data-testid={`${testIdPrefix}-${kind}-row-${pk}`}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      onClick={() => pick(row)}
                      style={{ width: "100%", textAlign: "left",
                               padding: "8px 10px", background: highlighted ? "#eef2ff" : "transparent",
                               border: "none", borderBottom: "1px solid #e5e7eb",
                               cursor: "pointer", display: "block" }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-strong)" }}>
                  {cfg.primaryLabel(row)}
                </div>
                {cfg.secondaryLabel(row) && (
                  <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>
                    {cfg.secondaryLabel(row)}
                  </div>
                )}
              </button>
            );
          })}
          {loaded && !error && (
            <button type="button"
                    data-testid={`${testIdPrefix}-${kind}-manual-toggle`}
                    onClick={() => { setManualMode(true); setOpen(false); }}
                    style={{ width: "100%", padding: 8, fontSize: 11,
                             background: "#fafafa", border: "none",
                             borderTop: "1px solid #e5e7eb", cursor: "pointer",
                             color: "var(--ink-soft)" }}>
              Type manually instead →
            </button>
          )}
        </div>
      )}
      {manualMode && (
        <div>
          <input data-testid={`${testIdPrefix}-${kind}-manual`}
                 type="text" value={value || ""}
                 required={required}
                 placeholder={`Enter ${kind === "project" ? "project number" : "unit number"} manually`}
                 onChange={(e) => onChange?.({ [cfg.primaryKey]: e.target.value, manual: true })}
                 style={{ width: "100%", padding: 6, fontSize: 12 }} />
          <button type="button"
                  data-testid={`${testIdPrefix}-${kind}-manual-cancel`}
                  onClick={() => { setManualMode(false); setError(""); ensureLoaded(); }}
                  style={{ marginTop: 4, padding: "2px 8px", fontSize: 10, background: "#fff",
                           border: "1px solid #cbd5e1", borderRadius: 3, cursor: "pointer",
                           color: "var(--ink-soft)" }}>
            Use list instead
          </button>
        </div>
      )}
    </div>
  );
}
