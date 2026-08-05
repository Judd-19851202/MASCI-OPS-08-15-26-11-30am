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
import HrPageShell from "@/components/HrPageShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPlatformTime } from "@/lib/platformTime";

const LANE_LABEL = {
  hr: "HR",
  safety: "Safety",
  asset: "Asset Administration",
  corporate_import: "Corporate Import",
};

const LANE_STYLE = {
  hr: "border-purple-300 bg-purple-50 text-purple-900",
  safety: "border-cyan-300 bg-cyan-50 text-cyan-900",
  asset: "border-orange-300 bg-orange-50 text-orange-900",
  corporate_import: "border-slate-300 bg-slate-50 text-slate-900",
};

const STATE_STYLE = {
  pending_classification: "bg-amber-100 text-amber-900 border-amber-300",
  pending_match: "bg-amber-100 text-amber-900 border-amber-300",
  pending_approval: "bg-yellow-100 text-yellow-900 border-yellow-300",
  linked: "bg-emerald-100 text-emerald-900 border-emerald-300",
  rejected: "bg-red-100 text-red-900 border-red-300",
};

const CONTROL_CLASS = "wp17-focus-ring mt-1 flex h-[3rem] w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 text-sm text-[color:var(--ink-strong)]";
const TEXTAREA_CLASS = "wp17-focus-ring mt-1 w-full rounded-[1rem] border border-red-300 bg-white px-3.5 py-2.5 text-sm text-[color:var(--ink-strong)]";

function formatDate(value) {
  if (!value) return "—";
  return formatPlatformTime(value);
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
    fetchVocabulary().then((payload) => {
      setVocab(payload);
      const first = payload?.allowed_lanes_for_actor?.[0] || "hr";
      setActiveLane(first);
    }).catch((e) => toast.error(String(e.message || e)));
  }, []);

  const load = useCallback(async () => {
    if (!activeLane) return;
    setBusy(true);
    try {
      const payload = await fetchQueue(activeLane);
      setQueue({ records: payload.records || [], count: payload.count || 0 });
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }, [activeLane]);

  useEffect(() => {
    load();
  }, [load]);

  const allowedLanes = vocab?.allowed_lanes_for_actor || [];

  return (
    <HrPageShell title="Record review queue" kicker="HR · Historical record review">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6" data-testid="historical-records-queue">
        <Card data-testid="queue-header">
          <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Historical records")} · {t("Review queue")}
              </div>
              <CardTitle>{t("Review each record before it becomes part of the permanent file")}</CardTitle>
              <CardDescription className="max-w-3xl">
                {t("Approve only the records that are linked to the right person and clearly labeled. Rejected items stay saved for history but do not appear in active employee records.")}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={() => navigate(-1)} data-testid="queue-back">
                <ArrowLeft className="h-4 w-4" /> {t("Back")}
              </Button>
              <Button type="button" variant="outline" onClick={load} disabled={busy} data-testid="queue-refresh-header">
                <RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
              </Button>
              <Button type="button" onClick={() => navigate("/hr/historical-records/intake")} data-testid="queue-open-intake">
                <FileText className="h-4 w-4" /> {t("Add record")}
              </Button>
            </div>
          </CardHeader>
        </Card>

        <Card data-testid="queue-lane-tabs">
          <CardContent className="flex flex-wrap items-center gap-2 pt-5">
            {allowedLanes.map((lane) => (
              <button
                key={lane}
                type="button"
                onClick={() => setActiveLane(lane)}
                className={`wp17-focus-ring rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors ${activeLane === lane ? LANE_STYLE[lane] : "border-transparent text-slate-700 hover:bg-slate-100"}`}
                data-testid={`queue-lane-tab-${lane}`}
              >
                {t(LANE_LABEL[lane] || lane)}
              </button>
            ))}
            <div className="ml-auto flex items-center gap-2">
              <Button type="button" variant="ghost" onClick={load} disabled={busy} data-testid="queue-refresh">
                <RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} /> {t("Refresh")}
              </Button>
              <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-mono text-slate-600" data-testid="queue-count">
                {queue.count} {t("waiting")}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-3" data-testid="queue-records">
          {queue.records.length === 0 ? (
            <Card data-testid="queue-empty">
              <CardContent className="p-10 text-center text-sm text-slate-500">
                <Inbox className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                {t("This lane is clear right now. There are no records waiting for review.")}
              </CardContent>
            </Card>
          ) : (
            queue.records.map((record) => (
              <RecordCard
                key={record.id}
                rec={record}
                vocab={vocab}
                expanded={expandId === record.id}
                onToggle={() => setExpandId((current) => (current === record.id ? null : record.id))}
                onChanged={load}
              />
            ))
          )}
        </div>
      </div>
    </HrPageShell>
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

  const canApprove = useMemo(() => Boolean(rec.employee_id && rec.record_type), [rec.employee_id, rec.record_type]);
  const availableTypes = vocab?.record_types_by_lane?.[editLane] || [];
  const fileUrl = `${process.env.REACT_APP_BACKEND_URL}/api/employee-records/records/${rec.id}/file`;

  const onApprove = async () => {
    setBusy(true);
    try {
      await approveRecord(rec.id, "");
      toast.success(t("Record approved."));
      onChanged();
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const onReject = async () => {
    if (!rejectReason.trim()) {
      toast.error(t("Reason is required to reject."));
      return;
    }
    setBusy(true);
    try {
      await rejectRecord(rec.id, rejectReason);
      toast.success(t("Record rejected."));
      setShowReject(false);
      setRejectReason("");
      onChanged();
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const onSaveEdits = async () => {
    const patch = {};
    if (editEmpId && editEmpId !== rec.employee_id) patch.employee_id = editEmpId;
    if (editType && editType !== rec.record_type) patch.record_type = editType;
    if (editLane && editLane !== rec.ownership_lane) patch.ownership_lane = editLane;
    if (Object.keys(patch).length === 0) {
      toast.info(t("No changes."));
      return;
    }
    setBusy(true);
    try {
      await reassignRecord(rec.id, patch);
      toast.success(t("Record updated."));
      onChanged();
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className={expanded ? "border-[color:var(--ink-strong)] shadow-[var(--shadow-panel)]" : ""} data-testid={`queue-record-${rec.id}`}>
      <CardContent className="pt-5">
        <button type="button" onClick={onToggle} className="w-full text-left" data-testid={`queue-record-toggle-${rec.id}`}>
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-mono uppercase tracking-widest ${LANE_STYLE[lane] || "border-slate-300 bg-slate-100 text-slate-800"}`}>
                  {LANE_LABEL[lane] || lane}
                </span>
                <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-mono uppercase tracking-widest ${STATE_STYLE[rec.approval_status] || "border-slate-300 bg-slate-100 text-slate-800"}`}>
                  {rec.approval_status.replace(/_/g, " ")}
                </span>
                <span className="text-xs font-mono text-slate-500">#{rec.id.slice(0, 8)}</span>
              </div>
              <div className="mt-2 font-display text-lg font-black text-slate-900">
                {(rec.record_type || t("(unclassified)")).replace(/_/g, " ")}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-700">
                <span className="inline-flex items-center gap-1">
                  <User className="h-3 w-3 text-slate-400" />
                  {rec.employee_name_snapshot || t("(unlinked)")}
                </span>
                {rec.source_file_name ? (
                  <span className="inline-flex items-center gap-1">
                    <FileText className="h-3 w-3 text-slate-400" />
                    <span className="font-mono text-xs">{rec.source_file_name}</span>
                  </span>
                ) : null}
                <span className="text-xs text-slate-500">{formatDate(rec.created_at)}</span>
              </div>
            </div>
            <ChevronRight className={`mt-1 h-4 w-4 shrink-0 text-slate-400 transition-transform ${expanded ? "rotate-90" : ""}`} />
          </div>
        </button>

        {expanded ? (
          <div className="mt-4 space-y-4 border-t border-slate-200 pt-4" data-testid={`queue-record-detail-${rec.id}`}>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="sm:col-span-3">
                <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Reassign employee")}</label>
                <div className="mt-1" data-testid={`queue-emp-combo-${rec.id}`}>
                  <EmployeeCombo
                    value={editEmpName}
                    onChange={(value) => setEditEmpName(value)}
                    onPick={(emp) => {
                      setEditEmpId(emp?.id || "");
                      setEditEmpName(emp?.name || "");
                    }}
                    testId={`queue-emp-picker-${rec.id}`}
                  />
                </div>
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Lane")}</label>
                <select value={editLane} onChange={(e) => setEditLane(e.target.value)} className={CONTROL_CLASS} data-testid={`queue-lane-${rec.id}`}>
                  {(vocab?.allowed_lanes_for_actor || []).map((value) => (
                    <option key={value} value={value}>{LANE_LABEL[value] || value}</option>
                  ))}
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Record type")}</label>
                <select value={editType} onChange={(e) => setEditType(e.target.value)} className={CONTROL_CLASS} data-testid={`queue-type-${rec.id}`}>
                  <option value="">{t("(pick)")}</option>
                  {availableTypes.map((rt) => (
                    <option key={rt} value={rt}>{rt.replace(/_/g, " ")}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={onSaveEdits} disabled={busy} data-testid={`queue-save-${rec.id}`}>
                <Undo2 className="h-4 w-4" /> {t("Save changes")}
              </Button>
              {rec.source_file_ref ? (
                <Button type="button" variant="outline" onClick={async () => {
                  try {
                    const response = await fetch(fileUrl, { headers: authHeaders(), redirect: "follow" });
                    if (response.redirected) {
                      window.open(response.url, "_blank", "noopener");
                      return;
                    }
                    const json = await response.json();
                    if (json.source_file_ref?.startsWith("data:")) {
                      window.open(json.source_file_ref, "_blank", "noopener");
                    } else {
                      toast.error(t("Preview unavailable."));
                    }
                  } catch {
                    toast.error(t("Preview unavailable."));
                  }
                }} data-testid={`queue-file-${rec.id}`}>
                  <FileText className="h-4 w-4" /> {t("View original")}
                </Button>
              ) : null}
              <div className="ml-auto flex flex-wrap gap-2">
                <Button type="button" variant="destructive" onClick={() => setShowReject((value) => !value)} disabled={busy} data-testid={`queue-reject-${rec.id}`}>
                  <X className="h-4 w-4" /> {t("Reject")}
                </Button>
                <Button type="button" variant="secondary" onClick={onApprove} disabled={busy || !canApprove} title={canApprove ? "" : t("Employee and record type must be set before approval.")} data-testid={`queue-approve-${rec.id}`}>
                  <CheckCircle2 className="h-4 w-4" /> {t("Approve")}
                </Button>
              </div>
            </div>

            {!canApprove ? (
              <div className="rounded-[1rem] border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900" data-testid={`queue-approval-blocked-${rec.id}`}>
                <ShieldCheck className="mr-1 inline h-3 w-3" />
                {t("Employee link and record type are both required before approval.")}
              </div>
            ) : null}

            {showReject ? (
              <div className="rounded-[1rem] border border-red-300 bg-red-50 p-3" data-testid={`queue-reject-form-${rec.id}`}>
                <label htmlFor={`reject-reason-${rec.id}`} className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-800">
                  {t("Reason for rejection")} <span className="text-red-600">*</span>
                </label>
                <textarea
                  id={`reject-reason-${rec.id}`}
                  rows={2}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className={TEXTAREA_CLASS}
                  data-testid={`queue-reject-reason-${rec.id}`}
                />
                <div className="mt-2 flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => { setShowReject(false); setRejectReason(""); }} data-testid={`queue-reject-cancel-${rec.id}`}>
                    {t("Cancel")}
                  </Button>
                  <Button type="button" variant="destructive" onClick={onReject} disabled={busy || !rejectReason.trim()} data-testid={`queue-reject-confirm-${rec.id}`}>
                    {t("Confirm rejection")}
                  </Button>
                </div>
              </div>
            ) : null}

            {rec.notes ? (
              <div className="rounded-[1rem] border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                <span className="font-mono text-[9px] uppercase tracking-widest text-slate-500">{t("Notes")}</span>
                <div>{rec.notes}</div>
              </div>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}