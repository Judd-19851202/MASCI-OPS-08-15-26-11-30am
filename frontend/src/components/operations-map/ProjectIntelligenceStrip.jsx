import React from "react";

/* Project Intelligence Strip — sits between Operations Banner and the
 * map canvas. Renders a horizontally-scrollable row of project /
 * geofence / yard / unassigned rollup cards. Backend computes the
 * rollups in /api/operations-map/snapshot.project_rollups. */
function fmtAge(iso) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 60_000)   return `${Math.round(ms/1000)}s ago`;
  if (ms < 3600_000) return `${Math.round(ms/60_000)}m ago`;
  if (ms < 86400_000)return `${Math.round(ms/3600_000)}h ago`;
  return `${Math.round(ms/86400_000)}d ago`;
}

function toneFor(r) {
  if ((r.needs_attention ?? 0) > 0) return "rose";
  if ((r.offline ?? 0) > r.reporting) return "slate";
  if (r.reporting > 0) return "emerald";
  return "slate";
}

export default function ProjectIntelligenceStrip({ rollups = [] }) {
  return (
    <section className="ops-map-projects" data-testid="ops-map-projects-strip"
             style={{ gridColumn: "1 / 3", background: "#ffffff",
                      borderBottom: "1px solid #e2e8f0",
                      padding: "10px 16px", overflowX: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontFamily: "Chivo, IBM Plex Sans, sans-serif",
                       fontWeight: 900, fontSize: 11, color: "#0f172a",
                       letterSpacing: "0.08em", textTransform: "uppercase",
                       whiteSpace: "nowrap" }}>
          Project Intelligence
        </span>
        <div style={{ display: "flex", gap: 8, flex: 1 }}>
          {rollups.length === 0 && (
            <div data-testid="ops-map-projects-empty"
                 style={{ color: "#94a3b8", fontSize: 13, padding: "8px 0" }}>
              No projects assigned · waiting for geofence data
            </div>
          )}
          {rollups.map((r, i) => {
            const tone = toneFor(r);
            const toneBg  = { rose: "#fff1f2", emerald: "#ecfdf5", slate: "#f8fafc" }[tone];
            const toneBd  = { rose: "#fecdd3", emerald: "#a7f3d0", slate: "#e2e8f0" }[tone];
            const accent  = { rose: "#be123c", emerald: "#047857", slate: "#475569" }[tone];
            return (
              <div key={i} data-testid={`ops-map-project-card-${i}`}
                   style={{ minWidth: 180, background: toneBg, border: `1px solid ${toneBd}`,
                            borderRadius: 10, padding: "8px 12px" }}>
                <div style={{ fontFamily: "Chivo, IBM Plex Sans, sans-serif",
                              fontWeight: 900, fontSize: 13, color: "#0f172a",
                              overflow: "hidden", textOverflow: "ellipsis",
                              whiteSpace: "nowrap", marginBottom: 4 }}>
                  {r.name}
                </div>
                <div style={{ fontSize: 11, color: accent, lineHeight: 1.5 }}>
                  <strong>{r.total}</strong> Assets ·{" "}
                  <strong>{r.reporting}</strong> Reporting
                  {r.needs_attention > 0 && <> · <strong>{r.needs_attention}</strong> Attention</>}
                  {r.offline > 0 && <> · <strong>{r.offline}</strong> Offline</>}
                </div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
                  Last activity {fmtAge(r.last_activity_at)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
