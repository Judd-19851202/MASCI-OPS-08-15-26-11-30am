import React from "react";

/* Project Intelligence Strip — ranked operational areas.
 *
 * Card hierarchy:
 *   • Card 0 (top-ranked) carries the `primary` flag → larger title,
 *     thicker severity wedge, and a one-line "PRIMARY ATTENTION AREA"
 *     pill (only when its severity is rose). Operators see the worst
 *     area before reading anything else.
 *   • Cards 1-4 keep the severity tint but render smaller / quieter.
 *   • Healthy cards stay subdued so they never compete with risk.
 *
 * Confidence badge — high=emerald, medium=amber, low=rose, unknown=slate.
 * Source label — short operator-language (Project / Geofence / GPS Location
 * / Unassigned / Unknown).
 */
function fmtAge(iso) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 60_000)    return `${Math.round(ms/1000)}s ago`;
  if (ms < 3600_000)  return `${Math.round(ms/60_000)}m ago`;
  if (ms < 86400_000) return `${Math.round(ms/3600_000)}h ago`;
  return `${Math.round(ms/86400_000)}d ago`;
}

function severityTone(r) {
  const attn = r.attention_required_count ?? r.needs_attention ?? 0;
  const off  = r.offline_count ?? r.offline ?? 0;
  const conn = r.connected_count ?? r.reporting ?? 0;
  const tot  = r.total ?? 0;
  if ((r.bucket_type || "") === "unassigned" && tot > 0) return "slate";
  if (attn > 0) return "rose";
  if (conn === 0 && off > 0) return "slate";
  if (conn > 0 && off === 0 && attn === 0) return "emerald";
  return "amber";
}

const SOURCE_SHORT = {
  explicit_project:    "Project",
  geofence_membership: "Geofence",
  gps_location:        "GPS Location",
  missing_assignment:  "Unassigned",
  unknown:             "Unknown",
};

function ConfidenceBadge({ level }) {
  const tone = level === "high"   ? "emerald"
             : level === "medium" ? "amber"
             : level === "low"    ? "rose"
             : "slate";
  const label = level === "high"   ? "High Confidence"
              : level === "medium" ? "Medium Confidence"
              : level === "low"    ? "Low Confidence"
              : "Unknown Confidence";
  return (
    <span className={`ops-conf-badge ops-conf-${tone}`} data-testid="ops-conf-badge">
      {label}
    </span>
  );
}

export default function ProjectIntelligenceStrip({ rollups = [], overflow = 0, total = 0 }) {
  const visible = rollups || [];

  const subtitle =
    visible.length === 0
      ? "Waiting for telemetry"
      : total <= 1
        ? "Top area"
        : "Top areas needing attention";

  return (
    <section className="ops-map-projects" data-testid="ops-map-projects-strip">
      <div className="ops-map-projects-header">
        <span className="ops-map-projects-title">Project Intelligence</span>
        <span className="ops-map-projects-meta" data-testid="ops-map-projects-meta">
          {subtitle}
        </span>
      </div>

      <div className="ops-map-projects-rail">
        {visible.length === 0 && (
          <div data-testid="ops-map-projects-empty" className="ops-map-projects-empty">
            No active areas yet · waiting for telemetry
          </div>
        )}

        {visible.map((r, i) => {
          const tone = severityTone(r);
          const isPrimary = i === 0 && tone === "rose";
          const src  = SOURCE_SHORT[r.assignment_source || r.source || "unknown"] || "Unknown";
          const level = r.assignment_confidence || r.confidence || "low";
          const connected = r.connected_count ?? r.reporting ?? 0;
          const attention = r.attention_required_count ?? r.needs_attention ?? 0;
          const offline   = r.offline_count ?? r.offline ?? 0;
          const isUnassigned = (r.bucket_type || "") === "unassigned";

          return (
            <div key={i}
                 className={`ops-map-project-card tone-${tone}${isPrimary ? " primary" : ""}`}
                 data-testid={`ops-map-project-card-${i}`}>
              {isPrimary && (
                <div className="ops-map-project-card-pill"
                     data-testid={`ops-map-project-card-${i}-primary-pill`}>
                  Primary Attention Area
                </div>
              )}

              {/* Line 1 · NAME — dominant */}
              <div className="ops-map-project-card-name"
                   data-testid={`ops-map-project-card-${i}-name`}>
                {(r.display_name || r.name || "").toUpperCase()}
              </div>

              {/* Line 2 · asset count — secondary */}
              <div className="ops-map-project-card-assets">
                <span className="num">{r.total}</span>
                <span className="lbl">Assets</span>
              </div>

              {/* Line 3 · breakdown */}
              <div className="ops-map-project-card-breakdown">
                {isUnassigned && attention === 0 && offline === r.total ? (
                  <span className="kw kw-attn" data-testid={`ops-map-project-card-${i}-cleanup`}>
                    Needs Cleanup
                  </span>
                ) : (
                  <>
                    <span data-testid={`ops-map-project-card-${i}-connected`}>
                      <strong>{connected}</strong> Connected
                    </span>
                    <span className="sep">·</span>
                    <span className="kw kw-attn" data-testid={`ops-map-project-card-${i}-attention`}>
                      <strong>{attention}</strong> Attention
                    </span>
                    <span className="sep">·</span>
                    <span className="kw kw-off" data-testid={`ops-map-project-card-${i}-offline`}>
                      <strong>{offline}</strong> Offline
                    </span>
                  </>
                )}
              </div>

              {/* Line 3b · WHY — top 3 attention reasons (real data) */}
              {Array.isArray(r.attention_breakdown) && r.attention_breakdown.length > 0 && (
                <div className="ops-map-project-card-reasons"
                     data-testid={`ops-map-project-card-${i}-reasons`}>
                  {r.attention_breakdown.slice(0, 3).map((b) => (
                    <span key={b.id} className="reason-row">
                      <strong>{b.count}</strong> {b.label}
                    </span>
                  ))}
                </div>
              )}

              {/* Line 3c · NEXT — operational next-action + owner */}
              {r.next_action && (
                <div className="ops-map-project-card-next"
                     data-testid={`ops-map-project-card-${i}-next`}>
                  <span className="next-prefix">Next:</span>{" "}
                  <span className="next-text">{r.next_action}</span>
                  {r.dominant_owner && (
                    <div className="ops-map-project-card-owner"
                         data-testid={`ops-map-project-card-${i}-owner`}>
                      Owner: {r.dominant_owner}
                    </div>
                  )}
                </div>
              )}

              {/* Line 4 · recency */}
              <div className="ops-map-project-card-last">
                Last activity {fmtAge(r.last_activity_at)}
              </div>

              {/* Line 5 · source + confidence */}
              <div className="ops-map-project-card-source"
                   data-testid={`ops-map-project-card-${i}-source`}>
                <span className="src-label">{src}</span>
                <ConfidenceBadge level={level} />
              </div>
            </div>
          );
        })}

        {overflow > 0 && (
          <div className="ops-map-project-overflow"
               data-testid="ops-map-projects-overflow">
            <span className="ops-map-project-overflow-num">+{overflow}</span>
            <span className="ops-map-project-overflow-lbl">
              more {overflow === 1 ? "area" : "areas"}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}
