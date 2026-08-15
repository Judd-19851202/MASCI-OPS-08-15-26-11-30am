// MOTIVE-DATA-002A · Asset Mapping Admin Center.
// MOTIVE-DATA-003 · Operational Impact Command Card added at top.
// Single operational workspace. Read-mostly · approve/reject only.
import React, { useEffect, useState, useCallback, useMemo, useRef } from "react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { RefreshCw, Loader2, CheckCircle2, XCircle, Activity, TrendingUp, BookOpen, Target, AlertTriangle } from "lucide-react";

const BAND = {
  HIGH:    "bg-emerald-50 border-emerald-400 text-emerald-900",
  MEDIUM:  "bg-amber-50 border-amber-400 text-amber-900",
  LOW:     "bg-red-50 border-red-300 text-red-800",
  UNKNOWN: "bg-slate-50 border-slate-200 text-slate-700",
};

// Unavailable-as-zero guard for percentage stats: a null/undefined score
// reads as an em dash, never a hard "0%"/"null%"/"undefined%".
const pctOr = (v) => (v != null && Number.isFinite(Number(v)) ? `${Number(v)}%` : "—");


const READINESS = {
  READY_FOR_ACTIVATION: {
    label: "READY FOR ACTIVATION",
    cls: "bg-emerald-50 border-emerald-500 text-emerald-900",
    dot: "bg-emerald-600",
  },
  PARTIALLY_READY: {
    label: "PARTIALLY READY",
    cls: "bg-amber-50 border-amber-500 text-amber-900",
    dot: "bg-amber-500",
  },
  NOT_READY: {
    label: "NOT READY",
    cls: "bg-red-50 border-red-400 text-red-900",
    dot: "bg-red-600",
  },
};

export default function AdminAssetMapping() {
  const [coverage, setCoverage] = useState(null);
  const [audit, setAudit] = useState(null);
  const [exec, setExec] = useState(null);
  const [impact, setImpact] = useState(null);
  const [topUnmapped, setTopUnmapped] = useState([]);
  const [queue, setQueue] = useState([]);
  const [counts, setCounts] = useState({});
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);
  const [bandFilter, setBandFilter] = useState("ALL"); // MOTIVE-DATA-003 R2
  const queueRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [c, a, e, i, t, q] = await Promise.all([
          api.get("/admin/asset-mapping/coverage"),
          api.get("/admin/asset-mapping/audit"),
          api.get("/admin/executive-summary"),
          api.get("/admin/asset-mapping/operational-impact"),
          api.get("/admin/asset-mapping/top-unmapped?limit=10"),
          api.get("/admin/asset-mapping/queue"),
        ]);
        if (cancelled) return;
        setCoverage(c.data); setAudit(a.data?.answers || {});
        setExec(e.data); setImpact(i.data);
        setTopUnmapped(t.data?.rows || []);
        setQueue(q.data?.rows || []); setCounts(q.data?.counts || {});
      } catch (err) {
        if (!cancelled) toast.error(`Load failed: ${err?.response?.data?.detail || err.message}`);
      }
    })();
    return () => { cancelled = true; };
  }, [tick]);

  const runScan = useCallback(async () => {
    setBusy(true);
    try {
      const r = await api.post("/admin/asset-mapping/scan");
      const b = r.data.bands || {};
      toast.success(`Scanned ${r.data.trucks_scanned} · HIGH ${b.HIGH||0} · MED ${b.MEDIUM||0} · UNKNOWN ${b.UNKNOWN||0}`);
      setTick((t) => t + 1);
    } catch (e) { toast.error(`Scan failed: ${e?.response?.data?.detail || e.message}`); }
    finally { setBusy(false); }
  }, []);

  const approve = async (id) => {
    try { await api.post(`/admin/asset-mapping/${id}/approve`); toast.success("Approved"); setTick(t=>t+1); }
    catch (e) { toast.error(`Approve failed: ${e?.response?.data?.detail || e.message}`); }
  };
  const reject = async (id) => {
    try { await api.post(`/admin/asset-mapping/${id}/reject`); toast.success("Rejected"); setTick(t=>t+1); }
    catch (e) { toast.error(`Reject failed: ${e?.response?.data?.detail || e.message}`); }
  };
  const bulkApproveHigh = async () => {
    const ids = queue.filter(r => r.confidence_band === "HIGH" && r.status === "Matched").map(r => r.id);
    if (ids.length === 0) { toast.error("No HIGH proposals to approve"); return; }
    try {
      const r = await api.post("/admin/asset-mapping/bulk-approve", { ids });
      toast.success(`Approved ${r.data.approved_count} · skipped ${r.data.skipped_count}`);
      setTick(t=>t+1);
    } catch (e) { toast.error(`Bulk failed: ${e?.response?.data?.detail || e.message}`); }
  };

  // MOTIVE-DATA-003 R2 · Review HIGH Confidence Matches
  const reviewHigh = () => {
    setBandFilter("HIGH");
    setTimeout(() => {
      queueRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  };

  const filteredQueue = useMemo(() => {
    if (bandFilter === "ALL") return queue;
    return queue.filter(r => r.confidence_band === bandFilter);
  }, [queue, bandFilter]);

  return (
    <AdminShell title="Asset Mapping" section="command-center">
      <div className="space-y-4" data-testid="asset-mapping-page">
        <div className="rounded border-2 border-slate-300 bg-white p-4 flex items-start justify-between gap-3">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
              MOTIVE-DATA-002 · Asset Mapping Admin Center
            </div>
            <h2 className="text-xl font-black text-slate-900 mt-0.5">Single operational workspace</h2>
            <p className="text-sm text-slate-600 max-w-2xl mt-1">
              See what&apos;s mapped · what&apos;s not · what to fix first · expected operational impact.
              No automation. Operator approves every link.
            </p>
          </div>
          <Button onClick={runScan} disabled={busy} className="bg-slate-900 hover:bg-black text-white" data-testid="am-scan-btn">
            {busy ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-1" />}
            Run Scan
          </Button>
        </div>

        {/* MOTIVE-DATA-003 · Operational Impact Command Card */}
        {impact && (
          <div className="rounded border-2 border-slate-900 bg-white p-4" data-testid="am-operational-impact">
            <div className="flex items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-slate-800" />
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
                  MOTIVE-DATA-003 · Operational Impact
                </div>
              </div>
              {impact.readiness && (
                <div
                  className={`px-3 py-1 rounded border-2 font-mono text-[11px] font-black uppercase tracking-wider flex items-center gap-2 ${READINESS[impact.readiness]?.cls || ""}`}
                  data-testid="am-readiness-banner"
                  data-readiness={impact.readiness}
                >
                  <span className={`inline-block w-2 h-2 rounded-full ${READINESS[impact.readiness]?.dot}`} />
                  {READINESS[impact.readiness]?.label || impact.readiness}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="am-impact-metrics">
              <Stat l="Current Trust" v={pctOr(impact.current.trust_score_pct)} testid="am-impact-current-trust" />
              <Stat l="Potential Trust" v={pctOr(impact.potential.trust_score_pct)} testid="am-impact-potential-trust" />
              <Stat l="HIGH Matches Waiting" v={impact.actions.high_confidence_waiting} testid="am-impact-high-waiting" />
              <Stat l="Est. Dispatches Impacted" v={impact.actions.estimated_dispatches_impacted} testid="am-impact-dispatches" />
              <Stat l="Est. Assets Confirmed" v={impact.actions.estimated_assets_confirmed} testid="am-impact-assets-confirmed" />
              <Stat l="Coverage %" v={`${impact.current.coverage_pct}%`} testid="am-impact-coverage" />
              <Stat l="Mapped Assets" v={impact.current.mapped_assets} testid="am-impact-mapped" />
              <Stat l="Unmapped Assets" v={impact.current.unmapped_assets} testid="am-impact-unmapped" />
            </div>

            {/* Impact Preview Summary · current vs projected */}
            <div className="mt-3 rounded border-2 border-slate-300 bg-slate-50 p-3" data-testid="am-impact-preview">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-700 font-bold mb-2">
                If all HIGH-confidence proposals were approved
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="rounded border border-slate-300 bg-white p-2" data-testid="am-impact-current">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-slate-600 font-bold mb-1">Current State</div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <KV l="Coverage" v={`${impact.current.coverage_pct}%`} />
                    <KV l="Trust" v={pctOr(impact.current.trust_score_pct)} />
                    <KV l="Mapped" v={impact.current.mapped_assets} />
                  </div>
                </div>
                <div className="rounded border-2 border-emerald-500 bg-emerald-50 p-2" data-testid="am-impact-projected">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-emerald-800 font-bold mb-1">Projected State</div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <KV l="Coverage" v={`${impact.potential.coverage_pct}%`} accent />
                    <KV l="Trust" v={pctOr(impact.potential.trust_score_pct)} accent />
                    <KV l="Mapped" v={impact.potential.mapped_assets} accent />
                  </div>
                </div>
              </div>
              {impact.readiness_reason && (
                <div className="mt-2 text-[11px] font-mono text-slate-600" data-testid="am-impact-reason">
                  {impact.readiness_reason}
                </div>
              )}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button
                onClick={reviewHigh}
                disabled={(impact.actions.high_confidence_waiting || 0) === 0}
                className="bg-emerald-700 hover:bg-emerald-800 text-white"
                data-testid="am-review-high-btn"
              >
                <CheckCircle2 className="w-4 h-4 mr-1" />
                Review HIGH Confidence Matches ({impact.actions.high_confidence_waiting})
              </Button>
              <a
                href="https://github.com/masci-safety-hub/blob/main/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md"
                onClick={(e) => {
                  e.preventDefault();
                  toast.info("Activation Runbook: /app/memory/MOTIVE_DAY1_ACTIVATION_RUNBOOK.md");
                }}
                className="inline-flex items-center gap-1 px-3 py-2 rounded border-2 border-slate-400 text-slate-800 hover:bg-slate-50 text-sm font-bold"
                data-testid="am-runbook-link"
              >
                <BookOpen className="w-4 h-4" />
                Open Activation Runbook
              </a>
              {impact.readiness === "NOT_READY" && (
                <div className="flex items-center gap-1 text-[11px] font-mono text-red-700 ml-1" data-testid="am-not-ready-hint">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Resolve HIGH matches + map remaining trucks to lift readiness
                </div>
              )}
            </div>
          </div>
        )}

        {/* Verification Coverage tile */}
        {coverage && exec && (
          <div className="rounded border-2 border-slate-300 bg-white p-4" data-testid="am-coverage">
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
              {[
                ["Dispatch", coverage.total_dispatch_trucks],
                ["Mapped", coverage.mapped_assets],
                ["Unmapped", coverage.unmapped_assets],
                ["Coverage %", `${coverage.coverage_pct}%`],
                ["Trust Score", pctOr(exec.trust_score_pct)],
                ["Potential", pctOr(exec.potential_trust_score_pct)],
              ].map(([l, v]) => (
                <div key={l} className="px-3 py-2 rounded bg-slate-50 border border-slate-200">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-slate-700">{l}</div>
                  <div className="text-2xl font-black text-slate-900">{v}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top 10 unmapped (002C) */}
        <div className="rounded border-2 border-slate-300 bg-white p-3" data-testid="am-top-unmapped">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-slate-600" />
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
              Top 10 unmapped (highest active-dispatch volume)
            </div>
          </div>
          {topUnmapped.length === 0 ? (
            <div className="text-xs text-slate-500 px-2 py-2">No active unmapped trucks.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 font-mono text-[10px] uppercase text-slate-700 text-left">
                <tr><th className="px-2 py-1">Truck</th><th className="px-2 py-1">Active Dispatches</th><th className="px-2 py-1">Suggested</th><th className="px-2 py-1">Confidence</th><th className="px-2 py-1">Est. Verification Gain</th></tr>
              </thead>
              <tbody>
                {topUnmapped.map((r, i) => (
                  <tr key={r.truck_id} className="border-t border-slate-100" data-testid={`am-top-row-${i}`}>
                    <td className="px-2 py-1 font-mono font-bold">{r.truck_id}</td>
                    <td className="px-2 py-1 font-mono">{r.active_dispatch_count}</td>
                    <td className="px-2 py-1 text-slate-700">{r.suggested_match || "—"}</td>
                    <td className="px-2 py-1">
                      <span className={`px-1.5 py-0.5 rounded border font-mono text-[10px] font-bold ${BAND[r.confidence_band] || BAND.UNKNOWN}`}>
                        {r.confidence_band}
                      </span>
                    </td>
                    <td className="px-2 py-1 font-mono">+{r.estimated_verification_gain_dispatches}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Reconciliation queue */}
        <div ref={queueRef} className="rounded border-2 border-slate-300 bg-white p-3" data-testid="am-queue">
          <div className="flex items-center justify-between mb-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
              Reconciliation Queue · {counts.TOTAL || 0} total · HIGH {counts.HIGH || 0} · MED {counts.MEDIUM || 0} · LOW {counts.LOW || 0} · UNK {counts.UNKNOWN || 0} · Verified {counts.VERIFIED || 0} · Rejected {counts.REJECTED || 0}
            </div>
            <Button onClick={bulkApproveHigh} className="bg-emerald-700 hover:bg-emerald-800 text-white" data-testid="am-bulk-high-btn">
              <CheckCircle2 className="w-4 h-4 mr-1" />Bulk Approve HIGH
            </Button>
          </div>
          {/* MOTIVE-DATA-003 R2 · band filter chips */}
          <div className="flex flex-wrap gap-1 mb-2" data-testid="am-queue-filter">
            {["ALL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((b) => (
              <button
                key={b}
                onClick={() => setBandFilter(b)}
                data-testid={`am-queue-filter-${b}`}
                className={`px-2 py-0.5 rounded border font-mono text-[10px] font-bold ${bandFilter === b ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"}`}
              >
                {b}
              </button>
            ))}
            {bandFilter !== "ALL" && (
              <span className="text-[10px] font-mono text-slate-500 ml-1 self-center">
                showing {filteredQueue.length} of {queue.length}
              </span>
            )}
          </div>
          {filteredQueue.length === 0 ? (
            <div className="text-xs text-slate-500 px-2 py-2">{queue.length === 0 ? "Empty queue. Run \u201CRun Scan\u201D first." : "No proposals in this band."}</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 font-mono text-[10px] uppercase text-slate-700 text-left">
                <tr><th className="px-2 py-1">Truck</th><th className="px-2 py-1">Motive Asset</th><th className="px-2 py-1">Confidence</th><th className="px-2 py-1">Reason</th><th className="px-2 py-1">Status</th><th className="px-2 py-1">Action</th></tr>
              </thead>
              <tbody>
                {filteredQueue.slice(0, 50).map((r) => {
                  const terminal = r.status === "Verified" || r.status === "Rejected";
                  return (
                    <tr key={r.id} className="border-t border-slate-100" data-testid={`am-row-${r.id}`}>
                      <td className="px-2 py-1 font-mono font-bold">{r.truck_id}</td>
                      <td className="px-2 py-1 text-slate-700">{r.motive_label || "—"}</td>
                      <td className="px-2 py-1">
                        <span className={`px-1.5 py-0.5 rounded border font-mono text-[10px] font-bold ${BAND[r.confidence_band] || BAND.UNKNOWN}`}>
                          {r.confidence_band} {r.confidence_score != null ? `${(Number(r.confidence_score) * 100).toFixed(0)}%` : "—"}
                        </span>
                      </td>
                      <td className="px-2 py-1 font-mono text-[10px] text-slate-600">{r.match_signal?.kind || "—"}</td>
                      <td className="px-2 py-1 font-mono text-[10px]">{r.status}</td>
                      <td className="px-2 py-1">
                        {terminal ? <span className="text-slate-400 italic text-xs">—</span> : (
                          <div className="flex gap-1">
                            <Button size="sm" onClick={() => approve(r.id)} disabled={!r.motive_mapping_id} className="h-6 bg-emerald-700 hover:bg-emerald-800 text-white text-xs" data-testid={`am-approve-${r.id}`}>
                              <CheckCircle2 className="w-3 h-3 mr-0.5" />Approve
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => reject(r.id)} className="h-6 border-2 border-red-300 text-red-700 hover:bg-red-50 text-xs" data-testid={`am-reject-${r.id}`}>
                              <XCircle className="w-3 h-3 mr-0.5" />Reject
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Executive Summary (002G) */}
        {exec && (
          <div className="rounded border-2 border-slate-300 bg-white p-3" data-testid="am-exec-summary">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-slate-600" />
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
                Executive Operations Summary
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
              <Stat l="Projects Verified" v={exec.projects_verified} />
              <Stat l="Projects Pending" v={exec.projects_pending} />
              <Stat l="Mapped Assets" v={exec.mapped_assets} />
              <Stat l="Unmapped Assets" v={exec.unmapped_assets} />
              <Stat l="Trust Score" v={pctOr(exec.trust_score_pct)} />
              <Stat l="Potential Trust" v={pctOr(exec.potential_trust_score_pct)} />
              <Stat l="Coverage" v={`${exec.coverage_pct}%`} />
              <Stat l="Top Risk" v={(exec.highest_risk_gaps || [])[0]?.truck_id || "—"} />
            </div>
          </div>
        )}

        {audit && (
          <div className="text-[10px] text-slate-500 font-mono">
            Audit · Q7 coverage {audit.q7_coverage_pct}% · Q8 verification unlock {audit.q8_verification_unlock_pct}% · Q5 dups {audit.q5_total_duplicates} · Q6 conflicts {audit.q6_total_conflicts}
          </div>
        )}
      </div>
    </AdminShell>
  );
}

function Stat({ l, v, testid }) {
  return (
    <div className="px-3 py-2 rounded bg-slate-50 border border-slate-200" data-testid={testid}>
      <div className="font-mono text-[10px] uppercase tracking-wider text-slate-700">{l}</div>
      <div className="text-xl font-black text-slate-900">{v}</div>
    </div>
  );
}

function KV({ l, v, accent }) {
  return (
    <div>
      <div className="font-mono text-[9px] uppercase tracking-wider text-slate-600">{l}</div>
      <div className={`font-black ${accent ? "text-emerald-900 text-lg" : "text-slate-900 text-base"}`}>{v}</div>
    </div>
  );
}
