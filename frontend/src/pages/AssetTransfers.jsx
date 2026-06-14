// AssetTransfers.jsx — Phase I · Asset Transfer System.
//
// List of asset transfers + request modal + detail drawer with state-
// machine action buttons. Receiving uses unified SignatureCapture
// (source_module=equipment.transfer). Reuses StatusBadge / shared UI
// primitives. NO duplicate asset SOT — equipment_master is the truth.
//
// Routes touched (backend):
//   GET    /api/asset-transfers                 (list with filters)
//   GET    /api/asset-transfers/{id}            (detail)
//   POST   /api/asset-transfers                 (create as Requested)
//   POST   /api/asset-transfers/{id}/approve
//   POST   /api/asset-transfers/{id}/reject     (reason required)
//   POST   /api/asset-transfers/{id}/in-transit
//   POST   /api/asset-transfers/{id}/receive    (signature required)
//   POST   /api/asset-transfers/{id}/cancel
//   POST   /api/asset-transfers/{id}/close

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Truck, RefreshCw, Loader2, Plus, X, ChevronRight,
  CheckCircle2, XCircle, Send, Inbox, Ban, Archive, Eraser,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { tintFor } from "@/lib/statusBadges";

const STATUS_FILTERS = [
  "All", "Requested", "Approved", "In Transit",
  "Received", "Closed", "Rejected", "Cancelled",
];

const STATUS_TINT = {
  Requested:    "bg-amber-50 text-amber-900 border-amber-300",
  Approved:     "bg-indigo-50 text-indigo-900 border-indigo-300",
  "In Transit": "bg-blue-50 text-blue-900 border-blue-300",
  Received:     "bg-emerald-50 text-emerald-900 border-emerald-300",
  Closed:       "bg-slate-50 text-slate-700 border-slate-300",
  Rejected:     "bg-rose-50 text-rose-900 border-rose-300",
  Cancelled:    "bg-slate-50 text-slate-500 border-slate-300",
};

// Allowed transitions, mirrors backend TRANSITIONS map.
const NEXT_ACTIONS = {
  Requested:    [
    { key: "approve",    label: "Approve",      icon: CheckCircle2 },
    { key: "reject",     label: "Needs Revision", icon: XCircle, needsReason: true },
    { key: "cancel",     label: "Cancel",       icon: Ban },
  ],
  Approved:     [
    { key: "in-transit", label: "Mark In-Transit", icon: Send },
    { key: "cancel",     label: "Cancel",          icon: Ban },
  ],
  "In Transit": [
    { key: "receive",    label: "Mark Received",   icon: Inbox, needsSig: true },
    { key: "cancel",     label: "Cancel",          icon: Ban },
  ],
  Received:     [
    { key: "close",      label: "Close",           icon: Archive },
  ],
  Closed:       [],
  Rejected:     [],
  Cancelled:    [],
};

export default function AssetTransfers() {
  const [data, setData] = useState({ items: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("All");
  const [selectedId, setSelectedId] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const params = status !== "All" ? { status } : {};
      const r = await api.get("/asset-transfers", { params });
      setData(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => { load(); }, [load]);

  const summary = useMemo(() => {
    const s = { total: 0 };
    for (const it of data.items || []) {
      s[it.status] = (s[it.status] || 0) + 1;
      s.total++;
    }
    return s;
  }, [data]);

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6" data-testid="asset-transfers-page">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div className="flex items-center gap-3 min-w-0">
          <Truck className="w-5 h-5 text-slate-700 shrink-0" />
          <div>
            <h1 className="text-lg sm:text-xl font-bold font-display text-slate-900 leading-tight">
              Asset Transfers
            </h1>
            <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-slate-500 mt-0.5">
              Equipment movement · live status
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button onClick={() => setShowCreate(true)} size="sm" data-testid="asset-transfer-new-btn">
            <Plus className="w-3.5 h-3.5 mr-1" /> Request Transfer
          </Button>
          <Button onClick={load} variant="outline" size="sm" disabled={loading} data-testid="asset-transfers-refresh">
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </div>

      {/* Status chip filters */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`text-xs font-mono px-2 py-1 rounded border-2 transition-colors ${
              status === s
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
            }`}
            data-testid={`asset-transfer-filter-${s.replace(/ /g, "-").toLowerCase()}`}
          >
            {s}
            {s !== "All" && summary[s] > 0 && (
              <span className="ml-1 text-[10px] opacity-80">· {summary[s]}</span>
            )}
          </button>
        ))}
      </div>

      {error && (
        <div className="border-2 border-rose-300 bg-rose-50 text-rose-800 p-3 rounded-md font-mono text-xs mb-3" data-testid="asset-transfers-error">
          {String(error)}
        </div>
      )}

      {loading && !data.items?.length && (
        <div className="border border-slate-200 bg-white p-4 rounded-md font-mono text-xs text-slate-500">
          Loading transfers…
        </div>
      )}

      {!loading && (data.items?.length === 0) && (
        <div className="border-2 border-dashed border-slate-300 bg-white text-slate-500 italic p-6 rounded-md text-center text-sm" data-testid="asset-transfers-empty">
          No transfers match the current filter.
        </div>
      )}

      {data.items?.length > 0 && (
        <div className="border-2 border-slate-300 bg-white rounded-md overflow-hidden" data-testid="asset-transfers-table">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 border-b-2 border-slate-200">
                <tr>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600 w-24">Status</th>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600">Equipment</th>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600">From → To</th>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600">Requested by</th>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600">Created</th>
                  <th className="w-8 p-2" aria-hidden="true" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => setSelectedId(row.id)}
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    data-testid={`asset-transfer-row-${row.id}`}
                  >
                    <td className="p-2 align-middle">
                      <span className={`inline-block px-2 py-0.5 rounded-full border-2 text-[10px] font-mono uppercase tracking-wider font-bold ${STATUS_TINT[row.status] || "bg-white border-slate-200 text-slate-700"}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="p-2 align-middle font-mono text-slate-800">
                      <div className="font-bold flex items-center gap-1.5">
                        {row.equipment_unit_id || row.equipment_id}
                        {row.equipment_category === "Trench Safety" && (
                          <span
                            className="inline-block px-1.5 py-0.5 rounded text-[8px] font-mono uppercase tracking-wider font-bold bg-cyan-100 text-cyan-900 border border-cyan-300"
                            title="Trench Safety asset"
                            data-testid="transfer-trench-badge"
                          >
                            Trench Safety
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[200px]">{row.equipment_label}</div>
                    </td>
                    <td className="p-2 align-middle text-[11px]">
                      <span className="text-slate-500">{row.from_project_number || "—"}</span>
                      {" → "}
                      <span className="font-bold text-slate-900">{row.to_project_number}</span>
                    </td>
                    <td className="p-2 align-middle text-[11px] text-slate-700 truncate max-w-[180px]">
                      {row.requested_by}
                    </td>
                    <td className="p-2 align-middle text-[10px] font-mono text-slate-500">
                      {String(row.created_at).slice(0, 16).replace("T", " ")}
                    </td>
                    <td className="p-2 align-middle text-slate-300">
                      <ChevronRight className="w-3.5 h-3.5" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showCreate && (
        <CreateTransferDialog
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
        />
      )}

      {selectedId && (
        <TransferDetailDrawer
          id={selectedId}
          onClose={() => setSelectedId(null)}
          onAfterAction={() => load()}
        />
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────
// Create dialog
// ──────────────────────────────────────────────────────────────────
function CreateTransferDialog({ onClose, onCreated }) {
  const [equipmentId, setEquipmentId] = useState("");
  const [toProject, setToProject] = useState("");
  const [toLocation, setToLocation] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async () => {
    setSubmitting(true); setErr(null);
    try {
      await api.post("/asset-transfers", {
        equipment_id: equipmentId.trim(),
        to_project_number: toProject.trim(),
        to_location_label: toLocation.trim() || undefined,
        reason: reason.trim() || undefined,
      });
      onCreated();
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = equipmentId.trim() && toProject.trim() && !submitting;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-end sm:items-center justify-center p-2 sm:p-4" data-testid="asset-transfer-create-dialog">
      <div className="bg-white rounded-md border-2 border-slate-300 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-3 border-b-2 border-slate-200">
          <h2 className="font-display font-bold text-slate-900">Request Asset Transfer</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900" data-testid="asset-transfer-create-close">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 block mb-1">Equipment ID</label>
            <Input
              value={equipmentId}
              onChange={(e) => setEquipmentId(e.target.value)}
              placeholder="e.g. EQ-1234"
              data-testid="asset-transfer-create-equipment-id"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 block mb-1">Destination Project #</label>
            <Input
              value={toProject}
              onChange={(e) => setToProject(e.target.value)}
              placeholder="e.g. 25-12"
              data-testid="asset-transfer-create-to-project"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 block mb-1">Destination Location (optional)</label>
            <Input
              value={toLocation}
              onChange={(e) => setToLocation(e.target.value)}
              placeholder="e.g. South Yard"
              data-testid="asset-transfer-create-to-location"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 block mb-1">Reason (optional)</label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why this transfer is needed"
              rows={3}
              data-testid="asset-transfer-create-reason"
            />
          </div>
          {err && (
            <div className="border-2 border-rose-300 bg-rose-50 text-rose-800 p-2 rounded font-mono text-xs">
              {String(err)}
            </div>
          )}
        </div>
        <div className="p-3 border-t-2 border-slate-200 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} size="sm" disabled={!canSubmit} data-testid="asset-transfer-create-submit">
            {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
            Submit Request
          </Button>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────
// Detail drawer with state-machine action buttons
// ──────────────────────────────────────────────────────────────────
function TransferDetailDrawer({ id, onClose, onAfterAction }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [actionInFlight, setActionInFlight] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const r = await api.get(`/asset-transfers/${id}`);
      setDoc(r.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const doAction = async (action, payload = {}) => {
    setActionInFlight(action); setErr(null);
    try {
      await api.post(`/asset-transfers/${id}/${action}`, payload);
      await load();
      onAfterAction?.();
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setActionInFlight(null);
    }
  };

  const actions = doc ? (NEXT_ACTIONS[doc.status] || []) : [];

  return (
    <div className="fixed inset-0 z-40 bg-black/30 flex justify-end" onClick={onClose}>
      <div
        className="bg-white border-l-2 border-slate-300 w-full max-w-md h-full overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        data-testid="asset-transfer-detail-drawer"
      >
        <div className="flex items-center justify-between p-3 border-b-2 border-slate-200 sticky top-0 bg-white z-10">
          <h2 className="font-display font-bold text-slate-900 text-sm">Transfer Detail</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900" data-testid="asset-transfer-detail-close">
            <X className="w-4 h-4" />
          </button>
        </div>

        {loading && <div className="p-4 font-mono text-xs text-slate-500">Loading…</div>}
        {err && (
          <div className="m-3 border-2 border-rose-300 bg-rose-50 text-rose-800 p-2 rounded font-mono text-xs">{String(err)}</div>
        )}
        {doc && (
          <div className="p-3 space-y-3 text-xs">
            <div>
              <span className={`inline-block px-2 py-0.5 rounded-full border-2 text-[10px] font-mono uppercase tracking-wider font-bold ${STATUS_TINT[doc.status]}`}>
                {doc.status}
              </span>
            </div>
            <KV k="Equipment" v={`${doc.equipment_unit_id || doc.equipment_id} · ${doc.equipment_label || ""}`} />
            <KV k="From" v={`${doc.from_project_number || "—"}${doc.from_location_label ? " · " + doc.from_location_label : ""}`} />
            <KV k="To" v={`${doc.to_project_number}${doc.to_location_label ? " · " + doc.to_location_label : ""}`} />
            <KV k="Requested by" v={doc.requested_by} />
            {doc.reason && <KV k="Reason" v={doc.reason} />}
            {doc.rejection_reason && <KV k="Rejection reason" v={doc.rejection_reason} />}
            <KV k="Created" v={String(doc.created_at).slice(0, 16).replace("T", " ")} />
            {doc.approved_at && <KV k="Approved" v={String(doc.approved_at).slice(0, 16).replace("T", " ")} />}
            {doc.in_transit_at && <KV k="In transit" v={String(doc.in_transit_at).slice(0, 16).replace("T", " ")} />}
            {doc.received_at && <KV k="Received" v={String(doc.received_at).slice(0, 16).replace("T", " ")} />}
            {doc.closed_at && <KV k="Closed" v={String(doc.closed_at).slice(0, 16).replace("T", " ")} />}

            {/* Action buttons */}
            {actions.length > 0 && (
              <div className="border-t-2 border-slate-200 pt-3">
                <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 mb-2">Next actions</div>
                <div className="flex flex-col gap-2">
                  {actions.map((a) => (
                    <ActionButton
                      key={a.key}
                      action={a}
                      busy={actionInFlight === a.key}
                      onRun={(payload) => doAction(a.key, payload)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Audit trail */}
            {Array.isArray(doc.audit) && doc.audit.length > 0 && (
              <div className="border-t-2 border-slate-200 pt-3">
                <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 mb-2">Audit Trail</div>
                <ul className="space-y-1 text-[11px] font-mono" data-testid="asset-transfer-audit-list">
                  {doc.audit.slice().reverse().map((a) => (
                    <li key={a.id} className="border-l-2 border-slate-200 pl-2">
                      <span className="font-bold text-slate-800">{a.action}</span>
                      <span className="text-slate-400 mx-1">·</span>
                      <span className="text-slate-600">{String(a.at).slice(0, 16).replace("T", " ")}</span>
                      {a.actor?.name && (
                        <span className="text-slate-500"> · {a.actor.name}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function KV({ k, v }) {
  return (
    <div>
      <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-500">{k}</div>
      <div className="text-slate-900 break-words">{v || "—"}</div>
    </div>
  );
}

function ActionButton({ action, busy, onRun }) {
  const [showInline, setShowInline] = useState(false);
  const [reason, setReason] = useState("");
  const [sig, setSig] = useState({ signer_name: "", signature_image: "", refusal: false, refusal_reason: "" });

  // Simple action — no extra input.
  if (!action.needsReason && !action.needsSig) {
    const I = action.icon;
    return (
      <Button
        onClick={() => onRun({})}
        disabled={busy}
        variant={action.key === "cancel" ? "outline" : "default"}
        size="sm"
        className="justify-start"
        data-testid={`asset-transfer-action-${action.key}`}
      >
        {busy ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <I className="w-3.5 h-3.5 mr-1" />}
        {action.label}
      </Button>
    );
  }
  // Reason-required (reject).
  if (action.needsReason) {
    const I = action.icon;
    if (!showInline) {
      return (
        <Button onClick={() => setShowInline(true)} variant="outline" size="sm" className="justify-start" data-testid={`asset-transfer-action-${action.key}`}>
          <I className="w-3.5 h-3.5 mr-1" /> {action.label}
        </Button>
      );
    }
    return (
      <div className="border-2 border-slate-200 rounded p-2">
        <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 mb-1">Reject reason</div>
        <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} data-testid={`asset-transfer-action-${action.key}-reason`} />
        <div className="flex gap-2 mt-2 justify-end">
          <Button variant="outline" size="sm" onClick={() => setShowInline(false)}>Cancel</Button>
          <Button size="sm" disabled={!reason.trim() || busy} onClick={() => onRun({ reason: reason.trim() })} data-testid={`asset-transfer-action-${action.key}-submit`}>
            {busy ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : null}
            Confirm {action.label}
          </Button>
        </div>
      </div>
    );
  }
  // Signature-required (receive).
  if (action.needsSig) {
    const I = action.icon;
    if (!showInline) {
      return (
        <Button onClick={() => setShowInline(true)} size="sm" className="justify-start" data-testid={`asset-transfer-action-${action.key}`}>
          <I className="w-3.5 h-3.5 mr-1" /> {action.label}
        </Button>
      );
    }
    const canSubmit = sig.signer_name.trim() &&
      (sig.refusal ? (sig.refusal_reason || "").trim() : !!sig.signature_image);
    return (
      <div className="border-2 border-slate-200 rounded p-2 space-y-2">
        <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600">Confirm receipt</div>
        <Input
          value={sig.signer_name}
          onChange={(e) => setSig((s) => ({ ...s, signer_name: e.target.value }))}
          placeholder="Receiver name"
          data-testid="asset-transfer-receive-signer-name"
        />
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={sig.refusal}
            onChange={(e) => setSig((s) => ({ ...s, refusal: e.target.checked }))}
            id="receive-refusal"
            data-testid="asset-transfer-receive-refusal-toggle"
          />
          <label htmlFor="receive-refusal" className="text-[11px] font-mono text-slate-700">Mark as refusal (e.g. damaged)</label>
        </div>
        {sig.refusal ? (
          <Textarea
            value={sig.refusal_reason}
            onChange={(e) => setSig((s) => ({ ...s, refusal_reason: e.target.value }))}
            placeholder="Reason for refusal"
            rows={2}
            data-testid="asset-transfer-receive-refusal-reason"
          />
        ) : (
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-600 mb-1">Signature</div>
            <InlineSigPad
              onChange={(img) => setSig((s) => ({ ...s, signature_image: img }))}
            />
          </div>
        )}
        <div className="flex gap-2 mt-2 justify-end">
          <Button variant="outline" size="sm" onClick={() => setShowInline(false)}>Cancel</Button>
          <Button size="sm" disabled={!canSubmit || busy} onClick={() => onRun(sig)} data-testid={`asset-transfer-action-${action.key}-submit`}>
            {busy ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : null}
            Confirm Receipt
          </Button>
        </div>
      </div>
    );
  }
  return null;
}

// ──────────────────────────────────────────────────────────────────
// InlineSigPad — minimal canvas signature pad. Emits base64 PNG via
// onChange(dataURL). Decoupled from /api/signatures (parent endpoint
// /asset-transfers/:id/receive captures the signature server-side).
// touch-action:none + dpr-aware to behave correctly on field mobile.
// ──────────────────────────────────────────────────────────────────
function InlineSigPad({ onChange }) {
  const canvasRef = useRef(null);
  const drawingRef = useRef(false);
  const lastRef = useRef({ x: 0, y: 0 });
  const [hasStrokes, setHasStrokes] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#0f172a";
  }, []);

  const pos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const t = e.touches ? e.touches[0] : e;
    return { x: t.clientX - rect.left, y: t.clientY - rect.top };
  };

  const start = (e) => {
    e.preventDefault();
    drawingRef.current = true;
    lastRef.current = pos(e);
  };
  const move = (e) => {
    if (!drawingRef.current) return;
    e.preventDefault();
    const p = pos(e);
    const ctx = canvasRef.current.getContext("2d");
    ctx.beginPath();
    ctx.moveTo(lastRef.current.x, lastRef.current.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    lastRef.current = p;
    if (!hasStrokes) setHasStrokes(true);
  };
  const end = () => {
    if (!drawingRef.current) return;
    drawingRef.current = false;
    try {
      const url = canvasRef.current.toDataURL("image/png");
      onChange?.(url);
    } catch {
      /* canvas tainted — ignore */
    }
  };
  const clear = () => {
    const ctx = canvasRef.current.getContext("2d");
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    setHasStrokes(false);
    onChange?.("");
  };

  return (
    <div className="border-2 border-dashed border-slate-300 rounded bg-white">
      <canvas
        ref={canvasRef}
        className="w-full h-[140px] block bg-white rounded"
        style={{ touchAction: "none" }}
        onMouseDown={start}
        onMouseMove={move}
        onMouseUp={end}
        onMouseLeave={end}
        onTouchStart={start}
        onTouchMove={move}
        onTouchEnd={end}
        data-testid="asset-transfer-receive-sig-canvas"
      />
      <div className="flex items-center justify-between px-2 py-1 border-t-2 border-slate-200">
        <span className="text-[10px] font-mono text-slate-500">
          {hasStrokes ? "Signature captured" : "Sign above"}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={clear}
          disabled={!hasStrokes}
          data-testid="asset-transfer-receive-sig-clear"
        >
          <Eraser className="w-3.5 h-3.5 mr-1" /> Clear
        </Button>
      </div>
    </div>
  );
}
