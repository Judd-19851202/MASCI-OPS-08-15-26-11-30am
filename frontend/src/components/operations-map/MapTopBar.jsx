import React, { useEffect, useRef, useState } from "react";
import { searchAssets } from "@/lib/operations-map/useMapSnapshot";
import { useDebouncedValue } from "@/lib/operations-map/useMapState";

export default function MapTopBar({ counts, onSelect, lastFetchMs, motiveActive }) {
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
      <strong style={{ color: "#f1f5f9", letterSpacing: "0.04em" }}>FORGEDOPS · LIVE OPERATIONS</strong>
      <div className="ops-map-search" ref={ref}>
        <input
          data-testid="ops-map-search-input"
          placeholder="Search unit, VIN, driver…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
        />
        {open && hits.length > 0 && (
          <div data-testid="ops-map-search-results"
               style={{ position: "absolute", marginTop: 4, background: "#0b1320",
                        border: "1px solid #334155", borderRadius: 8, width: 480,
                        maxHeight: 320, overflowY: "auto", zIndex: 50 }}>
            {hits.map((h, i) => (
              <button key={i} data-testid={`ops-map-search-hit-${i}`}
                onClick={() => { onSelect(h.unit_number || h.key); setOpen(false); setQ(""); }}
                style={{ display: "block", width: "100%", textAlign: "left",
                         padding: "8px 12px", background: "transparent", border: 0,
                         color: "#e2e8f0", cursor: "pointer", fontSize: 14, borderTop: "1px solid #1f2937" }}>
                <span style={{ color: "#94a3b8", fontSize: 11, textTransform: "uppercase", marginRight: 8 }}>{h.kind}</span>
                <strong>{h.label || h.key}</strong>
                {h.vin && <span style={{ color: "#64748b", marginLeft: 8 }}>· {h.vin}</span>}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="ops-map-legend" data-testid="ops-map-legend">
        <span><span className="dot green" />{counts?.green ?? 0} Active</span>
        <span><span className="dot amber" />{counts?.amber ?? 0} Stale</span>
        <span><span className="dot red" />{counts?.red ?? 0} Critical</span>
        <span><span className="dot gray" />{counts?.gray ?? 0} Offline</span>
      </div>
      <div style={{ color: "#94a3b8", fontSize: 12 }} data-testid="ops-map-motive-chip">
        <span style={{
          display: "inline-block", width: 8, height: 8, borderRadius: 4,
          background: motiveActive ? "#22c55e" : "#64748b", marginRight: 6,
        }}/>
        Motive {motiveActive ? "Active" : "Standby"}
        {lastFetchMs != null && <span style={{ marginLeft: 12 }}>·  {lastFetchMs} ms</span>}
      </div>
    </header>
  );
}
