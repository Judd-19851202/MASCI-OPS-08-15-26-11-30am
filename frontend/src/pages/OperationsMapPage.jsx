import React, { useMemo } from "react";
import "@/components/operations-map/OperationsMap.css";
import MapCanvas from "@/components/operations-map/MapCanvas";
import MapTopBar from "@/components/operations-map/MapTopBar";
import MapFilterRail from "@/components/operations-map/MapFilterRail";
import MapTimelineDock from "@/components/operations-map/MapTimelineDock";
import AssetCardSheet from "@/components/operations-map/AssetCardSheet";
import { useMapState } from "@/lib/operations-map/useMapState";
import { useMapSnapshot, useTimeline } from "@/lib/operations-map/useMapSnapshot";

export default function OperationsMapPage() {
  const { filters, selected, setTypes, setStatus, setDriver, selectAsset } = useMapState();
  const { data, loading, error, lastFetchMs } = useMapSnapshot({ refreshMs: 15000 });
  const { rows: timelineRows } = useTimeline({ refreshMs: 15000 });

  const motiveActive = !error && (data?.counts?.green ?? 0) + (data?.counts?.amber ?? 0) > 0;
  const projects = useMemo(() => [], []);   // wire to dispatch project list in V2

  return (
    <div className="ops-map-shell" data-testid="operations-map-page">
      <div className="ops-map-grid">
        <MapTopBar
          counts={data?.counts}
          onSelect={selectAsset}
          lastFetchMs={lastFetchMs}
          motiveActive={motiveActive}
        />
        <MapFilterRail
          filters={filters}
          setTypes={setTypes}
          setStatus={setStatus}
          setDriver={setDriver}
          projects={projects}
        />
        <MapCanvas snapshot={data} filters={filters} onSelect={selectAsset} />
        <MapTimelineDock rows={timelineRows} />
        {selected && (
          <AssetCardSheet assetKey={selected} onClose={() => selectAsset(null)} />
        )}
        {loading && !data && (
          <div data-testid="ops-map-loading"
               style={{ position: "absolute", top: 80, left: "50%", transform: "translateX(-50%)",
                        color: "#94a3b8", background: "rgba(14,22,38,0.9)",
                        padding: "8px 14px", borderRadius: 8 }}>
            Loading live operations…
          </div>
        )}
        {error && (
          <div data-testid="ops-map-error"
               style={{ position: "absolute", top: 80, left: "50%", transform: "translateX(-50%)",
                        color: "#f87171", background: "rgba(44,14,14,0.95)",
                        padding: "8px 14px", borderRadius: 8 }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
