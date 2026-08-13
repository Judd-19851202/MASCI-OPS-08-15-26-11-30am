import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, Building2, Plus, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

/**
 * SupplierCombo
 * -------------
 * Searchable picker for the MASCI subcontractor / supplier list, fed by
 * GET /api/suppliers. Same UX as EmployeeCombo / EquipmentCombo.
 * Always allows free-text fallback so forms still work for one-off vendors.
 */
/**
 * Module-level cache.
 *
 *   - `_cache` holds the LAST SUCCESSFUL response. We only assign to it when
 *     the GET actually returned a valid items array — never store an empty
 *     fallback so a transient failure doesn't permanently poison every
 *     downstream Combo render.
 *   - `_cachePromise` lets concurrent mounts share an in-flight request.
 *   - `loadList()` ALWAYS retries on error / non-array body — the next mount
 *     gets a fresh fetch instead of the empty fallback.
 */
let _cache = null;
let _cachePromise = null;

async function loadList() {
  if (_cache && Array.isArray(_cache.items) && _cache.items.length > 0) {
    return _cache;
  }
  if (_cachePromise) return _cachePromise;
  _cachePromise = api
    .get("/suppliers", { timeout: 30000, skipSessionStatus: true })
    .then((r) => {
      if (Array.isArray(r?.data?.items)) {
        if (r.data.items.length > 0) {
          _cache = r.data;
        }
        return r.data;
      }
      // Non-array response → don't poison the cache. Return empty for THIS
      // call but leave _cache null so the next mount tries again.
      return { items: [], count: 0 };
    })
    .catch(() => {
      // Network / CORS / timeout error → return empty for this call but
      // do NOT cache, so the user gets a fresh load on the next interaction.
      return { items: [], count: 0 };
    })
    .finally(() => {
      _cachePromise = null;
    });
  return _cachePromise;
}

export function clearSupplierCache() {
  _cache = null;
  _cachePromise = null;
}

export const SupplierCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  "data-testid": dataTestId,
  testId = "supplier-combo",
  className = "",
}) => {
  const { t } = useT();
  const testIdBase = dataTestId || testId;
  const ph = placeholder || t("Type or pick a supplier…");
  const [data, setData] = useState({ items: [], count: 0 });
  const [serverResults, setServerResults] = useState(null);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    let retryTimer = null;
    const tryLoad = (attempt) => {
      loadList().then((d) => {
        if (!alive) return;
        setData(d);
        // If we got an empty list, retry once with backoff. Field crews
        // experience CORS / network blips on first mount, and silently
        // serving them an empty dropdown is the "no employees" bug.
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

  // Population-independent SERVER-SIDE search: on typing, the supplier master is
  // searched in the DB across the ENTIRE canonical population (not just the
  // cached first page), so a vendor is discoverable regardless of master size.
  useEffect(() => {
    const term = (value || "").trim();
    if (term.length < 1) { setServerResults(null); return; }
    let alive = true;
    const timer = setTimeout(async () => {
      try {
        const r = await api.get("/suppliers", { params: { q: term, limit: 50 }, skipSessionStatus: true });
        if (alive) setServerResults(Array.isArray(r.data?.items) ? r.data.items : []);
      } catch { if (alive) setServerResults(null); }
    }, 220);
    return () => { alive = false; clearTimeout(timer); };
  }, [value]);

  // Filter the list using the SAME text the user is typing in the main
  // input — no separate search box, no autoFocus stealing focus.
  const filtered = useMemo(() => {
    const q = (value || "").trim().toLowerCase();
    const items = data.items || [];
    if (!q) return items.slice(0, 200); // first page when empty (page size, not a population cap)
    const localMatches = items.filter((it) => (it.name || "").toLowerCase().includes(q));
    const merged = [...localMatches];
    const seen = new Set(localMatches.map((it) => it.id || it.name));
    for (const it of (serverResults || [])) {
      const key = it.id || it.name;
      if (!seen.has(key)) { seen.add(key); merged.push(it); }
    }
    return merged.slice(0, 200); // display page size on RESULTS (full population already searched)
  }, [data, value, serverResults]);

  const pick = (it) => {
    onChange?.(it.name || "");
    onPick?.(it);
    setOpen(false);
  };

  const [addingNew, setAddingNew] = useState(false);
  const addToList = async (rawName) => {
    const name = (rawName || "").trim();
    if (name.length < 2) return;
    setAddingNew(true);
    try {
      const r = await api.post("/suppliers/add", { name }, { skipSessionStatus: true });
      const created = r?.data?.created;
      const sup = r?.data?.supplier;
      clearSupplierCache();
      const fresh = await loadList();
      setData(fresh);
      toast.success(
        created ? `Added "${name}" to vendor list` : `"${name}" already on list`
      );
      if (sup) {
        onChange?.(sup.name || name);
        onPick?.(sup);
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
  const exactMatch = filtered.some(
    (it) => (it.name || "").toLowerCase() === (value || "").trim().toLowerCase()
  );
  const showCustomTag = !!(value || "").trim() && !exactMatch && total > 0;

  return (
    <div className={`relative ${className}`} ref={wrapRef} data-testid={testIdBase}>
      <div className="flex gap-1.5">
        <Input
          value={value}
          onChange={(e) => {
            onChange?.(e.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder={ph}
          className="flex-1 h-12 text-[0.95rem] border-2 border-slate-300 focus:border-red-700"
          data-testid={`${testIdBase}-input`}
          autoComplete="off"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-12 w-12 border-2 border-slate-300 hover:border-red-700 hover:text-red-700 shrink-0"
          onClick={() => {
            // If cache is empty, force a re-fetch when the user clicks the
            // chevron (self-recovery from a transient first-load failure).
            if ((data?.items?.length || 0) === 0) {
              clearSupplierCache();
              loadList().then((d) => setData(d));
            }
            setOpen((v) => !v);
          }}
          data-testid={`${testIdBase}-toggle`}
          title={t("Browse supplier list")}
          aria-label={t("Browse supplier list")}
        >
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </div>

      {open && (
        <div
          className="absolute z-30 mt-2 w-full max-h-80 overflow-auto rounded-[1rem] border-2 border-slate-300 bg-white shadow-xl"
          data-testid={`${testIdBase}-panel`}
        >
          {filtered.length === 0 ? (
            <div className="p-3 text-sm text-slate-700">
              <div className="text-center text-slate-500 mb-3">
                {total === 0
                  ? t("Supplier list not uploaded yet — type freely.")
                  : t("No matches.")}
              </div>
              {!!(value || "").trim() && (value || "").trim().length >= 2 && (
                <button
                  type="button"
                  onClick={() => addToList(value)}
                  disabled={addingNew}
                  onMouseDown={(e) => e.preventDefault()}
                  className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold uppercase tracking-wide text-xs h-10 rounded border-b-2 border-emerald-800"
                  data-testid={`${testIdBase}-add-btn`}
                >
                  {addingNew ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  {t("Add")} &quot;{value}&quot; {t("to vendor list")}
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
                    onClick={() => addToList(value)}
                    disabled={addingNew}
                    onMouseDown={(e) => e.preventDefault()}
                    className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold uppercase tracking-wider text-[10px] h-7 px-2 rounded border-b-2 border-emerald-800 shrink-0"
                    data-testid={`${testIdBase}-add-btn`}
                  >
                    {addingNew ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Plus className="w-3 h-3" />
                    )}
                    {t("Add to list")}
                  </button>
                </div>
              )}
              {filtered.map((it, idx) => {
                const selected = value && value === it.name;
                return (
                  <button
                    key={(it.id || `s-${idx}`) + "-" + idx}
                    type="button"
                    onClick={() => pick(it)}
                    onMouseDown={(e) => e.preventDefault()}
                    className={`w-full text-left px-4 py-3 text-[0.95rem] hover:bg-red-50 border-b border-slate-100 ${
                      selected ? "bg-red-100" : ""
                    }`}
                    data-testid={`${testIdBase}-item-${idx}`}
                  >
                    <div className="flex items-center gap-2">
                      <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="font-bold text-slate-900">{it.name}</span>
                    </div>
                  </button>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default SupplierCombo;