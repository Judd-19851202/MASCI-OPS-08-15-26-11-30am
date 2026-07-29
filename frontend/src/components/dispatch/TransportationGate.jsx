/**
 * TRACK 16.09 · Transportation Gate UI primitives for Dispatch.
 *
 * Exports:
 *   - useTransportationGate(driverRefId, truckRefId)  → {state, blocked, ...}
 *   - <TransportationEligibilityChip />               → inline chip
 *   - <OverrideRequiredModal />                       → drawer for authorized override
 *
 * Reuses existing dispatch auth headers — no new endpoints from the
 * client other than the Track 16.09 backend gate (check + override).
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ShieldAlert, ShieldCheck, AlertTriangle, X, Hourglass, Lock } from "lucide-react";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const API = process.env.REACT_APP_BACKEND_URL;

function gateHeaders() {
  return {
    "Content-Type": "application/json",
    ...buildScopedPortalAuthHeaders(["admin", "dispatch"]),
  };
}

const CHIP_STYLES = {
  eligible: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-800", icon: ShieldCheck, label: "Eligible" },
  pending_review: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-900", icon: Hourglass, label: "Pending Review" },
  needs_correction: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-900", icon: AlertTriangle, label: "Needs Correction" },
  expired: { bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-900", icon: AlertTriangle, label: "Expired" },
  suspended: { bg: "bg-red-50", border: "border-red-200", text: "text-red-800", icon: ShieldAlert, label: "Suspended" },
  not_dispatchable: { bg: "bg-red-50", border: "border-red-200", text: "text-red-800", icon: ShieldAlert, label: "Not Dispatchable" },
  override_approved: { bg: "bg-sky-50", border: "border-sky-200", text: "text-sky-800", icon: Lock, label: "Override Approved" },
};

// ---------- Hook -----------------------------------------------------------
export function useTransportationGate(driverRefId, truckRefId) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const check = useCallback(async () => {
    if (!driverRefId && !truckRefId) {
      setResult(null);
      return;
    }
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/dispatch/transportation/check`, {
        method: "POST",
        headers: gateHeaders(),
        body: JSON.stringify({
          driver_id: driverRefId || null,
          truck_id: truckRefId || null,
        }),
      });
      if (r.ok) {
        setResult(await r.json());
      } else {
        setResult(null);
      }
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [driverRefId, truckRefId]);
  useEffect(() => { check(); }, [check]);
  return { result, loading, refresh: check };
}

// ---------- Chip -----------------------------------------------------------
export function TransportationEligibilityChip({ result, loading }) {
  if (loading) {
    return (
      <span
        data-testid="tx-elig-chip-loading"
        className="inline-flex items-center gap-1 text-xs text-slate-400 italic"
      >
        Checking eligibility…
      </span>
    );
  }
  if (!result) return null;
  const style = CHIP_STYLES[result.state] || CHIP_STYLES.pending_review;
  const Icon = style.icon;
  return (
    <span
      data-testid={`tx-elig-chip-${result.state}`}
      className={`inline-flex items-center gap-1 ${style.bg} ${style.border} ${style.text} border rounded-full px-2 py-0.5 text-[11px] font-medium`}
      title={result.message}
    >
      <Icon className="h-3 w-3" /> {style.label}
    </span>
  );
}

// ---------- Reasons block ---------------------------------------------------
export function GateReasonList({ result }) {
  if (!result || !result.blocked) return null;
  return (
    <ul data-testid="tx-elig-reasons" className="mt-2 ml-3 text-xs text-red-800 list-disc">
      {(result.reason_labels || []).map((label, i) => (
        <li key={i} data-testid={`tx-elig-reason-${i}`}>{label}</li>
      ))}
    </ul>
  );
}

// ---------- Override Modal -------------------------------------------------
const REASON_CODES = [
  { code: "emergency_dispatch", label: "Emergency dispatch" },
  { code: "compliance_pending_review", label: "Compliance pending review" },
  { code: "rolling_correction", label: "Rolling correction in flight" },
  { code: "other", label: "Other (explain)" },
];

export function OverrideRequiredModal({ block, driverRefId, truckRefId,
                                          onClose, onApproved, isAuthorized }) {
  const [reason, setReason] = useState("emergency_dispatch");
  const [explanation, setExplanation] = useState("");
  const [hours, setHours] = useState(24);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async () => {
    if (!ack || explanation.length < 10) return;
    setBusy(true);
    setErr(null);
    try {
      const r = await fetch(`${API}/api/dispatch/transportation/override`, {
        method: "POST",
        headers: gateHeaders(),
        body: JSON.stringify({
          driver_id: driverRefId || null,
          truck_id: truckRefId || null,
          reason_code: reason,
          explanation,
          duration_hours: hours,
          acknowledgement: true,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        setErr(j.detail || j.message || `Override failed (${r.status})`);
        return;
      }
      onApproved(j);
    } catch (e) {
      setErr(e.message || "Network error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="tx-override-modal" className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <header className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-700" />
            <h2 className="font-semibold text-slate-900">Override Required</h2>
          </div>
          <button data-testid="tx-override-close" onClick={onClose} className="text-slate-500 hover:text-slate-900">
            <X className="h-5 w-5" />
          </button>
        </header>
        <div className="px-5 py-4 space-y-3 text-sm">
          <div className="bg-amber-50 border border-amber-200 rounded p-2 text-xs">
            <div className="font-semibold text-amber-900">Blocking reasons</div>
            <ul className="mt-1 ml-4 list-disc text-amber-900">
              {(block.reason_labels || []).map((l, i) => (
                <li key={i} data-testid={`tx-override-block-${i}`}>{l}</li>
              ))}
            </ul>
          </div>

          {!isAuthorized ? (
            <div data-testid="tx-override-unauthorized" className="bg-slate-50 border border-slate-200 rounded p-3 text-slate-700">
              Contact Admin, Operations, or Transportation Manager to approve an override.
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Reason</label>
                <select data-testid="tx-override-reason" value={reason} onChange={(e) => setReason(e.target.value)} className="w-full border border-slate-300 rounded px-2 py-1.5">
                  {REASON_CODES.map(r => <option key={r.code} value={r.code}>{r.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Explanation (required, min 10 chars)</label>
                <textarea
                  data-testid="tx-override-explanation"
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  placeholder="Production-critical haul. Compliance status confirmed via …"
                  className="w-full border border-slate-300 rounded px-2 py-1.5 min-h-[72px]"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Override duration (hours, max 168)</label>
                <input
                  data-testid="tx-override-hours"
                  type="number" min={1} max={168}
                  value={hours} onChange={(e) => setHours(Math.max(1, Math.min(168, parseInt(e.target.value, 10) || 1)))}
                  className="w-full border border-slate-300 rounded px-2 py-1.5"
                />
              </div>
              <label className="flex items-start gap-2 text-xs text-slate-700 mt-1">
                <input data-testid="tx-override-ack" type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} className="mt-0.5" />
                <span>I understand this override allows dispatch despite an unresolved Transportation requirement and does not mark the requirement complete.</span>
              </label>
              {err ? <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2">{err}</div> : null}
            </>
          )}
        </div>
        <footer className="px-5 py-3 border-t border-slate-200 flex items-center justify-end gap-2">
          <button data-testid="tx-override-cancel" onClick={onClose} className="text-slate-700 text-sm hover:underline">Cancel</button>
          {isAuthorized ? (
            <button
              data-testid="tx-override-approve"
              onClick={submit}
              disabled={!ack || explanation.length < 10 || busy}
              className="inline-flex items-center gap-2 bg-amber-700 hover:bg-amber-800 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded"
            >
              <Lock className="h-4 w-4" /> {busy ? "Approving…" : "Approve override"}
            </button>
          ) : null}
        </footer>
      </div>
    </div>
  );
}

export function isOverrideAuthorized() {
  return Boolean(buildScopedPortalAuthHeaders(["admin"])["X-Admin-Token"]);
}
