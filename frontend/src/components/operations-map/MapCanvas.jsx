import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// Track 13.4A · co-locate the `.ops-map-canvas` CSS with the
// component that owns the class so styling travels with the
// component whenever it's re-used (e.g. DispatchMapHero) and
// doesn't depend on the parent page importing OperationsMap.css.
import "./OperationsMap.css";
import { spriteUrl, KIND_LIST } from "@/lib/operations-map/icons";

/* MapCanvas — Track 15.63 hardened
 * ----------------------------------
 * Renders the MapLibre WebGL canvas with two GeoJSON sources:
 *   - assets (clustered)
 *   - geofences (polygon fill + outline)
 *
 * Props:
 *   snapshot: { assets:[], geofences:[], counts:{} }
 *   filters:  { types:[], status:[], driver, project }
 *   onSelect: fn(unit_number) — invoked when a marker is clicked
 *
 * Stability contract (Track 15.63):
 *   - The MapLibre instance is constructed ONCE per mount. It is NOT
 *     re-created when `snapshot`, `filters`, or `onSelect` change
 *     identity. Polling refreshes (15-s tick) push new GeoJSON into
 *     the existing sources via `setData` — viewport (zoom, center,
 *     pitch, bearing) is preserved by definition because the same map
 *     instance keeps owning the camera.
 *   - `onSelect` is read through a ref so caller-side inline arrow
 *     functions don't trigger any re-creation of event handlers.
 *   - Filter changes are dispatched through `setData` only when the
 *     filtered feature signature actually changes, so reference-only
 *     re-renders are absorbed without DOM churn.
 */
const TILE_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      // CARTO dark basemap — free, no API key, CORS-friendly, CDN-backed.
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
      ],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors © CARTO",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

const DEFAULT_CENTER = [-81.0, 28.9]; // East-central Florida (MASCI service area)
const DEFAULT_ZOOM = 8;
const ALL_BANDS = ["green", "amber", "red", "gray"];

const FALLBACK_MARKER_TONE = {
  green: { ring: "#10b981", fill: "#064e3b", text: "#d1fae5" },
  amber: { ring: "#f59e0b", fill: "#78350f", text: "#fef3c7" },
  red: { ring: "#e11d48", fill: "#4c0519", text: "#ffe4e6" },
  gray: { ring: "#94a3b8", fill: "#334155", text: "#e2e8f0" },
};

export default function MapCanvas({ snapshot, filters, onSelect }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  // Stable callback ref so caller-side inline `onSelect` arrows do NOT
  // tear down and re-create the map (Track 15.63 root cause #1).
  const onSelectRef = useRef(onSelect);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  // Last-applied GeoJSON signatures — used to skip setData calls when
  // the rendered feature set hasn't actually changed (Track 15.63 #3).
  const lastAssetsSigRef = useRef("");
  const lastGeofencesSigRef = useRef("");
  const fallbackMarkersRef = useRef([]);
  const renderProbeRef = useRef(null);

  const [ready, setReady] = useState(false);

  const clearFallbackMarkers = () => {
    fallbackMarkersRef.current.forEach((marker) => {
      try { marker.remove(); } catch { /* ignore */ }
    });
    fallbackMarkersRef.current = [];
  };

  const renderFallbackMarkers = (map, features) => {
    clearFallbackMarkers();
    features.slice(0, 200).forEach((feature) => {
      const tone = FALLBACK_MARKER_TONE[feature.properties.band] || FALLBACK_MARKER_TONE.gray;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "ops-map-fallback-marker";
      button.dataset.testid = `ops-map-fallback-${feature.properties.unit_number || "asset"}`;
      button.title = `${feature.properties.unit_number || "Asset"} · ${feature.properties.band || "unknown"}`;
      button.style.width = "18px";
      button.style.height = "18px";
      button.style.borderRadius = "999px";
      button.style.border = `3px solid ${tone.ring}`;
      button.style.background = tone.fill;
      button.style.boxShadow = "0 0 0 1px rgba(15,23,42,0.65), 0 3px 10px rgba(15,23,42,0.28)";
      button.style.cursor = "pointer";
      button.style.padding = "0";
      button.style.display = "grid";
      button.style.placeItems = "center";
      button.setAttribute("aria-label", button.title);
      const centerDot = document.createElement("span");
      centerDot.style.width = "4px";
      centerDot.style.height = "4px";
      centerDot.style.borderRadius = "999px";
      centerDot.style.background = tone.text;
      button.appendChild(centerDot);
      button.addEventListener("click", () => {
        const cb = onSelectRef.current;
        if (feature.properties.unit_number && typeof cb === "function") cb(feature.properties.unit_number);
      });
      const marker = new maplibregl.Marker({ element: button, anchor: "center" })
        .setLngLat(feature.geometry.coordinates)
        .addTo(map);
      fallbackMarkersRef.current.push(marker);
    });
  };

  // ---------------------------------------------------------------------
  // Map instance — created ONCE per mount. No prop-driven re-creation.
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: TILE_STYLE,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      attributionControl: true,
      // Track 13.4A · keep WebGL drawing buffer so Playwright / browser
      // screenshots actually capture the rendered map tiles.
      preserveDrawingBuffer: true,
    });
    mapRef.current = map;

    // Optional e2e hook — exposes the map ref to a well-known window slot
    // so the Track 15.63 reproduction harness can probe zoom/center without
    // changing public behaviour. No-op in production unless something reads
    // these globals.
    try {
      if (typeof window !== "undefined") {
        // 1. Stable list of all live MapLibre instances on the page.
        if (!Array.isArray(window.__MASCI_MAP_REFS__)) window.__MASCI_MAP_REFS__ = [];
        window.__MASCI_MAP_REFS__.push(map);
        // 2. Latest-map convenience pointer.
        window.__MASCI_MAP_REF__ = map;
        // 3. Mount counter — increments on every fresh MapLibre Map construction
        //    (so a re-mount of MapCanvas is detectable).
        window.__MASCI_MAP_MOUNT_COUNT__ = (window.__MASCI_MAP_MOUNT_COUNT__ || 0) + 1;
        // 4. Optional legacy hook (kept for back-compat with prior harness).
        if (typeof window.__MASCI_REGISTER_MAP__ === "function") {
          window.__MASCI_REGISTER_MAP__(map);
        }
      }
    } catch { /* ignore */ }

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");

    map.on("load", async () => {
      // Pre-load sprite icons (one per kind × band combo)
      for (const kind of KIND_LIST) {
        for (const band of ALL_BANDS) {
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

      // assets source — clustered. Per-cluster aggregates compute the worst
      // severity contained, so the cluster ring tone reflects operational
      // risk (rose for any Attention Required, slate for Offline-heavy,
      // amber for Idle, emerald for healthy).
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
            [">", ["get", "has_red"],   0], "#e11d48",
            [">", ["get", "has_gray"],  0], "#94a3b8",
            [">", ["get", "has_amber"], 0], "#f59e0b",
            "#10b981",
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

      // Marker click — route through the ref so caller-side inline arrows
      // don't tear down the listener on every render. Stop event bubbling
      // so the click does not also trigger map-level handlers (which would
      // briefly recenter the camera and cause the visible "jump"). See
      // Track 15.63 root cause #4.
      map.on("click", "asset-marker", (e) => {
        try { if (e.originalEvent) { e.originalEvent.stopPropagation(); } } catch { /* ignore */ }
        const f = e.features && e.features[0];
        const unit = f && f.properties && f.properties.unit_number;
        const cb = onSelectRef.current;
        if (unit && typeof cb === "function") cb(unit);
      });
      map.on("mouseenter", "asset-marker", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "asset-marker", () => { map.getCanvas().style.cursor = ""; });

      map.on("click", "asset-clusters", async (e) => {
        try { if (e.originalEvent) { e.originalEvent.stopPropagation(); } } catch { /* ignore */ }
        const f = map.queryRenderedFeatures(e.point, { layers: ["asset-clusters"] })[0];
        if (!f) return;
        const clusterId = f.properties.cluster_id;
        const p = f.properties;
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
        const src = map.getSource("assets");
        const zoom = await src.getClusterExpansionZoom(clusterId);
        if (e.originalEvent && e.originalEvent.shiftKey) {
          map.easeTo({ center: f.geometry.coordinates, zoom });
        }
      });

      map.on("mouseenter", "asset-clusters", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "asset-clusters", () => { map.getCanvas().style.cursor = ""; });

      setReady(true);
    });

    return () => {
      if (renderProbeRef.current) {
        clearTimeout(renderProbeRef.current);
        renderProbeRef.current = null;
      }
      clearFallbackMarkers();
      try {
        if (typeof window !== "undefined") {
          if (Array.isArray(window.__MASCI_MAP_REFS__)) {
            const idx = window.__MASCI_MAP_REFS__.indexOf(map);
            if (idx >= 0) window.__MASCI_MAP_REFS__.splice(idx, 1);
          }
          if (window.__MASCI_MAP_REF__ === map) {
            window.__MASCI_MAP_REF__ = (window.__MASCI_MAP_REFS__ || []).slice(-1)[0] || null;
          }
          window.__MASCI_MAP_DISPOSE_COUNT__ = (window.__MASCI_MAP_DISPOSE_COUNT__ || 0) + 1;
        }
      } catch { /* ignore */ }
      try { map.remove(); } catch { /* ignore */ }
      mapRef.current = null;
      setReady(false);
    };
    // Intentionally empty deps — map instance is mount-stable.
  }, []);

  // ---------------------------------------------------------------------
  // Snapshot + filter dispatch.
  //
  // This effect runs whenever the snapshot, filters, or `ready` flag
  // changes IDENTITY, but it only writes to MapLibre when the resulting
  // feature signature actually changes — so reference-only re-renders
  // are silently absorbed and never disturb the viewport.
  // ---------------------------------------------------------------------
  useEffect(() => {
    if (!mapRef.current || !ready || !snapshot) return;
    const map = mapRef.current;
    const tSet = new Set(filters?.types || []);
    // Empty status array == "all bands" (matches the `types` filter semantics).
    const sSet = new Set(filters?.status?.length ? filters.status : ALL_BANDS);
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

    // Cheap structural signature — avoids JSON.stringify on the full
    // collection when nothing meaningful changed.
    const assetsSig = features
      .map((f) => `${f.properties.unit_number}|${f.geometry.coordinates[0].toFixed(5)}|${f.geometry.coordinates[1].toFixed(5)}|${f.properties.band}|${f.properties.attention_reason}`)
      .join(";");
    if (assetsSig !== lastAssetsSigRef.current) {
      map.getSource("assets")?.setData({ type: "FeatureCollection", features });
      lastAssetsSigRef.current = assetsSig;
    }

    if (renderProbeRef.current) {
      clearTimeout(renderProbeRef.current);
      renderProbeRef.current = null;
    }
    renderProbeRef.current = window.setTimeout(() => {
      if (!mapRef.current) return;
      const activeMap = mapRef.current;
      const countRendered = () => {
        try {
          return activeMap.queryRenderedFeatures(undefined, {
            layers: ["asset-clusters", "asset-marker"],
          }).length;
        } catch {
          return 0;
        }
      };
      const firstPass = countRendered();
      if (features.length > 0 && firstPass === 0) {
        try { activeMap.resize(); } catch { /* ignore */ }
        try { activeMap.getSource("assets")?.setData({ type: "FeatureCollection", features }); } catch { /* ignore */ }
        try { activeMap.triggerRepaint(); } catch { /* ignore */ }
        window.setTimeout(() => {
          if (!mapRef.current) return;
          const secondPass = countRendered();
          if (features.length > 0 && secondPass === 0) {
            renderFallbackMarkers(activeMap, features);
          } else {
            clearFallbackMarkers();
          }
        }, 350);
      } else {
        clearFallbackMarkers();
      }
    }, 150);

    const gfFeatures = (snapshot.geofences || []).map((g) => ({
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [g.polygon.map(([lat, lon]) => [lon, lat])] },
      properties: { id: g.id, name: g.name, category: g.category },
    }));
    const gfSig = gfFeatures
      .map((f) => `${f.properties.id}|${f.properties.category}|${f.geometry.coordinates[0].length}`)
      .join(";");
    if (gfSig !== lastGeofencesSigRef.current) {
      map.getSource("geofences")?.setData({ type: "FeatureCollection", features: gfFeatures });
      lastGeofencesSigRef.current = gfSig;
    }
  }, [snapshot, filters, ready]);

  return <div ref={containerRef} className="ops-map-canvas" data-testid="ops-map-canvas" />;
}
