import React, { useEffect, useState } from "react";
import { fetchAsset } from "@/lib/operations-map/useMapSnapshot";
import MapTrustChip from "./MapTrustChip";
import { ASSET_KIND_LABEL } from "@/lib/operations-map/icons";
import {
  describeEventFamily,
  describeOperationalState,
} from "@/lib/operations-map/eventVocab";

const SOURCE_LABEL = {
  explicit_project:    "Explicit Project",
  geofence_membership: "Geofence Membership",
  gps_location:        "GPS Location",
  missing_assignment:  "Missing Assignment",
  unknown:             "Unknown",
};
const CONFIDENCE_LABEL = {
  high:   "High Confidence",
  medium: "Medium Confidence",
  low:    "Low Confidence",
};

function fmtAge(iso) {
  if (!iso) return null;
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 60_000)   return `${Math.round(ms/1000)} seconds ago`;
  if (ms < 3600_000) return `${Math.round(ms/60_000)} minutes ago`;
  if (ms < 86400_000)return `${Math.round(ms/3600_000)} hours ago`;
  return `${Math.round(ms/86400_000)} days ago`;
}

function bearingCompass(b) {
  if (b == null) return null;
  const dirs = ["N","NE","E","SE","S","SW","W","NW"];
  return dirs[Math.round(((b % 360) / 45)) % 8];
}

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
  const assignment = a?.assignment || {};
  const opState = describeOperationalState(data?.asset_health?.status);
  const openIssues = data?.open_defects?.length ?? 0;
  const openInspections = data?.open_inspections?.length ?? 0;

  return (
    <aside className="ops-map-sheet ops-map-asset-sheet" data-testid="ops-map-asset-sheet">
      <button className="close" onClick={onClose} data-testid="ops-map-asset-sheet-close" aria-label="Close">×</button>
      {loading && <div style={{ color: "#94a3b8" }}>Loading…</div>}
      {error   && <div style={{ color: "#f87171" }} data-testid="ops-map-asset-sheet-error">{error}</div>}
      {a && (
        <>
          {/* 1 · Asset Identity */}
          <div data-testid="ops-map-asset-sheet-identity">
            <h2 data-testid="ops-map-asset-sheet-title">{a.unit_number || "Unknown"}</h2>
            <div className="meta">
              {ASSET_KIND_LABEL[a.marker_kind] || a.asset_kind || "asset"}
              {a.equipment_name ? ` · ${a.equipment_name}` : ""}
            </div>
          </div>

          {/* 2 · Current Assignment */}
          <section data-testid="ops-map-asset-sheet-assignment">
            <div className="section-title">Current Assignment</div>
            <div className="big-line">
              {data?.geofence_status?.inside
                ? data.geofence_status.name
                : assignment.name || "Unassigned / Unknown"}
            </div>
            <div className="sub-line">
              <span className="conf">
                {CONFIDENCE_LABEL[assignment.confidence] || "Low Confidence"}
              </span>
              {" · "}
              <span>Source: {SOURCE_LABEL[assignment.source] || "Unknown"}</span>
            </div>
          </section>

          {/* 3 · Operational State */}
          <section data-testid="ops-map-asset-sheet-health">
            <div className="section-title">Operational State</div>
            <div className={`state-badge state-${data?.asset_health?.status || "gray"}`}
                 data-testid="ops-map-asset-sheet-operational-state">
              {opState}
            </div>
          </section>

          {/* 4 · Operator */}
          <section data-testid="ops-map-asset-sheet-operator">
            <div className="section-title">Operator</div>
            <div className="big-line">
              {data?.driver?.name || "Unassigned"}
            </div>
            {data?.driver?.username && (
              <div className="sub-line">{data.driver.username}</div>
            )}
          </section>

          {/* 5 · Last Position Update */}
          <section data-testid="ops-map-asset-sheet-position">
            <div className="section-title">Last Position Update</div>
            <div className="big-line">
              {fmtAge(a.last_seen_at) || "No fix yet"}
            </div>
            <div className="sub-line">
              {a.lat != null && a.lon != null
                ? `${a.lat.toFixed(5)}, ${a.lon.toFixed(5)}`
                : <span style={{ color: "#be123c" }}>position missing — not interpolated</span>}
            </div>
            <div className="kv">
              <div className="k">Speed</div>
              <div className="v">
                {a.speed_mph != null ? `${a.speed_mph} mph`
                  : a.speed_kph != null ? `${a.speed_kph} km/h` : "—"}
              </div>
              <div className="k">Heading</div>
              <div className="v">
                {a.bearing != null
                  ? `${Math.round(a.bearing)}° ${bearingCompass(a.bearing) || ""}`
                  : "—"}
              </div>
              <div className="k">VIN</div>
              <div className="v" style={{ fontFamily: "IBM Plex Mono, monospace", fontSize: 12 }}>
                {a.vin || "—"}
              </div>
            </div>
          </section>

          {/* 6 · Open Issues */}
          <section data-testid="ops-map-asset-sheet-open-issues">
            <div className="section-title">Open Issues</div>
            <div className="big-line">
              {openIssues + openInspections === 0
                ? "None"
                : `${openIssues + openInspections} Open Item${openIssues + openInspections === 1 ? "" : "s"}`}
            </div>
            {openIssues > 0 && (
              <div className="sub-line" data-testid="ops-map-asset-sheet-open-defects">
                {openIssues} defect{openIssues === 1 ? "" : "s"}
              </div>
            )}
            {openInspections > 0 && (
              <div className="sub-line" data-testid="ops-map-asset-sheet-open-inspections">
                {openInspections} inspection{openInspections === 1 ? "" : "s"}
              </div>
            )}
          </section>

          {/* 7 · Recent Activity */}
          <section data-testid="ops-map-asset-sheet-events">
            <div className="section-title">Recent Activity</div>
            {(data?.recent_events || []).length === 0 && (
              <div style={{ color: "#94a3b8", fontSize: 13 }}>No activity yet.</div>
            )}
            {(data?.recent_events || []).slice(0, 8).map((e, i) => (
              <div key={i} className="activity-row">
                <span className="ts">{e.event_at?.slice(11, 19) || ""}</span>
                <span className="lbl">
                  {describeEventFamily(e.event_family || e.event_kind)}
                  {e.severity && <span style={{ color: "#be123c", marginLeft: 6 }}>{e.severity}</span>}
                  {e.source === "webhook" && <span className="live-chip">live</span>}
                </span>
              </div>
            ))}
          </section>

          {/* 8 · Trust / Data Source */}
          <section data-testid="ops-map-asset-sheet-trust">
            <div className="section-title">Data Source</div>
            <MapTrustChip trust={a.trust} />
            <div className="sub-line" style={{ marginTop: 6 }}>
              {data?.motive_status?.enabled
                ? <>Telemetry connected{data?.motive_status?.webhook_armed && <> · live feed armed</>}</>
                : <>Telemetry disconnected</>}
            </div>
          </section>
        </>
      )}
    </aside>
  );
}
