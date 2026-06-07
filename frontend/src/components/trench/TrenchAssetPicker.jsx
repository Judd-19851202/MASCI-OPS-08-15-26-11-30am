// Phase 10A-B · Trench Asset Picker (Correction 4 + 5)
// Multi-select pulled from /api/trench-safety/excavations/public/asset-roster.
// Filterable by asset_type (Trench Box · Road Plate · End Panel · Spreader Bar · …).
import React, { useEffect, useMemo, useState } from "react";
import { X, Search, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

// Module-level loader to satisfy the "no set-state-in-effect" rule.
async function _loadRoster(assetType) {
  try {
    const params = {};
    if (assetType) params.asset_type = assetType;
    const r = await api.get("/trench-safety/excavations/public/asset-roster", { params });
    return Array.isArray(r.data?.items) ? r.data.items : [];
  } catch {
    return [];
  }
}

export default function TrenchAssetPicker({ selected = [], onChange, assetType, testId = "trench-asset-picker", maxItems = 12 }) {
  const { t } = useT();
  const [q, setQ] = useState("");
  const [state, setState] = useState({ roster: [], loading: true });
  const { roster, loading } = state;

  useEffect(() => {
    let alive = true;
    _loadRoster(assetType).then((items) => {
      if (alive) setState({ roster: items, loading: false });
    });
    return () => { alive = false; };
  }, [assetType]);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return roster.slice(0, maxItems);
    return roster
      .filter((a) => `${a.asset_id} ${a.serial_number} ${a.assigned_location}`.toLowerCase().includes(term))
      .slice(0, maxItems);
  }, [roster, q, maxItems]);

  const toggle = (assetId) => {
    if (selected.includes(assetId)) onChange(selected.filter((s) => s !== assetId));
    else onChange([...selected, assetId]);
  };

  const selectedAssets = selected.map((id) => roster.find((a) => a.asset_id === id) || { asset_id: id, asset_type: "?", operational_status: "?" });

  return (
    <div data-testid={testId}>
      {/* Selected chips */}
      {selectedAssets.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2" data-testid={`${testId}-selected`}>
          {selectedAssets.map((a) => (
            <span key={a.asset_id} className="inline-flex items-center gap-1 bg-cyan-700 text-white text-xs font-bold font-mono uppercase px-2 py-1 rounded" data-testid={`${testId}-chip-${a.asset_id}`}>
              {a.asset_id}
              <button type="button" onClick={() => toggle(a.asset_id)} className="hover:bg-cyan-800 rounded" aria-label={`Remove ${a.asset_id}`} data-testid={`${testId}-chip-remove-${a.asset_id}`}>
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search box */}
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t(assetType ? `Search ${assetType}s by ID, serial, or location…` : "Search assets by ID, serial, or location…")}
          className="pl-8 w-full h-11 border-2 border-slate-300 rounded font-mono uppercase text-sm focus:border-cyan-600 focus:outline-none"
          data-testid={`${testId}-search`}
        />
      </div>

      {/* Roster results */}
      <div className="mt-2 border border-slate-200 rounded max-h-72 overflow-y-auto" data-testid={`${testId}-list`}>
        {loading ? (
          <div className="p-3 text-sm text-slate-500 inline-flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> {t("Loading roster…")}</div>
        ) : filtered.length === 0 ? (
          <div className="p-3 text-sm text-slate-500 italic">{q ? t("No match in registry.") : t("Type to search the certified registry.")}</div>
        ) : (
          <ul>
            {filtered.map((a) => {
              const isSel = selected.includes(a.asset_id);
              const statusColor =
                a.operational_status === "Available" ? "text-emerald-700" :
                a.operational_status === "Inspection Hold" ? "text-amber-700" :
                a.operational_status === "Repair" ? "text-red-700" :
                "text-slate-700";
              return (
                <li key={a.asset_id}>
                  <button
                    type="button"
                    onClick={() => toggle(a.asset_id)}
                    className={"w-full text-left px-3 py-2 border-b border-slate-100 last:border-0 flex items-start gap-2 " + (isSel ? "bg-cyan-50" : "hover:bg-slate-50")}
                    data-testid={`${testId}-row-${a.asset_id}`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-black text-slate-900">{a.asset_id}</span>
                        <span className="text-[10px] font-bold uppercase tracking-[0.12em] bg-slate-900 text-white px-1.5 py-0.5 rounded">{a.asset_type}</span>
                        {a.size_label && <span className="text-[10px] text-slate-500 font-mono">{a.size_label}</span>}
                        <span className={`text-[10px] font-bold uppercase tracking-[0.12em] ${statusColor}`}>{a.operational_status}</span>
                        {a.open_holds_count > 0 && (
                          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-amber-800">· {a.open_holds_count} hold{a.open_holds_count !== 1 ? "s" : ""}</span>
                        )}
                        {a.tabulated_data_available && (
                          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-cyan-700">· Tab Data</span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {[
                          a.serial_number && `SN: ${a.serial_number}`,
                          a.assigned_location && `Loc: ${a.assigned_location}`,
                          a.condition && `Cond: ${a.condition}`,
                          a.rated_depth_ft && `Rated: ${a.rated_depth_ft} ft`,
                        ].filter(Boolean).join(" · ")}
                      </div>
                    </div>
                    {isSel && <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-cyan-700 self-center">Selected ✓</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
