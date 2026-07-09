// Track 13.28 Phase 2 — Shop Manager queue.
//
// MOUNTED AT: /shop/manager/queue (behind RequireShop).
// Backend: GET /api/shop/manager/queue · POST /assign · /reassign · /manager-review.
//
// Doctrine:
//   - Repair Complete ≠ RTS. No RTS action surfaces here.
//   - Manager can ONLY assign, reassign, review (approve/reject).
//   - Dispatch retains /clear authority (out of this surface).
//   - No cost / no inventory / no MaintainX.
//
// Reference: TRACK_13_28A · TRACK_13_28 · TRACK_13_28_PHASE_2.
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card, EmptyState } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

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

const BUCKETS = [
  { id: "unassigned",     label: "Unassigned",      tone: "#a33" },
  { id: "assigned",       label: "Assigned",        tone: "#c47" },
  { id: "accepted",       label: "Accepted",         tone: "#357" },
  { id: "in_progress",    label: "In progress",     tone: "#258" },
  { id: "pending_review", label: "Pending review",  tone: "#a86" },
  { id: "rts_pending",    label: "RTS pending",     tone: "#137a48" },
];

function ShopUserPicker({ users, value, onChange, testid }) {
  return (
    <select
      data-testid={testid}
      value={value || ""}
      onChange={(e) => {
        const u = users.find((x) => x.id === e.target.value);
        onChange(u || null);
      }}
      style={{ padding: 6, fontSize: 12, minWidth: 180 }}
    >
      <option value="">Choose mechanic…</option>
      {users.map((u) => (
        <option key={u.id} value={u.id}>{u.role ? `${u.name} · ${u.role}` : u.name}</option>
      ))}
    </select>
  );
}

function AssignBar({ defect, mechanics, onAssign }) {
  const [picked, setPicked] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const isReassign = !!defect.assigned_to_mechanic_id;
  const submit = async () => {
    if (!picked) { setErr("Pick a mechanic first."); return; }
    setBusy(true); setErr("");
    try {
      await onAssign(defect, picked, isReassign);
      setPicked(null);
    } catch (e) { setErr(e.message || "Assignment failed."); }
    setBusy(false);
  };
  return (
    <div data-testid={`manager-queue-assign-bar-${defect.id}`} style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 6 }}>
      <ShopUserPicker
        users={mechanics}
        value={picked && picked.id}
        onChange={setPicked}
        testid={`manager-queue-assign-select-${defect.id}`}
      />
      <button
        data-testid={`manager-queue-assign-submit-${defect.id}`}
        type="button"
        onClick={submit}
        disabled={busy || !picked}
        style={{
          padding: "5px 10px", fontSize: 12,
          background: picked && !busy ? "var(--brand-primary, #1b4965)" : "#aaa",
          color: "#fff", border: "none", borderRadius: 4,
        }}
      >
        {isReassign ? "Reassign" : "Assign"}
      </button>
      {err && <span style={{ color: "#a33", fontSize: 11 }}>{err}</span>}
    </div>
  );
}

function ReviewBar({ defect, onReview }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async (approved) => {
    if (!approved && (note || "").trim().length < 5) {
      setErr("Reject reason required (≥5 chars).");
      return;
    }
    setBusy(true); setErr("");
    try {
      await onReview(defect, approved, (note || "").trim());
      setOpen(false); setNote("");
    } catch (e) { setErr(e.message || "Review failed."); }
    setBusy(false);
  };
  if (!open) {
    return (
      <button
        data-testid={`manager-queue-review-open-${defect.id}`}
        type="button"
        onClick={() => setOpen(true)}
        style={{ padding: "5px 10px", fontSize: 12, marginTop: 6 }}
      >Open review</button>
    );
  }
  return (
    <div data-testid={`manager-queue-review-panel-${defect.id}`} style={{ marginTop: 6, padding: 8, background: "#f4f6f8", borderRadius: 4 }}>
      <div style={{ fontSize: 12, marginBottom: 4 }}>
        Mechanic: <strong>{defect.assigned_to_mechanic_name || defect.repaired_by_name || "—"}</strong> · Repair notes:
        <em style={{ marginLeft: 4 }}>{defect.repair_notes || "(none)"}</em>
      </div>
      {(defect.parts_used && defect.parts_used.length > 0) && (
        <div style={{ fontSize: 11, marginBottom: 6 }}>
          Parts used: {defect.parts_used.map((p, i) => (
            <span key={i} style={{ marginRight: 6 }}>
              {p.quantity}× {p.part_name}{p.part_number ? ` [${p.part_number}]` : ""}
            </span>
          ))}
        </div>
      )}
      {(defect.parts_on_order && defect.parts_on_order.length > 0) && (
        <div style={{ fontSize: 11, marginBottom: 6, color: "#a86" }}>
          Parts on order: {defect.parts_on_order.map((p) => p.part_name).join(", ")}
        </div>
      )}
      <textarea
        data-testid={`manager-queue-review-note-${defect.id}`}
        rows={2}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Reviewer notes (required if rejecting)…"
        style={{ width: "100%", fontSize: 12, padding: 6, fontFamily: "inherit" }}
      />
      <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
        <button data-testid={`manager-queue-review-approve-${defect.id}`} type="button" onClick={() => submit(true)} disabled={busy} style={{ padding: "5px 10px", fontSize: 12, background: "var(--brand-success, #137a48)", color: "#fff", border: "none", borderRadius: 4 }}>
          Approve
        </button>
        <button data-testid={`manager-queue-review-reject-${defect.id}`} type="button" onClick={() => submit(false)} disabled={busy} style={{ padding: "5px 10px", fontSize: 12, background: "#a33", color: "#fff", border: "none", borderRadius: 4 }}>
          Reject & send back
        </button>
        <button data-testid={`manager-queue-review-cancel-${defect.id}`} type="button" onClick={() => { setOpen(false); setNote(""); }} disabled={busy} style={{ padding: "5px 10px", fontSize: 12 }}>
          Cancel
        </button>
      </div>
      {err && <div style={{ color: "#a33", fontSize: 11, marginTop: 4 }}>{err}</div>}
    </div>
  );
}

function DefectRow({ defect, mechanics, onAssign, onReview, bucketId }) {
  const reportedAt = defect.reported_at ? formatPlatformTime(defect.reported_at) : "—";
  const assignedAt = defect.assigned_at ? formatPlatformTime(defect.assigned_at) : "—";
  const startedAt = defect.repair_started_at ? formatPlatformTime(defect.repair_started_at) : "—";
  const completedAt = defect.repaired_at ? formatPlatformTime(defect.repaired_at) : "—";
  const unitNumber = defect.trailer_unit_number || defect.truck_unit_number || "—";
  return (
    <Card data-testid={`manager-queue-row-${defect.id}`}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700 }}>
            Unit <span data-testid={`manager-queue-row-unit-${defect.id}`}>{unitNumber}</span> · {(defect.item_text || defect.category || "(no description)")}
          </div>
          <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
            Source: <strong>{(defect.inspection_kind || "manual").toUpperCase()}</strong> ·
            severity <strong style={{ color: (defect.severity || "").toLowerCase() === "oos" ? "#a33" : "#777" }}>{defect.severity || "—"}</strong>
            {" · "}reported by {defect.reported_by_name || "—"} · {reportedAt}
          </div>
          <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
            Mechanic: <strong>{defect.assigned_to_mechanic_name || "—"}</strong>
            {" · "}assigned {assignedAt}
            {" · "}started {startedAt}
            {" · "}completed {completedAt}
          </div>
          {defect.shop_manager_reviewed_at && (
            <div style={{ fontSize: 11, color: "var(--brand-success, #137a48)", marginTop: 2 }}>
              Reviewed by {defect.shop_manager_reviewed_by_name || "—"} · awaiting Dispatch RTS.
            </div>
          )}
        </div>
      </div>
      {(bucketId === "unassigned" || bucketId === "assigned" || bucketId === "accepted" || bucketId === "in_progress") && (
        <AssignBar defect={defect} mechanics={mechanics} onAssign={onAssign} />
      )}
      {bucketId === "pending_review" && (
        <ReviewBar defect={defect} onReview={onReview} />
      )}
    </Card>
  );
}

export default function ShopManagerQueue() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [mechanics, setMechanics] = useState([]);
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    setError("");
    try {
      const body = await api("/api/shop/manager/queue");
      setData(body);
    } catch (e) { setError(e.message || "Failed to load queue."); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    // Use the existing shop-users admin endpoint to populate the
    // mechanic picker (live source · no invented names).
    api("/api/admin/shop-users")
      .then((rows) => setMechanics(
        (Array.isArray(rows) ? rows : (rows && rows.users) || [])
          .filter((u) => u.is_active !== false && (u.role || "").toLowerCase() !== "shop manager")
          .map((u) => ({ id: u.id, name: u.name || u.email, role: u.role || "" }))
      ))
      .catch(() => setMechanics([]));
  }, []);

  const onAssign = useCallback(async (defect, mechanic, isReassign) => {
    const path = isReassign
      ? `/api/shop/fleet/defects/${defect.id}/reassign`
      : `/api/shop/fleet/defects/${defect.id}/assign`;
    await api(path, {
      method: "POST",
      body: { mechanic_id: mechanic.id, mechanic_name: mechanic.name, notes: "" },
    });
    await load();
  }, [load]);

  const onReview = useCallback(async (defect, approved, notes) => {
    await api(`/api/shop/fleet/defects/${defect.id}/manager-review`, {
      method: "POST",
      body: { approved, notes },
    });
    await load();
  }, [load]);

  const filteredBuckets = useMemo(() => {
    if (!data) return [];
    return BUCKETS.filter((b) => filter === "all" || filter === b.id)
      .map((b) => ({ ...b, defects: (data.buckets || {})[b.id] || [] }));
  }, [data, filter]);

  return (
    <div data-testid="shop-manager-queue-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Portal · Manager Queue"
        pageTitle="Shop Manager Queue"
        subtitle="Every defect by assignment state. Assign · reassign · review repairs. Repair complete still requires return-to-service verification by Dispatch."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="shop-manager-queue-back-to-shop" />
            <button
              data-testid="shop-manager-queue-refresh"
              onClick={load}
              type="button"
              style={{ padding: "6px 12px", fontSize: 12 }}
            >Refresh</button>
          </div>
        }
      >
        {error && (
          <div data-testid="shop-manager-queue-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, marginBottom: 16, color: "#a33", fontSize: 12 }}>
            {error}
          </div>
        )}

        <div data-testid="shop-manager-queue-counts-strip" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          <button
            data-testid="shop-manager-queue-filter-all"
            type="button"
            onClick={() => setFilter("all")}
            style={{
              padding: "6px 10px", fontSize: 11, fontWeight: 700,
              background: filter === "all" ? "var(--brand-primary, #1b4965)" : "#ddd",
              color: filter === "all" ? "#fff" : "#222",
              border: "none", borderRadius: 4,
            }}
          >All · {data ? data.total : "—"}</button>
          {BUCKETS.map((b) => {
            const count = (data && data.counts && data.counts[b.id]) || 0;
            return (
              <button
                key={b.id}
                data-testid={`shop-manager-queue-filter-${b.id}`}
                type="button"
                onClick={() => setFilter(b.id)}
                style={{
                  padding: "6px 10px", fontSize: 11, fontWeight: 700,
                  background: filter === b.id ? b.tone : "#eee",
                  color: filter === b.id ? "#fff" : "#222",
                  border: "none", borderRadius: 4,
                }}
              >{b.label} · {count}</button>
            );
          })}
        </div>

        {data === null && (
          <div data-testid="shop-manager-queue-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>
        )}

        {data !== null && (data.total || 0) === 0 && (
          <EmptyState
            data-testid="shop-manager-queue-empty"
            kicker="No defects in scope"
            title="Nothing pending right now."
            body="Open defects, mechanic assignments, and pending reviews will appear here."
          />
        )}

        {filteredBuckets.map((bucket) => (
          bucket.defects.length > 0 && (
            <section key={bucket.id} data-testid={`shop-manager-queue-bucket-${bucket.id}`} style={{ marginBottom: 18 }}>
              <h3 style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: bucket.tone, marginBottom: 8 }}>
                {bucket.label} · {bucket.defects.length}
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 10 }}>
                {bucket.defects.map((d) => (
                  <DefectRow
                    key={d.id}
                    defect={d}
                    mechanics={mechanics}
                    onAssign={onAssign}
                    onReview={onReview}
                    bucketId={bucket.id}
                  />
                ))}
              </div>
            </section>
          )
        ))}
      </PortalShell>
    </div>
  );
}
