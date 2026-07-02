// Track 19.21b · Historical Records — Review Queue page
// -----------------------------------------------------------------
// HR sees every lane. Safety sees Safety lane. Asset Admin sees Asset
// lane. Approve / reject / reassign / edit metadata inline.
//
// Route: /hr/historical-records/queue
// Zero drift: additive read+approve surface — never mutates employees.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft, CheckCircle2, ChevronRight, FileText, Inbox,
  RefreshCw, ShieldCheck, Undo2, User, X,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  approveRecord, authHeaders, fetchQueue, fetchVocabulary,
  reassignRecord, rejectRecord,
} from "@/lib/employeeRecordsApi";
import { EmployeeCombo } from "@/components/EmployeeCombo";

const LANE_LABEL = {
  hr: "HR",
  safety: "Safety",
  asset: "Asset Administration",
  corporate_import: "Corporate Import",
};

const LANE_STYLE = {
  hr:               "border-purple-300 bg-purple-50 text-purple-900",
  safety:           "border-cyan-300 bg-cyan-50 text-cyan-900",
  asset:            "border-orange-300 bg-orange-50 text-orange-900",
  corporate_import: "border-slate-300 bg-slate-50 text-slate-900",
};

const STATE_STYLE = {
  pending_classification: "bg-amber-100 text-amber-900 border-amber-300",
  pending_match:          "bg-amber-100 text-amber-900 border-amber-300",
  pending_approval:       "bg-yellow-100 text-yellow-900 border-yellow-300",
  linked:                 "bg-emerald-100 text-emerald-900 border-emerald-300",
  rejected:               "bg-red-100 text-red-900 border-red-300",
};

function _fmtDate(x) {
  if (!x) return "—";
  try { return new Date(x).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
  catch { return x; }
}

export default function HistoricalRecordsQueue() {
  const { t } = useT();
  const navigate = useNavigate();
  const [vocab, setVocab] = useState(null);
  const [activeLane, setActiveLane] = useState(null);
  const [queue, setQueue] = useState({ records: [], count: 0 });
  const [busy, setBusy] = useState(false);
  const [expandId, setExpandId] = useState(null);

  useEffect(() => {
    fetchVocabulary().then((v) => {
      setVocab(v);
      const first = v?.allowed_lanes_for_actor?.[0] || "hr";
      setActiveLane(first);
    }).catch((e) => toast.error(String(e.message || e)));
  }, []);

  const load = useCallback(async () => {
    if (!activeLane) return;
    setBusy(true);
    try {
      const q = await fetchQueue(activeLane);
      setQueue({ records: q.records || [], count: q.count || 0 });
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  }, [activeLane]);

  useEffect(() => { load(); }, [load]);

  const allowedLanes = vocab?.allowed_lanes_for_actor || [];

  return (
    <div className="min-h-screen bg-slate-50" data-testid="historical-records-queue">
      <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
            data-testid="queue-back"
          >
            <ArrowLeft className="w-4 h-4" /> {t("Back")}
          </button>
          <button
            type="button"
            onClick={() => navigate("/hr/historical-records/intake")}
            className="inline-flex items-center gap-2 rounded-md bg-purple-700 text-white px-3 py-1.5 text-sm font-semibold hover:bg-purple-800"
            data-testid="queue-open-intake"
          >
            <FileText className="w-3.5 h-3.5" /> {t("Add Historical Record")}
          </button>
        </div>

        {/* Header */}
        <header className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5"
                data-testid="queue-header">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Historical Records")} · {t("Review Queue")}
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
            {t("Review & Approve Records")}
          </h1>
          <p className="mt-2 text-sm text-slate-600 max-w-3xl">
            {t("Approved records surface on Employee 360°. Rejected records are archived for audit but never appear as active lifecycle events.")}
          </p>
        </header>

        {/* Lane tabs */}
        <div className="rounded-xl border-2 border-slate-300 bg-white p-2 flex flex-wrap gap-2"
             data-testid="queue-lane-tabs">
          {allowedLanes.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => setActiveLane(l)}
              className={`px-3 py-1.5 rounded-md text-sm font-semibold border-2 transition-colors ${
                activeLane === l ? LANE_STYLE[l] : "border-transparent text-slate-700 hover:bg-slate-100"
              }`}
              data-testid={`queue-lane-tab-${l}`}
            >
              {t(LANE_LABEL[l] || l)}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2 pr-2">
            <button
              type="button"
              onClick={load}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
              data-testid="queue-refresh"
            >
              <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
            </button>
            <div className="text-xs text-slate-500 font-mono" data-testid="queue-count">
              {queue.count} {t("pending")}
            </div>
          </div>
        </div>

        {/* Records list */}
        <div className="space-y-3" data-testid="queue-records">
          {queue.records.length === 0 ? (
            <div className="rounded-xl border-2 border-slate-200 bg-white p-8 text-center text-slate-500 text-sm"
                 data-testid="queue-empty">
              <Inbox className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              {t("Queue is clear. No records awaiting review in this lane.")}
            </div>
          ) : (
            queue.records.map((rec) => (
              <RecordCard
                key={rec.id}
                rec={rec}
                vocab={vocab}
                expanded={expandId === rec.id}
                onToggle={() => setExpandId((cur) => cur === rec.id ? null : rec.id)}
                onChanged={load}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function RecordCard({ rec, vocab, expanded, onToggle, onChanged }) {
  const { t } = useT();
  const [busy, setBusy] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);
  const [editEmpName, setEditEmpName] = useState(rec.employee_name_snapshot || "");
  const [editEmpId, setEditEmpId] = useState(rec.employee_id || "");
  const [editType, setEditType] = useState(rec.record_type || "");
  const [editLane, setEditLane] = useState(rec.ownership_lane || "");
  const lane = rec.ownership_lane;

  const canApprove = useMemo(() => (
    !!rec.employee_id && !!rec.record_type
  ), [rec.employee_id, rec.record_type]);

  const availableTypes = vocab?.record_types_by_lane?.[editLane] || [];

  const onApprove = async () => {
    setBusy(true);
    try {
      await approveRecord(rec.id, "");
      toast.success(t("Record approved."));
      onChanged();
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  };

  const onReject = async () => {
    if (!rejectReason.trim()) { toast.error(t("Reason is required to reject.")); return; }
    setBusy(true);
    try {
      await rejectRecord(rec.id, rejectReason);
      toast.success(t("Record rejected."));
      setShowReject(false);
      setRejectReason("");
      onChanged();
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  };

  const onSaveEdits = async () => {
    const patch = {};
    if (editEmpId && editEmpId !== rec.employee_id) patch.employee_id = editEmpId;
    if (editType && editType !== rec.record_type) patch.record_type = editType;
    if (editLane && editLane !== rec.ownership_lane) patch.ownership_lane = editLane;
    if (Object.keys(patch).length === 0) { toast.info(t("No changes.")); return; }
    setBusy(true);
    try {
      await reassignRecord(rec.id, patch);
      toast.success(t("Record updated."));
      onChanged();
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  };

  const fileUrl = `${process.env.REACT_APP_BACKEND_URL}/api/employee-records/records/${rec.id}/file`;

  return (
    <div className={`rounded-xl border-2 bg-white p-4 ${expanded ? "border-slate-900 shadow-md" : "border-slate-200"}`}
         data-testid={`queue-record-${rec.id}`}>
      {/* Row header */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full text-left"
        data-testid={`queue-record-toggle-${rec.id}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest ${LANE_STYLE[lane] || "border-slate-300 bg-slate-100 text-slate-800"}`}>
                {LANE_LABEL[lane] || lane}
              </span>
              <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest ${STATE_STYLE[rec.approval_status] || ""}`}>
                {rec.approval_status.replace(/_/g, " ")}
              </span>
              <span className="text-xs font-mono text-slate-500">#{rec.id.slice(0, 8)}</span>
            </div>
            <div className="mt-1 font-display text-base font-black text-slate-900">
              {(rec.record_type || t("(unclassified)")).replace(/_/g, " ")}
            </div>
            <div className="mt-1 text-sm text-slate-700 flex flex-wrap gap-x-4 gap-y-1">
              <span className="inline-flex items-center gap-1">
                <User className="w-3 h-3 text-slate-400" />
                {rec.employee_name_snapshot || t("(unlinked)")}
              </span>
              {rec.source_file_name && (
                <span className="inline-flex items-center gap-1">
                  <FileText className="w-3 h-3 text-slate-400" />
                  <span className="font-mono text-xs">{rec.source_file_name}</span>
                </span>
              )}
              <span className="text-xs text-slate-500">{_fmtDate(rec.created_at)}</span>
            </div>
          </div>
          <ChevronRight className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`} />
        </div>
      </button>

      {expanded && (
        <div className="mt-4 border-t border-slate-200 pt-4 space-y-4"
             data-testid={`queue-record-detail-${rec.id}`}>
          {/* Metadata edit */}
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="sm:col-span-3">
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Reassign employee")}
              </label>
              <div className="mt-1" data-testid={`queue-emp-combo-${rec.id}`}>
                <EmployeeCombo
                  value={editEmpName}
                  onChange={(v) => setEditEmpName(v)}
                  onPick={(emp) => {
                    setEditEmpId(emp?.id || "");
                    setEditEmpName(emp?.name || "");
                  }}
                  testId={`queue-emp-picker-${rec.id}`}
                />
              </div>
            </div>
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Lane")}
              </label>
              <select
                value={editLane}
                onChange={(e) => setEditLane(e.target.value)}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-2 py-1.5 text-sm font-mono"
                data-testid={`queue-lane-${rec.id}`}
              >
                {(vocab?.allowed_lanes_for_actor || []).map((l) => (
                  <option key={l} value={l}>{LANE_LABEL[l] || l}</option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Record type")}
              </label>
              <select
                value={editType}
                onChange={(e) => setEditType(e.target.value)}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-2 py-1.5 text-sm font-mono"
                data-testid={`queue-type-${rec.id}`}
              >
                <option value="">{t("(pick)")}</option>
                {availableTypes.map((rt) => (
                  <option key={rt} value={rt}>{rt.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onSaveEdits}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-50"
              data-testid={`queue-save-${rec.id}`}
            >
              <Undo2 className="w-3.5 h-3.5" /> {t("Save edits")}
            </button>
            {rec.source_file_ref && (
              <a
                href={fileUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={async (e) => {
                  // GET the download URL with auth headers, then follow the redirect.
                  e.preventDefault();
                  try {
                    const r = await fetch(fileUrl, { headers: authHeaders(), redirect: "follow" });
                    if (r.redirected) { window.open(r.url, "_blank", "noopener"); return; }
                    const j = await r.json();
                    if (j.source_file_ref?.startsWith("data:")) {
                      window.open(j.source_file_ref, "_blank", "noopener");
                    } else {
                      toast.error(t("Preview unavailable."));
                    }
                  } catch { toast.error(t("Preview unavailable.")); }
                }}
                className="inline-flex items-center gap-1.5 rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 hover:bg-slate-100"
                data-testid={`queue-file-${rec.id}`}
              >
                <FileText className="w-3.5 h-3.5" /> {t("View original")}
              </a>
            )}
            <div className="ml-auto flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setShowReject((x) => !x)}
                disabled={busy}
                className="inline-flex items-center gap-1.5 rounded-md bg-red-600 text-white px-3 py-1.5 text-sm font-semibold hover:bg-red-700 disabled:opacity-50"
                data-testid={`queue-reject-${rec.id}`}
              >
                <X className="w-3.5 h-3.5" /> {t("Reject")}
              </button>
              <button
                type="button"
                onClick={onApprove}
                disabled={busy || !canApprove}
                title={canApprove ? "" : t("Employee and record type must be set before approval.")}
                className="inline-flex items-center gap-1.5 rounded-md bg-emerald-700 text-white px-3 py-1.5 text-sm font-semibold hover:bg-emerald-800 disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid={`queue-approve-${rec.id}`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" /> {t("Approve")}
              </button>
            </div>
          </div>

          {!canApprove && (
            <div className="rounded-md bg-amber-50 border border-amber-300 px-3 py-2 text-xs text-amber-900"
                 data-testid={`queue-approval-blocked-${rec.id}`}>
              <ShieldCheck className="inline w-3 h-3 mr-1" />
              {t("Employee link and record type are both required before approval.")}
            </div>
          )}

          {showReject && (
            <div className="rounded-md bg-red-50 border border-red-300 p-3"
                 data-testid={`queue-reject-form-${rec.id}`}>
              <label htmlFor={`reject-reason-${rec.id}`}
                     className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-800">
                {t("Reason for rejection")} <span className="text-red-600">*</span>
              </label>
              <textarea
                id={`reject-reason-${rec.id}`}
                rows={2}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="mt-1 w-full rounded-md border-2 border-red-300 bg-white px-3 py-2 text-sm"
                data-testid={`queue-reject-reason-${rec.id}`}
              />
              <div className="mt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { setShowReject(false); setRejectReason(""); }}
                  className="rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 hover:bg-slate-100"
                  data-testid={`queue-reject-cancel-${rec.id}`}
                >
                  {t("Cancel")}
                </button>
                <button
                  type="button"
                  onClick={onReject}
                  disabled={busy || !rejectReason.trim()}
                  className="rounded-md bg-red-600 text-white px-3 py-1.5 text-sm font-semibold hover:bg-red-700 disabled:opacity-50"
                  data-testid={`queue-reject-confirm-${rec.id}`}
                >
                  {t("Confirm Rejection")}
                </button>
              </div>
            </div>
          )}

          {rec.notes && (
            <div className="rounded-md bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-700">
              <span className="font-mono uppercase tracking-widest text-[9px] text-slate-500">{t("Notes")}</span>
              <div>{rec.notes}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
