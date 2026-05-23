// EmployeeRosterField.jsx — iter359 · UI-Level Employee Linkage Enforcement
//
// Unified entry pattern that replaces the legacy "type the name AND
// optionally pick a master record" UX. This component captures BOTH
// values from one interaction: name + canonical employee_id when the
// user picks from the roster, OR a free-text value with a visible
// "this won't be linked to the employee master" warning when they don't.
//
// Operational coaching is baked in — the field itself tells the user
// what happens downstream when an unlinked record is created
// (it becomes an EMP_LINK_UNRESOLVABLE finding in Governance Health).
// That makes the linkage governance loop visible at the moment of
// entry rather than after the fact.
//
// Mobile-first: tap-friendly, fast, tolerant of imperfect spelling
// (debounced server-side search), supports free-text fallback for
// subcontractors / non-employees so field workflows are never blocked.

import React, { useEffect, useRef, useState } from "react";
import { Search, User, AlertCircle, CheckCircle2 } from "lucide-react";
import axios from "axios";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";

const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Props:
 *   value        : { id?: string, name: string, linked: boolean }
 *   onChange     : ({ id, name, linked }) => void
 *   label        : string (defaults to "Employee")
 *   required     : boolean
 *   placeholder  : string
 *   allowFreeText: boolean (default true — false locks field to roster only)
 *   testId       : string  (data-testid prefix for the input + suggestions)
 */
export default function EmployeeRosterField({
  value = { id: "", name: "", linked: false },
  onChange,
  label = "Employee",
  required = false,
  placeholder = "Type name to search roster",
  allowFreeText = true,
  testId = "employee-roster-field",
}) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(value.name || "");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const wrapRef = useRef(null);

  // Sync external value into local query when it changes from outside.
  useEffect(() => { setQuery(value.name || ""); }, [value.name]);

  // Close suggestions on outside click.
  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const search = (q) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const trimmed = (q || "").trim();
    if (!trimmed) { setResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await axios.get(`${API_BASE}/master-lookup/employees`, {
          params: { q: trimmed, limit: 8 },
        });
        const items = Array.isArray(r.data?.items) ? r.data.items :
                      Array.isArray(r.data) ? r.data : [];
        setResults(items);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);
  };

  const handleInput = (e) => {
    const v = e.target.value;
    setQuery(v);
    setOpen(true);
    search(v);
    // Reflect free-text immediately upstream (linked=false until picked).
    if (allowFreeText) {
      onChange?.({ id: "", name: v, linked: false });
    }
  };

  const pick = (item) => {
    // /api/master-lookup/employees returns flat {id, name, employee_id, trade, role, email}.
    // Tolerate legacy `{label, raw:{name}}` shape too in case any caller wraps.
    const name = item.name || item.label || item.raw?.name || query;
    onChange?.({ id: item.id, name, linked: true });
    setQuery(name);
    setOpen(false);
  };

  const linked = !!value.id && value.linked;
  const unresolvedFreeText = (value.name || "").trim().length > 0 && !linked;

  return (
    <div ref={wrapRef} className="relative" data-testid={testId}>
      {label ? (
        <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold flex items-center gap-1">
          <User className="w-3 h-3" /> {label}
          {required ? <span className="text-rose-600">*</span> : null}
        </label>
      ) : null}
      <div className="relative mt-1">
        <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        <Input
          value={query}
          onChange={handleInput}
          onFocus={() => { if (query) { setOpen(true); search(query); } }}
          placeholder={placeholder}
          className={`pl-9 ${linked ? "border-emerald-500" : unresolvedFreeText ? "border-amber-500" : ""}`}
          data-testid={`${testId}-input`}
        />
        {linked ? (
          <CheckCircle2 className="w-4 h-4 absolute right-2.5 top-1/2 -translate-y-1/2 text-emerald-600" />
        ) : unresolvedFreeText ? (
          <AlertCircle className="w-4 h-4 absolute right-2.5 top-1/2 -translate-y-1/2 text-amber-600" />
        ) : null}
        {open && (results.length > 0 || loading) ? (
          <div className="absolute z-30 left-0 right-0 mt-1 bg-white border border-slate-300 rounded-md shadow-lg max-h-64 overflow-auto" data-testid={`${testId}-suggestions`}>
            {loading ? (
              <div className="px-3 py-2 text-xs font-mono text-slate-500">{t("Searching…")}</div>
            ) : null}
            {results.map((item) => {
              // Flat shape from /api/master-lookup/employees: {id, name, employee_id, trade, role, email}.
              const displayName = item.name || item.label || item.raw?.name || "";
              const subRole = item.role || item.trade || item.raw?.position || "";
              const subEmail = item.email || item.raw?.email || "";
              return (
              <button
                type="button"
                key={item.id}
                onClick={() => pick(item)}
                className="w-full text-left px-3 py-2 hover:bg-emerald-50 border-b border-slate-100 last:border-b-0"
                data-testid={`${testId}-suggestion-${item.id}`}
              >
                <div className="text-sm font-semibold text-slate-900">{displayName}</div>
                {subRole || subEmail ? (
                  <div className="text-[11px] font-mono text-slate-500">
                    {subRole}{subRole && subEmail ? " · " : ""}{subEmail}
                  </div>
                ) : null}
              </button>
              );
            })}
            {!loading && results.length === 0 ? (
              <div className="px-3 py-2 text-xs font-mono text-slate-500">{t("No roster match.")}</div>
            ) : null}
          </div>
        ) : null}
      </div>

      {/* Operational coaching footer — visible at entry time */}
      {linked ? (
        <div className="mt-1 text-[11px] text-emerald-700 font-mono inline-flex items-center gap-1" data-testid={`${testId}-linked-status`}>
          <CheckCircle2 className="w-3 h-3" /> {t("Linked to roster")} · employee_id={value.id?.slice(0, 8)}…
        </div>
      ) : unresolvedFreeText ? (
        <div className="mt-1 text-[11px] text-amber-700 leading-snug" data-testid={`${testId}-unresolved-warning`}>
          <span className="font-mono font-bold uppercase tracking-wider">{t("Not in roster")}.</span>{" "}
          {t("Saved as free-text. This will appear as an EMP_LINK_UNRESOLVABLE finding in Governance Health until you either pick from the roster or add this person to the employee master.")}{" "}
          <a href="/admin/operational-language#roster_backed_selector" target="_blank" rel="noreferrer" className="underline">
            {t("What does this mean?")}
          </a>
        </div>
      ) : null}
    </div>
  );
}
