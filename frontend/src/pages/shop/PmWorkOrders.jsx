// Track 13.31 — PM Work Order queue + detail (single combined surface).
// Routes:
//   /shop/pm/work-orders      → queue (optional ?status=)
//   /shop/pm/work-orders/:id  → detail + lifecycle actions
import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams, useNavigate } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

const STATUS_TONE = {
  open:           { bg: "#fef2f2", text: "#991b1b", label: "Unassigned" },
  assigned:       { bg: "#fffbeb", text: "#92400e", label: "Assigned" },
  accepted:       { bg: "#eff6ff", text: "#1e40af", label: "Accepted" },
  in_progress:    { bg: "#eff6ff", text: "#1e40af", label: "In progress" },
  waiting_parts:  { bg: "#fffbeb", text: "#92400e", label: "Waiting parts" },
  completed:      { bg: "#fffbeb", text: "#92400e", label: "Pending review" },
  reviewed:       { bg: "#dcfce7", text: "#166534", label: "Reviewed" },
  rejected:       { bg: "#fef2f2", text: "#991b1b", label: "Rejected back" },
  closed:         { bg: "#e5e7eb", text: "#374151", label: "Closed" },
};

export default function PmWorkOrders() {
  const { id } = useParams();
  return id ? <PmWorkOrderDetail id={id} /> : <PmWorkOrderQueue />;
}

function PmWorkOrderQueue() {
  const { t } = useT();
  const [params] = useSearchParams();
  const filter = params.get("status") || "";
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  useEffect(() => {
    (async () => {
      try {
        const q = filter ? `?status=${filter}` : "";
        const r = await fetch(`${API}/api/shop/pm/work-orders${q}`, { headers: authHeaders() });
        const b = await r.json();
        if (!r.ok) throw new Error(b.detail || `HTTP ${r.status}`);
        setItems(b.items || []);
      } catch (e) { setErr(e.message); }
    })();
  }, [filter]);

  return (
    <div data-testid="pm-work-orders-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell portalName="MASCI" portalRole={t("Shop Operations")}
                   pageTitle={t("PM Work Orders")}
                   subtitle={`${t("Queue")}${filter ? ` · ${t(STATUS_TONE[filter]?.label || filter)}` : ""}. ${t("PM completion does not RTS.")}`}>
        <BackToShopLink />
        {err && <div data-testid="pm-work-orders-error" style={{ padding: 12, background: "#fee2e2", color: "#7f1d1d", borderRadius: 4, marginBottom: 12 }}>{err}</div>}
        {items.length === 0 && <div data-testid="pm-work-orders-empty" style={{ padding: 12, background: "var(--paper-card)", border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", fontSize: 12, color: "var(--ink-soft)" }}>No PM work orders matching this filter.</div>}
        {items.map((w) => {
          const t = STATUS_TONE[w.status] || STATUS_TONE.open;
          return (
            <Link key={w.id} to={`/shop/pm/work-orders/${w.id}`} data-testid={`pm-work-orders-row-${w.id}`}
                  style={{ display: "block", padding: "12px 14px", marginBottom: 6, background: "var(--paper-card)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           color: "inherit", textDecoration: "none" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
                <div>
                  <strong style={{ fontSize: 14 }}>{w.unit_number}</strong>
                  <span style={{ marginLeft: 8, fontSize: 12, color: "var(--ink-strong)" }}>· {w.pm_name}</span>
                </div>
                <span style={{ padding: "3px 10px", borderRadius: 3, background: t.bg, color: t.text, fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>{t.label}</span>
              </div>
              <div style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 4 }}>
                Due {w.due_basis}{w.assigned_to_mechanic_name ? ` · mechanic ${w.assigned_to_mechanic_name}` : ""}
              </div>
            </Link>
          );
        })}
      </PortalShell>
    </div>
  );
}

function PmWorkOrderDetail({ id }) {
  const navigate = useNavigate();
  const [wo, setWo] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [completeForm, setCompleteForm] = useState({
    notes: "", completion_meter: "", completed_by_name: "",
    checklist_results: [], parts_used: [], parts_on_order: [],
  });
  const [reviewForm, setReviewForm] = useState({ decision: "approve", notes: "", reviewer_name: "" });
  const [assignForm, setAssignForm] = useState({ mechanic_id: "", mechanic_name: "" });

  const refresh = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/shop/pm/work-orders/${id}`, { headers: authHeaders() });
      const b = await r.json();
      if (!r.ok) throw new Error(b.detail || `HTTP ${r.status}`);
      setWo(b.work_order);
      setCompleteForm((f) => ({ ...f, checklist_results: (b.work_order.checklist_results || []).map(c => ({ ...c, pass: c.pass ?? true, notes: c.notes ?? "" })) }));
    } catch (e) { setErr(e.message); }
  }, [id]);
  useEffect(() => { refresh(); }, [refresh]);

  async function act(path, body) {
    setErr(""); setBusy(true);
    try {
      const r = await fetch(`${API}/api/shop/pm/work-orders/${id}/${path}`, {
        method: "POST", headers: authHeaders(),
        body: body !== undefined ? JSON.stringify(body) : null,
      });
      const b = await r.json();
      if (!r.ok) throw new Error(b.detail || `HTTP ${r.status}`);
      await refresh();
    } catch (e) { setErr(e.message); }
    setBusy(false);
  }

  if (!wo) return (
    <div data-testid="pm-work-order-detail-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell portalName="MASCI" portalRole="Shop Operations" pageTitle="PM Work Order">
        <BackToShopLink />
        {err ? <div style={{ padding: 12, background: "#fee2e2", color: "#7f1d1d", borderRadius: 4 }}>{err}</div>
             : <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>Loading…</div>}
      </PortalShell>
    </div>
  );

  const t = STATUS_TONE[wo.status] || STATUS_TONE.open;
  const lblStyle = { display: "block", fontSize: 11, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 4 };
  const inpStyle = { width: "100%", padding: "8px 10px", fontSize: 13, border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", background: "var(--paper-card)", color: "var(--ink-strong)" };

  return (
    <div data-testid="pm-work-order-detail-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell portalName="MASCI" portalRole="Shop Operations"
                   pageTitle={`PM · ${wo.unit_number}`}
                   subtitle={`${wo.pm_name} · due ${wo.due_basis}. PM completion does NOT return the unit to service.`}>
        <BackToShopLink />
        {err && <div data-testid="pm-work-order-detail-error" style={{ padding: 12, background: "#fee2e2", color: "#7f1d1d", borderRadius: 4, marginBottom: 12 }}>{err}</div>}

        <Card title={<span>Status <span data-testid="pm-work-order-status" style={{ marginLeft: 10, padding: "3px 10px", borderRadius: 3, background: t.bg, color: t.text, fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>{t.label}</span></span>}>
          <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>
            <div>Assigned to: <strong style={{ color: "var(--ink-strong)" }}>{wo.assigned_to_mechanic_name || "—"}</strong></div>
            <div>Completed by: <strong style={{ color: "var(--ink-strong)" }}>{wo.completed_by_name || "—"}</strong>{wo.completion_meter != null ? ` · meter ${wo.completion_meter}` : ""}</div>
            <div>Reviewed by: <strong style={{ color: "var(--ink-strong)" }}>{wo.manager_reviewed_by || "—"}</strong>{wo.manager_review_decision ? ` · ${wo.manager_review_decision}` : ""}</div>
          </div>
        </Card>

        {wo.status === "open" && (
          <Card title="Assign to mechanic">
            <form onSubmit={(e) => { e.preventDefault(); act("assign", assignForm); }} data-testid="pm-assign-form" style={{ display: "grid", gap: 10 }}>
              <div>
                <label style={lblStyle}>Mechanic id *</label>
                <input data-testid="pm-assign-input-id" required value={assignForm.mechanic_id}
                       onChange={(e) => setAssignForm(f => ({ ...f, mechanic_id: e.target.value }))} style={inpStyle} />
              </div>
              <div>
                <label style={lblStyle}>Mechanic name *</label>
                <input data-testid="pm-assign-input-name" required value={assignForm.mechanic_name}
                       onChange={(e) => setAssignForm(f => ({ ...f, mechanic_name: e.target.value }))} style={inpStyle} />
              </div>
              <button data-testid="pm-assign-submit" type="submit" disabled={busy}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer",
                               background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                               border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)", justifySelf: "start" }}>
                Assign mechanic
              </button>
            </form>
          </Card>
        )}

        {wo.status === "assigned" && (
          <button data-testid="pm-action-accept" type="button" disabled={busy} onClick={() => act("accept")}
                  style={{ padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer", margin: "12px 0",
                           background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                           border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)" }}>
            Accept assignment
          </button>
        )}

        {(wo.status === "accepted" || wo.status === "in_progress" || wo.status === "waiting_parts") && (
          <Card title="Start / progress">
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button data-testid="pm-action-start" type="button" disabled={busy} onClick={() => act("start", { notes: "", waiting_parts: false })}
                      style={{ padding: "8px 16px", fontSize: 12, fontWeight: 700, cursor: "pointer",
                               background: "var(--paper-card)", color: "var(--ink-strong)",
                               border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)" }}>
                Mark in progress
              </button>
              <button data-testid="pm-action-waiting-parts" type="button" disabled={busy} onClick={() => act("start", { notes: "", waiting_parts: true })}
                      style={{ padding: "8px 16px", fontSize: 12, fontWeight: 700, cursor: "pointer",
                               background: "#fffbeb", color: "#92400e",
                               border: "1px solid #fde68a", borderRadius: "var(--radius-card)" }}>
                Mark waiting on parts
              </button>
            </div>
          </Card>
        )}

        {(wo.status === "accepted" || wo.status === "in_progress" || wo.status === "waiting_parts") && (
          <Card title="Complete PM">
            <form onSubmit={(e) => { e.preventDefault(); act("complete", {
              notes: completeForm.notes,
              completion_meter: completeForm.completion_meter === "" ? null : Number(completeForm.completion_meter),
              checklist_results: completeForm.checklist_results,
              parts_used: completeForm.parts_used.filter(p => p.name?.trim()).map(p => ({ ...p, quantity: Number(p.quantity) || 1 })),
              parts_on_order: completeForm.parts_on_order.filter(p => p.name?.trim()).map(p => ({ ...p, quantity: Number(p.quantity) || 1 })),
              completed_by_name: completeForm.completed_by_name,
            }); }} data-testid="pm-complete-form" style={{ display: "grid", gap: 10 }}>
              <div>
                <label style={lblStyle}>Completion meter (if hours/miles)</label>
                <input data-testid="pm-complete-meter" type="number" min="0" step="any"
                       value={completeForm.completion_meter}
                       onChange={(e) => setCompleteForm(f => ({ ...f, completion_meter: e.target.value }))}
                       style={inpStyle} />
              </div>
              <div>
                <label style={lblStyle}>Completed by *</label>
                <input data-testid="pm-complete-by" required value={completeForm.completed_by_name}
                       onChange={(e) => setCompleteForm(f => ({ ...f, completed_by_name: e.target.value }))} style={inpStyle} />
              </div>
              <div>
                <label style={lblStyle}>Notes (min 10 chars) *</label>
                <textarea data-testid="pm-complete-notes" rows={3} required minLength={10} maxLength={4000}
                          value={completeForm.notes}
                          onChange={(e) => setCompleteForm(f => ({ ...f, notes: e.target.value }))}
                          style={{ ...inpStyle, fontFamily: "inherit" }} />
              </div>
              <div>
                <label style={lblStyle}>Checklist</label>
                {completeForm.checklist_results.length === 0 && <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>No checklist on this PM.</div>}
                {completeForm.checklist_results.map((c, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, marginBottom: 4, alignItems: "center" }}>
                    <input data-testid={`pm-complete-checklist-pass-${i}`} type="checkbox" checked={!!c.pass}
                           onChange={(e) => setCompleteForm(f => ({ ...f, checklist_results: f.checklist_results.map((x, j) => j === i ? { ...x, pass: e.target.checked } : x) }))} />
                    <span style={{ fontSize: 13, color: "var(--ink-strong)" }}>{c.label}</span>
                  </div>
                ))}
              </div>
              <button data-testid="pm-complete-submit" type="submit" disabled={busy}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer",
                               background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                               border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)", justifySelf: "start" }}>
                Mark PM complete
              </button>
            </form>
          </Card>
        )}

        {wo.status === "completed" && (
          <Card title="Manager review">
            <form onSubmit={(e) => { e.preventDefault(); act("manager-review", reviewForm); }} data-testid="pm-review-form" style={{ display: "grid", gap: 10 }}>
              <div>
                <label style={lblStyle}>Decision *</label>
                <select data-testid="pm-review-decision" value={reviewForm.decision}
                        onChange={(e) => setReviewForm(f => ({ ...f, decision: e.target.value }))}
                        style={inpStyle}>
                  <option value="approve">Approve</option>
                  <option value="reject">Reject — send back to mechanic</option>
                </select>
              </div>
              <div>
                <label style={lblStyle}>Reviewer name *</label>
                <input data-testid="pm-review-reviewer" required value={reviewForm.reviewer_name}
                       onChange={(e) => setReviewForm(f => ({ ...f, reviewer_name: e.target.value }))} style={inpStyle} />
              </div>
              <div>
                <label style={lblStyle}>Notes</label>
                <textarea data-testid="pm-review-notes" rows={2} maxLength={2000}
                          value={reviewForm.notes}
                          onChange={(e) => setReviewForm(f => ({ ...f, notes: e.target.value }))}
                          style={{ ...inpStyle, fontFamily: "inherit" }} />
              </div>
              <button data-testid="pm-review-submit" type="submit" disabled={busy}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer",
                               background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                               border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)", justifySelf: "start" }}>
                Submit review
              </button>
            </form>
          </Card>
        )}

        <Card title="Checklist results (read-only snapshot)">
          {(wo.checklist_results || []).length === 0 && <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>No checklist captured.</div>}
          {(wo.checklist_results || []).map((c, i) => (
            <div key={i} style={{ fontSize: 12, padding: "4px 0", borderBottom: "1px dashed #e5e7eb" }}>
              <span style={{ display: "inline-block", width: 18 }}>{c.pass ? "✓" : "·"}</span>
              {c.label}{c.notes ? <em style={{ marginLeft: 8, color: "var(--ink-soft)" }}>— {c.notes}</em> : null}
            </div>
          ))}
        </Card>

        <Card title="Parts used">
          {(wo.parts_used || []).length === 0 && <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>None recorded.</div>}
          {(wo.parts_used || []).map((p, i) => (
            <div key={i} style={{ fontSize: 12, padding: "4px 0", borderBottom: "1px dashed #e5e7eb" }}>
              <strong>{p.name}</strong>{p.part_number ? ` · ${p.part_number}` : ""}{p.manufacturer ? ` · ${p.manufacturer}` : ""} × {p.quantity}
            </div>
          ))}
        </Card>

        <div data-testid="pm-work-order-rts-note" style={{
          marginTop: 12, padding: "var(--pad-card)", background: "var(--paper-card)",
          border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)",
          color: "var(--ink-soft)", fontSize: 12,
        }}>
          <strong style={{ color: "var(--ink-strong)" }}>PM completion does not return a unit to service.</strong>{" "}
          Dispatch retains RTS authority. PM completion creates an Asset Service Event but does not clear an OOS unit.
        </div>
      </PortalShell>
    </div>
  );
}
