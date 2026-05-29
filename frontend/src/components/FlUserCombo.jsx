// FlUserCombo.jsx — Phase V.2 · Daily Report Field-Logic Refinement.
//
// Searchable role-aware picker for the Field Leadership roster
// (GET /api/field-leadership-roster).  Mirrors the EmployeeCombo UX
// so the form feels uniform, but stays scoped to field-leadership
// roles (Superintendent / Foreman / General Foreman / Field
// Supervisor / Truck Boss / Working Supervisor).
//
// Doctrine:
//  - Manual fallback is ALWAYS allowed: if the user's name isn't in
//    the FL roster, they can type it directly and the form still
//    submits.  This honors the operator directive "Do not block
//    report submission if picker data is missing."
//  - No PII is shown beyond name + role.
//  - Module-level cache mirrors EmployeeCombo / SupplierCombo so a
//    transient network blip doesn't permanently poison the picker.

import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";

let _cache = null;
let _cachePromise = null;

async function loadRoster() {
  if (_cache && Array.isArray(_cache.items) && _cache.items.length > 0) {
    return _cache;
  }
  if (_cachePromise) return _cachePromise;
  _cachePromise = api
    .get("/field-leadership-roster", { timeout: 30000 })
    .then((r) => {
      if (Array.isArray(r?.data?.items)) {
        _cache = r.data;
        return _cache;
      }
      return { items: [], count: 0 };
    })
    .catch(() => ({ items: [], count: 0 }))
    .finally(() => {
      _cachePromise = null;
    });
  return _cachePromise;
}

export function clearFlRosterCache() {
  _cache = null;
  _cachePromise = null;
}

/**
 * Props:
 *  - value         : current free-text value (FL user name)
 *  - onChange      : (string) => void
 *  - onPick        : optional (user) => void
 *  - placeholder   : string
 *  - testId        : optional data-testid prefix
 *  - className     : extra wrapper classes
 *  - allowedRoles  : optional Array<string> — when set, only roster
 *                    entries whose `role` is in this list appear in
 *                    the dropdown.  Free-text typing is ALWAYS still
 *                    allowed regardless of this filter.
 */
export const FlUserCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  testId = "fl-user-combo",
  className = "",
  allowedRoles = null,
}) => {
  const { t } = useT();
  const ph = placeholder || t("Type or pick a name…");
  const [data, setData] = useState({ items: [], count: 0 });
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    let retryTimer = null;
    const tryLoad = (attempt) => {
      loadRoster().then((d) => {
        if (!alive) return;
        setData(d);
        if ((d?.items?.length || 0) === 0 && attempt < 2) {
          retryTimer = setTimeout(() => tryLoad(attempt + 1), 1500 * (attempt + 1));
        }
      });
    };
    tryLoad(0);
    return () => {
      alive = false;
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, []);

  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const roleFilterSet = useMemo(() => {
    if (!Array.isArray(allowedRoles) || allowedRoles.length === 0) return null;
    return new Set(allowedRoles.map((r) => (r || "").toLowerCase()));
  }, [allowedRoles]);

  const filtered = useMemo(() => {
    const q = (value || "").trim().toLowerCase();
    let items = data.items || [];
    if (roleFilterSet) {
      items = items.filter((it) =>
        roleFilterSet.has(((it.role || "").toLowerCase()))
      );
    }
    if (!q) return items.slice(0, 200);
    return items
      .filter((it) => {
        const hay = [it.name, it.role].filter(Boolean).join(" ").toLowerCase();
        return hay.includes(q);
      })
      .slice(0, 200);
  }, [data, value, roleFilterSet]);

  const pick = (it) => {
    onChange?.(it.name || "");
    onPick?.(it);
    setOpen(false);
  };

  const total = (data.items || []).length;
  const exactMatch = filtered.some(
    (it) => (it.name || "").toLowerCase() === (value || "").trim().toLowerCase()
  );
  const showCustomTag = !!(value || "").trim() && !exactMatch && total > 0;

  return (
    <div className={`relative ${className}`} ref={wrapRef}>
      <div className="flex gap-1.5">
        <Input
          value={value}
          onChange={(e) => {
            onChange?.(e.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder={ph}
          className="flex-1 h-11 text-base border-2 border-slate-300 focus:border-red-700"
          data-testid={`${testId}-input`}
          autoComplete="off"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-11 w-11 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 shrink-0"
          onClick={() => {
            if ((data.items || []).length === 0) {
              clearFlRosterCache();
              loadRoster().then((d) => setData(d));
            }
            setOpen((o) => !o);
          }}
          data-testid={`${testId}-toggle`}
          aria-label={t("Open picker")}
        >
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </div>

      {showCustomTag && (
        <div
          className="mt-1 text-[11px] uppercase tracking-[0.2em] text-slate-500 font-mono"
          data-testid={`${testId}-custom`}
        >
          {t("Manual entry — not on field-leadership roster")}
        </div>
      )}

      {open && (
        <div
          className="absolute z-30 mt-1 w-full max-h-72 overflow-auto rounded-md border border-slate-300 bg-white shadow-lg"
          data-testid={`${testId}-list`}
        >
          {filtered.length === 0 ? (
            <div className="px-3 py-2 text-xs text-slate-500 font-mono">
              {total === 0
                ? t("Roster unavailable — manual entry is fine.")
                : t("No matches. Manual entry is fine.")}
            </div>
          ) : (
            filtered.map((it, i) => (
              <button
                key={`${it.name}-${i}`}
                type="button"
                onClick={() => pick(it)}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 border-b border-slate-100 last:border-b-0"
                data-testid={`${testId}-option-${i}`}
              >
                <div className="text-sm font-medium text-slate-900">{it.name}</div>
                {it.role && (
                  <div className="text-[11px] uppercase tracking-[0.2em] text-slate-500 font-mono">
                    {it.role}
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default FlUserCombo;
