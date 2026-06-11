import React from "react";

/* Operations Banner — six-tile operational summary that sits above
 * the map canvas. Binds to `operational_summary` from
 * /api/operations-map/snapshot — a backend-authored, MASCI-native
 * vocabulary block (Working / Idle / Needs Attention / Offline /
 * Total / Reporting). Falls back to raw counts only if the new field
 * is missing, so the surface degrades safely during a partial deploy.
 */
const FALLBACK = [
  { id: "total",     label: "Total Assets",    tone: "slate"   },
  { id: "reporting", label: "Reporting",       tone: "slate"   },
  { id: "working",   label: "Working",         tone: "emerald" },
  { id: "idle",      label: "Idle",            tone: "amber"   },
  { id: "attention", label: "Needs Attention", tone: "rose"    },
  { id: "offline",   label: "Offline",         tone: "slate"   },
];

function fallbackFromCounts(counts = {}) {
  return [
    { id: "total",     label: "Total Assets",    tone: "slate",   value: counts.total ?? 0 },
    { id: "reporting", label: "Reporting",       tone: "slate",   value: counts.with_gps ?? 0 },
    { id: "working",   label: "Working",         tone: "emerald", value: counts.green ?? 0 },
    { id: "idle",      label: "Idle",            tone: "amber",   value: counts.amber ?? 0 },
    { id: "attention", label: "Needs Attention", tone: "rose",    value: counts.red ?? 0 },
    { id: "offline",   label: "Offline",         tone: "slate",   value: counts.gray ?? 0 },
  ];
}

export default function MapOperationsBanner({ summary, counts }) {
  const tiles =
    Array.isArray(summary) && summary.length > 0
      ? summary
      : fallbackFromCounts(counts);

  return (
    <section className="ops-map-banner" data-testid="ops-map-banner" aria-label="Operations summary">
      {tiles.map((t) => {
        const tone = t.tone || (FALLBACK.find((f) => f.id === t.id)?.tone) || "slate";
        return (
          <div key={t.id}
               className={`tile tone-${tone}`}
               data-testid={`ops-map-banner-${t.id}`}>
            <span className="k">{t.label}</span>
            <span className="v" data-testid={`ops-map-banner-${t.id}-value`}>
              {t.value ?? 0}
            </span>
          </div>
        );
      })}
    </section>
  );
}
