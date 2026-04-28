import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, Search, X, User } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";

/**
 * EmployeeCombo
 * -------------
 * Searchable picker for the MASCI employee roster (GET /api/employees).
 * Mirrors the EquipmentCombo UX so all forms feel uniform.
 *
 * Props
 * - value:        current free-text value (employee name)
 * - onChange:     (string) => void
 * - onPick:       optional (employeeObj) => void
 * - placeholder:  string
 * - testId:       optional data-testid prefix
 * - className:    extra wrapper classes
 *
 * Always allows free-text entries (so the form still works before the
 * roster is uploaded by the admin).
 */
let _cache = null;
let _cachePromise = null;

async function loadRoster() {
  if (_cache) return _cache;
  if (_cachePromise) return _cachePromise;
  _cachePromise = api
    .get("/employees")
    .then((r) => {
      _cache = Array.isArray(r.data?.items)
        ? r.data
        : { items: [], count: 0 };
      return _cache;
    })
    .catch(() => ({ items: [], count: 0 }))
    .finally(() => {
      _cachePromise = null;
    });
  return _cachePromise;
}

/** Allow other modules to bust the cache after an admin upload. */
export function clearEmployeeCache() {
  _cache = null;
  _cachePromise = null;
}

export const EmployeeCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  testId = "employee-combo",
  className = "",
}) => {
  const { t } = useT();
  const ph = placeholder || t("Type or pick an employee…");
  const [data, setData] = useState({ items: [], count: 0 });
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    loadRoster().then((d) => {
      if (alive) setData(d);
    });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const items = data.items || [];
    if (!q) return items.slice(0, 200); // show first 200 to keep DOM light
    return items
      .filter((it) => {
        const hay = [
          it.name,
          it.employee_id,
          it.role,
          it.trade,
          it.crew,
          it.email,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .slice(0, 200);
  }, [data, query]);

  const pick = (it) => {
    const label = it.name || "";
    onChange?.(label);
    onPick?.(it);
    setOpen(false);
    setQuery("");
  };

  const total = data.count || (data.items || []).length;
  const showFooterTip =
    !total ||
    (filtered.length === 0 && total > 0);

  return (
    <div className={`relative ${className}`} ref={wrapRef}>
      <div className="flex gap-1.5">
        <Input
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onFocus={() => setOpen(true)}
          placeholder={ph}
          className="flex-1 h-11 text-base border-2 border-slate-300 focus:border-red-700"
          data-testid={`${testId}-input`}
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-11 w-11 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 shrink-0"
          onClick={() => setOpen((v) => !v)}
          data-testid={`${testId}-toggle`}
          title={t("Browse roster")}
        >
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </div>

      {open && (
        <div
          className="absolute z-30 mt-1 w-full max-h-72 overflow-auto rounded-md border-2 border-slate-300 bg-white shadow-xl"
          data-testid={`${testId}-panel`}
        >
          <div className="sticky top-0 bg-white border-b border-slate-200 p-2 flex items-center gap-2">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("Search by name, ID, trade…")}
              className="flex-1 outline-none text-sm bg-transparent"
              autoFocus
              data-testid={`${testId}-search`}
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="text-slate-400 hover:text-slate-700"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          {filtered.length === 0 ? (
            <div className="p-4 text-sm text-slate-500 text-center">
              {total === 0
                ? t("Roster not uploaded yet — type the name freely.")
                : t("No matches — your typed value will be saved as custom.")}
            </div>
          ) : (
            filtered.map((it, idx) => {
              const selected = value && value === it.name;
              return (
                <button
                  key={(it.id || `e-${idx}`) + "-" + idx}
                  type="button"
                  onClick={() => pick(it)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-red-50 border-b border-slate-100 ${
                    selected ? "bg-red-100" : ""
                  }`}
                  data-testid={`${testId}-item-${idx}`}
                >
                  <div className="flex items-center gap-2">
                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="font-bold text-slate-900">{it.name}</span>
                    {it.employee_id && (
                      <span className="font-mono text-[11px] text-slate-500">
                        #{it.employee_id}
                      </span>
                    )}
                  </div>
                  {(it.trade || it.role || it.crew) && (
                    <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                      {[it.trade, it.role, it.crew].filter(Boolean).join(" · ")}
                    </div>
                  )}
                </button>
              );
            })
          )}
          {showFooterTip && (
            <div className="sticky bottom-0 bg-slate-50 border-t border-slate-200 px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">
              {t("Tip: type freely for anyone not in the roster.")}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EmployeeCombo;
