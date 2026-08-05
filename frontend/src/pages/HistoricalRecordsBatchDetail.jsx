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
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";
import HrPageShell from "@/components/HrPageShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const LANE_LABEL = {
  hr: "HR", safety: "Safety", asset: "Asset", corporate_import: "Corporate Import",
};

const STATE_STYLE = {
  pending_classification: "bg-amber-100 text-amber-900 border-amber-300",
  pending_match: "bg-amber-100 text-amber-900 border-amber-300",
  pending_approval: "bg-yellow-100 text-yellow-900 border-yellow-300",
  linked: "bg-emerald-100 text-emerald-900 border-emerald-300",
  rejected: "bg-red-100 text-red-900 border-red-300",
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

  const [applyType, setApplyType] = useState("");
  const [applyEmpId, setApplyEmpId] = useState("");
  const [applyEmpName, setApplyEmpName] = useState("");
  const [applyDate, setApplyDate] = useState("");

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const result = await fetchBatch(batchId);
      setBatch(result.batch);
      setRecords(result.records || []);
      setCounts(result.counts || {});
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
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
      const result = await batchUpload(batchId, Array.from(fileList));
      toast.success(t("Uploaded {n} file(s)").replace("{n}", String(result.created || 0)));
      await load();
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
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
      const result = await batchApply(batchId, patch);
      toast.success(t("Applied to {n} record(s).").replace("{n}", String(result.modified || 0)));
      await load();
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const onApproveAll = async () => {
    setBusy(true);
    try {
      const result = await batchApproveAll(batchId);
      toast.success(t("Approved {n} record(s).").replace("{n}", String(result.approved || 0)));
      await load();
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const readyToApprove = counts.pending_approval || 0;
  const stillSorting = (counts.pending_classification || 0) + (counts.pending_match || 0);

  if (!batch) {
    return (
      <HrPageShell title="Record intake session" kicker="HR · Historical record review">
        <Card className="mx-auto max-w-3xl" data-testid="historical-records-batch-detail">
          <CardContent className="flex min-h-[14rem] items-center justify-center text-slate-500">
            <div className="font-mono text-sm" data-testid="batch-detail-loading">{t("Loading session…")}</div>
          </CardContent>
        </Card>
      </HrPageShell>
    );
  }

  return (
    <HrPageShell title="Record intake session" kicker="HR · Historical record review">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6" data-testid="historical-records-batch-detail">
        <Card data-testid="batch-detail-header">
          <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-3">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Session")} · {LANE_LABEL[batch.ownership_lane]} · #{batch.id.slice(0, 8)}
              </div>
              <CardTitle>{sanitizeOperatorReference(batch.label, t("(unlabeled session)")) || t("(unlabeled session)")}</CardTitle>
              <CardDescription className="max-w-3xl">
                {t("Keep every file in one review lane, assign it to the right employee record, and approve the set with a clear source trail.")}
              </CardDescription>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <StatChip label={t("Files")} value={batch.file_count ?? 0} />
                <StatChip label={t("Records")} value={batch.record_count ?? 0} />
                <StatChip label={t("Still sorting")} value={stillSorting} tone="amber" />
                <StatChip label={t("Ready")} value={readyToApprove} tone="yellow" />
                <StatChip label={t("Approved")} value={counts.linked || 0} tone="emerald" />
                <StatChip label={t("Rejected")} value={counts.rejected || 0} tone="red" />
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={() => navigate("/hr/historical-records/batches")} data-testid="batch-detail-back">
                <ArrowLeft className="h-4 w-4" /> {t("All sessions")}
              </Button>
              <Button type="button" variant="secondary" onClick={() => navigate("/hr/historical-records/queue")} data-testid="batch-detail-open-queue">
                <Inbox className="h-4 w-4" /> {t("Open review queue")}
              </Button>
            </div>
          </CardHeader>
          {(batch.source_name || batch.source_type || batch.source_location) ? (
            <CardContent className="pt-0">
              <div className="rounded-[1.4rem] border border-dashed border-[color:var(--border-hairline)] bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-slate-700" data-testid="batch-detail-provenance">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Source trail")}</div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {batch.source_name ? <span className="font-semibold">{sanitizeOperatorReference(batch.source_name, batch.source_name)}</span> : null}
                  {batch.source_type ? <span className="text-slate-500">· {sanitizeOperatorReference(batch.source_type, batch.source_type)}</span> : null}
                  {batch.source_location ? <span className="text-slate-500">· {sanitizeOperatorReference(batch.source_location, batch.source_location)}</span> : null}
                </div>
                <div className="mt-2 text-xs text-slate-500">{t("Every file in this session keeps the same source trail for the review team.")}</div>
              </div>
            </CardContent>
          ) : null}
        </Card>

        <section className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
          <Card className="border-dashed" data-testid="batch-detail-upload">
            <CardHeader>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Add files")}</div>
              <CardTitle>{t("Drop the next set of records into this session")}</CardTitle>
              <CardDescription>{t("Each file lands here first so the team can sort it, match it, and approve it before it becomes part of the employee record.")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-0">
              <Button type="button" asChild data-testid="batch-upload-cta">
                <label htmlFor="batch-file-input" className="cursor-pointer">
                  <Upload className="h-4 w-4" />
                  {uploading ? t("Uploading…") : t("Upload files to this session")}
                </label>
              </Button>
              <p className="text-sm text-slate-600">
                {t("Select many files at once. Each file will wait here until someone assigns it to the right employee record.")}
              </p>
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
            </CardContent>
          </Card>

          <Card data-testid="batch-detail-apply">
            <CardHeader>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Bulk update")}</div>
              <CardTitle>{t("Set shared record details before final review")}</CardTitle>
              <CardDescription>{t("Use this only for details that should be applied across every file that is still waiting in this session.")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-0">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="batch-apply-type" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Record type")}</label>
                  <select
                    id="batch-apply-type"
                    value={applyType}
                    onChange={(e) => setApplyType(e.target.value)}
                    className="wp17-focus-ring mt-1 flex h-[3rem] w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 text-sm text-[color:var(--ink-strong)]"
                    data-testid="batch-apply-type"
                  >
                    <option value="">{t("(leave)")}</option>
                    {recordTypeOptions.map((rt) => (
                      <option key={rt} value={rt}>{rt.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="batch-apply-date" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Effective date")}</label>
                  <Input
                    id="batch-apply-date"
                    type="date"
                    value={applyDate}
                    onChange={(e) => setApplyDate(e.target.value)}
                    className="mt-1"
                    data-testid="batch-apply-date"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Employee")}</label>
                  <div className="mt-1" data-testid="batch-apply-employee-wrap">
                    <EmployeeCombo
                      value={applyEmpName}
                      onChange={(value) => setApplyEmpName(value)}
                      onPick={(emp) => {
                        setApplyEmpId(emp?.id || "");
                        setApplyEmpName(emp?.name || "");
                      }}
                      testId="batch-apply-employee"
                    />
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button type="button" onClick={onBulkApply} disabled={busy} data-testid="batch-apply-submit">
                  <Layers className="h-4 w-4" /> {t("Apply to all waiting files")}
                </Button>
                <Button type="button" variant="secondary" onClick={onApproveAll} disabled={busy || readyToApprove === 0} title={readyToApprove === 0 ? t("No records ready to approve.") : ""} data-testid="batch-approve-all">
                  <CheckCircle2 className="h-4 w-4" /> {t("Approve all ready ({n})").replace("{n}", String(readyToApprove))}
                </Button>
                <Button type="button" variant="ghost" onClick={load} disabled={busy} data-testid="batch-detail-refresh">
                  <RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>

        <Card data-testid="batch-detail-records">
          <CardHeader>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Files waiting in this session")} · {records.length}</div>
            <CardTitle>{t("Review list")}</CardTitle>
            <CardDescription>{t("Open each file from here when it needs a closer review before approval.")}</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            {records.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center text-sm text-slate-500" data-testid="batch-detail-empty">
                {t("No files in this session yet. Upload the next set to get started.")}
              </div>
            ) : (
              <ul className="space-y-3">
                {records.map((record) => (
                  <li key={record.id} className="rounded-[1.5rem] border border-[color:var(--border-hairline)] bg-white/90 p-4 shadow-sm" data-testid={`batch-record-${record.id}`}>
                    <div className="flex items-start gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="truncate text-sm font-semibold text-slate-900">
                            {(record.record_type || t("(unclassified)")).replace(/_/g, " ")}
                          </span>
                          <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-widest ${STATE_STYLE[record.approval_status] || ""}`}>
                            {record.approval_status?.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
                          <span className="font-mono text-[11px]">{sanitizeOperatorReference(record.source_file_name, "—") || "—"}</span>
                          {record.employee_name_snapshot ? (
                            <span className="inline-flex items-center gap-1">
                              <UserCheck className="h-3 w-3 text-emerald-600" /> {sanitizeOperatorReference(record.employee_name_snapshot, t("Employee record"))}
                            </span>
                          ) : (
                            <span className="text-amber-800">{t("(no employee yet)")}</span>
                          )}
                          {record.effective_date ? <span>{t("Eff")}: {record.effective_date.slice(0, 10)}</span> : null}
                        </div>
                      </div>
                      <Button type="button" variant="ghost" onClick={() => navigate("/hr/historical-records/queue")} className="shrink-0" data-testid={`batch-record-open-${record.id}`}>
                        {t("Review")} <ChevronRight className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </HrPageShell>
  );
}

function StatChip({ label, value, tone = "slate" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-800 border-slate-300",
    amber: "bg-amber-100 text-amber-900 border-amber-300",
    yellow: "bg-yellow-100 text-yellow-900 border-yellow-300",
    emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
    red: "bg-red-100 text-red-900 border-red-300",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${tones[tone]}`}>
      <span className="font-mono text-[9px] uppercase tracking-widest opacity-70">{label}</span>
      <span>{value}</span>
    </span>
  );
}