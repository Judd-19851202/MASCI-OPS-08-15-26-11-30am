// HR — Payroll Variance (Exact CSV diff).
// Paste an Exact payroll CSV → backend matches by employee + week and
// surfaces variance vs. supervisor-reported masci_crews hours from
// Daily Reports. Per-row approve/dispute decisions are persisted.
//
// Color codes:
//   🟢 match           — within 1 min
//   🟡 minor           — 1 min – threshold (default 15 min)
//   🔴 flag            — ≥ threshold
//   ⚫ unmatched       — no MASCI hours found for the name key
//   🟥 missing_from_payroll — MASCI hours but no Exact row
//
// Weekly cron (Sunday 18:00 UTC) emails the most recent batch to
// hrmanager@mascigc.com + jaymn.judd@mascigc.com.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Loader2, Upload, FileDown, CheckCircle2, AlertOctagon, MessageSquareWarning,
  ClipboardPaste, RefreshCcw,
} from "lucide-react";
import { api, API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import HrPageShell from "@/components/HrPageShell";
import { getHrToken } from "@/lib/hrAuth";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { HelpTipBlock } from "@/components/HelpTip";
import {
  useFormDraft, getActorId, DraftStatusPill, DraftRestorePrompt,
} from "@/lib/resiliency";

const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

const FLAG_META = {
  match:                { color: "bg-emerald-100 text-emerald-800 border-emerald-300", label: "Match" },
  minor:                { color: "bg-amber-100 text-amber-800 border-amber-300",       label: "Minor" },
  flag:                 { color: "bg-red-100 text-red-800 border-red-300",             label: "Flagged" },
  unmatched:            { color: "bg-slate-200 text-slate-700 border-slate-400",       label: "Unmatched" },
  missing_from_payroll: { color: "bg-rose-200 text-rose-900 border-rose-400",          label: "Missing in Payroll" },
};

function defaultWeekEnding() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

export default function HrPayrollVariance() {
  const { t } = useT();
  const [weekEnding, setWeekEnding] = useState(defaultWeekEnding());
  const [threshold, setThreshold] = useState(15);
  const [csvText, setCsvText] = useState("");
  const [batch, setBatch] = useState(null);
  const [recent, setRecent] = useState([]);
  const [busy, setBusy] = useState(false);
  const [loadingRecent, setLoadingRecent] = useState(true);

  const fetchRecent = useCallback(async () => {
    setLoadingRecent(true);
    try {
      const r = await api.get("/hr/payroll-variance/recent");
      setRecent(r.data?.batches || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load recent batches"));
    } finally {
      setLoadingRecent(false);
    }
  }, [t]);

  useEffect(() => { fetchRecent(); }, [fetchRecent]);

  // iter438 · Phase 31 · Pass C · draft protection for the pasted CSV
  // + threshold + week-ending. A foreman pasting a 500-line payroll
  // CSV must NEVER lose it on refresh.
  const actorId = useMemo(() => getActorId(), []);
  const draftPayload = useMemo(
    () => ({ weekEnding, threshold, csvText }),
    [weekEnding, threshold, csvText],
  );
  const {
    pendingDraft, draftStatus, restore, discard, commit,
  } = useFormDraft("hr-payroll-variance", draftPayload, actorId);

  const onRestoreDraft = useCallback(() => {
    const d = restore();
    if (!d) return;
    if (d.weekEnding) setWeekEnding(d.weekEnding);
    if (typeof d.threshold !== "undefined") setThreshold(d.threshold);
    if (typeof d.csvText === "string") setCsvText(d.csvText);
    toast.success(t("Draft restored"));
  }, [restore, t]);
  const onDiscardDraft = useCallback(() => {
    discard();
    toast.message(t("Draft discarded"));
  }, [discard, t]);

  const upload = async () => {
    if (!csvText.trim()) return toast.error(t("Paste your Exact CSV first"));
    setBusy(true);
    try {
      const r = await api.post("/hr/payroll-variance/upload", {
        week_ending: weekEnding,
        csv_text: csvText,
        threshold_minutes: Math.max(1, parseInt(threshold, 10) || 15),
        source: "exact",
      });
      setBatch(r.data.batch);
      toast.success(t("Variance batch created"));
      // iter438 · clear draft on successful upload.
      await commit();
      fetchRecent();
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Upload failed"));
    } finally {
      setBusy(false);
    }
  };

  const loadBatch = async (id) => {
    setBusy(true);
    try {
      const r = await api.get(`/hr/payroll-variance/${id}`);
      setBatch(r.data.batch);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load batch"));
    } finally {
      setBusy(false);
    }
  };

  const setDecision = async (rowIndex, decision, noteOverride) => {
    if (!batch) return;
    const note = noteOverride ?? (batch.rows[rowIndex].decision_note || "");
    try {
      const r = await api.post(`/hr/payroll-variance/${batch.id}/decision`, {
        row_index: rowIndex, decision, note,
      });
      setBatch((b) => {
        const rows = [...b.rows];
        rows[rowIndex] = r.data.row;
        return { ...b, rows };
      });
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not save decision"));
    }
  };

  const downloadCsv = async () => {
    if (!batch) return;
    try {
      const tok = getHrToken();
      const r = await fetch(`${API}/hr/payroll-variance/${batch.id}.csv`, { headers: { "X-HR-Token": tok } });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `MASCI_payroll_variance_${batch.week_ending}.csv`;
      document.body.appendChild(a); a.click(); a.remove();
    } catch {
      toast.error(t("CSV download failed"));
    }
  };

  const summary = useMemo(() => {
    if (!batch) return null;
    return {
      total: batch.total_rows,
      matched: batch.matched_rows,
      flagged: batch.flagged_rows,
      pending: (batch.rows || []).filter((r) => r.decision === "pending" && r.flag !== "match").length,
    };
  }, [batch]);

  return (
    <HrPageShell title="Payroll Variance" kicker="HR · Exact CSV Cross-Check">
      <HelpTipBlock formKey="payroll-variance" showCounter />
      {/* iter438 · Phase 31 · Pass C · calm draft restore prompt for
          the paste/upload flow. Pasted CSVs can be hundreds of lines —
          never lose them on refresh. */}
      <DraftRestorePrompt
        pendingDraft={pendingDraft}
        onRestore={onRestoreDraft}
        onDiscard={onDiscardDraft}
        testId="hr-pv-draft-restore-prompt"
      />

      {/* Upload panel */}
      <Card className="p-5 mb-6 border-2 border-purple-200 bg-purple-50/30" data-testid="hr-pv-upload-card">
        <div className="flex items-start gap-3 mb-3">
          <ClipboardPaste className="w-5 h-5 text-purple-700 mt-1" />
          <div className="flex-1">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-lg font-black">{t("Paste your Exact payroll export")}</h2>
              <DraftStatusPill status={draftStatus} testId="hr-pv-draft-pill" />
            </div>
            <p className="text-sm text-slate-600">
              {t("Paste the CSV from Exact for the week — the system matches each row to MASCI supervisor-reported hours and flags every variance above the threshold.")}
            </p>
          </div>
        </div>
        <HelpTipBlock formKey="payroll-variance.upload" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-3 mb-3">
          <div className="min-w-0">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Week Ending")}</Label>
            <Input type="date" value={weekEnding} onChange={(e) => setWeekEnding(e.target.value)} className={`${inputCls} w-full`} data-testid="hr-pv-week" />
          </div>
          <div className="min-w-0">
            <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Threshold (minutes)")}</Label>
            <Input type="number" min="1" max="120" value={threshold} onChange={(e) => setThreshold(e.target.value)} className={`${inputCls} w-full`} data-testid="hr-pv-threshold" />
          </div>
          <div className="min-w-0 sm:col-span-2 xl:col-span-2 flex items-end justify-end gap-2">
            <Button variant="outline" onClick={() => setCsvText("")} disabled={busy || !csvText}>{t("Clear")}</Button>
            <Button onClick={upload} disabled={busy || !csvText.trim()} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-pv-upload">
              {busy ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Upload className="w-4 h-4 mr-1" />}
              {t("Run Variance")}
            </Button>
          </div>
        </div>
        <Textarea
          value={csvText}
          onChange={(e) => setCsvText(e.target.value)}
          placeholder={t("Employee Name,Employee ID,Regular Hours,Overtime Hours,Total Hours\nJohn Smith,E1001,40,2.5,42.5\n...")}
          rows={6}
          className="font-mono text-xs border-2 border-slate-300"
          data-testid="hr-pv-textarea"
        />
        <p className="text-xs text-slate-500 mt-2">
          {t("Accepted columns: Employee Name (required), Regular Hours OR Total Hours (required), Overtime Hours, Employee ID, Week Ending. Comma, tab, or pipe-delimited.")}
        </p>
      </Card>

      {/* Recent batches */}
      <Card className="p-4 mb-6 border-2 border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-display text-sm font-black uppercase tracking-wider">{t("Recent Variance Batches")}</h3>
          <Button size="sm" variant="outline" onClick={fetchRecent} disabled={loadingRecent}>
            {loadingRecent ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
          </Button>
        </div>
        <HelpTipBlock formKey="payroll-variance.batches" />
        {recent.length === 0 ? (
          <div className="text-sm text-slate-500 py-3 text-center" data-testid="hr-pv-recent-empty">
            {t("No variance batches yet. Paste a CSV above to create the first one.")}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-left px-3 py-2">{t("Week Ending")}</th>
                  <th className="text-left px-3 py-2">{t("Created")}</th>
                  <th className="text-right px-3 py-2">{t("Total")}</th>
                  <th className="text-right px-3 py-2">{t("Matched")}</th>
                  <th className="text-right px-3 py-2">{t("Flagged")}</th>
                  <th className="text-right px-3 py-2">{t("Actions")}</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((b) => (
                  <tr key={b.id} className={`border-t border-slate-100 hover:bg-slate-50 ${batch?.id === b.id ? "bg-purple-50" : ""}`}>
                    <td className="px-3 py-2 font-mono">{b.week_ending}</td>
                    <td className="px-3 py-2 text-slate-600 font-mono text-xs">{(b.created_at || "").slice(0, 16).replace("T", " ")}</td>
                    <td className="px-3 py-2 text-right">{b.total_rows}</td>
                    <td className="px-3 py-2 text-right text-emerald-700">{b.matched_rows}</td>
                    <td className={`px-3 py-2 text-right font-bold ${b.flagged_rows > 0 ? "text-red-700" : "text-slate-500"}`}>{b.flagged_rows}</td>
                    <td className="px-3 py-2 text-right">
                      <Button size="sm" variant="outline" onClick={() => loadBatch(b.id)} className="h-7 text-xs" data-testid={`hr-pv-load-${b.id}`}>
                        {t("Open")}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Active batch detail */}
      {batch && (
        <Card className="overflow-hidden border-2 border-purple-300" data-testid="hr-pv-batch-card">
          <div className="bg-purple-700 text-white px-5 py-3 flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] opacity-80">{t("Active Batch · Week Ending")}</div>
              <div className="font-display text-lg font-black">{batch.week_ending}</div>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={downloadCsv} className="bg-white" data-testid="variance-csv-download">
                <FileDown className="w-4 h-4 mr-1" /> {t("Download CSV")}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-3 p-4 bg-slate-50 border-b border-slate-200">
            <Stat label={t("Total")} value={summary.total} />
            <Stat label={t("Matched")} value={summary.matched} cls="text-emerald-700" />
            <Stat label={t("Flagged")} value={summary.flagged} cls={summary.flagged > 0 ? "text-red-700" : ""} />
            <Stat label={t("Pending Review")} value={summary.pending} cls={summary.pending > 0 ? "text-amber-700" : ""} />
          </div>

          <div className="px-4 pt-4">
            <HelpTipBlock formKey="payroll-variance.row-decision" />
            <HelpTipBlock formKey="payroll-variance.dispute" />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-left px-3 py-2">{t("Employee")}</th>
                  <th className="text-right px-3 py-2">{t("Exact Reg")}</th>
                  <th className="text-right px-3 py-2">{t("Exact OT")}</th>
                  <th className="text-right px-3 py-2">{t("Exact Total")}</th>
                  <th className="text-right px-3 py-2">{t("MASCI Total")}</th>
                  <th className="text-right px-3 py-2">{t("Diff")}</th>
                  <th className="text-center px-3 py-2">{t("Flag")}</th>
                  <th className="text-center px-3 py-2">{t("Decision")}</th>
                </tr>
              </thead>
              <tbody>
                {batch.rows.map((r) => {
                  const meta = FLAG_META[r.flag] || FLAG_META.match;
                  return (
                    <tr key={r.row_index} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`hr-pv-row-${r.row_index}`}>
                      <td className="px-3 py-2">
                        <div className="font-semibold">{r.employee_name}</div>
                        {(r.masci_jobs || []).length > 0 && (
                          <div className="text-xs text-slate-500 font-mono">{r.masci_jobs.join(", ")}</div>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right font-mono">{r.exact_regular.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-mono">{r.exact_overtime.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-mono font-bold">{r.exact_total.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-mono">{r.masci_total.toFixed(2)}</td>
                      <td className={`px-3 py-2 text-right font-mono font-bold ${Math.abs(r.diff_minutes) >= batch.threshold_minutes ? "text-red-700" : Math.abs(r.diff_minutes) >= 1 ? "text-amber-700" : "text-emerald-700"}`}>
                        {r.diff_hours >= 0 ? "+" : ""}{r.diff_hours.toFixed(2)}
                        <div className="text-[10px] text-slate-500 font-normal">{r.diff_minutes.toFixed(0)} min</div>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${meta.color}`}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <DecisionButtons
                          row={r}
                          onDecide={(decision) => setDecision(r.row_index, decision)}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </HrPageShell>
  );
}

function Stat({ label, value, cls }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">{label}</div>
      <div className={`font-display text-xl font-black ${cls || ""}`}>{value ?? 0}</div>
    </div>
  );
}

function DecisionButtons({ row, onDecide }) {
  const { t } = useT();
  const decision = row.decision || "pending";
  return (
    <div className="inline-flex flex-col gap-1 items-center">
      <div className="inline-flex gap-1">
        <Button
          size="sm"
          variant={decision === "approve" ? "default" : "outline"}
          className={`h-7 px-2 ${decision === "approve" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}`}
          onClick={() => onDecide("approve")}
          data-testid={`hr-pv-approve-${row.row_index}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span className="ml-1 text-xs">{t("Approve")}</span>
        </Button>
        <Button
          size="sm"
          variant={decision === "dispute" ? "default" : "outline"}
          className={`h-7 px-2 ${decision === "dispute" ? "bg-red-600 hover:bg-red-700 text-white" : ""}`}
          onClick={() => onDecide("dispute")}
          data-testid={`hr-pv-dispute-${row.row_index}`}
        >
          <AlertOctagon className="w-3.5 h-3.5" />
          <span className="ml-1 text-xs">{t("Dispute")}</span>
        </Button>
      </div>
      {decision === "dispute" && row.decision_note && (
        <div className="text-[10px] text-slate-600 italic flex items-start gap-1 max-w-[160px] text-left">
          <MessageSquareWarning className="w-3 h-3 mt-0.5 shrink-0" />
          {row.decision_note}
        </div>
      )}
    </div>
  );
}
