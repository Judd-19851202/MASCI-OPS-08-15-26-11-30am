// Track 13.30C — Global Unit Search input for ShopHubV2 + Unit
// Intelligence section. Hits /api/shop/units/search (read-only).
// Honest empty/error states. No fake results.
import React, { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";

const API = process.env.REACT_APP_BACKEND_URL;
const MIN_LEN = 2;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

const SEV_CHIP = {
  oos:      { bg: "#7f1d1d", fg: "#ffe4e6", label: "OOS" },
  critical: { bg: "#9a3412", fg: "#fef3c7", label: "CRITICAL" },
  monitor:  { bg: "#a16207", fg: "#fefce8", label: "MONITOR" },
  info:     { bg: "#1e40af", fg: "#dbeafe", label: "INFO" },
  none:     { bg: "#166534", fg: "#dcfce7", label: "NONE" },
};
const STATUS_CHIP = {
  available:   { bg: "#dcfce7", fg: "#166534", label: "AVAILABLE" },
  oos:         { bg: "#fee2e2", fg: "#7f1d1d", label: "OOS" },
  maintenance: { bg: "#fef3c7", fg: "#92400e", label: "MAINTENANCE" },
  unknown:     { bg: "#e5e7eb", fg: "#374151", label: "—" },
};

export default function UnitSearch({ inline = false }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);
  const tRef = useRef(null);

  const runSearch = useCallback(async (term) => {
    setError(""); setLoading(true);
    try {
      const params = new URLSearchParams({ q: term, limit: "10" });
      const r = await fetch(`${API}/api/shop/units/search?${params}`, { headers: authHeaders() });
      const body = await r.json().catch(() => null);
      if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
      setResults(body.results || []);
      setCount(body.count || 0);
      setOpen(true);
    } catch (e) {
      setError(e.message || "Unit search unavailable. No data invented.");
      setResults([]); setCount(0); setOpen(true);
    }
    setLoading(false);
  }, []);

  // Debounce
  useEffect(() => {
    if (tRef.current) clearTimeout(tRef.current);
    const term = query.trim();
    if (term.length < MIN_LEN) { setResults([]); setCount(0); setOpen(false); return; }
    tRef.current = setTimeout(() => runSearch(term), 350);
    return () => { if (tRef.current) clearTimeout(tRef.current); };
  }, [query, runSearch]);

  // Click outside closes
  useEffect(() => {
    function onClick(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function onSubmit(e) {
    e.preventDefault();
    const term = query.trim();
    if (term.length < MIN_LEN) return;
    if (results.length === 1 && results[0].links?.unit_history) {
      navigate(results[0].links.unit_history);
    } else if (term) {
      // Fallback: navigate to Unit History landing — user types unit there
      navigate("/shop/units/history");
    }
  }

  return (
    <div ref={wrapRef} data-testid="shop-unit-search-root"
         style={{ position: "relative", width: inline ? "100%" : 480, maxWidth: "100%" }}>
      <form onSubmit={onSubmit} data-testid="shop-unit-search-form">
        <div style={{ position: "relative" }}>
          <input data-testid="shop-unit-search-input"
                 value={query} onChange={(e) => setQuery(e.target.value)}
                 placeholder="Search unit, asset, serial, model…"
                 onFocus={() => query.trim().length >= MIN_LEN && setOpen(true)}
                 style={{ width: "100%", padding: "10px 12px 10px 36px",
                          fontSize: 13, color: "var(--ink-strong)",
                          background: "var(--paper-card)",
                          border: "1px solid var(--border-bold)",
                          borderRadius: "var(--radius-card)" }} />
          <span aria-hidden="true" style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--ink-soft)", fontSize: 14 }}>⌕</span>
        </div>
      </form>
      {open && (
        <div data-testid="shop-unit-search-results"
             style={{ position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
                      background: "var(--paper-card)", border: "1px solid var(--border-bold)",
                      borderRadius: "var(--radius-card)", zIndex: 50,
                      maxHeight: 360, overflowY: "auto",
                      boxShadow: "0 4px 12px rgba(0,0,0,.08)" }}>
          {loading && (<div data-testid="shop-unit-search-loading"
            style={{ padding: 12, fontSize: 12, color: "var(--ink-soft)" }}>Searching…</div>)}
          {!loading && error && (
            <div data-testid="shop-unit-search-error"
              style={{ padding: 12, fontSize: 12, color: "#7f1d1d", background: "#fee2e2" }}>
              {error}
            </div>
          )}
          {!loading && !error && count === 0 && (
            <div data-testid="shop-unit-search-empty"
              style={{ padding: 12, fontSize: 12, color: "var(--ink-soft)" }}>
              No matching units found.
            </div>
          )}
          {!loading && !error && results.map((row) => {
            const sev = SEV_CHIP[row.highest_severity || "none"] || SEV_CHIP.none;
            const st = STATUS_CHIP[row.status] || STATUS_CHIP.unknown;
            const rowKey = row.unit_number || row.links?.unit_history || row.asset_name;
            const displayUnit = row.unit_number || row.asset_name || "—";
            return (
              <button key={rowKey} data-testid={`shop-unit-search-row-${row.unit_number || rowKey}`}
                      type="button"
                      onClick={() => { setOpen(false); navigate(row.links?.unit_history || "/shop/units/history"); }}
                      style={{ width: "100%", textAlign: "left", padding: "10px 12px",
                               background: "transparent", border: "none", borderBottom: "1px solid var(--border-soft, #e5e7eb)",
                               cursor: "pointer", display: "block" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <strong style={{ fontSize: 13, color: "var(--ink-strong)" }}>{displayUnit}</strong>
                  {!row.unit_number && (
                    <span style={{ padding: "1px 6px", borderRadius: 3, background: "#e5e7eb", color: "#374151", fontSize: 9, fontWeight: 700, letterSpacing: ".04em" }}>
                      NO UNIT #
                    </span>
                  )}
                  <span style={{ padding: "1px 6px", borderRadius: 3, background: st.bg, color: st.fg, fontSize: 10, fontWeight: 700 }}>{st.label}</span>
                  {row.open_defects_count > 0 && (
                    <span style={{ padding: "1px 6px", borderRadius: 3, background: sev.bg, color: sev.fg, fontSize: 10, fontWeight: 700 }}>
                      {row.open_defects_count} OPEN · {sev.label}
                    </span>
                  )}
                  {row.parts_on_order_count > 0 && (
                    <span style={{ padding: "1px 6px", borderRadius: 3, background: "#fef3c7", color: "#92400e", fontSize: 10, fontWeight: 700 }}>
                      {row.parts_on_order_count} PARTS
                    </span>
                  )}
                </div>
                <div style={{ marginTop: 2, fontSize: 11, color: "var(--ink-soft)" }}>
                  {row.unit_number ? `${row.asset_name || "—"} · ` : ""}{row.asset_type || "—"}
                  {row.assigned_mechanic ? ` · mechanic ${row.assigned_mechanic}` : ""}
                  {row.last_fuel_lube_visit?.visit_date ? ` · last fuel/lube ${row.last_fuel_lube_visit.visit_date}` : ""}
                </div>
              </button>
            );
          })}
          {!loading && !error && count > 0 && (
            <div style={{ padding: "6px 12px", fontSize: 10, color: "var(--ink-faint, #6b7280)" }}>
              {count} result{count === 1 ? "" : "s"} · click to open unit history
            </div>
          )}
        </div>
      )}
    </div>
  );
}
