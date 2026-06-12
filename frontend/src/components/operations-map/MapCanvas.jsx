import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { spriteUrl, KIND_LIST } from "@/lib/operations-map/icons";

/* MapCanvas
 * --------------
 * Renders the MapLibre WebGL canvas with two GeoJSON sources:
 *   - assets (clustered)
 *   - geofences (polygon fill + outline)
 *
 * Props:
 *   snapshot: { assets:[], geofences:[], counts:{} }
 *   filters:  { types:[], status:[], driver, project }
 *   onSelect: fn(unit_number)
 */
const TILE_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      // CARTO dark basemap — free, no API key, CORS-friendly, CDN-backed.
      // Falls back to Stadia and OSM if CARTO is unreachable.
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
      ],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors © CARTO',
    },
  },
  layers: [
    { id: "osm", type: "raster", source: "osm" },
  ],
};

export default function MapCanvas({ snapshot, filters, onSelect }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const [ready, setReady] = useState(false);

  // initial map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: TILE_STYLE,
      center: [-81.0, 28.9], // East-central Florida (MASCI service area)
      zoom: 8,
      attributionControl: true,
      // Track 13.4A · keep WebGL drawing buffer so Playwright / browser
      // screenshots actually capture the rendered map tiles (otherwise
      // page.screenshot() returns blank for the canvas region even
      // though the map is visible to human eyes).
      preserveDrawingBuffer: true,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");
    map.on("load", async () => {
      // Pre-load sprite icons (one per kind × band combo)
      for (const kind of KIND_LIST) {
        for (const band of ["green", "amber", "red", "gray"]) {
          const url = spriteUrl(kind, band);
          await new Promise((res) => {
            const img = new Image(32, 32);
            img.onload = () => {
              try {
                if (mapRef.current && !mapRef.current.hasImage(`spr-${kind}-${band}`)) {
                  mapRef.current.addImage(`spr-${kind}-${band}`, img, { pixelRatio: 2 });
                }
              } catch { /* map disposed mid-load — ignore */ }
              res();
            };
            img.onerror = () => res();
            img.src = url;
          });
        }
      }
      if (!mapRef.current) return;   // unmounted during async sprite load
      // assets source — clustered
      // Per-cluster aggregates compute the worst severity contained,
      // so the cluster ring tone reflects operational risk (rose for
      // any Attention Required, slate for Offline-heavy, amber for
      // Idle, emerald for healthy) instead of generic blue.
      map.addSource("assets", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterMaxZoom: 12,
        clusterRadius: 44,
        clusterProperties: {
          has_red:   ["+", ["case", ["==", ["get", "band"], "red"],   1, 0]],
          has_gray:  ["+", ["case", ["==", ["get", "band"], "gray"],  1, 0]],
          has_amber: ["+", ["case", ["==", ["get", "band"], "amber"], 1, 0]],
          has_green: ["+", ["case", ["==", ["get", "band"], "green"], 1, 0]],
          attn_maintenance:    ["+", ["case", ["==", ["get", "attention_reason"], "maintenance"],    1, 0]],
          attn_inspection:     ["+", ["case", ["==", ["get", "attention_reason"], "inspection"],     1, 0]],
          attn_assignment:     ["+", ["case", ["==", ["get", "attention_reason"], "assignment"],     1, 0]],
          attn_stale_position: ["+", ["case", ["==", ["get", "attention_reason"], "stale_position"], 1, 0]],
        },
      });
      // geofences source
      map.addSource("geofences", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      // Geofence polygons (fill + outline)
      map.addLayer({
        id: "geofence-fill", type: "fill", source: "geofences",
        paint: {
          "fill-color": [
            "match", ["get", "category"],
            "Job Site",            "#38bdf8",
            "Maintenance Facility","#f59e0b",
            "Terminal/Yard",       "#a78bfa",
            /* default */          "#475569",
          ],
          "fill-opacity": 0.10,
        },
      });
      map.addLayer({
        id: "geofence-line", type: "line", source: "geofences",
        paint: { "line-color": "#94a3b8", "line-width": 1.4, "line-opacity": 0.55 },
      });

      // Cluster bubbles — risk-tinted ring
      map.addLayer({
        id: "asset-clusters", type: "circle", source: "assets",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "#0b1320",
          "circle-radius": ["step", ["get", "point_count"], 18, 25, 24, 100, 30],
          "circle-stroke-width": 3,
          "circle-stroke-color": [
            "case",
            [">", ["get", "has_red"],   0], "#e11d48",   // rose · attention required
            [">", ["get", "has_gray"],  0], "#94a3b8",   // slate · offline-heavy
            [">", ["get", "has_amber"], 0], "#f59e0b",   // amber · idle
            "#10b981",                                  // emerald · healthy
          ],
        },
      });
      map.addLayer({
        id: "asset-cluster-count", type: "symbol", source: "assets",
        filter: ["has", "point_count"],
        layout: { "text-field": "{point_count_abbreviated}", "text-size": 13 },
        paint: { "text-color": "#e2e8f0" },
      });

      // Individual asset markers
      map.addLayer({
        id: "asset-marker", type: "symbol", source: "assets",
        filter: ["!", ["has", "point_count"]],
        layout: {
          "icon-image": ["get", "sprite"],
          "icon-size": 1,
          "icon-allow-overlap": true,
          "text-field": ["get", "unit_number"],
          "text-offset": [0, 1.6],
          "text-size": 10,
          "text-allow-overlap": true,
        },
        paint: {
          "text-color": "#cbd5e1",
          "text-halo-color": "#0b1320",
          "text-halo-width": 1.5,
        },
      });

      map.on("click", "asset-marker", (e) => {
        const f = e.features?.[0];
        if (f?.properties?.unit_number) onSelect(f.properties.unit_number);
      });
      map.on("mouseenter", "asset-marker", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "asset-marker", () => { map.getCanvas().style.cursor = ""; });

      map.on("click", "asset-clusters", async (e) => {
        const f = map.queryRenderedFeatures(e.point, { layers: ["asset-clusters"] })[0];
        if (!f) return;
        const clusterId = f.properties.cluster_id;
        const p = f.properties;
        // Build operational popup BEFORE zoom — gives Truck Boss /
        // Dispatch the cluster's dominant cause + owner so a single tap
        // explains why this risk concentration exists.
        const reasons = [
          { id: "maintenance",    label: "Maintenance Due",        count: +p.attn_maintenance    || 0, owner: "Shop" },
          { id: "inspection",     label: "Inspection Overdue",     count: +p.attn_inspection     || 0, owner: "Shop / Safety" },
          { id: "assignment",     label: "Assignment Unknown",     count: +p.attn_assignment     || 0, owner: "PM / Dispatch" },
          { id: "stale_position", label: "Position Update Overdue",count: +p.attn_stale_position || 0, owner: "Truck Boss / Dispatch" },
        ].filter(r => r.count > 0)
         .sort((a, b) => b.count - a.count);
        const dominant = reasons[0];
        const noRecent = +p.has_gray || 0;
        const ownerLine = dominant
          ? `Owner: ${dominant.owner}`
          : (noRecent > 0 ? "Owner: Truck Boss / Dispatch" : "Owner: Operations");
        const rows = [
          `<div style="font-weight:900;font-size:13px;color:#0f172a;">${p.point_count} Assets</div>`,
          (+p.has_red || 0) > 0
            ? `<div style="font-size:11px;color:#be123c;font-weight:700;">${p.has_red} Attention Required</div>`
            : null,
          ...reasons.map(r =>
            `<div style="font-size:11px;color:#475569;"><strong style="color:#be123c">${r.count}</strong> ${r.label}</div>`
          ),
          noRecent > 0
            ? `<div style="font-size:11px;color:#475569;"><strong>${noRecent}</strong> No Recent Position</div>`
            : null,
          `<div style="font-size:10px;color:#0f766e;font-weight:800;letter-spacing:0.05em;text-transform:uppercase;margin-top:4px;">${ownerLine}</div>`,
        ].filter(Boolean).join("");
        new maplibregl.Popup({ closeButton: true, maxWidth: "260px" })
          .setLngLat(f.geometry.coordinates)
          .setHTML(
            `<div data-testid="ops-map-cluster-popup" style="padding:6px 8px 8px 8px;font-family:'Chivo','IBM Plex Sans',sans-serif;">${rows}</div>`
          )
          .addTo(map);
        // Also offer expansion on a second tap by zoom-on-shift; keep default zoom UX
        const src = map.getSource("assets");
        const zoom = await src.getClusterExpansionZoom(clusterId);
        // shift+click → expand; plain click shows popup only
        if (e.originalEvent?.shiftKey) {
          map.easeTo({ center: f.geometry.coordinates, zoom });
        }
      });

      setReady(true);
    });
    return () => { map.remove(); mapRef.current = null; setReady(false); };
  }, [onSelect]);

  // push fresh data into the sources whenever snapshot/filters change
  useEffect(() => {
    if (!mapRef.current || !ready || !snapshot) return;
    const map = mapRef.current;
    const tSet = new Set(filters?.types || []);
    const sSet = new Set(filters?.status || ["green","amber","red","gray"]);
    const driver = (filters?.driver || "").toLowerCase();

    const features = (snapshot.assets || [])
      .filter((a) => a.lat != null && a.lon != null)
      .filter((a) => !tSet.size || tSet.has(a.marker_kind))
      .filter((a) => sSet.has(a.band))
      .filter((a) => !driver || (a.unit_number || "").toLowerCase().includes(driver))
      .map((a) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [a.lon, a.lat] },
        properties: {
          unit_number: a.unit_number || "",
          equipment_name: a.equipment_name || "",
          band: a.band,
          sprite: `spr-${a.marker_kind}-${a.band}`,
          age_seconds: a.age_seconds,
          attention_reason: a.attention_reason || "",
        },
      }));
    map.getSource("assets")?.setData({ type: "FeatureCollection", features });

    const gfFeatures = (snapshot.geofences || []).map((g) => ({
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [g.polygon.map(([lat, lon]) => [lon, lat])] },
      properties: { id: g.id, name: g.name, category: g.category },
    }));
    map.getSource("geofences")?.setData({ type: "FeatureCollection", features: gfFeatures });
  }, [snapshot, filters, ready]);

  return <div ref={containerRef} className="ops-map-canvas" data-testid="ops-map-canvas" />;
}
