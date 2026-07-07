// AdminOperationalIntelligence.jsx — Track 19.47 · DR-UNIFY-002 amendment.
// Cockpit UI over the existing Operational Intelligence engine.
// Zero drift — no new engine, no fake data, no live-send default.
//
// DR-UNIFY-002 additive: renders the shared `ApprovedDailyReportsPanel`
// at the bottom so admins can export the canonical English PDF of any
// approved Daily Report (legacy + modern in one unified list). NO PDF
// button on the field form — this remains the single management-side
// export surface.
//
// Consumes:
//   GET  /api/operational-intelligence/summary
//   GET  /api/operational-intelligence/{id}/preview        (rendered HTML)
//   POST /api/operational-intelligence/{id}/dispatch?dry_run=true
//   GET  /api/operational-intelligence/history
//   GET  /api/operational-intelligence/audit
//   GET  /api/daily-reports/approved                       (unified list)
//   GET  /api/daily-reports/{id}/pdf                       (download)

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, Eye, Send, Loader2, RefreshCcw, History as HistoryIcon,
  ClipboardList, ShieldCheck, X, AlertTriangle, Users,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
import { DrV2ApprovedReportsPanel } from "@/components/DrV2ApprovedReportsPanel";

const ATTENTION_COLORS = {
  LOW:      "bg-emerald-100 text-emerald-800 border-emerald-300",
  MEDIUM:   "bg-amber-100  text-amber-800  border-amber-300",
  HIGH:     "bg-orange-100 text-orange-800 border-orange-300",
  CRITICAL: "bg-red-100    text-red-800    border-red-300",
};

const ARROW_COLORS = {
  "▲": "text-emerald-700",
  "▼": "text-red-700",
  "→": "text-slate-500",
};

function AttentionChip({ level }) {
  const cls = ATTENTION_COLORS[level] || "bg-slate-100 text-slate-800 border-slate-300";
  return (
    <span
      data-testid="oi-attention-chip"
      className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-semibold ${cls}`}>
      {level || "—"}
    </span>
  );
}

function ScoreChip({ score, arrow, pct }) {
  const arrowCls = ARROW_COLORS[arrow] || "text-slate-500";
  return (
    <span
      data-testid="oi-score-chip"
      className="inline-flex items-baseline gap-2 text-2xl font-bold text-slate-900">
      {score ?? "—"}
      <span className={`text-base font-semibold ${arrowCls}`}>
        {arrow || "→"}
        {typeof pct === "number" ? ` ${pct.toFixed(1)}%` : ""}
      </span>
    </span>
  );
}

// Track 19.53 · P2 #12 — Cockpit sparkline mini-chart.
// Renders a tiny inline SVG "prior → current" trend from the OI summary
// payload's trend_direction + trend_percent. No new backend fetch.
// Consumes only fields already returned by GET /summary — zero drift.
function TrendSparkline({ score, arrow, pct }) {
  const hasScore = typeof score === "number";
  if (!hasScore) return null;
  const up = arrow === "▲" || arrow === "up";
  const down = arrow === "▼" || arrow === "down";
  const strokeCls = up ? "stroke-emerald-600" : down ? "stroke-red-600" : "stroke-slate-400";
  const magnitude = typeof pct === "number" ? Math.min(Math.abs(pct), 20) : 0;
  const y1 = up ? 18 : down ? 6 : 12;
  const y2 = up ? 6 + Math.max(0, 6 - magnitude / 4)
              : down ? 18 - Math.max(0, 6 - magnitude / 4)
              : 12;
  return (
    <svg
      data-testid="oi-trend-sparkline"
      width="72" height="24" viewBox="0 0 72 24"
      className="shrink-0"
      aria-hidden="true"
    >
      <line x1="4" y1={y1} x2="68" y2={y2} className={strokeCls} strokeWidth="2" strokeLinecap="round" />
      <circle cx="4" cy={y1} r="2.5" className={`fill-slate-300`} />
      <circle cx="68" cy={y2} r="3" className={up ? "fill-emerald-600" : down ? "fill-red-600" : "fill-slate-500"} />
    </svg>
  );
}

function TopStrip({ summary }) {
  if (!summary) return null;
  const b = summary.attention_buckets || {};
  const worst = summary.worst_product;
  const best = summary.best_product;
  const failures = summary.recent_failures || [];
  return (
    <div
      data-testid="oi-cockpit-top-strip"
      className="grid grid-cols-2 md:grid-cols-6 gap-3 rounded-lg border bg-white p-4 shadow-sm">
      <StripStat label="Products" value={summary.count ?? "—"} />
      <StripStat label="LOW"       value={b.LOW ?? 0}       tone="emerald" />
      <StripStat label="MEDIUM"    value={b.MEDIUM ?? 0}    tone="amber" />
      <StripStat label="HIGH"      value={b.HIGH ?? 0}      tone="orange" />
      <StripStat label="CRITICAL"  value={b.CRITICAL ?? 0}  tone="red" />
      <div className="col-span-2 md:col-span-1 rounded-md bg-slate-50 border p-2">
        <div className="text-[10px] font-semibold tracking-wider text-slate-500">DRY-RUN DEFAULT</div>
        <div className="mt-1 text-sm font-semibold text-slate-900">
          <ShieldCheck className="inline h-4 w-4 mr-1 text-emerald-700" />
          Live-send disabled
        </div>
      </div>
      {(worst || best) && (
        <div className="col-span-2 md:col-span-3 rounded-md bg-slate-50 border p-2">
          <div className="text-[10px] font-semibold tracking-wider text-slate-500">EXTREMES</div>
          <div className="mt-1 text-xs text-slate-800 flex flex-wrap gap-x-4">
            {worst && (
              <span data-testid="oi-worst-product">
                <span className="text-red-700 font-semibold">Worst:</span>{" "}
                {worst.display_name} ({worst.score} · {worst.attention_level})
              </span>
            )}
            {best && (
              <span data-testid="oi-best-product">
                <span className="text-emerald-700 font-semibold">Best:</span>{" "}
                {best.display_name} ({best.score} · {best.attention_level})
              </span>
            )}
          </div>
        </div>
      )}
      {failures.length > 0 && (
        <div className="col-span-2 md:col-span-3 rounded-md bg-red-50 border border-red-200 p-2">
          <div className="text-[10px] font-semibold tracking-wider text-red-700 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" /> RECENT FAILURES
          </div>
          <ul className="mt-1 text-xs text-red-900" data-testid="oi-recent-failures">
            {failures.slice(0, 3).map((f, i) => (
              <li key={i}>· {f.product_id} — {f.error}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function StripStat({ label, value, tone }) {
  const cls = tone === "emerald" ? "text-emerald-700" :
              tone === "amber"   ? "text-amber-700" :
              tone === "orange"  ? "text-orange-700" :
              tone === "red"     ? "text-red-700" :
                                    "text-slate-900";
  return (
    <div className="rounded-md bg-slate-50 border p-2" data-testid={`oi-strip-${label.toLowerCase()}`}>
      <div className="text-[10px] font-semibold tracking-wider text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${cls}`}>{value}</div>
    </div>
  );
}

function ProductCard({ p, onPreview, onDryRun, onHistory, onAudit }) {
  const disabled = p.status !== "implemented";
  return (
    <div
      data-testid={`oi-product-card-${p.product_id}`}
      className="rounded-lg border bg-white shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-base font-bold text-slate-900">{p.display_name}</div>
          <div className="text-[11px] font-mono text-slate-500">{p.product_id}</div>
        </div>
        <AttentionChip level={p.attention_level} />
      </div>
      <div className="flex items-center gap-3">
        <ScoreChip
          score={p.score}
          arrow={p.trend_direction}
          pct={p.trend_percent}
        />
        <TrendSparkline
          score={p.score}
          arrow={p.trend_direction}
          pct={p.trend_percent}
        />
        <div className="text-[11px] text-slate-500 leading-tight">
          <div>Confidence: {p.confidence || "—"}</div>
          <div>Freshness: {p.data_freshness || "—"}</div>
        </div>
      </div>
      <div className="text-[11px] text-slate-600 leading-snug">
        <div>
          <span className="font-semibold">Permission:</span> {p.permission_role}
        </div>
        <div>
          <span className="font-semibold">Schedule:</span>{" "}
          {p.schedule?.freq || "—"}{p.schedule?.hour_utc != null ? ` · ${p.schedule.hour_utc}:00 UTC` : ""}
        </div>
        <div>
          <span className="font-semibold">Last generated:</span>{" "}
          {p.last_generated_at ? new Date(p.last_generated_at).toLocaleString() : "—"}
        </div>
        <div>
          <span className="font-semibold">Last sent:</span>{" "}
          {p.last_sent_at ? new Date(p.last_sent_at).toLocaleString() : "—"}
          {p.last_status ? ` (${p.last_status}${p.last_recipient_count != null ? ` · ${p.last_recipient_count} recipients` : ""})` : ""}
        </div>
      </div>
      {p.top_attention_label && (
        <div className="text-xs bg-amber-50 border border-amber-200 rounded p-2 text-amber-900"
             data-testid={`oi-primary-attention-${p.product_id}`}>
          <span className="font-semibold">Attention:</span> {p.top_attention_label}
        </div>
      )}
      {p.error && (
        <div className="text-xs bg-red-50 border border-red-200 rounded p-2 text-red-800"
             data-testid={`oi-error-${p.product_id}`}>
          <AlertTriangle className="inline h-3 w-3 mr-1" />
          {p.error}
        </div>
      )}
      <div className="grid grid-cols-2 gap-2 mt-1">
        <Button size="sm" variant="outline" disabled={disabled}
                onClick={() => onPreview(p)}
                data-testid={`oi-preview-btn-${p.product_id}`}>
          <Eye className="h-3 w-3 mr-1" /> Preview
        </Button>
        <Button size="sm" variant="outline" disabled={disabled}
                onClick={() => onDryRun(p)}
                data-testid={`oi-dryrun-btn-${p.product_id}`}>
          <Send className="h-3 w-3 mr-1" /> Dry-run send
        </Button>
        <Button size="sm" variant="ghost"
                onClick={() => onHistory(p)}
                data-testid={`oi-history-btn-${p.product_id}`}>
          <HistoryIcon className="h-3 w-3 mr-1" /> History
        </Button>
        <Button size="sm" variant="ghost"
                onClick={() => onAudit(p)}
                data-testid={`oi-audit-btn-${p.product_id}`}>
          <ClipboardList className="h-3 w-3 mr-1" /> Audit
        </Button>
      </div>
    </div>
  );
}

function DrawerShell({ open, title, subtitle, onClose, children, testid }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex" data-testid={testid}>
      <div className="flex-1 bg-black/40" onClick={onClose} />
      <div className="w-full max-w-4xl bg-white shadow-xl border-l flex flex-col">
        <div className="flex items-start justify-between p-4 border-b bg-slate-50">
          <div>
            <div className="text-base font-bold text-slate-900">{title}</div>
            {subtitle && <div className="text-xs text-slate-500">{subtitle}</div>}
          </div>
          <Button size="sm" variant="ghost" onClick={onClose}
                  data-testid="oi-drawer-close">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-auto">{children}</div>
      </div>
    </div>
  );
}

function PreviewBody({ html, error }) {
  if (error) {
    return (
      <div className="p-6 text-red-800 bg-red-50 border border-red-200 rounded m-4"
           data-testid="oi-preview-error">
        <AlertTriangle className="inline h-4 w-4 mr-1" />
        {error}
      </div>
    );
  }
  if (!html) {
    return (
      <div className="p-6 text-slate-500 flex items-center gap-2"
           data-testid="oi-preview-loading">
        <Loader2 className="h-4 w-4 animate-spin" /> Composing preview…
      </div>
    );
  }
  return (
    <iframe
      title="operational-intelligence-preview"
      data-testid="oi-preview-iframe"
      sandbox=""
      srcDoc={html}
      className="w-full h-full min-h-[70vh] border-0 bg-white"
    />
  );
}

function TablePanel({ rows, columns, empty, testid }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="p-6 text-slate-500 text-sm" data-testid={`${testid}-empty`}>
        {empty || "No rows."}
      </div>
    );
  }
  return (
    <div className="overflow-auto p-4">
      <table className="w-full text-xs border-collapse" data-testid={testid}>
        <thead>
          <tr className="bg-slate-100">
            {columns.map((c, i) => (
              <th key={i} className="border p-2 text-left font-semibold text-slate-700 uppercase tracking-wider text-[10px]">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="hover:bg-slate-50 align-top">
              {columns.map((c, j) => (
                <td key={j} className="border p-2 text-slate-900">
                  {c.render ? c.render(r) : (r[c.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminOperationalIntelligence() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reloading, setReloading] = useState(false);

  const [previewProduct, setPreviewProduct] = useState(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewError, setPreviewError] = useState("");

  const [dryRunResult, setDryRunResult] = useState(null);
  const [dryRunProduct, setDryRunProduct] = useState(null);

  const [historyProduct, setHistoryProduct] = useState(null);
  const [historyRows, setHistoryRows] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [auditProduct, setAuditProduct] = useState(null);
  const [auditRows, setAuditRows] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get("/operational-intelligence/summary");
      setSummary(r.data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load OI summary"));
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const reload = async () => {
    setReloading(true);
    await load();
    setReloading(false);
    toast.success("Summary refreshed");
  };

  const openPreview = async (p) => {
    setPreviewProduct(p);
    setPreviewHtml("");
    setPreviewError("");
    try {
      const r = await api.get(
        `/operational-intelligence/${p.product_id}/preview`,
        { responseType: "text", transformResponse: [(x) => x] });
      setPreviewHtml(typeof r.data === "string" ? r.data : "");
    } catch (e) {
      setPreviewError(operationalError(e, "Preview failed"));
    }
  };

  const openDryRun = async (p) => {
    setDryRunProduct(p);
    setDryRunResult(null);
    try {
      const r = await api.post(
        `/operational-intelligence/${p.product_id}/dispatch`,
        {}, { params: { dry_run: true } });
      setDryRunResult(r.data);
      toast.success(`Dry-run complete · ${r.data?.send_status || "ok"}`);
    } catch (e) {
      const msg = operationalError(e, "Dry-run failed");
      setDryRunResult({ error: msg });
      toast.error(msg);
    }
  };

  const openHistory = async (p) => {
    setHistoryProduct(p);
    setHistoryRows([]);
    setHistoryLoading(true);
    try {
      const r = await api.get(`/operational-intelligence/history`, {
        params: { product_id: p.product_id, limit: 25 },
      });
      setHistoryRows(r.data?.history || []);
    } catch (e) {
      toast.error(operationalError(e, "History load failed"));
    } finally { setHistoryLoading(false); }
  };

  const openAudit = async (p) => {
    setAuditProduct(p);
    setAuditRows([]);
    setAuditLoading(true);
    try {
      const r = await api.get(`/operational-intelligence/audit`, {
        params: { product_id: p.product_id, limit: 25 },
      });
      setAuditRows(r.data?.audit || []);
    } catch (e) {
      toast.error(operationalError(e, "Audit load failed"));
    } finally { setAuditLoading(false); }
  };

  const products = summary?.products || [];

  return (
    <AdminShell title="Operational Intelligence" section="operational-intelligence">
      <div className="p-4 space-y-4" data-testid="admin-operational-intelligence">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Activity className="h-5 w-5 text-slate-700" />
              Operational Intelligence Cockpit
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              11 intelligence products · scores · previews · history · audit.
              Dry-run default. Zero drift.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={reload}
                    data-testid="oi-refresh-btn" disabled={reloading}>
              {reloading
                ? <Loader2 className="h-3 w-3 animate-spin mr-1" />
                : <RefreshCcw className="h-3 w-3 mr-1" />}
              Refresh
            </Button>
            <a href="/api/operational-intelligence/products"
               target="_blank" rel="noreferrer"
               className="text-xs text-slate-500 underline hover:text-slate-800"
               data-testid="oi-registry-link">
              Registry JSON
            </a>
          </div>
        </div>

        {loading ? (
          <div className="p-6 text-slate-500 flex items-center gap-2"
               data-testid="oi-cockpit-loading">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading summary…
          </div>
        ) : (
          <>
            <TopStrip summary={summary} />

            <div className="rounded-lg border bg-white shadow-sm p-3 flex items-start gap-3"
                 data-testid="oi-recipient-governance-entry">
              <Users className="h-5 w-5 text-slate-700 mt-0.5" />
              <div className="flex-1 text-xs text-slate-700">
                <div className="font-semibold text-slate-900 text-sm">Recipient Governance</div>
                Recipient/group CRUD is served by the admin API
                (<code>/api/operational-intelligence/recipients</code> ·{" "}
                <code>/api/operational-intelligence/groups</code>).
                Use the dedicated Recipient Management page below to
                add, edit, deactivate, and reactivate recipients.
              </div>
              <div className="flex flex-col gap-1">
                <a href="/admin/operational-intelligence/recipients"
                   className="text-xs underline text-emerald-700 hover:text-emerald-900 font-semibold"
                   data-testid="oi-recipients-manage-link">
                  Manage Recipients →
                </a>
                <a href="/api/operational-intelligence/recipients"
                   target="_blank" rel="noreferrer"
                   className="text-xs underline text-slate-700 hover:text-slate-900"
                   data-testid="oi-recipients-link">
                  Recipients JSON
                </a>
                <a href="/api/operational-intelligence/groups"
                   target="_blank" rel="noreferrer"
                   className="text-xs underline text-slate-700 hover:text-slate-900"
                   data-testid="oi-groups-link">
                  Groups JSON
                </a>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3"
                 data-testid="oi-product-grid">
              {products.map((p) => (
                <ProductCard
                  key={p.product_id}
                  p={p}
                  onPreview={openPreview}
                  onDryRun={openDryRun}
                  onHistory={openHistory}
                  onAudit={openAudit}
                />
              ))}
            </div>
          </>
        )}

        <DrawerShell
          open={!!previewProduct}
          title={previewProduct?.display_name || ""}
          subtitle={previewProduct?.product_id}
          onClose={() => { setPreviewProduct(null); setPreviewHtml(""); }}
          testid="oi-preview-drawer">
          <PreviewBody html={previewHtml} error={previewError} />
        </DrawerShell>

        <DrawerShell
          open={!!dryRunProduct}
          title={`Dry-run · ${dryRunProduct?.display_name || ""}`}
          subtitle={dryRunProduct?.product_id}
          onClose={() => { setDryRunProduct(null); setDryRunResult(null); }}
          testid="oi-dryrun-drawer">
          <div className="p-4 space-y-3 text-sm">
            {!dryRunResult ? (
              <div className="text-slate-500 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" /> Running dry-run…
              </div>
            ) : dryRunResult.error ? (
              <div className="p-4 bg-red-50 border border-red-200 rounded text-red-800"
                   data-testid="oi-dryrun-error">
                <AlertTriangle className="inline h-4 w-4 mr-1" />
                {dryRunResult.error}
              </div>
            ) : (
              <div className="rounded border bg-slate-50 p-3"
                   data-testid="oi-dryrun-result">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <StripStat label="Status" value={dryRunResult.send_status || "—"} />
                  <StripStat label="Dry-run" value={String(dryRunResult.dry_run)} />
                  <StripStat label="Recipients" value={dryRunResult.recipient_count ?? 0} />
                  <StripStat label="Dedupe key" value={
                    <span className="text-[10px] font-mono break-all">
                      {dryRunResult.dedupe_key || "—"}
                    </span>
                  } />
                </div>
                {Array.isArray(dryRunResult.recipients) && (
                  <div className="mt-3 text-xs">
                    <div className="font-semibold text-slate-700 mb-1">Recipient list (no email sent)</div>
                    <ul className="list-disc list-inside text-slate-600">
                      {dryRunResult.recipients.slice(0, 20).map((e, i) => <li key={i}>{e}</li>)}
                      {dryRunResult.recipients.length > 20 && (
                        <li className="text-slate-500 italic">
                          +{dryRunResult.recipients.length - 20} more…
                        </li>
                      )}
                    </ul>
                  </div>
                )}
                <div className="mt-3 text-[11px] text-emerald-700">
                  <ShieldCheck className="inline h-3 w-3 mr-1" />
                  Live email was NOT sent. Audit + history rows written.
                </div>
              </div>
            )}
          </div>
        </DrawerShell>

        <DrawerShell
          open={!!historyProduct}
          title={`History · ${historyProduct?.display_name || ""}`}
          subtitle={historyProduct?.product_id}
          onClose={() => setHistoryProduct(null)}
          testid="oi-history-drawer">
          {historyLoading ? (
            <div className="p-6 text-slate-500 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : (
            <TablePanel
              testid="oi-history-table"
              rows={historyRows}
              empty="No history rows recorded yet for this product."
              columns={[
                { label: "Generated", render: (r) => r.generated_at ? new Date(r.generated_at).toLocaleString() : "—" },
                { label: "Period", key: "period" },
                { label: "Score", render: (r) => r.score?.overall_score ?? "—" },
                { label: "Attention", render: (r) => <AttentionChip level={r.score?.attention_level} /> },
                { label: "Trend", render: (r) => `${r.score?.trend_direction || "→"}${r.score?.trend_percent != null ? ` ${r.score.trend_percent}%` : ""}` },
                { label: "Confidence", render: (r) => r.score?.confidence || "—" },
                { label: "By", key: "generated_by" },
              ]}
            />
          )}
        </DrawerShell>

        <DrawerShell
          open={!!auditProduct}
          title={`Audit · ${auditProduct?.display_name || ""}`}
          subtitle={auditProduct?.product_id}
          onClose={() => setAuditProduct(null)}
          testid="oi-audit-drawer">
          {auditLoading ? (
            <div className="p-6 text-slate-500 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : (
            <TablePanel
              testid="oi-audit-table"
              rows={auditRows}
              empty="No audit rows recorded yet for this product."
              columns={[
                { label: "At", render: (r) => r.at ? new Date(r.at).toLocaleString() : "—" },
                { label: "Event", key: "event" },
                { label: "Actor", key: "actor" },
                { label: "Status", render: (r) => (r.payload?.send_status) || "—" },
                { label: "Recipients", render: (r) => r.payload?.recipient_count ?? "—" },
                { label: "Dedupe", render: (r) => <span className="font-mono text-[10px] break-all">{r.payload?.dedupe_key || "—"}</span> },
              ]}
            />
          )}
        </DrawerShell>

        {/* DR-UNIFY-002 · Approved Daily Reports PDF export (unified legacy + modern) */}
        <section
          className="mt-6 space-y-3"
          data-testid="admin-approved-daily-reports"
        >
          <div>
            <div className="text-[10px] uppercase tracking-widest text-neutral-500">
              Approved Daily Reports
            </div>
            <div className="text-sm text-neutral-700">
              Canonical English PDF export · legacy + modern records in one list · management access only
            </div>
          </div>
          <DrV2ApprovedReportsPanel audience="admin" />
        </section>
      </div>
    </AdminShell>
  );
}
