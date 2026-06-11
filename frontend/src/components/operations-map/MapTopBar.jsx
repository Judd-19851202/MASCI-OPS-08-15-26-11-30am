import React, { useEffect, useRef, useState } from "react";
import { searchAssets } from "@/lib/operations-map/useMapSnapshot";
import { useDebouncedValue } from "@/lib/operations-map/useMapState";

/* Identity-aligned Operations Center top bar.
 * No "FORGEDOPS · LIVE OPERATIONS" lockup, no fleet-tracking terminology.
 * Title uses the platform-wide `Operations Center · Live Map` lockup
 * and the platform Chivo display face. */
export default function MapTopBar({ onSelect, lastFetchMs, motiveActive }) {
  const [q, setQ] = useState("");
  const dq = useDebouncedValue(q, 200);
  const [hits, setHits] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    let cancelled = false;
    if (!dq) { setHits([]); return; }
    searchAssets(dq).then((r) => { if (!cancelled) setHits(r.hits || []); });
    return () => { cancelled = true; };
  }, [dq]);

  useEffect(() => {
    const onDocClick = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <header className="ops-map-topbar" data-testid="ops-map-topbar">
      <div className="font-display" style={{ fontWeight: 900, fontSize: 16, color: "#0f172a", letterSpacing: "0.01em" }}>
        Operations Center <span style={{ color: "#94a3b8" }}>·</span> <span style={{ color: "#0d9488" }}>Live Map</span>
      </div>

      <div className="ops-map-search" ref={ref}>
        <input
          data-testid="ops-map-search-input"
          placeholder="Find asset, project, geofence, or operator…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
        />
        {open && hits.length > 0 && (
          <div data-testid="ops-map-search-results"
               style={{ position: "absolute", marginTop: 4, background: "#ffffff",
                        border: "1px solid #e2e8f0", borderRadius: 8, width: "100%",
                        maxHeight: 320, overflowY: "auto", zIndex: 50,
                        boxShadow: "0 6px 24px rgba(15,23,42,0.12)" }}>
            {hits.map((h, i) => (
              <button key={i} data-testid={`ops-map-search-hit-${i}`}
                onClick={() => { onSelect(h.unit_number || h.key); setOpen(false); setQ(""); }}
                style={{ display: "block", width: "100%", textAlign: "left",
                         padding: "8px 12px", background: "transparent", border: 0,
                         color: "#0f172a", cursor: "pointer", fontSize: 14, borderTop: "1px solid #f1f5f9" }}>
                <span style={{ color: "#64748b", fontSize: 10, textTransform: "uppercase",
                              letterSpacing: "0.08em", marginRight: 8, fontWeight: 600 }}>
                  {h.kind === "asset" ? "Asset" : "Operator"}
                </span>
                <strong style={{ color: "#0f172a" }}>{h.label || h.key}</strong>
                {h.vin && <span style={{ color: "#94a3b8", marginLeft: 8, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 }}>· {h.vin}</span>}
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ color: "#64748b", fontSize: 12 }} data-testid="ops-map-motive-chip">
        <span style={{
          display: "inline-block", width: 8, height: 8, borderRadius: 4,
          background: motiveActive ? "#10b981" : "#94a3b8", marginRight: 6,
        }}/>
        Telemetry {motiveActive ? "Live" : "Standby"}
        {lastFetchMs != null && <span style={{ marginLeft: 12 }}>· refresh {lastFetchMs} ms</span>}
      </div>
    </header>
  );
}
