// Track 13.28 Phase 2 — Mechanic "My Assignments" queue.
//
// MOUNTED AT: /shop/me (behind RequireShop).
// Backend: GET /api/shop/me/assignments · POST /accept · /start · /repair.
//
// Mechanic-only view:
//   - Mechanic sees only own assignments.
//   - Mechanic can accept / start / complete repairs.
//   - Mechanic CANNOT assign, reassign, approve, or RTS.
import React, { useEffect, useState, useCallback } from "react";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card, EmptyState } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
import RepairCompletionForm from "../../components/shop/RepairCompletionForm";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

async function api(path, opts = {}) {
  const r = await fetch(`${API}${path}`, {
    method: opts.method || "GET",
    headers: authHeaders(),
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const body = await r.json().catch(() => null);
  if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
  return body;
}

const STATES = [
  { id: "assigned",       label: "Assigned to me",   tone: "#c47" },
  { id: "accepted",       label: "Accepted",          tone: "#357" },
  { id: "in_progress",    label: "In progress",       tone: "#258" },
  { id: "pending_review", label: "Pending manager review", tone: "#a86" },
];

function AssignmentRow({ defect, bucketId, actorName, onAccept, onStart, onComplete }) {
  const [openRepair, setOpenRepair] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const unitNumber = defect.trailer_unit_number || defect.truck_unit_number || "—";
  const reportedAt = defect.reported_at ? formatPlatformTime(defect.reported_at) : "—";
  const acceptedAt = defect.accepted_at ? formatPlatformTime(defect.accepted_at) : "—";
  const startedAt = defect.repair_started_at ? formatPlatformTime(defect.repair_started_at) : "—";
  const completedAt = defect.repaired_at ? formatPlatformTime(defect.repaired_at) : "—";

  const doAccept = async () => {
    setBusy(true); setErr("");
    try { await onAccept(defect); } catch (e) { setErr(e.message); }
    setBusy(false);
  };
  const doStart = async () => {
    setBusy(true); setErr("");
    try { await onStart(defect); } catch (e) { setErr(e.message); }
    setBusy(false);
  };
  const doComplete = async (body) => {
    setBusy(true); setErr("");
    try { await onComplete(defect, body); setOpenRepair(false); } catch (e) { setErr(e.message); }
    setBusy(false);
  };

  return (
    <Card data-testid={`my-assignments-row-${defect.id}`}>
      <div style={{ fontSize: 13, fontWeight: 700 }}>
        Unit <span data-testid={`my-assignments-row-unit-${defect.id}`}>{unitNumber}</span> · {(defect.item_text || defect.category || "(no description)")}
      </div>
      <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
        Source: <strong>{(defect.inspection_kind || "manual").toUpperCase()}</strong> ·
        severity <strong style={{ color: (defect.severity || "").toLowerCase() === "oos" ? "#a33" : "#777" }}>{defect.severity || "—"}</strong>
        {" · "}reported {reportedAt}
      </div>
      <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
        Accepted {acceptedAt} · started {startedAt} · completed {completedAt}
      </div>
      {(defect.parts_used && defect.parts_used.length > 0) && (
        <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
          Parts used: {defect.parts_used.map((p, i) => (
            <span key={i} style={{ marginRight: 6 }}>
              {p.quantity}× {p.part_name}{p.part_number ? ` [${p.part_number}]` : ""}
            </span>
          ))}
        </div>
      )}
      {err && <div style={{ color: "#a33", fontSize: 11, marginTop: 4 }}>{err}</div>}

      {bucketId === "assigned" && (
        <div style={{ marginTop: 6 }}>
          <button
            data-testid={`my-assignments-accept-${defect.id}`}
            type="button"
            onClick={doAccept}
            disabled={busy}
            style={{ padding: "5px 12px", fontSize: 12, background: "var(--brand-primary, #1b4965)", color: "#fff", border: "none", borderRadius: 4 }}
          >Accept work</button>
        </div>
      )}
      {bucketId === "accepted" && (
        <div style={{ marginTop: 6 }}>
          <button
            data-testid={`my-assignments-start-${defect.id}`}
            type="button"
            onClick={doStart}
            disabled={busy}
            style={{ padding: "5px 12px", fontSize: 12, background: "#258", color: "#fff", border: "none", borderRadius: 4 }}
          >Start work</button>
        </div>
      )}
      {bucketId === "in_progress" && !openRepair && (
        <div style={{ marginTop: 6 }}>
          <button
            data-testid={`my-assignments-complete-open-${defect.id}`}
            type="button"
            onClick={() => setOpenRepair(true)}
            disabled={busy}
            style={{ padding: "5px 12px", fontSize: 12, background: "var(--brand-success, #137a48)", color: "#fff", border: "none", borderRadius: 4 }}
          >Complete repair…</button>
        </div>
      )}
      {bucketId === "in_progress" && openRepair && (
        <div style={{ marginTop: 8, padding: 10, background: "#f4f6f8", borderRadius: 4 }}>
          <RepairCompletionForm
            defect={defect}
            actorName={actorName}
            submitting={busy}
            onSubmit={doComplete}
            onCancel={() => setOpenRepair(false)}
            testidPrefix={`my-assignments-complete-form-${defect.id}`}
          />
        </div>
      )}
      {bucketId === "pending_review" && (
        <div style={{ marginTop: 6, fontSize: 11, color: "#a86" }}>
          Waiting for Shop Manager review. RTS still requires Dispatch.
        </div>
      )}
    </Card>
  );
}

export default function ShopMyAssignments() {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const body = await api("/api/shop/me/assignments");
      setData(body);
    } catch (e) { setError(e.message || "Failed to load assignments."); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const actorName = (data && data.actor_name) || "Shop User";

  const onAccept = useCallback(async (defect) => {
    await api(`/api/shop/fleet/defects/${defect.id}/accept`, { method: "POST", body: { notes: "" } });
    await load();
  }, [load]);
  const onStart = useCallback(async (defect) => {
    await api(`/api/shop/fleet/defects/${defect.id}/start`, { method: "POST", body: { notes: "" } });
    await load();
  }, [load]);
  const onComplete = useCallback(async (defect, body) => {
    await api(`/api/shop/fleet/defects/${defect.id}/repair`, {
      method: "POST",
      body: { actor_name: actorName, ...body },
    });
    await load();
  }, [load, actorName]);

  return (
    <div data-testid="shop-my-assignments-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Portal · My Assignments"
        pageTitle="My Assignments"
        subtitle="Defects assigned to you. Accept, start, then complete with repair notes and parts used. Repair complete still requires return-to-service verification by Dispatch."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="shop-my-assignments-back-to-shop" />
            <button
              data-testid="shop-my-assignments-refresh"
              onClick={load}
              type="button"
              style={{ padding: "6px 12px", fontSize: 12 }}
            >Refresh</button>
          </div>
        }
      >
        {error && (
          <div data-testid="shop-my-assignments-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, marginBottom: 16, color: "#a33", fontSize: 12 }}>
            {error}
          </div>
        )}

        {data && (
          <div style={{ fontSize: 12, color: "#555", marginBottom: 10 }}>
            Signed-in mechanic: <strong data-testid="shop-my-assignments-actor-name">{actorName}</strong>
            {" · "}
            assignments visible only when your shop login is linked to a Mechanic record (admin tokens see the manager queue at <code>/shop/manager/queue</code>).
          </div>
        )}

        {data === null && (
          <div data-testid="shop-my-assignments-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>
        )}

        {data !== null && (data.total || 0) === 0 && !data.actor_id && (
          <EmptyState
            data-testid="shop-my-assignments-empty-no-actor"
            kicker="Admin override"
            title="You are signed in as Admin."
            body="Per-mechanic queues require a Mechanic shop login. Use the Manager Queue at /shop/manager/queue for full visibility."
          />
        )}

        {data !== null && data.actor_id && (data.total || 0) === 0 && (
          <EmptyState
            data-testid="shop-my-assignments-empty"
            kicker="Nothing assigned"
            title="No defects assigned to you right now."
            body="When a Shop Manager assigns work, it will appear here in the Assigned bucket."
          />
        )}

        {data !== null && (data.total || 0) > 0 && STATES.map((bucket) => {
          const rows = (data.buckets && data.buckets[bucket.id]) || [];
          if (rows.length === 0) return null;
          return (
            <section key={bucket.id} data-testid={`shop-my-assignments-bucket-${bucket.id}`} style={{ marginBottom: 18 }}>
              <h3 style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: bucket.tone, marginBottom: 8 }}>
                {bucket.label} · {rows.length}
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: 10 }}>
                {rows.map((d) => (
                  <AssignmentRow
                    key={d.id}
                    defect={d}
                    bucketId={bucket.id}
                    actorName={actorName}
                    onAccept={onAccept}
                    onStart={onStart}
                    onComplete={onComplete}
                  />
                ))}
              </div>
            </section>
          );
        })}
      </PortalShell>
    </div>
  );
}
