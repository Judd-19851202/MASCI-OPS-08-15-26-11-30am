import React from "react";

/* Project Intelligence Strip — ranked operational buckets.
 * Backend pre-ranks the rollups (Attention Required desc → Offline
 * desc → Total desc → recency). We render the top 5 + an overflow
 * indicator. Each card shows operational counts plus the assignment
 * source + confidence so the operator can grade the rollup at a
 * glance. Cards are tall enough to read on iPad landscape (~12 ft
 * sight-line at command-center desk). */
function fmtAge(iso) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 60_000)   return `${Math.round(ms/1000)}s ago`;
  if (ms < 3600_000) return `${Math.round(ms/60_000)}m ago`;
  if (ms < 86400_000)return `${Math.round(ms/3600_000)}h ago`;
  return `${Math.round(ms/86400_000)}d ago`;
}

function toneFor(r) {
  if ((r.attention_required_count ?? r.needs_attention ?? 0) > 0) return "rose";
  if ((r.offline_count ?? r.offline ?? 0) > (r.connected_count ?? r.reporting ?? 0)) return "slate";
  if ((r.connected_count ?? r.reporting ?? 0) > 0) return "emerald";
  return "slate";
}

const SOURCE_LABEL = {
  explicit_project:    { label: "Explicit Project",    short: "Project" },
  geofence_membership: { label: "Geofence Membership", short: "Geofence" },
  gps_location:        { label: "GPS Location",        short: "Location" },
  missing_assignment:  { label: "Missing Assignment",  short: "Unassigned" },
  unknown:             { label: "Unknown",             short: "Unknown" },
};

const CONFIDENCE_TONE = {
  high:   { bg: "#ecfdf5", color: "#047857", label: "High Confidence" },
  medium: { bg: "#eff6ff", color: "#1d4ed8", label: "Medium Confidence" },
  low:    { bg: "#f1f5f9", color: "#64748b", label: "Low Confidence" },
};

export default function ProjectIntelligenceStrip({ rollups = [], overflow = 0, total = 0 }) {
  const visible = rollups || [];

  return (
    <section className="ops-map-projects" data-testid="ops-map-projects-strip">
      <div className="ops-map-projects-header">
        <span className="ops-map-projects-title">Project Intelligence</span>
        <span className="ops-map-projects-meta" data-testid="ops-map-projects-total">
          {total > 0 ? `${total} operational bucket${total === 1 ? "" : "s"}` : "no buckets yet"}
        </span>
      </div>

      <div className="ops-map-projects-rail">
        {visible.length === 0 && (
          <div data-testid="ops-map-projects-empty" className="ops-map-projects-empty">
            No operational buckets yet · waiting for telemetry
          </div>
        )}

        {visible.map((r, i) => {
          const tone = toneFor(r);
          const src  = SOURCE_LABEL[r.assignment_source || r.source || "unknown"] || SOURCE_LABEL.unknown;
          const conf = CONFIDENCE_TONE[r.assignment_confidence || r.confidence || "low"] || CONFIDENCE_TONE.low;
          const connected = r.connected_count ?? r.reporting ?? 0;
          const attention = r.attention_required_count ?? r.needs_attention ?? 0;
          const offline   = r.offline_count ?? r.offline ?? 0;

          return (
            <div key={i}
                 className={`ops-map-project-card tone-${tone}`}
                 data-testid={`ops-map-project-card-${i}`}>
              <div className="ops-map-project-card-name" data-testid={`ops-map-project-card-${i}-name`}>
                {r.display_name || r.name}
              </div>
              <div className="ops-map-project-card-primary">
                <span className="num">{r.total}</span>
                <span className="lbl">Assets</span>
              </div>
              <div className="ops-map-project-card-secondary">
                <span className="chip chip-conn"   data-testid={`ops-map-project-card-${i}-connected`}>
                  <strong>{connected}</strong> Connected
                </span>
                {attention > 0 && (
                  <span className="chip chip-attn" data-testid={`ops-map-project-card-${i}-attention`}>
                    <strong>{attention}</strong> Attention Required
                  </span>
                )}
                {offline > 0 && (
                  <span className="chip chip-off"  data-testid={`ops-map-project-card-${i}-offline`}>
                    <strong>{offline}</strong> Offline
                  </span>
                )}
              </div>
              <div className="ops-map-project-card-foot">
                <span className="last">Last activity {fmtAge(r.last_activity_at)}</span>
                <span className="src" data-testid={`ops-map-project-card-${i}-source`}
                      style={{ background: conf.bg, color: conf.color }}>
                  {src.short} · {conf.label}
                </span>
              </div>
            </div>
          );
        })}

        {overflow > 0 && (
          <div className="ops-map-project-overflow"
               data-testid="ops-map-projects-overflow">
            <span className="ops-map-project-overflow-num">+{overflow}</span>
            <span className="ops-map-project-overflow-lbl">more bucket{overflow === 1 ? "" : "s"}</span>
          </div>
        )}
      </div>
    </section>
  );
}
