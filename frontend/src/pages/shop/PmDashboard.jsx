// Track 13.31 — PM Engine Dashboard.
// Route: /shop/pm (RequireShop).
// Reads: GET /api/shop/pm/summary + GET /api/shop/pm/queue + GET /api/shop/pm/schedules
// No mutation here — see PmWorkOrderDetail for lifecycle actions.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { PortalShell, Card, StatusChip } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "shop"], { "Content-Type": "application/json" });
}

const STATUS_TONE = {
  overdue:       { bg: "#fef2f2", border: "#fecaca", text: "#991b1b" },
  due:           { bg: "#fffbeb", border: "#fde68a", text: "#92400e" },
  due_soon:      { bg: "#eff6ff", border: "#bfdbfe", text: "#1e40af" },
  ok:            { bg: "var(--paper-card)", border: "var(--border-bold)", text: "var(--ink-strong)" },
  paused:        { bg: "#f5f3ff", border: "#ddd6fe", text: "#5b21b6" },
  unknown_meter: { bg: "#f1f5f9", border: "#cbd5e1", text: "#475569" },
};
const STATUS_LABEL = {
  overdue: "Overdue", due: "Due now", due_soon: "Due soon",
  ok: "On track", paused: "Paused", unknown_meter: "Needs meter",
};

function Tile({ to, label, value, tone = "ok", testid }) {
  const t = STATUS_TONE[tone] || STATUS_TONE.ok;
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <div style={{ padding: "14px 16px", background: t.bg,
                    border: `1px solid ${t.border}`, borderRadius: "var(--radius-card)",
                    minHeight: 96, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase", color: t.text }}>{label}</div>
        <div data-testid={`${testid}-value`} style={{ fontSize: 32, fontWeight: 800, color: t.text, lineHeight: 1, marginTop: 6 }}>
          {value == null ? "—" : value}
        </div>
      </div>
    </Link>
  );
}

export default function PmDashboard() {
  const [summary, setSummary] = useState(null);
  const [queue, setQueue]     = useState(null);
  const [err, setErr]         = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [s, q] = await Promise.all([
          fetch(`${API}/api/shop/pm/summary`, { headers: authHeaders() }).then(r => r.json()),
          fetch(`${API}/api/shop/pm/queue`,   { headers: authHeaders() }).then(r => r.json()),
        ]);
        if (alive) { setSummary(s); setQueue(q); }
      } catch (e) {
        if (alive) setErr(e.message || "PM data unavailable.");
      }
    })();
    return () => { alive = false; };
  }, []);

  const sc = (summary?.schedule_counts) || {};
  const wo = (summary?.work_order_counts) || {};

  return (
    <div data-testid="pm-dashboard-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Operations"
        pageTitle="Preventive Maintenance"
        subtitle="Due · overdue · in flight · pending review. PM completion does NOT return units to service."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Link to="/shop/pm/templates" data-testid="pm-dashboard-link-templates"
                  style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                           background: "var(--paper-card)", color: "var(--ink-strong)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>PM Templates</Link>
            <Link to="/shop/pm/schedules" data-testid="pm-dashboard-link-schedules"
                  style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                           background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                           border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>PM Schedules</Link>
          </div>
        }
      >
        <BackToShopLink />
        {err && <div data-testid="pm-dashboard-error" style={{ padding: 12, background: "#fee2e2", color: "#7f1d1d", borderRadius: 4, marginBottom: 12 }}>{err}</div>}

        <section data-testid="pm-dashboard-schedule-tiles" style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".08em",
                        textTransform: "uppercase", color: "var(--ink-soft)" }}>Schedules</div>
          <h2 style={{ margin: "2px 0 12px", fontSize: 18, fontWeight: 800, color: "var(--ink-strong)" }}>Where the fleet stands right now</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
            <Tile to="/shop/pm/schedules?status=overdue" label="Overdue"        value={sc.overdue}  tone="overdue"  testid="pm-tile-overdue" />
            <Tile to="/shop/pm/schedules?status=due"     label="Due now"        value={sc.due}      tone="due"      testid="pm-tile-due" />
            <Tile to="/shop/pm/schedules?status=due_soon" label="Due soon"      value={sc.due_soon} tone="due_soon" testid="pm-tile-due-soon" />
            <Tile to="/shop/pm/schedules?status=ok"      label="On track"       value={sc.ok}       tone="ok"       testid="pm-tile-ok" />
            <Tile to="/shop/pm/schedules?status=paused"  label="Paused"         value={sc.paused}   tone="paused"   testid="pm-tile-paused" />
            <Tile to="/shop/pm/schedules?status=unknown_meter" label="Needs meter" value={sc.unknown_meter} tone="unknown_meter" testid="pm-tile-unknown-meter" />
          </div>
        </section>

        <section data-testid="pm-dashboard-wo-tiles" style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".08em",
                        textTransform: "uppercase", color: "var(--ink-soft)" }}>Work orders</div>
          <h2 style={{ margin: "2px 0 12px", fontSize: 18, fontWeight: 800, color: "var(--ink-strong)" }}>What the shop is working on</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
            <Tile to="/shop/pm/work-orders?status=open"          label="Unassigned"     value={summary?.unassigned ?? wo.open} tone="overdue" testid="pm-tile-wo-unassigned" />
            <Tile to="/shop/pm/work-orders?status=assigned"      label="Assigned"       value={wo.assigned}      tone="due"      testid="pm-tile-wo-assigned" />
            <Tile to="/shop/pm/work-orders?status=accepted"      label="Accepted"       value={wo.accepted}      tone="due_soon" testid="pm-tile-wo-accepted" />
            <Tile to="/shop/pm/work-orders?status=in_progress"   label="In progress"    value={wo.in_progress}   tone="due_soon" testid="pm-tile-wo-in-progress" />
            <Tile to="/shop/pm/work-orders?status=waiting_parts" label="Waiting parts"  value={wo.waiting_parts} tone="due"      testid="pm-tile-wo-waiting-parts" />
            <Tile to="/shop/pm/work-orders?status=completed"     label="Pending review" value={wo.completed}     tone="due"      testid="pm-tile-wo-pending-review" />
            <Tile to="/shop/pm/work-orders?status=reviewed"      label="Reviewed"       value={wo.reviewed}      tone="ok"       testid="pm-tile-wo-reviewed" />
            <Tile to="/shop/pm/work-orders?status=rejected"      label="Rejected back"  value={wo.rejected}      tone="overdue"  testid="pm-tile-wo-rejected" />
          </div>
        </section>

        <section data-testid="pm-dashboard-due-list" style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--ink-soft)" }}>Top action queue</div>
          <h2 style={{ margin: "2px 0 12px", fontSize: 18, fontWeight: 800, color: "var(--ink-strong)" }}>Overdue + due schedules</h2>
          {!queue ? <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>Loading…</div> : (
            <>
              {["overdue", "due", "due_soon"].map((bucket) => {
                const list = queue.schedules?.[bucket] || [];
                if (list.length === 0) return null;
                return (
                  <div key={bucket} style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "var(--ink-soft)", marginBottom: 6, textTransform: "uppercase" }}>{STATUS_LABEL[bucket]}</div>
                    {list.map((s) => (
                      <Link key={s.id} to={`/shop/pm/schedules?focus=${s.id}`}
                            data-testid={`pm-dashboard-due-row-${s.id}`}
                            style={{ display: "block", padding: "10px 12px", marginBottom: 6,
                                     background: STATUS_TONE[bucket].bg,
                                     border: `1px solid ${STATUS_TONE[bucket].border}`,
                                     borderRadius: "var(--radius-card)", color: "inherit", textDecoration: "none" }}>
                        <strong style={{ fontSize: 13, color: STATUS_TONE[bucket].text }}>{s.unit_number}</strong>
                        <span style={{ marginLeft: 8, fontSize: 12, color: "var(--ink-strong)" }}>· {s.template_name}</span>
                        <div style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 2 }}>{s.explanation}</div>
                      </Link>
                    ))}
                  </div>
                );
              })}
              {(queue.schedules?.overdue?.length ?? 0) === 0 &&
               (queue.schedules?.due?.length ?? 0) === 0 &&
               (queue.schedules?.due_soon?.length ?? 0) === 0 && (
                <div data-testid="pm-dashboard-due-empty"
                     style={{ fontSize: 12, color: "var(--ink-soft)", padding: "10px 12px",
                              background: "var(--paper-card)", border: "1px solid var(--border-bold)",
                              borderRadius: "var(--radius-card)" }}>
                  No overdue or due PM schedules right now.
                </div>
              )}
            </>
          )}
        </section>

        <div data-testid="pm-dashboard-rts-note" style={{
          padding: "var(--pad-card)", background: "var(--paper-card)",
          border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)",
          color: "var(--ink-soft)", fontSize: 12,
        }}>
          <strong style={{ color: "var(--ink-strong)" }}>PM completion does not return a unit to service.</strong>{" "}
          Dispatch retains RTS authority. MaintainX is dormant. Manufacturer database is not consumed.
        </div>
      </PortalShell>
    </div>
  );
}
