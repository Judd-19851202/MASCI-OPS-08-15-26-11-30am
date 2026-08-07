// Track 13.30 — Service Truck Daily Reconciliation · detail.
// Route: /shop/service-truck-reconciliation/:recId (RequireShop).
// Endpoint: GET /api/shop/service-truck-reconciliation/{id}
//           POST /api/shop/service-truck-reconciliation/{id}/review
import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
import { formatEmployeeIdentity } from "@/lib/identity";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
import { sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  return {
    "Content-Type": "application/json",
    ...buildScopedPortalAuthHeaders(["admin", "shop", "dispatch", "safety"]),
  };
}
function StatusChip({ status }) {
  const map = {
    green:      { bg: "#d4edda", fg: "#155724", label: "Within expected range" },
    yellow:     { bg: "#fff3cd", fg: "#856404", label: "Needs review" },
    red:        { bg: "#f8d7da", fg: "#721c24", label: "Significant variance" },
    incomplete: { bg: "#e2e3e5", fg: "#383d41", label: "Incomplete" },
  };
  const s = map[status] || { bg: "#eee", fg: "#222", label: status || "—" };
  return (
    <span data-testid={`strr-detail-chip-${status || "unknown"}`}
          style={{ padding: "2px 8px", borderRadius: 3, background: s.bg, color: s.fg, fontSize: 11, fontWeight: 700 }}>
      {s.label.toUpperCase()}
    </span>
  );
}

export default function ServiceTruckReconciliationDetail() {
  const { recId } = useParams();
  const [doc, setDoc] = useState(null);
  const [visits, setVisits] = useState([]);
  const [error, setError] = useState("");
  const [reviewerName, setReviewerName] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const r = await fetch(`${API}/api/shop/service-truck-reconciliation/${encodeURIComponent(recId)}`, { headers: authHeaders() });
      const body = await r.json().catch(() => null);
      if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
      setDoc(body.reconciliation);
      setVisits(body.linked_visits || []);
    } catch (e) { setError(e.message || "Failed to load."); }
  }, [recId]);

  useEffect(() => { load(); }, [load]);

  async function submitReview() {
    setReviewError("");
    if (reviewNotes.trim().length < 10 || !reviewerName.trim()) {
      setReviewError("Reviewer name and ≥10-character notes required."); return;
    }
    setReviewSubmitting(true);
    try {
      const r = await fetch(`${API}/api/shop/service-truck-reconciliation/${encodeURIComponent(recId)}/review`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ review_notes: reviewNotes.trim(), reviewer_name: reviewerName.trim() }),
      });
      const body = await r.json().catch(() => null);
      if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
      await load();
      setReviewNotes(""); setReviewerName("");
    } catch (e) { setReviewError(e.message || "Review failed."); }
    setReviewSubmitting(false);
  }

  const rows = (doc && doc.variance && doc.variance.rows) || [];

  return (
    <div data-testid="strr-detail-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Shop Portal · Service Truck Reconciliation"
        pageTitle={`Reconciliation ${recId}`}
        subtitle="Starting product, dispensed product, end-of-day check, and linked fuel/lube visits."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="strr-detail-back-to-shop" />
            <Link to="/shop/service-truck-reconciliation" data-testid="strr-detail-back"
                  style={{ padding: "6px 12px", fontSize: 12, background: "#eee", color: "#222", textDecoration: "none", borderRadius: 4 }}>← Records</Link>
            <button data-testid="strr-detail-print" type="button" onClick={() => window.print()} style={{ padding: "6px 12px", fontSize: 12 }}>Print</button>
          </div>
        }
      >
        {error && (
          <div data-testid="strr-detail-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, color: "#a33", fontSize: 12, marginBottom: 12 }}>
            Service truck reconciliation unavailable right now. · {error}
          </div>
        )}
        {!doc && !error && (<div data-testid="strr-detail-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>)}

        {doc && (
          <>
            <Card data-testid="strr-detail-header">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8, fontSize: 12 }}>
                <div>Daily check #: <strong>{doc.doc_id || doc.id || "—"}</strong></div>
                <div>Date: <strong>{doc.date}</strong></div>
                <div>Truck: <strong>{doc.service_truck_unit}</strong></div>
                <div>Tech: <strong>{sanitizeOperatorReference(doc.tech_name, "Tech record")}</strong>{doc.tech_id ? ` (${doc.tech_id})` : ""}</div>
                <div>Status: <strong data-testid="strr-detail-status">{doc.status}</strong></div>
                <div>Variance status: <StatusChip status={doc.variance_status} /></div>
                <div>Visits linked: <strong data-testid="strr-detail-visit-count">{doc.dispensed_quantities?.visit_count ?? 0}</strong></div>
                <div>Start submitted: <strong>{doc.start_submitted_at ? formatPlatformTime(doc.start_submitted_at) : "—"}</strong></div>
                <div>End submitted: <strong>{doc.end_submitted_at ? formatPlatformTime(doc.end_submitted_at) : "—"}</strong></div>
                <div>Reviewed by: <strong>{sanitizeOperatorReference(doc.reviewed_by, "—") || "—"}</strong>{doc.reviewed_at ? ` · ${formatPlatformTime(doc.reviewed_at)}` : ""}</div>
              </div>
            </Card>

            <Card data-testid="strr-detail-variance-table" style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Variance table</div>
              {rows.length === 0 && (
                <div style={{ fontSize: 12, color: "#666" }}>
                  No variance computed yet — day not closed. Close the day on the form to compute variance.
                </div>
              )}
              {rows.length > 0 && (
                <div data-testid="strr-detail-variance-grid"
                     style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr 1fr 1fr", gap: 4, fontSize: 11 }}>
                  <div style={{ fontWeight: 700 }}>Product</div>
                  <div style={{ fontWeight: 700 }}>Start</div>
                  <div style={{ fontWeight: 700 }}>Dispensed</div>
                  <div style={{ fontWeight: 700 }}>Expected end</div>
                  <div style={{ fontWeight: 700 }}>Actual end</div>
                  <div style={{ fontWeight: 700 }}>Variance</div>
                  <div style={{ fontWeight: 700 }}>Status</div>
                  {rows.map((row) => (
                    <React.Fragment key={row.field}>
                      <div data-testid={`strr-detail-row-product-${row.field}`}>{row.field}</div>
                      <div>{row.start}</div>
                      <div>{(doc.dispensed_quantities || {})[row.field] || 0}</div>
                      <div>{row.expected_end}</div>
                      <div>{row.actual_end}</div>
                      <div style={{ color: row.status === "red" ? "#a33" : row.status === "yellow" ? "#856404" : "#155724" }}>
                        {row.variance} {row.unit} ({(row.variance_pct * 100).toFixed(1)}%)
                      </div>
                      <div><StatusChip status={row.status} /></div>
                    </React.Fragment>
                  ))}
                </div>
              )}
            </Card>

            <Card data-testid="strr-detail-linked-visits" style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Linked Fuel/Lube Visits ({visits.length})</div>
              {visits.length === 0 && (
                <div style={{ fontSize: 12, color: "#666" }}>No matching fuel/lube visits for this truck on this date.</div>
              )}
              {visits.length > 0 && (
                <div style={{ display: "grid", gap: 6 }}>
                  {visits.map((v) => (
                    <Link key={v.id} to={`/shop/fuel-lube/${v.id}`}
                          data-testid={`strr-detail-visit-${v.id}`}
                          style={{ display: "block", padding: 8, background: "#f6f6f6", borderRadius: 3, textDecoration: "none", color: "inherit", fontSize: 12 }}>
                      <strong>{v.id}</strong> · Project {sanitizeOperatorProjectNumber(v.project_number, "Operations support") || "—"} · Tech {sanitizeOperatorReference(v.fuel_lube_tech_name, "Tech record") || "—"} ·
                      Units serviced {v.units_serviced} · Issues {v.issues_found_count || 0} ·
                      Red diesel {Number(v.totals?.red_diesel_gallons || 0).toFixed(1)} gal ·
                      DEF {Number(v.totals?.def_gallons || 0).toFixed(1)} gal
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            {(doc.status === "closed" || doc.status === "needs_review") && (
              <Card data-testid="strr-detail-review-block" style={{ marginTop: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
                  Shop Manager review {doc.reviewed_by ? `(currently · ${formatEmployeeIdentity(doc) || doc.reviewed_by})` : "(optional · operational notes only)"}
                </div>
                {doc.review_notes && (
                  <div data-testid="strr-detail-review-existing" style={{ padding: 8, background: "#fdf3f0", borderRadius: 3, fontSize: 12, marginBottom: 8 }}>
                    {doc.review_notes}
                  </div>
                )}
                <div style={{ display: "grid", gridTemplateColumns: "180px 1fr", gap: 6 }}>
                  <input data-testid="strr-detail-reviewer-name" placeholder="Reviewer name" value={reviewerName}
                         onChange={(e) => setReviewerName(e.target.value)} style={{ padding: 5, fontSize: 12 }} />
                  <textarea data-testid="strr-detail-review-notes" rows={2} placeholder="Operational notes (no disciplinary language)"
                            value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} style={{ padding: 6, fontSize: 12, resize: "vertical" }} />
                </div>
                {reviewError && (
                  <div data-testid="strr-detail-review-error" style={{ marginTop: 6, fontSize: 12, color: "#a33" }}>{reviewError}</div>
                )}
                <div style={{ marginTop: 8 }}>
                  <button data-testid="strr-detail-review-submit" type="button" onClick={submitReview} disabled={reviewSubmitting}
                          style={{ padding: "5px 12px", fontSize: 12, background: "var(--brand-primary,#1b4965)", color: "#fff", border: "none", borderRadius: 4 }}>
                    {reviewSubmitting ? "Saving…" : "Save review notes"}
                  </button>
                </div>
              </Card>
            )}

            <div data-testid="strr-detail-doctrine" style={{ marginTop: 24, padding: 12, fontSize: 11, color: "#666",
                  background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4 }}>
              Dispensed totals come from submitted fuel and lube visits. Review notes are operational context only. Email and file downloads are not available on this page yet, and print uses the browser&apos;s print window.
            </div>
          </>
        )}
      </PortalShell>
    </div>
  );
}
