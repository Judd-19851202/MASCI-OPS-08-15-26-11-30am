// Track 19.22 · Phase 4 · Bulk Batch detail — classification workflow
// Route: /hr/historical-records/batches/:batchId
//
// Flow: create batch (parent page) → upload many files here → bulk apply
// (assign one record_type / employee to all) → per-row overrides via the
// Review Queue → bulk approve-all when ready.
//
// Manual only. No OCR. No AI. Every record is human-approved.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft, CheckCircle2, ChevronRight, Inbox, Layers,
  RefreshCw, Upload, UserCheck,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  batchApply, batchApproveAll, batchUpload, fetchBatch, fetchVocabulary,
} from "@/lib/employeeRecordsApi";
import { EmployeeCombo } from "@/components/EmployeeCombo";

const LANE_LABEL = {
  hr: "HR", safety: "Safety", asset: "Asset", corporate_import: "Corporate Import",
};

const STATE_STYLE = {
  pending_classification: "bg-amber-100 text-amber-900 border-amber-300",
  pending_match:          "bg-amber-100 text-amber-900 border-amber-300",
  pending_approval:       "bg-yellow-100 text-yellow-900 border-yellow-300",
  linked:                 "bg-emerald-100 text-emerald-900 border-emerald-300",
  rejected:               "bg-red-100 text-red-900 border-red-300",
};

export default function HistoricalRecordsBatchDetail() {
  const { batchId } = useParams();
  const navigate = useNavigate();
  const { t } = useT();
  const [batch, setBatch] = useState(null);
  const [records, setRecords] = useState([]);
  const [counts, setCounts] = useState({});
  const [vocab, setVocab] = useState(null);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  // Bulk apply form
  const [applyType, setApplyType] = useState("");
  const [applyEmpId, setApplyEmpId] = useState("");
  const [applyEmpName, setApplyEmpName] = useState("");
  const [applyDate, setApplyDate] = useState("");

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const r = await fetchBatch(batchId);
      setBatch(r.batch);
      setRecords(r.records || []);
      setCounts(r.counts || {});
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  }, [batchId]);

  useEffect(() => {
    fetchVocabulary().then(setVocab).catch((e) => toast.error(String(e.message || e)));
    load();
  }, [load]);

  const recordTypeOptions = useMemo(() => {
    if (!batch || !vocab) return [];
    return vocab.record_types_by_lane?.[batch.ownership_lane] || [];
  }, [batch, vocab]);

  const onUpload = useCallback(async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    try {
      const r = await batchUpload(batchId, Array.from(fileList));
      toast.success(t("Uploaded {n} file(s)").replace("{n}", String(r.created || 0)));
      await load();
    } catch (e) { toast.error(String(e.message || e)); }
    finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }, [batchId, load, t]);

  const onBulkApply = async () => {
    if (!applyType && !applyEmpId && !applyDate) {
      toast.error(t("Set at least one field to apply."));
      return;
    }
    setBusy(true);
    try {
      const patch = {};
      if (applyType) patch.record_type = applyType;
      if (applyEmpId) {
        patch.employee_id = applyEmpId;
        patch.employee_name_snapshot = applyEmpName;
      }
      if (applyDate) patch.effective_date = applyDate;
      const r = await batchApply(batchId, patch);
      toast.success(t("Applied to {n} record(s).").replace("{n}", String(r.modified || 0)));
      await load();
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  };

  const onApproveAll = async () => {
    setBusy(true);
    try {
      const r = await batchApproveAll(batchId);
      toast.success(t("Approved {n} record(s).").replace("{n}", String(r.approved || 0)));
      await load();
    } catch (e) { toast.error(String(e.message || e)); }
    finally { setBusy(false); }
  };

  const readyToApprove = (counts.pending_approval || 0);
  const stillClassifying = (counts.pending_classification || 0) + (counts.pending_match || 0);

  if (!batch) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500 font-mono text-sm" data-testid="batch-detail-loading">
          {t("Loading batch…")}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="historical-records-batch-detail">
      <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate("/hr/historical-records/batches")}
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
            data-testid="batch-detail-back"
          >
            <ArrowLeft className="w-4 h-4" /> {t("All batches")}
          </button>
          <button
            type="button"
            onClick={() => navigate("/hr/historical-records/queue")}
            className="inline-flex items-center gap-2 rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 hover:bg-slate-100"
            data-testid="batch-detail-open-queue"
          >
            <Inbox className="w-3.5 h-3.5" /> {t("Open Review Queue")}
          </button>
        </div>

        {/* Header */}
        <header className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5"
                data-testid="batch-detail-header">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Batch")} · {LANE_LABEL[batch.ownership_lane]} · #{batch.id.slice(0, 8)}
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
            {batch.label || t("(unlabeled batch)")}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <StatChip label={t("Files")}       value={batch.file_count ?? 0} />
            <StatChip label={t("Records")}     value={batch.record_count ?? 0} />
            <StatChip label={t("Classifying")} value={stillClassifying} tone="amber" />
            <StatChip label={t("Ready")}       value={readyToApprove} tone="yellow" />
            <StatChip label={t("Approved")}    value={counts.linked || 0} tone="emerald" />
            <StatChip label={t("Rejected")}    value={counts.rejected || 0} tone="red" />
          </div>
          {/* Track 19.25 · Intake Session provenance strip. */}
          {(batch.source_name || batch.source_type || batch.source_location) && (
            <div className="mt-3 flex flex-wrap items-center gap-2 rounded-md bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-700"
                 data-testid="batch-detail-provenance">
              <span className="font-mono uppercase tracking-widest text-[9px] text-slate-500">{t("Session")}</span>
              {batch.source_name && <span><b>{batch.source_name}</b></span>}
              {batch.source_type && <span className="text-slate-500">· {batch.source_type}</span>}
              {batch.source_location && <span className="text-slate-500">· {batch.source_location}</span>}
              <span className="ml-auto text-[10px] text-slate-500">
                {t("Every file in this batch inherits this provenance.")}
              </span>
            </div>
          )}
        </header>

        {/* Upload dropzone */}
        <section className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-4"
                 data-testid="batch-detail-upload">
          <label htmlFor="batch-file-input"
                 className="inline-flex items-center gap-2 rounded-md bg-slate-900 text-white px-3 py-1.5 text-sm font-semibold cursor-pointer hover:bg-slate-800">
            <Upload className="w-3.5 h-3.5" />
            {uploading ? t("Uploading…") : t("Upload files to this batch")}
          </label>
          <input
            id="batch-file-input"
            ref={inputRef}
            type="file"
            className="hidden"
            multiple
            onChange={(e) => onUpload(e.target.files)}
            accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.heic,.heif,.doc,.docx,.xls,.xlsx,.xlsm,.csv,.txt,.rtf"
            data-testid="batch-file-input"
          />
          <p className="mt-2 text-xs text-slate-500">
            {t("Select many files — each becomes a staged record in this batch, ready for manual classification.")}
          </p>
        </section>

        {/* Bulk apply panel */}
        <section className="rounded-xl border-2 border-slate-300 bg-white p-4 space-y-3"
                 data-testid="batch-detail-apply">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Bulk classify")} · {t("apply to all still-unclassified rows")}
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label htmlFor="batch-apply-type"
                     className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Record type")}
              </label>
              <select
                id="batch-apply-type"
                value={applyType}
                onChange={(e) => setApplyType(e.target.value)}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-2 py-1.5 text-sm font-mono"
                data-testid="batch-apply-type"
              >
                <option value="">{t("(leave)")}</option>
                {recordTypeOptions.map((rt) => (
                  <option key={rt} value={rt}>{rt.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Employee")}
              </label>
              <div className="mt-1" data-testid="batch-apply-employee-wrap">
                <EmployeeCombo
                  value={applyEmpName}
                  onChange={(v) => setApplyEmpName(v)}
                  onPick={(emp) => {
                    setApplyEmpId(emp?.id || "");
                    setApplyEmpName(emp?.name || "");
                  }}
                  testId="batch-apply-employee"
                />
              </div>
            </div>
            <div>
              <label htmlFor="batch-apply-date"
                     className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Effective date")}
              </label>
              <input
                id="batch-apply-date"
                type="date"
                value={applyDate}
                onChange={(e) => setApplyDate(e.target.value)}
                className="mt-1 w-full rounded-md border-2 border-slate-300 bg-white px-2 py-1.5 text-sm"
                data-testid="batch-apply-date"
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onBulkApply}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 text-white px-4 py-2 text-sm font-semibold hover:bg-slate-800 disabled:opacity-50"
              data-testid="batch-apply-submit"
            >
              <Layers className="w-3.5 h-3.5" /> {t("Apply to all")}
            </button>
            <button
              type="button"
              onClick={onApproveAll}
              disabled={busy || readyToApprove === 0}
              title={readyToApprove === 0 ? t("No records ready to approve.") : ""}
              className="inline-flex items-center gap-2 rounded-md bg-emerald-700 text-white px-4 py-2 text-sm font-semibold hover:bg-emerald-800 disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="batch-approve-all"
            >
              <CheckCircle2 className="w-3.5 h-3.5" /> {t("Approve all ready ({n})").replace("{n}", String(readyToApprove))}
            </button>
            <button
              type="button"
              onClick={load}
              disabled={busy}
              className="ml-auto inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
              data-testid="batch-detail-refresh"
            >
              <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
            </button>
          </div>
        </section>

        {/* Records list */}
        <section className="rounded-xl border-2 border-slate-300 bg-white overflow-hidden"
                 data-testid="batch-detail-records">
          <div className="p-3 border-b border-slate-200 font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Records in this batch")} · {records.length}
          </div>
          {records.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-500" data-testid="batch-detail-empty">
              {t("No files yet. Upload some to get started.")}
            </div>
          ) : (
            <ul className="divide-y divide-slate-200">
              {records.map((r) => (
                <li key={r.id} className="p-3 flex items-start gap-3" data-testid={`batch-record-${r.id}`}>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-slate-900 truncate">
                        {(r.record_type || t("(unclassified)")).replace(/_/g, " ")}
                      </span>
                      <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-widest ${STATE_STYLE[r.approval_status] || ""}`}>
                        {r.approval_status?.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="mt-0.5 text-xs text-slate-600 flex flex-wrap gap-x-3">
                      <span className="font-mono text-[11px]">{r.source_file_name || "—"}</span>
                      {r.employee_name_snapshot ? (
                        <span className="inline-flex items-center gap-1">
                          <UserCheck className="w-3 h-3 text-emerald-600" /> {r.employee_name_snapshot}
                        </span>
                      ) : (
                        <span className="text-amber-800">{t("(no employee yet)")}</span>
                      )}
                      {r.effective_date && <span>{t("Eff")}: {r.effective_date.slice(0, 10)}</span>}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/hr/historical-records/queue`)}
                    className="text-[11px] font-semibold text-slate-600 hover:text-slate-900 shrink-0 inline-flex items-center gap-1"
                    data-testid={`batch-record-open-${r.id}`}
                  >
                    {t("Review")} <ChevronRight className="w-3 h-3" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function StatChip({ label, value, tone = "slate" }) {
  const tones = {
    slate:   "bg-slate-100 text-slate-800 border-slate-300",
    amber:   "bg-amber-100 text-amber-900 border-amber-300",
    yellow:  "bg-yellow-100 text-yellow-900 border-yellow-300",
    emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
    red:     "bg-red-100 text-red-900 border-red-300",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-semibold ${tones[tone]}`}>
      <span className="font-mono uppercase tracking-widest text-[9px] opacity-70">{label}</span>
      <span>{value}</span>
    </span>
  );
}
