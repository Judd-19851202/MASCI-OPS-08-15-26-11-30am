// MasterLookupCombobox — Iter138. Debounced typeahead picker for
// equipment_master + employees. Returns BOTH the master id and the
// canonical display label so create-forms can persist *_master_id +
// keep freetext fallback for "this isn't in master yet" cases.
//
// Usage:
//   <MasterLookupCombobox
//     kind="equipment"          // or "employees"
//     value={masterId}          // current id, or "" for empty
//     displayValue={text}       // current freetext display
//     onPick={(item) => {…}}    // item: {id, label, raw}
//     onClear={() => {…}}
//     placeholder="Search equipment…"
//     testIdPrefix="incident-eq"
//   />
//
// Behavior:
//   - User types → debounced fetch to /api/master-lookup/{kind}
//   - Dropdown shows matches; click attaches master id
//   - "Use exactly: '…'" option preserves freetext-only when no match
//   - Selected pick shows a green check + label; click X to clear
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Search, X, Check, Loader2, AlertCircle } from "lucide-react";

// Canonical public fallback per kind — used when the authenticated
// /master-lookup/{kind} endpoint rejects the current portal session (401)
// so the picker is ALWAYS master-backed instead of a silent empty list.
const PUBLIC_FALLBACK = {
  employees: "/hr/employee-roster/public",
  equipment: "/public/equipment-master-lookup",
};

const FORMAT = {
  equipment: (i) =>
    `${i.unit_number || i.make_model || "(no unit number)"}${i.make_model ? ` — ${i.make_model}` : ""}${i.category ? ` · ${i.category}` : ""}`,
  employees: (i) => {
    const name = i.name || `${i.first_name || ""} ${i.last_name || ""}`.trim() || "(no name)";
    const tail = i.email ? ` · ${i.email}` : i.employee_id ? ` · ${i.employee_id}` : i.role ? ` · ${i.role}` : "";
    return `${name}${tail}`;
  },
};

export default function MasterLookupCombobox({
  kind = "equipment",
  value = "",            // current master id (empty if freetext-only)
  displayValue = "",     // current freetext display
  onPick,
  onClear,
  placeholder,
  testIdPrefix = "mlc",
  disabled = false,
}) {
  const wrapRef = useRef(null);
  const inputRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchErr, setFetchErr] = useState(false);

  // Sync displayValue → q so the user sees what's currently bound
  useEffect(() => { setQ(displayValue || ""); }, [displayValue]);

  // iter139 — when we have a bound id but no displayValue (form
  // re-opened from server data), resolve the label via /by-id helper.
  useEffect(() => {
    if (!value || displayValue) return;
    let alive = true;
    (async () => {
      try {
        const r = await api.get(`/master-lookup/${kind}/by-id/${value}`, { skipSessionStatus: true });
        if (!alive || !r.data?.found) return;
        const fn = FORMAT[kind] || ((i) => i.id);
        const label = fn(r.data.item);
        setQ(label);
        onPick && onPick({ id: value, label, raw: r.data.item, _silent: true });
      } catch { /* swallow — orphaned id, leave blank */ }
    })();
    return () => { alive = false; };
    // Only fire when value first appears; we don't want re-resolve loops
     
  }, [displayValue, kind, onPick, value]);

  // Close on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Debounced fetch
  useEffect(() => {
    if (!open || q.trim().length < 1) { setItems([]); return; }
    let alive = true;
    const t = setTimeout(async () => {
      setLoading(true);
      const params = { q, limit: 20 };
      const fetchItems = async (path) => {
        const r = await api.get(path, { params, skipSessionStatus: true });
        return Array.isArray(r.data?.items) ? r.data.items : (Array.isArray(r.data) ? r.data : []);
      };
      try {
        let list = [];
        try {
          list = await fetchItems(`/master-lookup/${kind}`);
        } catch (e) {
          list = [];
        }
        if (!list.length && PUBLIC_FALLBACK[kind]) {
          list = await fetchItems(PUBLIC_FALLBACK[kind]);
        }
        if (alive) { setItems(list); setFetchErr(false); }
      } catch (e) {
        if (alive) { setItems([]); setFetchErr(true); }
      }
      finally { if (alive) setLoading(false); }
    }, 200);
    return () => { alive = false; clearTimeout(t); };
  }, [q, kind, open]);

  const fmt = FORMAT[kind] || ((i) => i.id);

  const handlePick = (item) => {
    const label = fmt(item);
    onPick && onPick({ id: item.id, label, raw: item });
    setOpen(false);
  };

  const handleFreeText = () => {
    // Persist the typed value as freetext (no master id)
    onPick && onPick({ id: "", label: q.trim(), raw: null });
    setOpen(false);
  };

  const handleClear = () => {
    setQ("");
    onClear && onClear();
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const hasBinding = !!value;

  return (
    <div ref={wrapRef} className="relative" data-testid={`${testIdPrefix}-wrap`}>
      <div className={`wp17-control relative flex items-center rounded-[1rem] border transition-colors ${
        hasBinding ? "border-emerald-300 bg-emerald-50/70 shadow-[0_18px_30px_rgba(5,150,105,0.08)]" : "border-[color:var(--border-bold)] bg-white"
      } ${disabled ? "opacity-60" : ""}`}>
        <span className="pl-2.5 pr-1 shrink-0">
          {hasBinding ? <Check className="w-4 h-4 text-emerald-700" /> : <Search className="w-4 h-4 text-slate-400" />}
        </span>
        <input
          ref={inputRef}
          type="text"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); if (hasBinding) onClear && onClear(); }}
          onFocus={() => setOpen(true)}
          placeholder={placeholder || (kind === "equipment" ? "Search by unit / make / VIN / serial…" : "Search by name / email / employee ID…")}
          className="flex-1 min-w-0 bg-transparent border-0 outline-none text-[0.95rem] py-3 px-1.5 text-[color:var(--ink-strong)] placeholder:text-[color:var(--ink-faint)]"
          disabled={disabled}
          data-testid={`${testIdPrefix}-input`}
          autoComplete="off"
        />
        {(q || hasBinding) && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="pr-2 text-slate-400 hover:text-red-600 shrink-0"
            tabIndex={-1}
            data-testid={`${testIdPrefix}-clear`}
            aria-label="Clear"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {hasBinding && (
        <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-mono uppercase tracking-[0.18em] text-emerald-800" data-testid={`${testIdPrefix}-bound`}>
          <Check className="w-3 h-3" />
          Linked to master record
        </div>
      )}

      {open && !disabled && (
        <div
          className="wp17-picker-panel absolute z-30 left-0 right-0 mt-2 max-h-72 overflow-y-auto p-1.5"
          data-testid={`${testIdPrefix}-dropdown`}
        >
          {loading && (
            <div className="wp17-picker-empty flex items-center gap-2">
              <Loader2 className="w-3 h-3 animate-spin" /> Searching…
            </div>
          )}
          {!loading && fetchErr && (
            <div className="wp17-picker-empty italic text-red-600" data-testid={`${testIdPrefix}-error`}>Master list unavailable — retry.</div>
          )}
          {!loading && !fetchErr && items.length === 0 && q.trim() && (
            <div className="wp17-picker-empty italic">No matches in master.</div>
          )}
          {!loading && items.length === 0 && !q.trim() && (
            <div className="wp17-picker-empty italic">Start typing to search…</div>
          )}
          {items.map((it) => (
            <button
              key={it.id}
              type="button"
              onClick={() => handlePick(it)}
              className="wp17-picker-option group text-left text-sm"
              data-testid={`${testIdPrefix}-item-${it.id}`}
            >
              <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
              <span className="flex-1 min-w-0 truncate">{fmt(it)}</span>
            </button>
          ))}
          {q.trim() && (
            <button
              type="button"
              onClick={handleFreeText}
              className="mt-1 flex w-full items-center gap-2 rounded-[0.95rem] border border-amber-200 bg-amber-50 px-3 py-2 text-left text-xs text-amber-900 transition-colors hover:bg-amber-100"
              data-testid={`${testIdPrefix}-freetext`}
              title="Save as text only — no master record will be linked"
            >
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              Use exactly: <strong className="mx-1">&quot;{q.trim()}&quot;</strong> (no master link)
            </button>
          )}
        </div>
      )}
    </div>
  );
}
