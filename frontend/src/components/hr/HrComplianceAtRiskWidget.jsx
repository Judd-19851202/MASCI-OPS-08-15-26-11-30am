// Track 19.33 · HR Compliance At Risk widget.
//
// Zero-drift · read-only. Consumes existing endpoint:
//   GET /api/operations/expirations/summary
// (from `backend/routes/sprint_a.py`; role-gated via `require_actor`).
//
// Surfaces employees who may require HR attention before risk becomes an
// incident. Turns HR from reactive to proactive without a schema, route, or
// permission change.
//
// Six-Pillars alignment:
//  • Simple — one glance, three bands (Critical · Warning · Info).
//  • Trusted — no mutation, no side effects, uses live existing data.
//  • Operational — every row deep-links to an existing HR surface.

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card, StatusChip, EmptyState } from "../../design-system";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;

// Severity classifier — pure client-side rendering rule; server-side data is
// unchanged. Critical = expired · Warning = expiring in ≤ 30 · Info = 31–60.
function classify(band) {
  if (band === "expired") return { severity: "Critical", statusKey: "pending_verification" };
  if (band === "in_30") return { severity: "Warning", statusKey: "pending_verification" };
  if (band === "in_60") return { severity: "Info", statusKey: "draft" };
  return { severity: "Info", statusKey: "draft" };
}

function daysUntil(iso) {
  if (!iso) return null;
  const d = new Date(iso.substring(0, 10) + "T00:00:00Z");
  if (Number.isNaN(d.getTime())) return null;
  const diff = Math.floor((d - new Date()) / 86400000);
  return diff;
}

function ownerLink(row) {
  // If the row is employee-scoped, deep-link to Employee 360.
  if (row.owner_id && row.source !== "document_expirations" || (row.owner_id && !row.owner_id.includes("EQ-"))) {
    return `/hr/employees/${encodeURIComponent(row.owner_id)}/profile`;
  }
  return `/document-expirations`;
}

export default function HrComplianceAtRiskWidget({ authHeaders }) {
  const { t } = useT();
  const [state, setState] = useState({ loaded: false, error: null, data: null });

  useEffect(() => {
    let cancelled = false;
    const headers = typeof authHeaders === "function" ? authHeaders() : (authHeaders || {});
    fetch(`${API}/api/operations/expirations/summary`, { headers })
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((body) => { if (!cancelled) setState({ loaded: true, error: null, data: body }); })
      .catch((e) => { if (!cancelled) setState({ loaded: true, error: e.message, data: null }); });
    return () => { cancelled = true; };
  }, [authHeaders]);

  const summary = useMemo(() => {
    const d = state.data || {};
    const counts = d.counts || {};
    const bands = d.bands || {};
    const total = (counts.expired || 0) + (counts.in_30 || 0);
    const rows = [
      ...(bands.expired || []).map((r) => ({ ...r, band: "expired" })),
      ...(bands.in_30 || []).map((r) => ({ ...r, band: "in_30" })),
    ].slice(0, 8);
    return { total, counts, rows };
  }, [state.data]);

  if (!state.loaded) {
    return (
      <Card
        title={t("Compliance At Risk")}
        description={t("Loading live compliance signals…")}
        status={<StatusChip statusKey="draft" compact label={t("Loading")} />}
      />
    );
  }

  if (state.error) {
    return (
      <Card
        title={t("Compliance At Risk")}
        description={t("Unable to load live compliance signals.")}
        status={<StatusChip statusKey="offline_feed" compact />}
      />
    );
  }

  const hasRisk = summary.total > 0 || (summary.rows && summary.rows.length > 0);

  return (
    <div data-testid="hr-compliance-at-risk-widget" style={{ marginBottom: 20 }}>
      <Card
        title={t("Compliance At Risk")}
        description={t("Employees or documents that likely need HR review before risk becomes an incident.")}
        metric={summary.total}
        variant={summary.total > 0 ? "warning" : "default"}
        status={
          summary.total > 0
            ? <StatusChip statusKey="pending_verification" compact label={t("Attention")} />
            : <StatusChip statusKey="verified" compact label={t("All clear")} />
        }
      >
        {!hasRisk ? (
          <EmptyState
            testId="hr-compliance-at-risk-empty"
            title={t("No compliance risk right now.")}
            explanation={t("No expired documents and none expiring in the next 30 days.")}
            severity="good"
          />
        ) : (
          <>
            <div data-testid="hr-compliance-at-risk-summary" style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "8px 0 12px" }}>
              <StatusChip statusKey="pending_verification" compact label={`${t("Expired")}: ${summary.counts.expired || 0}`} />
              <StatusChip statusKey="pending_verification" compact label={`${t("Expiring ≤ 30 days")}: ${summary.counts.in_30 || 0}`} />
              <StatusChip statusKey="draft" compact label={`${t("31–60 days")}: ${summary.counts.in_60 || 0}`} />
            </div>
            <ul data-testid="hr-compliance-at-risk-rows" style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {summary.rows.map((r, idx) => {
                const cls = classify(r.band);
                const days = daysUntil(r.expiration_date);
                const daysText = days === null ? "—" : (days < 0 ? `${Math.abs(days)}d ${t("overdue")}` : `${days}d`);
                const to = ownerLink(r);
                return (
                  <li key={`${r.id}-${idx}`} data-testid={`hr-compliance-at-risk-row-${idx}`}
                      style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
                               padding: "8px 0", borderTop: idx > 0 ? "1px solid var(--border-soft)" : "none",
                               gap: 12 }}>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--ink-strong)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {r.owner_name || r.title || "—"}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>
                        {r.title || r.kind || t("Document")} · {t("Due")}: {r.expiration_date || "—"}
                      </div>
                    </div>
                    <StatusChip statusKey={cls.statusKey} compact label={`${cls.severity} · ${daysText}`} />
                    <Link to={to} data-testid={`hr-compliance-at-risk-open-${idx}`}
                          style={{ fontSize: 11, fontWeight: 600, color: "var(--ink-strong)",
                                   textDecoration: "underline", whiteSpace: "nowrap" }}>
                      {t("Open")}
                    </Link>
                  </li>
                );
              })}
            </ul>
            <div style={{ marginTop: 10, textAlign: "right" }}>
              <Link to="/document-expirations" data-testid="hr-compliance-at-risk-open-all"
                    style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-strong)",
                             textDecoration: "underline" }}>
                {t("Open Document Expirations →")}
              </Link>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
