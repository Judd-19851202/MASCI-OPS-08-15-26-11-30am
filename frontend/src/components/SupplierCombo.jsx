import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, Search, X, Building2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";

/**
 * SupplierCombo
 * -------------
 * Searchable picker for the MASCI subcontractor / supplier list, fed by
 * GET /api/suppliers. Same UX as EmployeeCombo / EquipmentCombo.
 * Always allows free-text fallback so forms still work for one-off vendors.
 */
let _cache = null;
let _cachePromise = null;

async function loadList() {
  if (_cache) return _cache;
  if (_cachePromise) return _cachePromise;
  _cachePromise = api
    .get("/suppliers")
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

export function clearSupplierCache() {
  _cache = null;
  _cachePromise = null;
}

export const SupplierCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  testId = "supplier-combo",
  className = "",
}) => {
  const { t } = useT();
  const ph = placeholder || t("Type or pick a supplier…");
  const [data, setData] = useState({ items: [], count: 0 });
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    loadList().then((d) => {
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
    if (!q) return items.slice(0, 200);
    return items
      .filter((it) => (it.name || "").toLowerCase().includes(q))
      .slice(0, 200);
  }, [data, query]);

  const pick = (it) => {
    onChange?.(it.name || "");
    onPick?.(it);
    setOpen(false);
    setQuery("");
  };

  const total = data.count || (data.items || []).length;
  const showFooterTip = !total || (filtered.length === 0 && total > 0);

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
          title={t("Browse supplier list")}
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
              placeholder={t("Search by company name…")}
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
                ? t("Supplier list not uploaded yet — type freely.")
                : t("No matches — your typed value will be saved as custom.")}
            </div>
          ) : (
            filtered.map((it, idx) => {
              const selected = value && value === it.name;
              return (
                <button
                  key={(it.id || `s-${idx}`) + "-" + idx}
                  type="button"
                  onClick={() => pick(it)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-red-50 border-b border-slate-100 ${
                    selected ? "bg-red-100" : ""
                  }`}
                  data-testid={`${testId}-item-${idx}`}
                >
                  <div className="flex items-center gap-2">
                    <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="font-bold text-slate-900">{it.name}</span>
                  </div>
                </button>
              );
            })
          )}
          {showFooterTip && (
            <div className="sticky bottom-0 bg-slate-50 border-t border-slate-200 px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">
              {t("Tip: type freely for one-off vendors not in the list.")}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SupplierCombo;
