import React, { useEffect, useMemo } from "react";
import "@/components/operations-map/OperationsMap.css";
import MapCanvas from "@/components/operations-map/MapCanvas";
import MapTopBar from "@/components/operations-map/MapTopBar";
import MapOperationsBanner from "@/components/operations-map/MapOperationsBanner";
import ProjectIntelligenceStrip from "@/components/operations-map/ProjectIntelligenceStrip";
import MapFilterRail from "@/components/operations-map/MapFilterRail";
import MapTimelineDock from "@/components/operations-map/MapTimelineDock";
import AssetCardSheet from "@/components/operations-map/AssetCardSheet";
import { useMapState } from "@/lib/operations-map/useMapState";
import { useMapSnapshot, useTimeline } from "@/lib/operations-map/useMapSnapshot";

export default function OperationsMapPage() {
  // Use a platform-consistent page title.
  useEffect(() => {
    const prev = document.title;
    document.title = "Operations Center · Live Map · MASCI";
    return () => { document.title = prev; };
  }, []);

  const { filters, selected, setTypes, setStatus, setDriver, selectAsset } = useMapState();
  const { data, loading, error, lastFetchMs } = useMapSnapshot({ refreshMs: 15000 });
  const { rows: timelineRows } = useTimeline({ refreshMs: 15000 });

  const motiveActive = !error && (data?.counts?.green ?? 0) + (data?.counts?.amber ?? 0) > 0;

  // V1: projects and geofences are surfaced primarily; in V2 we wire the
  // projects feed from dispatch. For now the geofence list comes from the
  // snapshot payload (real Motive geofences) so the filter is meaningful
  // the moment production geofences populate.
  const geofences = useMemo(() => data?.geofences || [], [data]);
  const projects  = useMemo(() => [], []); // wired in V1.1 to dispatch project list

  return (
    <div className="ops-map-shell" data-testid="operations-map-page">
      <div className="ops-map-grid">
        <MapTopBar
          onSelect={selectAsset}
          lastFetchMs={lastFetchMs}
          motiveActive={motiveActive}
        />
        <MapOperationsBanner counts={data?.counts} />
        <ProjectIntelligenceStrip rollups={data?.project_rollups || []} />
        <MapFilterRail
          filters={filters}
          setTypes={setTypes}
          setStatus={setStatus}
          setDriver={setDriver}
          projects={projects}
          geofences={geofences}
        />
        <MapCanvas snapshot={data} filters={filters} onSelect={selectAsset} />
        <MapTimelineDock rows={timelineRows} />
        {selected && (
          <AssetCardSheet assetKey={selected} onClose={() => selectAsset(null)} />
        )}
        {loading && !data && (
          <div data-testid="ops-map-loading"
               style={{ position: "absolute", top: 144, left: "50%", transform: "translateX(-50%)",
                        color: "#475569", background: "#ffffff",
                        padding: "8px 14px", borderRadius: 8,
                        border: "1px solid #e2e8f0",
                        boxShadow: "0 4px 12px rgba(15,23,42,0.10)" }}>
            Loading Operations Center…
          </div>
        )}
        {error && (
          <div data-testid="ops-map-error"
               style={{ position: "absolute", top: 144, left: "50%", transform: "translateX(-50%)",
                        color: "#be123c", background: "#fff1f2",
                        padding: "8px 14px", borderRadius: 8,
                        border: "1px solid #fecdd3" }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
