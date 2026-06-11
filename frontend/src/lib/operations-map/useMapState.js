import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

/* URL-synced filter + selection state for the Operations Map.
 * One source of truth so deep links work. */
export function useMapState() {
  const [params, setParams] = useSearchParams();

  const get = useCallback((k, def) => params.get(k) ?? def, [params]);

  const types   = (get("types", "") || "").split(",").filter(Boolean);
  const status  = (get("status", "green,amber,red,gray") || "").split(",").filter(Boolean);
  const driver  = get("driver", "") || "";
  const project = get("project", "") || "";
  const selected = get("a", "") || "";

  const update = useCallback((patch) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0)) {
        next.delete(k);
      } else {
        next.set(k, Array.isArray(v) ? v.join(",") : String(v));
      }
    }
    setParams(next, { replace: true });
  }, [params, setParams]);

  return {
    filters: { types, status, driver, project },
    selected,
    setTypes:    (v) => update({ types: v }),
    setStatus:   (v) => update({ status: v }),
    setDriver:   (v) => update({ driver: v }),
    setProject:  (v) => update({ project: v }),
    selectAsset: (key) => update({ a: key || null }),
  };
}

export function useDebouncedValue(value, ms = 250) {
  const [v, setV] = useState(value);
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t); }, [value, ms]);
  return v;
}
