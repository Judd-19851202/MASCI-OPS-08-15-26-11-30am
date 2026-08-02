// IntegrationTruth.jsx — TRACK 22.3 · Integration Truth Surface.
//
// Admin-only single page exposing runtime truth about:
//   1. AI provider keys (read from os.environ, never .env placeholders)
//   2. Third-party integrations (three-state: config / connectivity / ops)
//   3. Legacy /api/dr-v2/* alias telemetry (30-day TTL + permanent aggregate)
//
// Trust doctrine (F-01 / F-02 remediation from Track 22.2):
//   • Never claim LIVE_VERIFIED without proof of recent activity.
//   • Report configuration, connectivity, and operational state
//     independently so operators can see whole picture.
//   • Only booleans and masked last-4 characters render on screen —
//     no raw secrets ever leave the server.
import React, { useCallback, useEffect, useState } from "react";
import {
  ShieldCheck,
  KeyRound,
  Cable,
  History,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Loader2,
  Clock,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { TruthOwnerPanel } from "@/components/admin/trust/TrustPrimitives";
import { operationalError } from "@/lib/errors";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

// ── Status → badge colour vocabulary ────────────────────────────────
const OVERALL_TONE = {
  LIVE_VERIFIED: "bg-emerald-100 text-emerald-800 border-emerald-300",
  CONFIGURED: "bg-blue-100 text-blue-800 border-blue-300",
  CONFIGURED_VIA_UNIVERSAL: "bg-blue-100 text-blue-800 border-blue-300",
  PARTIAL: "bg-amber-100 text-amber-800 border-amber-300",
  MISSING_CONFIG: "bg-amber-100 text-amber-800 border-amber-300",
  MISSING_SECRET: "bg-amber-100 text-amber-800 border-amber-300",
  UNREACHABLE: "bg-orange-100 text-orange-800 border-orange-300",
  MOCKED: "bg-slate-100 text-slate-700 border-slate-300",
  DISABLED: "bg-slate-100 text-slate-700 border-slate-300",
  ERROR: "bg-red-100 text-red-800 border-red-300",
  REACHABLE: "bg-emerald-100 text-emerald-800 border-emerald-300",
  NOT_APPLICABLE: "bg-slate-100 text-slate-600 border-slate-300",
  UNKNOWN: "bg-slate-100 text-slate-600 border-slate-300",
  IDLE: "bg-slate-100 text-slate-600 border-slate-300",
  STALE: "bg-amber-100 text-amber-800 border-amber-300",
  NO_ACTIVITY: "bg-slate-100 text-slate-600 border-slate-300",
  SAFE_TO_RETIRE: "bg-emerald-100 text-emerald-800 border-emerald-300",
  REVIEW_BEFORE_RETIRE: "bg-amber-100 text-amber-800 border-amber-300",
};

const Badge = ({ status, children }) => (
  <span
    data-testid={`truth-badge-${status}`}
    className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${
      OVERALL_TONE[status] || "bg-slate-100 text-slate-700 border-slate-300"
    }`}
  >
    {children || status}
  </span>
);

const Panel = ({ title, subtitle, icon: Icon, right, children }) => (
  <section
    data-testid={`truth-panel-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
    className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
  >
    <header className="flex items-start justify-between gap-4 pb-4">
      <div className="flex items-start gap-3">
        {Icon ? <Icon className="mt-0.5 h-5 w-5 text-slate-600" /> : null}
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {subtitle ? (
            <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>
          ) : null}
        </div>
      </div>
      {right}
    </header>
    <div>{children}</div>
  </section>
);

const fmtTime = (iso) => {
  if (!iso) return "—";
  try {
    return formatPlatformTime(iso);
  } catch {
    return String(iso);
  }
};

const fmtRelative = (iso) => {
  if (!iso) return "never";
  try {
    const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  } catch {
    return "—";
  }
};

// ── AI Keys panel ───────────────────────────────────────────────────
function AiKeysPanel({ data, onRefresh, loading, refreshCapability }) {
  return (
    <Panel
      title="AI Key Status"
      subtitle={data?.reads_from || "Live environment values"}
      icon={KeyRound}
      right={
        <Button
          data-testid="refresh-ai-keys-btn"
          size="sm"
          variant="outline"
          onClick={onRefresh}
          disabled={loading || refreshCapability?.available !== true}
          title={refreshCapability?.disabled_reason || "Refresh AI key status"}
        >
          {loading ? (
            <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCcw className="mr-1 h-3.5 w-3.5" />
          )}
          Refresh
        </Button>
      }
    >
      {!data ? (
        <div className="py-8 text-center text-sm text-slate-500">
          Loading AI key status…
        </div>
      ) : (
        <>
          <div className="mb-4 flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600">
            <Info className="h-3.5 w-3.5 text-slate-400" />
            <span>
              Live value check · managed secrets may be supplied outside the local settings file.
              This panel reflects the values the platform is using right now.
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {(data.providers || []).map((p) => (
              <div
                key={p.provider}
                data-testid={`ai-key-row-${p.provider}`}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium text-slate-900">{p.name}</div>
                  <Badge status={p.status} />
                </div>
                <div className="mt-2 space-y-1 text-xs text-slate-600">
                  <div>
                    <span className="text-slate-500">env var:</span>{" "}
                    <code className="rounded bg-slate-200 px-1">{p.env_var}</code>
                  </div>
                  <div>
                    <span className="text-slate-500">present:</span>{" "}
                    {p.key_present ? (
                      <CheckCircle2 className="inline h-3.5 w-3.5 text-emerald-600" />
                    ) : (
                      <XCircle className="inline h-3.5 w-3.5 text-slate-400" />
                    )}
                    {p.key_last4 ? (
                      <span className="ml-2 rounded bg-white px-2 py-0.5 font-mono text-[10px] tracking-wider text-slate-700">
                        {p.key_last4}
                      </span>
                    ) : null}
                  </div>
                  <div className="text-slate-500">{p.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </Panel>
  );
}

// ── Integrations panel ──────────────────────────────────────────────
function IntegrationsPanel({ data, onRefresh, loading, refreshCapability }) {
  return (
    <Panel
      title="Integration Truth"
      subtitle="Configuration · connectivity · operational activity — all three reported independently."
      icon={Cable}
      right={
        <div className="flex items-center gap-2">
          {data?.overall ? <Badge status={data.overall} /> : null}
          <Button
            data-testid="refresh-integrations-btn"
            size="sm"
            variant="outline"
            onClick={onRefresh}
            disabled={loading || refreshCapability?.available !== true}
            title={refreshCapability?.disabled_reason || "Refresh integration truth"}
          >
            {loading ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCcw className="mr-1 h-3.5 w-3.5" />
            )}
            Refresh
          </Button>
        </div>
      }
    >
      {!data ? (
        <div className="py-8 text-center text-sm text-slate-500">
          Loading integrations…
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Integration</th>
                <th className="py-2 pr-4">Overall</th>
                <th className="py-2 pr-4">Configuration</th>
                <th className="py-2 pr-4">Connectivity</th>
                <th className="py-2 pr-4">Operational</th>
                <th className="py-2 pr-4">Detail</th>
              </tr>
            </thead>
            <tbody>
              {(data.integrations || []).map((row) => (
                <tr
                  key={row.id}
                  data-testid={`integration-row-${row.id}`}
                  className="border-b border-slate-100 align-top last:border-b-0"
                >
                  <td className="py-3 pr-4 font-medium text-slate-900">
                    {row.name}
                    {row.expected_state === "MOCKED" ? (
                      <div className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">
                        Expected: mocked
                      </div>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">
                    <Badge status={row.overall} />
                  </td>
                  <td className="py-3 pr-4">
                    <Badge status={row.config_status} />
                    {row.api_key_last4 ? (
                      <div className="mt-1 font-mono text-[10px] text-slate-600">
                        {row.api_key_last4}
                      </div>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">
                    <Badge status={row.connectivity_status} />
                    {row.connectivity_latency_ms != null ? (
                      <div className="mt-1 text-[10px] text-slate-500">
                        {row.connectivity_latency_ms}ms
                      </div>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">
                    <Badge status={row.operational_status} />
                    {row.last_successful_sync_at ? (
                      <div className="mt-1 flex items-center gap-1 text-[10px] text-slate-500">
                        <Clock className="h-3 w-3" />
                        {fmtRelative(row.last_successful_sync_at)}
                      </div>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4 text-xs text-slate-600">
                    {row.detail || row.connectivity_detail || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

// ── Alias Telemetry panel ───────────────────────────────────────────
function AliasTelemetryPanel({ data, onRefresh, loading, refreshCapability }) {
  return (
    <Panel
      title="Legacy /api/dr-v2/* Alias Telemetry"
      subtitle="Migration signal only. Detail events auto-expire after 30 days; aggregates persist until DR-UNIFY-005 retires the aliases."
      icon={History}
      right={
        <Button
          data-testid="refresh-alias-telemetry-btn"
          size="sm"
          variant="outline"
          onClick={onRefresh}
          disabled={loading || refreshCapability?.available !== true}
          title={refreshCapability?.disabled_reason || "Refresh alias telemetry"}
        >
          {loading ? (
            <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCcw className="mr-1 h-3.5 w-3.5" />
          )}
          Refresh
        </Button>
      }
    >
      {!data ? (
        <div className="py-8 text-center text-sm text-slate-500">
          Loading alias telemetry…
        </div>
      ) : (
        <>
          <div
            data-testid="alias-summary"
            className="mb-4 grid grid-cols-3 gap-3"
          >
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Distinct routes hit
              </div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">
                {data.route_count ?? 0}
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Lifetime hits
              </div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">
                {data.lifetime_hits ?? 0}
              </div>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <div className="text-xs uppercase tracking-wide text-slate-500">
                Safe to retire
              </div>
              <div className="mt-1 text-2xl font-semibold text-emerald-700">
                {data.safe_to_retire_count ?? 0}
              </div>
            </div>
          </div>

          {(data.aggregates || []).length === 0 ? (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
              No legacy /api/dr-v2/* hits recorded yet. When DR-UNIFY-005
              runs, these aliases can be retired without operator disruption.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-4">Route</th>
                    <th className="py-2 pr-4">Recommendation</th>
                    <th className="py-2 pr-4">Lifetime hits</th>
                    <th className="py-2 pr-4">First seen</th>
                    <th className="py-2 pr-4">Last seen</th>
                    <th className="py-2 pr-4">Last role</th>
                    <th className="py-2 pr-4">Last env</th>
                  </tr>
                </thead>
                <tbody>
                  {data.aggregates.map((r) => (
                    <tr
                      key={r.route_key}
                      data-testid={`alias-agg-row-${r.route_key}`}
                      className="border-b border-slate-100 last:border-b-0"
                    >
                      <td className="py-2 pr-4 font-mono text-xs text-slate-900">
                        {r.route_key}
                      </td>
                      <td className="py-2 pr-4">
                        <Badge status={r.retirement_recommendation} />
                      </td>
                      <td className="py-2 pr-4 text-slate-800">
                        {r.lifetime_hits}
                      </td>
                      <td className="py-2 pr-4 text-xs text-slate-600">
                        {fmtTime(r.first_observed_at)}
                      </td>
                      <td className="py-2 pr-4 text-xs text-slate-600">
                        {fmtRelative(r.last_observed_at)}
                      </td>
                      <td className="py-2 pr-4 text-xs text-slate-600">
                        {r.last_role || "—"}
                      </td>
                      <td className="py-2 pr-4 text-xs text-slate-600">
                        {r.last_env || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Panel>
  );
}

function TruthOwnerBanner({ surface, relationship, checkedAt, primaryStatus }) {
  if (!surface) return null;
  return (
    <TruthOwnerPanel
      title="Primary source owner"
      surface={surface}
      relationship={{ ...relationship, canonical_status: primaryStatus || relationship?.canonical_status }}
      checkedAt={fmtTime(checkedAt)}
      testidPrefix="integration-truth-owner-banner"
    />
  );
}

// ── Page shell ──────────────────────────────────────────────────────
export default function IntegrationTruth() {
  const [aiKeys, setAiKeys] = useState(null);
  const [integrations, setIntegrations] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState({ ai: false, int: false, tel: false });
  const [refreshCapability, setRefreshCapability] = useState({
    available: false,
    disabled_reason: "Resolving refresh capability…",
  });

  const loadAiKeys = useCallback(async () => {
    setLoading((s) => ({ ...s, ai: true }));
    try {
      const { data } = await api.get("/admin/ai/keys/status");
      setAiKeys(data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load AI key status"));
    } finally {
      setLoading((s) => ({ ...s, ai: false }));
    }
  }, []);

  const loadIntegrations = useCallback(async () => {
    setLoading((s) => ({ ...s, int: true }));
    try {
      const { data } = await api.get("/admin/integrations/truth-status");
      setIntegrations(data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load integration truth"));
    } finally {
      setLoading((s) => ({ ...s, int: false }));
    }
  }, []);

  const loadTelemetry = useCallback(async () => {
    setLoading((s) => ({ ...s, tel: true }));
    try {
      const { data } = await api.get("/admin/dr-v2-alias-telemetry", {
        params: { recent_limit: 50 },
      });
      setTelemetry(data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load alias telemetry"));
    } finally {
      setLoading((s) => ({ ...s, tel: false }));
    }
  }, []);

  const loadCapabilities = useCallback(async () => {
    try {
      const { data } = await api.get("/admin/shared-capabilities");
      const match = (data.capabilities || []).find(
        (item) => item.capability_id === "truth.integration_truth.refresh",
      );
      setRefreshCapability(match || { available: false, disabled_reason: "Integration truth capability missing." });
    } catch {
      setRefreshCapability({ available: false, disabled_reason: "Unable to verify refresh capability." });
    }
  }, []);

  useEffect(() => {
    loadAiKeys();
    loadIntegrations();
    loadTelemetry();
    loadCapabilities();
  }, [loadAiKeys, loadCapabilities, loadIntegrations, loadTelemetry]);

  return (
    <AdminShell>
      <div
        data-testid="integration-truth-page"
        className="mx-auto max-w-6xl space-y-6 p-6"
      >
        <header className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-6 w-6 text-emerald-600" />
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">
                Integration Truth
              </h1>
              <p className="mt-1 text-sm text-slate-600">
                Live status for AI keys, connected services, and
                legacy alias usage. Configuration alone never gets a green
                badge — only proven activity does.
              </p>
            </div>
          </div>
          <div className="mt-3 flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-900">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
            <span>
              This surface exists so the
              platform cannot misstate live integrations. All values reflect what the platform is using right now; secrets are masked to the last 4 characters.
            </span>
          </div>
        </header>

        <TruthOwnerBanner
          surface={integrations?.truth_surface || telemetry?.truth_surface}
          relationship={integrations?.truth_relationship || telemetry?.truth_relationship}
          checkedAt={integrations?.checked_at || telemetry?.checked_at}
          primaryStatus={integrations?.overall}
        />

        <AiKeysPanel
          data={aiKeys}
          onRefresh={refreshCapability.available ? loadAiKeys : undefined}
          loading={loading.ai}
          refreshCapability={refreshCapability}
        />

        <IntegrationsPanel
          data={integrations}
          onRefresh={refreshCapability.available ? loadIntegrations : undefined}
          loading={loading.int}
          refreshCapability={refreshCapability}
        />

        <AliasTelemetryPanel
          data={telemetry}
          onRefresh={refreshCapability.available ? loadTelemetry : undefined}
          loading={loading.tel}
          refreshCapability={refreshCapability}
        />
      </div>
    </AdminShell>
  );
}
