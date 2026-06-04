// MaintainxP0Tab — OMEGA P0-A/P0-B Read-First Admin Surface
//
// Display-only visibility + control surface for the already-built
// MaintainX P0 backend. Talks ONLY to existing endpoints:
//   GET  /api/admin/maintainx/p0/config
//   POST /api/admin/maintainx/p0/test
//   POST /api/admin/maintainx/p0/dryrun
//   GET  /api/admin/maintainx/p0/dryrun-reports
//
// Security:
//   • Never displays the full API key — only `api_key_masked` /
//     `api_key_last4` / `api_key_present` returned by the backend.
//   • No "save secret" form. Secrets live in environment variables only.
//   • No write/create/update/delete buttons. No sync trigger.
//
// Routes are admin-strict on the backend; this component is rendered
// inside <AdminShell> which sits behind the admin gate.
import React, { useEffect, useState } from "react";
import {
  ShieldCheck, KeyRound, Globe2, ServerCog, Activity, PlayCircle,
  RefreshCcw, Loader2, CheckCircle2, XCircle, AlertTriangle,
  FileText, Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

const PILL_OK = "bg-emerald-100 text-emerald-900 border-emerald-300";
const PILL_WARN = "bg-amber-100 text-amber-900 border-amber-300";
const PILL_BAD = "bg-red-100 text-red-900 border-red-300";
const PILL_MUTED = "bg-slate-100 text-slate-600 border-slate-200";

function Pill({ tone = "muted", children, testId }) {
  const map = { ok: PILL_OK, warn: PILL_WARN, bad: PILL_BAD, muted: PILL_MUTED };
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-mono font-bold uppercase tracking-wide ${map[tone] || PILL_MUTED}`}
    >
      {children}
    </span>
  );
}

function StatRow({ icon: Icon, label, value, testId, tone }) {
  return (
    <div className="flex items-start gap-3 py-2 border-b border-slate-100 last:border-b-0">
      <Icon className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
          {label}
        </div>
        <div className="text-sm text-slate-800 break-words" data-testid={testId}>
          {value}
        </div>
      </div>
      {tone && <Pill tone={tone}>{tone}</Pill>}
    </div>
  );
}

export default function MaintainxP0Tab() {
  const [config, setConfig] = useState(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [dryRun, setDryRun] = useState(null);
  const [reports, setReports] = useState([]);
  const [reportsLoading, setReportsLoading] = useState(false);

  const loadConfig = async () => {
    setConfigLoading(true);
    try {
      const { data } = await api.get("/admin/maintainx/p0/config");
      setConfig(data);
    } catch (e) {
      toast.error(operationalError(e, "Could not load MaintainX config"));
    } finally {
      setConfigLoading(false);
    }
  };

  const loadReports = async () => {
    setReportsLoading(true);
    try {
      const { data } = await api.get("/admin/maintainx/p0/dryrun-reports", { params: { limit: 10 } });
      setReports(Array.isArray(data) ? data : []);
    } catch (e) {
      // Reports are optional — silent failure is acceptable
      setReports([]);
    } finally {
      setReportsLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
    loadReports();
  }, []);

  const onTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const { data } = await api.post("/admin/maintainx/p0/test");
      setTestResult(data);
      if (data?.ok) toast.success("MaintainX connection OK");
      else toast.error(data?.message || "Connection failed");
    } catch (e) {
      toast.error(operationalError(e, "Test connection failed"));
    } finally {
      setTesting(false);
    }
  };

  const onDryRun = async (save) => {
    setRunning(true);
    setDryRun(null);
    try {
      const { data } = await api.post(
        "/admin/maintainx/p0/dryrun",
        null,
        { params: { save: save ? "true" : "false" } },
      );
      setDryRun(data);
      toast.success(
        save
          ? "Dry-run saved to maintainx_dryrun_reports"
          : "Dry-run complete (not saved)",
      );
      if (save) loadReports();
    } catch (e) {
      toast.error(operationalError(e, "Dry-run failed"));
    } finally {
      setRunning(false);
    }
  };

  const apiKeyPresent = !!config?.api_key_present;
  const writeEnabled = !!config?.write_enabled;
  const syncEnabled = !!config?.sync_enabled;

  return (
    <div className="space-y-4" data-testid="mx-p0-root">
      {/* ── Safety banner ──────────────────────────────────────────── */}
      <div
        className="bg-amber-50 border-2 border-amber-300 rounded-md p-4 flex items-start gap-3"
        data-testid="mx-p0-safety-banner"
      >
        <Lock className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-amber-900 font-black">
            Read-First Safety
          </div>
          <p className="text-sm text-amber-950 mt-1 leading-snug">
            Writes are disabled. This screen <strong>cannot</strong> create, update, or delete
            MaintainX work orders, MaintainX assets, MASCI equipment records, DVIR data,
            RTS records, shop, or dispatch records. The MaintainX API key is read from a
            secure server-side environment variable and is never sent to the browser in full.
          </p>
        </div>
      </div>

      {/* ── Configuration card ─────────────────────────────────────── */}
      <section
        className="bg-white border border-slate-200 rounded-md p-4"
        data-testid="mx-p0-config-card"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-slate-700" />
            <h3 className="font-display text-lg font-black tracking-tight">
              Configuration
            </h3>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={loadConfig}
            disabled={configLoading}
            data-testid="mx-p0-config-refresh"
          >
            {configLoading
              ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              : <RefreshCcw className="w-3.5 h-3.5 mr-1" />}
            Refresh
          </Button>
        </div>

        {!config && configLoading && (
          <div className="text-sm text-slate-500 py-4">Loading…</div>
        )}

        {config && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            <StatRow
              icon={KeyRound}
              label="API key configured"
              value={
                <span className="inline-flex items-center gap-2">
                  {apiKeyPresent ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span data-testid="mx-p0-key-status">Yes</span>
                      {config.api_key_masked && (
                        <span
                          className="font-mono text-xs text-slate-500"
                          data-testid="mx-p0-key-masked"
                          title="Last 4 characters of the API key — for confirmation only"
                        >
                          {config.api_key_masked}
                        </span>
                      )}
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-amber-600" />
                      <span data-testid="mx-p0-key-status">No — set MAINTAINX_API_KEY in env</span>
                    </>
                  )}
                </span>
              }
            />
            <StatRow
              icon={Globe2}
              label="Base URL"
              value={
                <span className="font-mono text-xs text-slate-700" data-testid="mx-p0-base-url">
                  {config.base_url || "—"}
                </span>
              }
            />
            <StatRow
              icon={Activity}
              label="Sync enabled"
              value={
                <Pill
                  tone={syncEnabled ? "warn" : "ok"}
                  testId="mx-p0-sync-flag"
                >
                  {syncEnabled ? "TRUE — review" : "FALSE — safe"}
                </Pill>
              }
            />
            <StatRow
              icon={ServerCog}
              label="Write enabled"
              value={
                <Pill
                  tone={writeEnabled ? "bad" : "ok"}
                  testId="mx-p0-write-flag"
                >
                  {writeEnabled ? "TRUE — review" : "FALSE — safe"}
                </Pill>
              }
            />
          </div>
        )}

        <div className="mt-3 pt-3 border-t border-slate-100">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
            Environment safety status
          </div>
          <div className="text-sm text-slate-700 mt-1" data-testid="mx-p0-env-safety">
            {apiKeyPresent
              ? (writeEnabled
                  ? "API key present · WRITE enabled — verify backend kill-switches"
                  : "API key present · WRITE disabled — safe for read-only operations")
              : "API key not configured — pipeline will return missing_api_key gracefully"}
          </div>
        </div>
      </section>

      {/* ── Connection test card ───────────────────────────────────── */}
      <section
        className="bg-white border border-slate-200 rounded-md p-4"
        data-testid="mx-p0-test-card"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-slate-700" />
            <h3 className="font-display text-lg font-black tracking-tight">
              Connection Test
            </h3>
          </div>
          <Button
            onClick={onTest}
            disabled={testing}
            data-testid="mx-p0-test-btn"
            size="sm"
          >
            {testing
              ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              : <PlayCircle className="w-3.5 h-3.5 mr-1" />}
            Test Connection
          </Button>
        </div>

        {testResult ? (
          <div
            className={`text-sm rounded-md p-3 border ${
              testResult.ok
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-amber-50 border-amber-200 text-amber-900"
            }`}
            data-testid="mx-p0-test-result"
          >
            <div className="flex items-center gap-2 font-bold">
              {testResult.ok
                ? <CheckCircle2 className="w-4 h-4" />
                : <AlertTriangle className="w-4 h-4" />}
              {testResult.ok
                ? "Connected"
                : `Failed · ${testResult.status || testResult.code || "unknown"}`}
            </div>
            <div className="mt-1 text-xs">
              {testResult.message || "—"}
            </div>
          </div>
        ) : (
          <div className="text-xs text-slate-500">
            Press <strong>Test Connection</strong> to probe the MaintainX API
            using the server-side environment key. No secret data is sent to the
            browser.
          </div>
        )}
      </section>

      {/* ── Asset dry-run card ─────────────────────────────────────── */}
      <section
        className="bg-white border border-slate-200 rounded-md p-4"
        data-testid="mx-p0-dryrun-card"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-700" />
            <h3 className="font-display text-lg font-black tracking-tight">
              Asset Dry-Run (Read-Only)
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => onDryRun(false)}
              disabled={running}
              size="sm"
              variant="outline"
              data-testid="mx-p0-dryrun-btn"
            >
              {running
                ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                : <PlayCircle className="w-3.5 h-3.5 mr-1" />}
              Run Dry-Run
            </Button>
            <Button
              onClick={() => onDryRun(true)}
              disabled={running}
              size="sm"
              data-testid="mx-p0-dryrun-save-btn"
            >
              {running
                ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                : <PlayCircle className="w-3.5 h-3.5 mr-1" />}
              Run + Save Report
            </Button>
          </div>
        </div>

        {dryRun ? <DryRunSummary report={dryRun} /> : (
          <div className="text-xs text-slate-500">
            A dry-run pulls MaintainX assets, matches them to MASCI equipment,
            and reports classifications. No writes are performed against
            MaintainX or MASCI. "Run + Save Report" appends the result to the
            audit collection <code className="font-mono">maintainx_dryrun_reports</code>.
          </div>
        )}
      </section>

      {/* ── Saved reports card ─────────────────────────────────────── */}
      <section
        className="bg-white border border-slate-200 rounded-md p-4"
        data-testid="mx-p0-reports-card"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-700" />
            <h3 className="font-display text-lg font-black tracking-tight">
              Saved Reports
            </h3>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={loadReports}
            disabled={reportsLoading}
            data-testid="mx-p0-reports-refresh"
          >
            {reportsLoading
              ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              : <RefreshCcw className="w-3.5 h-3.5 mr-1" />}
            Refresh
          </Button>
        </div>

        {reports.length === 0 ? (
          <div className="text-xs text-slate-500" data-testid="mx-p0-reports-empty">
            No saved dry-run reports yet. Use <strong>Run + Save Report</strong> to capture one.
          </div>
        ) : (
          <ul className="space-y-1 text-sm" data-testid="mx-p0-reports-list">
            {reports.map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between py-1 border-b border-slate-100 last:border-b-0"
                data-testid={`mx-p0-report-row-${r.id}`}
              >
                <div className="min-w-0">
                  <div className="font-mono text-xs text-slate-700 truncate">{r.id}</div>
                  <div className="text-[11px] text-slate-500">
                    {r.started_at || "—"} · pulled {r.totals?.maintainx_assets_pulled ?? 0}
                    {" · MASCI "}{r.totals?.masci_equipment_count ?? 0}
                  </div>
                </div>
                <Pill tone={(r.totals?.errors || 0) > 0 ? "warn" : "ok"}>
                  {(r.totals?.errors || 0) > 0 ? "ERRORS" : "OK"}
                </Pill>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function DryRunSummary({ report }) {
  const t = report?.totals || {};
  const cells = [
    { label: "MaintainX pulled", key: "maintainx_assets_pulled", tone: "muted" },
    { label: "MASCI count", key: "masci_equipment_count", tone: "muted" },
    { label: "Exact match", key: "exact_match", tone: "ok" },
    { label: "Probable match", key: "probable_match", tone: "ok" },
    { label: "Possible duplicate", key: "possible_duplicate", tone: "warn" },
    { label: "Conflict", key: "conflict", tone: "warn" },
    { label: "Missing in MASCI", key: "missing_in_masci", tone: "warn" },
    { label: "Missing in MaintainX", key: "missing_in_maintainx", tone: "warn" },
    { label: "Dup-risk blocked", key: "duplicate_risk_blocked", tone: "bad" },
    { label: "Dup-risk safe", key: "duplicate_risk_safe", tone: "ok" },
    { label: "Errors", key: "errors", tone: (t.errors || 0) > 0 ? "bad" : "ok" },
  ];

  const writes = report?.writes_performed || {};
  const totalWrites = Object.values(writes).reduce((a, b) => a + (Number(b) || 0), 0);

  return (
    <div className="space-y-3" data-testid="mx-p0-dryrun-result">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {cells.map((c) => (
          <div
            key={c.key}
            className="border border-slate-200 rounded-md px-3 py-2 bg-slate-50"
            data-testid={`mx-p0-counter-${c.key}`}
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">
              {c.label}
            </div>
            <div className="text-lg font-display font-black text-slate-900 tabular-nums">
              {t[c.key] ?? 0}
            </div>
          </div>
        ))}
      </div>

      <div
        className={`text-xs rounded-md p-2 border ${
          totalWrites === 0
            ? "bg-emerald-50 border-emerald-200 text-emerald-900"
            : "bg-red-50 border-red-200 text-red-900"
        }`}
        data-testid="mx-p0-writes-verified"
      >
        <div className="font-bold flex items-center gap-1">
          {totalWrites === 0
            ? <CheckCircle2 className="w-3.5 h-3.5" />
            : <AlertTriangle className="w-3.5 h-3.5" />}
          Writes performed during this run
        </div>
        <div className="font-mono mt-1">
          MaintainX: {writes.maintainx ?? 0} · equipment_master: {writes.equipment_master ?? 0} ·
          asset_mappings: {writes.asset_mappings ?? 0} · fleet_defects: {writes.fleet_defects ?? 0}
        </div>
      </div>

      <div className="text-[11px] text-slate-500 flex items-center gap-2">
        <span className="font-mono">Run ID:</span>
        <code className="font-mono text-slate-700" data-testid="mx-p0-run-id">{report.id}</code>
        <span>· saved={String(!!report.saved)}</span>
      </div>
    </div>
  );
}
