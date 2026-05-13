// AdminBackupVerificationPanel — admin tool for the weekly R2 backup
// verification cron (iter79). Shows:
//   - whether the cron is enabled + next scheduled fire
//   - recipients
//   - last-run timestamp + verdict
//   - a "Preview" button (build report, don't email)
//   - a "Run Now" button (build + email immediately)
//
// Endpoints: /api/admin/backup-verification/{state,preview,run-now}

import React, { useEffect, useState } from "react";
import {
  ShieldCheck, Loader2, MailCheck, Eye, CalendarClock, AlertOctagon,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { toast } from "sonner";

const VERDICT_TONE = {
  pass: { color: "text-green-700", bg: "bg-green-50", border: "border-green-300", label: "HEALTHY" },
  warn: { color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-300", label: "WARNING" },
  fail: { color: "text-red-700", bg: "bg-red-50", border: "border-red-300", label: "FAILED" },
};

function fmtAge(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    const hrs = (Date.now() - d.getTime()) / 36e5;
    if (hrs < 1) return `${Math.round(hrs * 60)}m ago`;
    if (hrs < 24) return `${hrs.toFixed(1)}h ago`;
    return `${(hrs / 24).toFixed(1)}d ago`;
  } catch { return "—"; }
}

function fmtNext(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      weekday: "short", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit", timeZoneName: "short",
    });
  } catch { return "—"; }
}

export default function AdminBackupVerificationPanel() {
  const [state, setState] = useState(null);
  const [report, setReport] = useState(null);
  const [loadingState, setLoadingState] = useState(true);
  const [previewing, setPreviewing] = useState(false);
  const [sending, setSending] = useState(false);

  const refresh = async () => {
    setLoadingState(true);
    try {
      const r = await api.get("/admin/backup-verification/state");
      setState(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load verification state");
    } finally {
      setLoadingState(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const handlePreview = async () => {
    setPreviewing(true);
    try {
      const r = await api.get("/admin/backup-verification/preview");
      setReport(r.data?.report || null);
      const v = r.data?.report?.verdict;
      if (v === "pass") toast.success("Verification report built — system healthy");
      else if (v === "warn") toast.warning("Verification report built — warnings detected");
      else if (v === "fail") toast.error("Verification report built — failures detected");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  const handleRunNow = async () => {
    if (!window.confirm(
      "Send the backup verification email to:\n\n" +
      ((state?.recipients || []).join("\n") || "(no recipients configured)") +
      "\n\nProceed?"
    )) return;
    setSending(true);
    try {
      const r = await api.post("/admin/backup-verification/run-now", {});
      setReport(r.data?.report || null);
      if (r.data?.sent) {
        toast.success(`Sent to ${(r.data.recipients || []).join(", ")}`);
        refresh();
      } else {
        toast.error(r.data?.error || "Send failed");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Run-now failed");
    } finally {
      setSending(false);
    }
  };

  const verdict = report?.verdict;
  const tone = verdict ? VERDICT_TONE[verdict] : null;
  const r2 = report?.r2 || {};
  const ledger = report?.ledger || {};
  const issues = [...(r2.issues || []), ...(ledger.issues || [])];

  return (
    <Card
      className="p-5 sm:p-6 mt-4 border-2 border-slate-300 bg-white"
      data-testid="backup-verification-panel"
    >
      <div className="flex items-start justify-between gap-3 mb-3 flex-wrap">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-md bg-slate-900">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-display text-lg font-black tracking-tight text-slate-900">
              Backup Verification Cron
            </h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Weekly automated email that confirms your Cloudflare R2 backup
              archive is alive, recent, and well-sized. Catches the case where
              the backend thinks it backed up but R2 actually rejected the
              upload — gives you a positive heartbeat instead of only firing
              when something breaks.
            </p>
          </div>
        </div>
        <div className="text-xs font-mono tracking-[0.15em] uppercase text-slate-500">
          ITER79
        </div>
      </div>

      {loadingState ? (
        <div className="flex items-center gap-2 text-slate-600 py-3">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading cron state…
        </div>
      ) : state ? (
        <div className="grid sm:grid-cols-2 gap-3 mb-4">
          <div className="border border-slate-200 rounded-md p-3 bg-slate-50">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold flex items-center gap-1">
              <CalendarClock className="w-3 h-3" /> Schedule
            </div>
            <div className="text-sm text-slate-900 mt-1">
              {state.enabled ? (
                <>
                  <strong>{state.schedule.day_label}</strong> at{" "}
                  <strong>{String(state.schedule.hour_utc).padStart(2, "0")}:00 UTC</strong>
                </>
              ) : (
                <span className="text-slate-500 italic">Cron disabled</span>
              )}
            </div>
            <div className="text-xs text-slate-600 mt-1">
              Next: <code className="text-[11px]">{fmtNext(state.next_fire_iso)}</code>
            </div>
          </div>

          <div className="border border-slate-200 rounded-md p-3 bg-slate-50">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold flex items-center gap-1">
              <MailCheck className="w-3 h-3" /> Recipients · Last Run
            </div>
            <div className="text-sm text-slate-900 mt-1 truncate" title={(state.recipients || []).join(", ")}>
              {state.recipients?.length
                ? state.recipients.join(", ")
                : <span className="text-amber-700 italic">None configured</span>}
            </div>
            <div className="text-xs text-slate-600 mt-1">
              Last sent: <strong>{fmtAge(state.last_run_iso)}</strong>
              {state.last_was_manual ? " (manual)" : ""}
            </div>
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2 mb-4">
        <Button
          onClick={handlePreview}
          disabled={previewing}
          variant="outline"
          className="border-slate-400"
          data-testid="bv-preview-btn"
        >
          {previewing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Eye className="w-4 h-4 mr-2" />}
          Preview Report
        </Button>
        <Button
          onClick={handleRunNow}
          disabled={sending || !state?.recipients?.length}
          className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
          data-testid="bv-run-now-btn"
        >
          {sending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <MailCheck className="w-4 h-4 mr-2" />}
          Send Verification Now
        </Button>
      </div>

      {report && (
        <div
          className={`rounded-md border-2 p-4 ${tone?.bg} ${tone?.border}`}
          data-testid="bv-report-preview"
        >
          <div className="flex items-center gap-2 mb-2">
            {verdict === "pass" ? (
              <CheckCircle2 className={`w-5 h-5 ${tone?.color}`} />
            ) : (
              <AlertOctagon className={`w-5 h-5 ${tone?.color}`} />
            )}
            <div className={`font-display text-lg font-black ${tone?.color}`}>
              {tone?.label}
            </div>
            <div className="ml-auto text-xs font-mono text-slate-500 tracking-wider uppercase">
              {report.ts ? new Date(report.ts).toLocaleString() : ""}
            </div>
          </div>

          {issues.length > 0 && (
            <ul className="mb-3 text-sm text-red-800 space-y-1 list-disc list-inside">
              {issues.map((i, idx) => (
                <li key={idx}>{i}</li>
              ))}
            </ul>
          )}

          <div className="grid sm:grid-cols-3 gap-3 text-sm">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">R2 Archives</div>
              <div className="text-slate-900 mt-1">
                <strong>{r2.archive_count ?? 0}</strong> archives ·{" "}
                <strong>{r2.total_size_human || "0 B"}</strong>
              </div>
              <div className="text-xs text-slate-600">
                Newest: {r2.newest_age_hrs != null ? `${r2.newest_age_hrs.toFixed(1)}h ago` : "—"}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Local Ledger</div>
              <div className="text-slate-900 mt-1 capitalize">
                Status: <strong>{ledger.status || "—"}</strong>
              </div>
              <div className="text-xs text-slate-600">
                Last full: {ledger?.last_full?.ts ? fmtAge(ledger.last_full.ts) : "—"}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Records</div>
              <div className="text-slate-900 mt-1">
                <strong>{(report.data?.total_records || 0).toLocaleString()}</strong> total
              </div>
              <div className="text-xs text-slate-600">
                {Object.keys(report.data?.per_collection_counts || {}).length} collections
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
