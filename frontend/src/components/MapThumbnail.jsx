import React from "react";

/**
 * MapThumbnail — keyless OpenStreetMap tile preview for printed PDFs.
 *
 * Renders a 3x2 grid of OSM raster tiles centered on the supplied lat/lng,
 * with a red MASCI marker overlaid at the precise sub-tile pixel offset.
 * Only renders if both lat & lng are valid numbers.
 *
 *   <MapThumbnail lat={29.13} lng={-80.99} />
 *
 * Default zoom 16 ≈ street level. The whole block is wrapped in a
 * `print:block` print-only container by default so the screen view stays
 * compact, but pass `screen` to also show on screen.
 */

const TILE_PX = 256;
const COLS = 3;
const ROWS = 2;

const lngToTileX = (lng, z) => ((lng + 180) / 360) * 2 ** z;
const latToTileY = (lat, z) => {
  const r = (lat * Math.PI) / 180;
  return ((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * 2 ** z;
};

export function MapThumbnail({
  lat,
  lng,
  zoom = 16,
  screen = false,
  className = "",
}) {
  const numLat = Number(lat);
  const numLng = Number(lng);
  if (!isFinite(numLat) || !isFinite(numLng)) return null;

  const tx = lngToTileX(numLng, zoom);
  const ty = latToTileY(numLat, zoom);

  // Anchor: top-left tile of the COLS×ROWS grid so the marker sits roughly
  // in the visual center.
  const x0 = Math.floor(tx) - Math.floor(COLS / 2);
  const y0 = Math.floor(ty) - Math.floor(ROWS / 2);

  // Marker pixel offset within the grid.
  const markerX = (tx - x0) * TILE_PX;
  const markerY = (ty - y0) * TILE_PX;

  const tiles = [];
  for (let row = 0; row < ROWS; row++) {
    for (let col = 0; col < COLS; col++) {
      tiles.push({
        x: x0 + col,
        y: y0 + row,
        left: col * TILE_PX,
        top: row * TILE_PX,
      });
    }
  }

  const wrapperCls = screen
    ? "block"
    : "hidden print:block";

  return (
    <div
      className={`${wrapperCls} ${className}`}
      data-testid="map-thumbnail"
    >
      <div
        className="relative overflow-hidden border-2 border-slate-300 rounded"
        style={{
          width: COLS * TILE_PX,
          height: ROWS * TILE_PX,
          maxWidth: "100%",
        }}
      >
        {tiles.map((t) => (
          <img
            key={`${t.x}-${t.y}`}
            src={`https://tile.openstreetmap.org/${zoom}/${t.x}/${t.y}.png`}
            alt=""
            width={TILE_PX}
            height={TILE_PX}
            crossOrigin="anonymous"
            style={{
              position: "absolute",
              left: t.left,
              top: t.top,
              userSelect: "none",
              pointerEvents: "none",
            }}
          />
        ))}
        {/* Marker (MASCI red pin) */}
        <svg
          width="28"
          height="36"
          viewBox="0 0 28 36"
          style={{
            position: "absolute",
            left: markerX - 14,
            top: markerY - 32,
            filter: "drop-shadow(0 1px 2px rgba(0,0,0,0.5))",
            pointerEvents: "none",
          }}
        >
          <path
            d="M14 0C6.27 0 0 6.27 0 14c0 9.5 14 22 14 22s14-12.5 14-22c0-7.73-6.27-14-14-14z"
            fill="#C8102E"
            stroke="#000"
            strokeWidth="1.5"
          />
          <circle cx="14" cy="14" r="5" fill="#fff" />
        </svg>
      </div>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
        OpenStreetMap · {numLat.toFixed(5)}, {numLng.toFixed(5)} · zoom {zoom}
      </div>
    </div>
  );
}

export default MapThumbnail;
