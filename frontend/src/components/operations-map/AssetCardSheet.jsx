import React, { useEffect, useState } from "react";
import { fetchAsset } from "@/lib/operations-map/useMapSnapshot";
import MapTrustChip from "./MapTrustChip";
import { ASSET_KIND_LABEL } from "@/lib/operations-map/icons";

export default function AssetCardSheet({ assetKey, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!assetKey) { setData(null); return; }
    let cancelled = false;
    setLoading(true); setError(null);
    fetchAsset(assetKey)
      .then((r) => { if (!cancelled) setData(r); })
      .catch((e) => { if (!cancelled) setError(e?.response?.data?.detail || e?.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [assetKey]);

  if (!assetKey) return null;

  const a = data?.asset;
  return (
    <aside className="ops-map-sheet ops-map-asset-sheet" data-testid="ops-map-asset-sheet">
      <button className="close" onClick={onClose} data-testid="ops-map-asset-sheet-close" aria-label="Close">×</button>
      {loading && <div style={{ color: "#94a3b8" }}>Loading…</div>}
      {error   && <div style={{ color: "#f87171" }} data-testid="ops-map-asset-sheet-error">{error}</div>}
      {a && (
        <>
          <h2 data-testid="ops-map-asset-sheet-title">{a.unit_number || "Unknown"}</h2>
          <div className="meta">
            {ASSET_KIND_LABEL[a.marker_kind] || a.asset_kind || "asset"} · {a.equipment_name || "—"}
          </div>
          <MapTrustChip trust={a.trust} />

          <section>
            <div className="kv">
              <div className="k">Last GPS</div>
              <div className="v">
                {a.lat != null && a.lon != null
                  ? `${a.lat.toFixed(5)}, ${a.lon.toFixed(5)}`
                  : <span style={{ color: "#f87171" }}>missing — not interpolated</span>}
              </div>
              <div className="k">Last Update</div>
              <div className="v" data-testid="ops-map-asset-sheet-last-update">{a.last_seen_at || "—"}</div>
              <div className="k">Speed</div>
              <div className="v">{a.speed_mph != null ? `${a.speed_mph} mph` : a.speed_kph != null ? `${a.speed_kph} km/h` : "—"}</div>
              <div className="k">Heading</div>
              <div className="v">{a.bearing != null ? `${Math.round(a.bearing)}°` : "—"}</div>
              <div className="k">VIN</div>
              <div className="v" style={{ fontFamily: "monospace", fontSize: 12 }}>{a.vin || "—"}</div>
            </div>
          </section>

          <section data-testid="ops-map-asset-sheet-driver">
            <div className="kv">
              <div className="k">Driver</div>
              <div className="v">
                {data?.driver?.name ? data.driver.name : <span style={{ color: "#94a3b8" }}>unassigned</span>}
                {data?.driver?.username && <span style={{ color: "#64748b" }}> · {data.driver.username}</span>}
              </div>
              <div className="k">Geofence</div>
              <div className="v">
                {data?.geofence_status?.inside
                  ? <span style={{ color: "#22c55e" }}>INSIDE · {data.geofence_status.name}</span>
                  : <span style={{ color: "#94a3b8" }}>outside known geofences</span>}
              </div>
            </div>
          </section>

          <section data-testid="ops-map-asset-sheet-health">
            <div className="kv">
              <div className="k">Operational State</div>
              <div className="v">{
                ({ green: "Working", amber: "Idle", red: "Attention Required", gray: "Offline" }[data?.asset_health?.status] || "Unknown")
              }</div>
              <div className="k">Telemetry</div>
              <div className="v">
                {data?.motive_status?.enabled ? "Connected" : "Disconnected"}
                {data?.motive_status?.webhook_armed && <span style={{ color: "#0d9488", marginLeft: 8 }}>· live link armed</span>}
              </div>
              <div className="k">Open Issues</div>
              <div className="v">{(data?.open_defects?.length ?? 0)}</div>
              <div className="k">Open Inspections</div>
              <div className="v">{(data?.open_inspections?.length ?? 0)}</div>
            </div>
          </section>

          <section data-testid="ops-map-asset-sheet-events">
            <h4 style={{ color: "#64748b", margin: "4px 0 4px 0", fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Recent Events
            </h4>
            {(data?.recent_events || []).length === 0 && (
              <div style={{ color: "#94a3b8", fontSize: 13 }}>No events yet.</div>
            )}
            {(data?.recent_events || []).slice(0, 8).map((e, i) => (
              <div key={i} style={{ display: "grid", gridTemplateColumns: "78px 1fr", gap: 8, fontSize: 12, padding: "2px 0", color: "#cbd5e1" }}>
                <span style={{ color: "#64748b", fontVariantNumeric: "tabular-nums" }}>
                  {e.event_at?.slice(11, 19) || ""}
                </span>
                <span>
                  {e.event_family || e.event_kind}
                  {e.severity && <span style={{ color: "#f87171", marginLeft: 6 }}>{e.severity}</span>}
                  {e.source === "webhook" && <span style={{ color: "#38bdf8", marginLeft: 6 }}>live</span>}
                </span>
              </div>
            ))}
          </section>
        </>
      )}
    </aside>
  );
}
