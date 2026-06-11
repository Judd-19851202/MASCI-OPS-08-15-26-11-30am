import React from "react";

/* Operations Banner — six-tile operational summary. Tiles are
 * decision-supporting. The Attention Required tile renders an
 * embedded breakdown (Maintenance Due / Inspection Overdue /
 * Assignment Unknown / Position Update Overdue) so operators see
 * WHY assets need attention, not just THAT they do. */
const MICROCOPY = {
  total:     "All tracked equipment",
  assigned:  "In known projects or areas",
  connected: "Sending position data",
  working:   "Moving or active now",
  idle:      "Connected, not moving",
  attention: "Needs review",
  offline:   "Not recently reporting",
};

const FALLBACK = [
  { id: "total",     label: "Total Assets",       tone: "slate"   },
  { id: "assigned",  label: "Assets Assigned",    tone: "slate"   },
  { id: "working",   label: "Working",            tone: "emerald" },
  { id: "idle",      label: "Idle",               tone: "amber"   },
  { id: "attention", label: "Attention Required", tone: "rose"    },
  { id: "offline",   label: "No Recent Position", tone: "slate"   },
];

function fallbackFromCounts(counts = {}) {
  return [
    { id: "total",     label: "Total Assets",       tone: "slate",   value: counts.total ?? 0 },
    { id: "assigned",  label: "Assets Assigned",    tone: "slate",   value: counts.with_gps ?? 0 },
    { id: "working",   label: "Working",            tone: "emerald", value: counts.green ?? 0 },
    { id: "idle",      label: "Idle",               tone: "amber",   value: counts.amber ?? 0 },
    { id: "attention", label: "Attention Required", tone: "rose",    value: counts.red ?? 0 },
    { id: "offline",   label: "No Recent Position", tone: "slate",   value: counts.gray ?? 0 },
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
        const helper = MICROCOPY[t.id] || "";
        const breakdown = Array.isArray(t.breakdown) ? t.breakdown : null;
        return (
          <div key={t.id}
               className={`tile tone-${tone}${t.id === "attention" ? " tile-attention" : ""}`}
               title={helper}
               data-testid={`ops-map-banner-${t.id}`}>
            <span className="k">{t.label}</span>
            <span className="v" data-testid={`ops-map-banner-${t.id}-value`}>
              {t.value ?? 0}
            </span>
            {t.id === "attention" && breakdown && breakdown.length > 0 ? (
              <ul className="ops-map-banner-breakdown"
                  data-testid={`ops-map-banner-${t.id}-breakdown`}>
                {breakdown.slice(0, 4).map((b) => (
                  <li key={b.id}>
                    <span className="bd-count" data-testid={`ops-map-banner-attention-bd-${b.id}`}>
                      {b.count}
                    </span>
                    <span className="bd-label">{b.label}</span>
                    {b.owner && (
                      <span className="bd-owner" data-testid={`ops-map-banner-attention-bd-${b.id}-owner`}>
                        — {b.owner}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <span className="hint" data-testid={`ops-map-banner-${t.id}-hint`}>
                {helper}
              </span>
            )}
          </div>
        );
      })}
    </section>
  );
}
