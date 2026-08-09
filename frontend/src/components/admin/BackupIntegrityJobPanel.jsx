import React, { useEffect, useState } from "react";
import { CheckCircle2, Loader2, RefreshCcw, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { formatPlatformTime } from "@/lib/platformTime";

const STATE_STYLES = {
  completed: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  running: "bg-sky-100 text-sky-800 ring-sky-200",
  queued: "bg-amber-100 text-amber-900 ring-amber-200",
  failed: "bg-rose-100 text-rose-800 ring-rose-200",
};

export function BackupIntegrityJobPanel({ testIdPrefix = "backup-integrity" }) {
  const [integrityState, setIntegrityState] = useState(null);
  const [integrityLoading, setIntegrityLoading] = useState(false);
  const [integrityStarting, setIntegrityStarting] = useState(false);

  const refreshIntegrity = async () => {
    setIntegrityLoading(true);
    try {
      const [statusRes, latestRes] = await Promise.allSettled([
        api.get("/admin/backups/integrity-check/status"),
        api.get("/admin/backups/integrity-check/latest"),
      ]);
      const current = statusRes.status === "fulfilled" ? statusRes.value.data : null;
      const latest = latestRes.status === "fulfilled" ? latestRes.value.data : null;
      setIntegrityState(current || latest || null);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load integrity status"));
    } finally {
      setIntegrityLoading(false);
    }
  };

  useEffect(() => {
    refreshIntegrity();
  }, []);

  useEffect(() => {
    if (!integrityState || !["queued", "running"].includes(integrityState.state)) return undefined;
    const id = window.setInterval(refreshIntegrity, 4000);
    return () => window.clearInterval(id);
  }, [integrityState?.state]);

  const startIntegrity = async () => {
    if (integrityStarting || ["queued", "running"].includes(integrityState?.state)) return;
    setIntegrityStarting(true);
    try {
      const r = await api.post("/admin/backups/integrity-check/start");
      setIntegrityState(r.data);
      toast.success("Integrity check started.");
    } catch (e) {
      const data = e?.response?.data;
      if (e?.response?.status === 409 && data) {
        setIntegrityState(data);
        toast.info("Integrity check already running — showing current job.");
      } else {
        toast.error(operationalError(e, "Integrity check failed to start"));
      }
    } finally {
      setIntegrityStarting(false);
    }
  };

  const stateTone = STATE_STYLES[integrityState?.state] || "bg-slate-100 text-slate-700 ring-slate-200";

  return (
    <section
      className="rounded-[var(--radius-card)] border border-sky-200 bg-white p-4 shadow-sm"
      data-testid={`${testIdPrefix}-root`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-sky-700 font-bold">
            Backup integrity
          </div>
          <h3 className="mt-1 font-display text-lg font-black tracking-tight text-slate-900">
            Manifest verification belongs in Storage & Recovery.
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            This job validates the backup manifests and recovery evidence without claiming PASS until the
            asynchronous check fully completes.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={refreshIntegrity}
            disabled={integrityLoading}
            data-testid={`${testIdPrefix}-refresh`}
          >
            {integrityLoading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5 mr-1" />}
            Refresh
          </Button>
          <Button
            onClick={startIntegrity}
            disabled={integrityStarting || ["queued", "running"].includes(integrityState?.state)}
            data-testid={`${testIdPrefix}-start`}
          >
            {(integrityStarting || ["queued", "running"].includes(integrityState?.state)) ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Running…</> : <>Start integrity check</>}
          </Button>
        </div>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="rounded-[var(--radius-card)] border border-slate-200 bg-slate-50 p-4" data-testid={`${testIdPrefix}-status-card`}>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-widest ring-1 ${stateTone}`} data-testid={`${testIdPrefix}-state`}>
              {integrityState?.state || "never run"}
            </span>
            {integrityState?.integrity_result ? (
              <span className="text-xs font-semibold text-slate-700" data-testid={`${testIdPrefix}-result`}>
                {integrityState.integrity_result}
              </span>
            ) : null}
          </div>

          <dl className="mt-3 grid gap-2 text-xs text-slate-700 sm:grid-cols-2">
            <div>
              <dt className="font-mono uppercase tracking-wide text-slate-500">Job ID</dt>
              <dd data-testid={`${testIdPrefix}-job-id`}>{integrityState?.job_id || "—"}</dd>
            </div>
            <div>
              <dt className="font-mono uppercase tracking-wide text-slate-500">Manifest count</dt>
              <dd data-testid={`${testIdPrefix}-manifest-count`}>{integrityState?.manifest_count_evaluated ?? "—"}</dd>
            </div>
            <div>
              <dt className="font-mono uppercase tracking-wide text-slate-500">Started</dt>
              <dd data-testid={`${testIdPrefix}-started-at`}>{formatPlatformTime(integrityState?.started_at || integrityState?.created_at)}</dd>
            </div>
            <div>
              <dt className="font-mono uppercase tracking-wide text-slate-500">Completed</dt>
              <dd data-testid={`${testIdPrefix}-completed-at`}>{formatPlatformTime(integrityState?.completed_at)}</dd>
            </div>
            <div>
              <dt className="font-mono uppercase tracking-wide text-slate-500">Duration</dt>
              <dd data-testid={`${testIdPrefix}-duration`}>{integrityState?.duration_s != null ? `${integrityState.duration_s}s` : "—"}</dd>
            </div>
            <div>
              <dt className="font-mono uppercase tracking-wide text-slate-500">Classification</dt>
              <dd data-testid={`${testIdPrefix}-classification`}>{integrityState?.classification || "—"}</dd>
            </div>
          </dl>

          {integrityState?.error ? (
            <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800" data-testid={`${testIdPrefix}-error`}>
              <strong>Failure:</strong> {integrityState.error}
            </div>
          ) : null}
        </div>

        <div className="rounded-[var(--radius-card)] border border-slate-200 bg-slate-50 p-4" data-testid={`${testIdPrefix}-guidance`}>
          <div className="flex items-start gap-2 text-slate-700">
            <ShieldAlert className="mt-0.5 h-4 w-4 text-sky-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">Truth rule</div>
              <p className="mt-1 text-xs leading-relaxed">
                A queued or running job is pending evidence only. Recovery posture should stay ATTENTION or
                CRITICAL until the completed job proves integrity.
              </p>
            </div>
          </div>
          {integrityState?.state === "completed" ? (
            <div className="mt-3 flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
              <CheckCircle2 className="mt-0.5 h-4 w-4" />
              <span>Completed jobs can inform Storage & Recovery evidence, but they do not upgrade unrelated readiness claims.</span>
            </div>
          ) : (
            <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900" data-testid={`${testIdPrefix}-pending-note`}>
              PASS/FAIL is not final until the job reaches <strong>completed</strong>.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
