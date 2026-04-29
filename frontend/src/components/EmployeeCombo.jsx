import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, User } from "lucide-react";
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

  // Filter the roster using the SAME text the user is typing in the main
  // input — no separate search box, no focus-stealing autoFocus. This is the
  // single source of truth for both the form value AND the list filter.
  const filtered = useMemo(() => {
    const q = (value || "").trim().toLowerCase();
    const items = data.items || [];
    if (!q) return items.slice(0, 200); // show first 200 when empty
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
  }, [data, value]);

  const pick = (it) => {
    const label = it.name || "";
    onChange?.(label);
    onPick?.(it);
    setOpen(false);
  };

  const total = data.count || (data.items || []).length;
  // "Custom value" is what the user typed that doesn't exactly match any roster name
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
          {filtered.length === 0 ? (
            <div className="p-4 text-sm text-slate-500 text-center">
              {total === 0
                ? t("Roster not uploaded yet — type the name freely.")
                : t("No matches — your typed name will be saved.")}
            </div>
          ) : (
            <>
              {showCustomTag && (
                <div className="px-3 py-2 text-xs bg-amber-50 border-b-2 border-amber-300 text-amber-900 font-mono">
                  {t("Will save as new entry:")} <strong className="font-bold">{value}</strong>
                </div>
              )}
              {filtered.map((it, idx) => {
                const selected = value && value === it.name;
                return (
                  <button
                    key={(it.id || `e-${idx}`) + "-" + idx}
                    type="button"
                    onClick={() => pick(it)}
                    onMouseDown={(e) => e.preventDefault()}
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
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default EmployeeCombo;
