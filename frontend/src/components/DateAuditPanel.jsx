import React, { useState } from "react";
import {
  CalendarClock,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  RefreshCcw,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import AdminPasswordConfirm from "@/components/AdminPasswordConfirm";

/**
 * DateAuditPanel — one-shot diagnostic + repair tool for the
 * timezone bugs fixed on 2026-05-05 (formatDateLong UTC-midnight parse +
 * the late-night UTC-rollover default-pre-fill in QA/QC inspections).
 *
 * Two buckets:
 *   - "suspects": high-confidence Bug-2 victims. We auto-suggest
 *     rolling the stored date back by one day. Each row gets an
 *     "Apply fix" button gated by AdminPasswordConfirm.
 *   - "review": records where the stored date is >1 day from the
 *     local-ET submission date. Usually legitimate backdates; we
 *     surface them for visual review only — no auto-suggest.
 *
 * The scan is read-only and can be run as many times as you like.
 * Apply mutates a single record at a time; you can re-scan after
 * each apply to confirm the row dropped out of the suspect bucket.
 */
export default function DateAuditPanel() {
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState(null);
  const [pendingFix, setPendingFix] = useState(null);
  const [appliedIds, setAppliedIds] = useState(new Set());

  const runScan = async () => {
    setBusy(true);
    try {
      const r = await api.get("/admin/date-audit");
      setData(r.data);
      setAppliedIds(new Set());
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Scan failed");
    } finally {
      setBusy(false);
    }
  };

  const applyFix = async (row) => {
    if (!row?.suggested_date) return;
    try {
      await api.post("/admin/date-audit/apply", {
        collection: row.collection,
        record_id: row.id,
        new_date: row.suggested_date,
      });
      setAppliedIds((prev) => {
        const next = new Set(prev);
        next.add(`${row.collection}:${row.id}`);
        return next;
      });
      toast.success(
        `Fixed ${row.label} · ${row.project_name || row.id} → ${row.suggested_date}`,
      );
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Apply failed");
    }
  };

  return (
    <section
      className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-7 mb-8 shadow-sm"
      data-testid="date-audit-panel"
    >
      <div className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-amber-600 text-white shrink-0">
          <CalendarClock className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-bold">
            One-shot · Timezone Bug Sweep
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Date Audit
          </h2>
          <p className="text-sm text-slate-600 mt-2 max-w-3xl">
            Scans every report collection for records whose stored date doesn't
            line up with the local-ET timestamp the crew actually submitted on.
            High-confidence matches are bucketed as <strong>Suspects</strong>{" "}
            (auto-suggest a fix, gated by admin password). Off-by-many-days
            records are bucketed for <strong>Review</strong> (read-only — these
            are usually legitimate backdates).
          </p>
        </div>
        <Button
          onClick={runScan}
          disabled={busy}
          variant="outline"
          className="h-9 text-xs font-mono uppercase tracking-wide"
          data-testid="date-audit-scan-btn"
        >
          {busy ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> Scanning…
            </>
          ) : (
            <>
              <RefreshCcw className="w-3.5 h-3.5 mr-1" /> {data ? "Re-scan" : "Run scan"}
            </>
          )}
        </Button>
      </div>

      {!data && !busy && (
        <div className="text-sm text-slate-500 italic border-2 border-dashed border-slate-200 rounded p-6 text-center">
          Click <strong>Run scan</strong> above to inspect every safety, daily,
          equipment, and QA/QC report for date-field drift.
        </div>
      )}

      {data && (
        <>
          {/* Totals strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
            <Stat label="Scanned" value={data.totals?.scanned || 0} tone="slate" />
            <Stat
              label="Suspects"
              value={data.totals?.suspect || 0}
              tone={(data.totals?.suspect || 0) > 0 ? "amber" : "emerald"}
            />
            <Stat label="Review" value={data.totals?.review || 0} tone="slate" />
            <Stat label="OK" value={data.totals?.ok || 0} tone="emerald" />
          </div>

          {/* Suspects table */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-700" />
              <h3 className="font-display font-black text-slate-900">
                Suspects ({data.suspects?.length || 0})
              </h3>
            </div>
            {(!data.suspects || data.suspects.length === 0) ? (
              <div className="text-sm text-emerald-800 bg-emerald-50 border-2 border-emerald-200 rounded p-3 inline-flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                No high-confidence Bug-2 victims found. Nothing to repair.
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-200 rounded">
                <table className="w-full text-sm" data-testid="date-audit-suspects-table">
                  <thead className="bg-amber-50">
                    <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-amber-900">
                      <th className="px-3 py-2">Form</th>
                      <th className="px-3 py-2">Project</th>
                      <th className="px-3 py-2">Person</th>
                      <th className="px-3 py-2">Stored</th>
                      <th className="px-3 py-2">Suggested</th>
                      <th className="px-3 py-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.suspects.map((row) => {
                      const key = `${row.collection}:${row.id}`;
                      const applied = appliedIds.has(key);
                      return (
                        <tr
                          key={key}
                          className={`border-t border-slate-100 ${applied ? "bg-emerald-50 text-slate-500" : ""}`}
                          data-testid={`date-audit-suspect-${row.id}`}
                        >
                          <td className="px-3 py-2 font-medium text-xs">{row.label}</td>
                          <td className="px-3 py-2 text-xs">
                            {row.project_name || "—"}
                            {row.project_number ? (
                              <span className="text-slate-500"> · {row.project_number}</span>
                            ) : null}
                          </td>
                          <td className="px-3 py-2 text-xs text-slate-600">{row.person || "—"}</td>
                          <td className="px-3 py-2 font-mono text-xs">{row.stored_date}</td>
                          <td className="px-3 py-2 font-mono text-xs text-emerald-800 font-bold">
                            {row.suggested_date}
                          </td>
                          <td className="px-3 py-2 text-right">
                            {applied ? (
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-emerald-100 text-emerald-800 font-mono text-[10px] uppercase tracking-wide">
                                <CheckCircle2 className="w-3 h-3" /> Fixed
                              </span>
                            ) : (
                              <Button
                                size="sm"
                                onClick={() => setPendingFix(row)}
                                className="h-8 text-xs bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
                                data-testid={`date-audit-apply-${row.id}`}
                              >
                                Apply fix
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Review table */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Eye className="w-4 h-4 text-slate-600" />
              <h3 className="font-display font-black text-slate-900">
                Review only ({data.review?.length || 0})
              </h3>
              <span className="text-xs text-slate-500">
                — usually legitimate backdates; no fix suggested
              </span>
            </div>
            {(!data.review || data.review.length === 0) ? (
              <div className="text-sm text-slate-500 italic">No records flagged for review.</div>
            ) : (
              <div className="overflow-x-auto border border-slate-200 rounded">
                <table className="w-full text-sm" data-testid="date-audit-review-table">
                  <thead className="bg-slate-50">
                    <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
                      <th className="px-3 py-2">Form</th>
                      <th className="px-3 py-2">Project</th>
                      <th className="px-3 py-2">Person</th>
                      <th className="px-3 py-2">Stored</th>
                      <th className="px-3 py-2">Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.review.map((row) => (
                      <tr
                        key={`${row.collection}:${row.id}`}
                        className="border-t border-slate-100"
                      >
                        <td className="px-3 py-2 font-medium text-xs">{row.label}</td>
                        <td className="px-3 py-2 text-xs">
                          {row.project_name || "—"}
                          {row.project_number ? (
                            <span className="text-slate-500"> · {row.project_number}</span>
                          ) : null}
                        </td>
                        <td className="px-3 py-2 text-xs text-slate-600">{row.person || "—"}</td>
                        <td className="px-3 py-2 font-mono text-xs">{row.stored_date}</td>
                        <td className="px-3 py-2 text-xs text-slate-600">{row.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      <AdminPasswordConfirm
        open={!!pendingFix}
        onOpenChange={(o) => !o && setPendingFix(null)}
        title={pendingFix ? `Roll back ${pendingFix.label} date by 1 day?` : ""}
        description={
          pendingFix
            ? `Stored date: ${pendingFix.stored_date} → New date: ${pendingFix.suggested_date}. ${pendingFix.reason}`
            : ""
        }
        confirmLabel="Apply fix"
        destructive
        onConfirm={async () => {
          const row = pendingFix;
          setPendingFix(null);
          await applyFix(row);
        }}
        testId="date-audit-confirm"
      />
    </section>
  );
}

function Stat({ label, value, tone }) {
  const tones = {
    slate: "border-slate-200 bg-slate-50 text-slate-900",
    amber: "border-amber-300 bg-amber-50 text-amber-900",
    emerald: "border-emerald-300 bg-emerald-50 text-emerald-900",
  };
  return (
    <div className={`border-2 rounded p-3 ${tones[tone] || tones.slate}`}>
      <div className="font-mono text-[9px] uppercase tracking-[0.25em] opacity-70 font-bold">
        {label}
      </div>
      <div className="font-display text-2xl font-black leading-none mt-1">{value}</div>
    </div>
  );
}
