import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, User, Plus, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

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
/**
 * Module-level cache. See SupplierCombo for the same defensive pattern:
 *
 *   - `_cache` holds the LAST SUCCESSFUL response. Empty fallbacks are NEVER
 *     stored, so a transient CORS / network blip doesn't permanently poison
 *     every later render.
 *   - The next mount after a failure gets a fresh fetch.
 */
let _cache = null;
let _cachePromise = null;

async function loadRoster() {
  if (_cache && Array.isArray(_cache.items) && _cache.items.length > 0) {
    return _cache;
  }
  if (_cachePromise) return _cachePromise;
  _cachePromise = api
    .get("/employees", { timeout: 30000 })
    .then((r) => {
      if (Array.isArray(r?.data?.items)) {
        _cache = r.data;
        return _cache;
      }
      return { items: [], count: 0 };
    })
    .catch(() => {
      return { items: [], count: 0 };
    })
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
    let retryTimer = null;
    const tryLoad = (attempt) => {
      loadRoster().then((d) => {
        if (!alive) return;
        setData(d);
        // Auto-retry up to 2x if the first load returns empty — handles
        // transient CORS / network blips on combo mount.
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

  const [addingNew, setAddingNew] = useState(false);
  const addToRoster = async (rawName) => {
    const name = (rawName || "").trim();
    if (name.length < 2) return;
    setAddingNew(true);
    try {
      const r = await api.post("/employees/add", { name });
      const created = r?.data?.created;
      const emp = r?.data?.employee;
      // Bust the module-level cache so subsequent combos see this person.
      clearEmployeeCache();
      // Refresh local roster
      const fresh = await loadRoster();
      setData(fresh);
      toast.success(
        created ? `Added "${name}" to MASCI roster` : `"${name}" already on roster`
      );
      if (emp) {
        onChange?.(emp.name || name);
        onPick?.(emp);
      }
      setOpen(false);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Failed to add";
      toast.error(msg);
    } finally {
      setAddingNew(false);
    }
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
          onClick={() => {
            // Self-recover: if the cache loaded empty, force a re-fetch
            // when the user clicks the chevron.
            if ((data?.items?.length || 0) === 0) {
              clearEmployeeCache();
              loadRoster().then((d) => setData(d));
            }
            setOpen((v) => !v);
          }}
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
            <div className="p-3 text-sm text-slate-700">
              <div className="text-center text-slate-500 mb-3">
                {total === 0
                  ? t("Roster not uploaded yet — type the name freely.")
                  : t("No matches.")}
              </div>
              {!!(value || "").trim() && (value || "").trim().length >= 2 && (
                <button
                  type="button"
                  onClick={() => addToRoster(value)}
                  disabled={addingNew}
                  onMouseDown={(e) => e.preventDefault()}
                  className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold uppercase tracking-wide text-xs h-10 rounded border-b-2 border-emerald-800"
                  data-testid={`${testId}-add-btn`}
                >
                  {addingNew ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  {t("Add")} "{value}" {t("to MASCI roster")}
                </button>
              )}
            </div>
          ) : (
            <>
              {showCustomTag && (
                <div className="px-3 py-2 bg-amber-50 border-b-2 border-amber-300 flex items-center gap-2">
                  <div className="flex-1 text-xs text-amber-900 font-mono truncate">
                    {t("Will save as new entry:")}{" "}
                    <strong className="font-bold">{value}</strong>
                  </div>
                  <button
                    type="button"
                    onClick={() => addToRoster(value)}
                    disabled={addingNew}
                    onMouseDown={(e) => e.preventDefault()}
                    className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold uppercase tracking-wider text-[10px] h-7 px-2 rounded border-b-2 border-emerald-800 shrink-0"
                    data-testid={`${testId}-add-btn`}
                  >
                    {addingNew ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Plus className="w-3 h-3" />
                    )}
                    {t("Add to roster")}
                  </button>
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
