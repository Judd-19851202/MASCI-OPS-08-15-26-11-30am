import React from "react";

/* Operations Banner — six-tile operational summary that sits above
 * the map canvas. Replaces the inline status legend (which used
 * fleet-tracking vocabulary). Uses platform tone tokens
 * (emerald/amber/rose/slate) for status alignment with the rest of
 * the Operations Center modules.
 */
const TILES = [
  { id: "total",      label: "Total Assets",        tone: "slate"   },
  { id: "reporting",  label: "Reporting",           tone: "slate"   },
  { id: "working",    label: "Working",             tone: "emerald" },
  { id: "idle",       label: "Idle",                tone: "amber"   },
  { id: "attention",  label: "Needs Attention",     tone: "rose"    },
  { id: "offline",    label: "Offline",             tone: "slate"   },
];

export default function MapOperationsBanner({ counts = {} }) {
  // counts shape from /api/operations-map/snapshot:
  //   total, green, amber, red, gray, unmapped, with_gps
  // Re-cast to operational vocabulary:
  const total     = counts.total ?? 0;
  const reporting = counts.with_gps ?? 0;
  const working   = counts.green ?? 0;
  const idle      = counts.amber ?? 0;
  const attention = counts.red ?? 0;
  const offline   = counts.gray ?? 0;

  const values = { total, reporting, working, idle, attention, offline };

  return (
    <section className="ops-map-banner" data-testid="ops-map-banner" aria-label="Operations summary">
      {TILES.map((t) => (
        <div key={t.id}
             className={`tile tone-${t.tone}`}
             data-testid={`ops-map-banner-${t.id}`}>
          <span className="k">{t.label}</span>
          <span className="v" data-testid={`ops-map-banner-${t.id}-value`}>
            {values[t.id]}
          </span>
        </div>
      ))}
    </section>
  );
}
