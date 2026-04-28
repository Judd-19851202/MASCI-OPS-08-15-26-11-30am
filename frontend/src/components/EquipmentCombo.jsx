import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, Check, Search, X } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";

/**
 * EquipmentCombo
 * --------------
 * Searchable, category-grouped equipment picker fed by GET /api/equipment-master.
 * Always allows free-text input as a fallback (operators can type custom unit
 * numbers / equipment that isn't in the master list).
 *
 * Props
 * - value:        current string value
 * - onChange:     (string) => void
 * - onPick:       optional (item) => void  — fires when user picks a master unit
 * - placeholder:  string
 * - filterCategories: optional array of category names to limit the picker to
 *                  (e.g. ["Excavators"] for the Pre-Op when type=Excavator)
 * - testId:       optional data-testid prefix
 * - className:    extra classes for the input
 */
let _cache = null;
let _cachePromise = null;

async function loadMaster() {
  if (_cache) return _cache;
  if (_cachePromise) return _cachePromise;
  _cachePromise = api
    .get("/equipment-master")
    .then((r) => {
      _cache = r.data || { categories: [], items: [], grouped: {} };
      return _cache;
    })
    .catch(() => ({ categories: [], items: [], grouped: {} }))
    .finally(() => {
      _cachePromise = null;
    });
  return _cachePromise;
}

export const EquipmentCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  filterCategories = null,
  testId = "equipment-combo",
  className = "",
}) => {
  const { t } = useT();
  const ph = placeholder || t("Type or pick a unit…");
  const [data, setData] = useState({ categories: [], items: [], grouped: {} });
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    loadMaster().then((d) => {
      if (alive) setData(d);
    });
    return () => {
      alive = false;
    };
  }, []);

  // Close on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const grouped = useMemo(() => {
    const src = data.grouped || {};
    const cats = filterCategories
      ? Object.keys(src).filter((c) => filterCategories.includes(c))
      : Object.keys(src);
    const q = query.trim().toLowerCase();
    const out = {};
    for (const c of cats.sort()) {
      const list = (src[c] || []).filter((it) => {
        if (!q) return true;
        const hay = [
          it.unit_number,
          it.make_model,
          String(it.year || ""),
          it.vin_serial_number,
          it.plate,
          it.display_label,
          c,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      });
      if (list.length) out[c] = list;
    }
    return out;
  }, [data, query, filterCategories]);

  const totalShown = useMemo(
    () => Object.values(grouped).reduce((n, l) => n + l.length, 0),
    [grouped]
  );

  const pick = (it) => {
    const label = it.display_label || it.make_model || "";
    onChange?.(label);
    onPick?.(it);
    setOpen(false);
    setQuery("");
  };

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
          title={t("Browse fleet")}
        >
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </div>

      {open && (
        <div
          className="absolute z-30 mt-1 w-full max-h-80 overflow-auto rounded-md border-2 border-slate-300 bg-white shadow-xl"
          data-testid={`${testId}-panel`}
        >
          <div className="sticky top-0 bg-white border-b border-slate-200 p-2 flex items-center gap-2">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("Search unit #, make, model, VIN…")}
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
          {totalShown === 0 ? (
            <div className="p-4 text-sm text-slate-500 text-center">
              {data.count === 0
                ? t("Equipment list not loaded yet.")
                : t("No matches — your typed value will be saved as custom.")}
            </div>
          ) : (
            Object.entries(grouped).map(([cat, list]) => (
              <div key={cat}>
                <div className="sticky top-[42px] bg-slate-100 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-700 font-bold px-3 py-1.5 border-y border-slate-200">
                  {cat}
                  <span className="ml-2 text-slate-500 normal-case font-normal tracking-normal">
                    ({list.length})
                  </span>
                </div>
                {list.map((it, idx) => {
                  const selected =
                    value && (value === it.display_label || value === it.unit_number);
                  return (
                    <button
                      key={(it.id || `${cat}-${idx}`) + "-" + idx}
                      type="button"
                      onClick={() => pick(it)}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-red-50 border-b border-slate-100 ${
                        selected ? "bg-red-100" : ""
                      }`}
                      data-testid={`${testId}-item-${cat}-${idx}`}
                    >
                      <div className="flex items-center gap-2">
                        {selected && <Check className="w-3.5 h-3.5 text-red-700 shrink-0" />}
                        <span className="font-bold text-slate-900">
                          {it.unit_number || "—"}
                        </span>
                        <span className="text-slate-500">·</span>
                        <span className="text-slate-700">
                          {(it.year ? it.year + " " : "") + it.make_model}
                        </span>
                      </div>
                      {(it.plate || it.vin_serial_number) && (
                        <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                          {it.plate ? `Plate ${it.plate}` : ""}
                          {it.plate && it.vin_serial_number ? " · " : ""}
                          {it.vin_serial_number ? `VIN/SN ${it.vin_serial_number}` : ""}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}
          <div className="sticky bottom-0 bg-slate-50 border-t border-slate-200 px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">
            {t("Tip: type freely for custom equipment not in fleet.")}
          </div>
        </div>
      )}
    </div>
  );
};

export default EquipmentCombo;
