import { useEffect, useMemo, useState, useRef } from "react";
import { ChevronsUpDown, Check } from "lucide-react";
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
/**
 * Module-level cache. See SupplierCombo for the defensive pattern:
 *   - `_cache` only stores SUCCESSFUL non-empty responses.
 *   - Empty fallbacks are returned for the call but NEVER cached, so
 *     transient CORS / network blips don't permanently poison every
 *     downstream Combo render.
 */
let _cache = null;
let _cachePromise = null;
let _publicCache = null;
let _publicCachePromise = null;

async function loadMaster({ publicFallback = false } = {}) {
  const cache = publicFallback ? _publicCache : _cache;
  const cachePromise = publicFallback ? _publicCachePromise : _cachePromise;
  if (cache && Array.isArray(cache.items) && cache.items.length > 0) {
    return cache;
  }
  if (cachePromise) return cachePromise;
  const promise = api
    .get(publicFallback ? "/public/equipment-master-lookup" : "/equipment-master", { timeout: 30000, skipSessionStatus: true })
    .then((r) => {
      if (r?.data && Array.isArray(r.data.items) && r.data.items.length > 0) {
        if (publicFallback) {
          _publicCache = r.data;
          return _publicCache;
        }
        _cache = r.data;
        return _cache;
      }
      return { categories: [], items: [], grouped: {} };
    })
    .catch(() => ({ categories: [], items: [], grouped: {} }))
    .finally(() => {
      if (publicFallback) {
        _publicCachePromise = null;
      } else {
        _cachePromise = null;
      }
    });
  if (publicFallback) {
    _publicCachePromise = promise;
  } else {
    _cachePromise = promise;
  }
  return promise;
}

export function clearEquipmentCache() {
  _cache = null;
  _cachePromise = null;
  _publicCache = null;
  _publicCachePromise = null;
}

export const EquipmentCombo = ({
  value = "",
  onChange,
  onPick,
  placeholder,
  filterCategories = null,
  publicFallback = false,
  "data-testid": dataTestId,
  testId = "equipment-combo",
  className = "",
}) => {
  const { t } = useT();
  const testIdBase = dataTestId || testId;
  const ph = placeholder || t("Type or pick a unit…");
  const [data, setData] = useState({ categories: [], items: [], grouped: {} });
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    let alive = true;
    let retryTimer = null;
    const tryLoad = (attempt) => {
      loadMaster({ publicFallback }).then((d) => {
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
  }, [publicFallback]);

  // Close on outside click
  useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Filter the fleet using the SAME text the user types in the main input.
  // No separate search box, no autoFocus stealing focus.
  const grouped = useMemo(() => {
    const src = data.grouped || {};
    const cats = filterCategories
      ? Object.keys(src).filter((c) => filterCategories.includes(c))
      : Object.keys(src);
    const q = (value || "").trim().toLowerCase();
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
  }, [data, value, filterCategories]);

  const totalShown = useMemo(
    () => Object.values(grouped).reduce((n, l) => n + l.length, 0),
    [grouped]
  );

  const pick = (it) => {
    // Track 15.73 Slice 1 · trust fix · emit canonical unit_number (not
    // display_label). Storing the long human label as the unit identifier
    // broke every downstream lookup that keys on equipment_master.unit_number
    // (Pre-Op classification chip, canonical inspection template, fleet
    // aggregator). Fallback chain preserves backwards-compatibility for
    // legacy equipment_master rows that lack a unit_number.
    const label = it.unit_number || it.display_label || it.make_model || "";
    onChange?.(label);
    onPick?.(it);
    setOpen(false);
  };

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
          className="flex-1 h-12 text-[0.95rem] border-[color:var(--border-bold)] focus:border-[color:var(--brand-primary)]"
          data-testid={`${testIdBase}-input`}
          autoComplete="off"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="h-12 w-12 shrink-0 rounded-[1rem] border-[color:var(--border-bold)] hover:border-red-700 hover:text-red-700"
          onClick={() => {
            // Self-recover: if cache loaded empty, force a re-fetch.
            if ((data?.items?.length || 0) === 0) {
              clearEquipmentCache();
              loadMaster().then((d) => setData(d));
            }
            setOpen((v) => !v);
          }}
          data-testid={`${testIdBase}-toggle`}
          title={t("Browse fleet")}
          aria-label={t("Browse fleet")}
        >
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </div>

      {open && (
        <div
          className="wp17-picker-panel absolute z-30 mt-2 w-full max-h-80 overflow-auto p-1.5"
          data-testid={`${testIdBase}-panel`}
        >
          {totalShown === 0 ? (
            <div className="wp17-picker-empty text-center">
              {data.count === 0
                ? t("Equipment list not loaded yet.")
                : t("No matches — your typed value will be saved.")}
            </div>
          ) : (
            Object.entries(grouped).map(([cat, list]) => (
              <div key={cat}>
                <div className="sticky top-0 rounded-[0.85rem] border border-slate-200/80 bg-slate-100/95 px-3 py-1.5 text-[10px] font-mono font-bold uppercase tracking-[0.2em] text-slate-700">
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
                      onMouseDown={(e) => e.preventDefault()}
                      className="wp17-picker-option group text-left text-sm"
                      data-selected={selected ? "true" : "false"}
                      data-testid={`${testIdBase}-item-${cat}-${idx}`}
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
        </div>
      )}
    </div>
  );
};

export default EquipmentCombo;
