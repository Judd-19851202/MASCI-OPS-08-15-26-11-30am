/**
 * <PlatformTrustValidator> — Track 15.75D
 *
 * In-app, admin-gated, read-only Production Trust Validator card.
 * Reads:
 *   GET /api/admin/platform-trust/validate
 *
 * Replaces the prior shell-script (track_15_75c_prod_validate.sh)
 * workflow: a logged-in super-admin can now verify every Track
 * 15.74 → 15.75C trust contract from the admin UI itself — no
 * tokens to copy, no DevTools, no Mongo queries.
 *
 * Surfaces:
 *   - Final band (green / amber / red) with explicit reasons
 *   - System heartbeat (mongo · scheduler · backup_recent)
 *   - Email routing mode + critical-route emptiness
 *   - Audit-status integrity (allowed-status enforcement)
 *   - Per-workflow delivery health (7 calling_modules, last 24h)
 *   - PM-email coverage summary
 *   - Dead-letter health summary
 *
 * Honors hard rules: no secrets, no recipient lists, no env values,
 * no mutations.
 */
import React, { useState, useCallback, useEffect } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  RotateCw,
  CheckCircle2,
  Activity,
  Database,
  Mail,
  Users,
  Inbox,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const BAND = {
  green: { tone: "bg-emerald-50 border-emerald-200", pill: "bg-emerald-100 text-emerald-800 border-emerald-300", Icon: ShieldCheck, label: "Trusted" },
  amber: { tone: "bg-amber-50 border-amber-200", pill: "bg-amber-100 text-amber-800 border-amber-300", Icon: AlertTriangle, label: "Attention" },
  "amber-no-activity": { tone: "bg-slate-50 border-slate-200", pill: "bg-slate-100 text-slate-700 border-slate-300", Icon: Clock, label: "No activity" },
  red: { tone: "bg-rose-50 border-rose-200", pill: "bg-rose-100 text-rose-800 border-rose-300", Icon: XCircle, label: "Critical" },
};

function Badge({ band, children }) {
  const cfg = BAND[band] || BAND.amber;
  const { Icon } = cfg;
  return (
    <span
      data-testid={`trust-band-${band}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.pill}`}
    >
      <Icon size={12} />
      {children || cfg.label}
    </span>
  );
}

function Card({ icon: Icon, title, band, children, testId }) {
  const cfg = BAND[band] || BAND.amber;
  return (
    <div
      data-testid={testId}
      className={`rounded-2xl border p-4 ${cfg.tone}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          {Icon && <Icon size={16} className="text-slate-600" />}
          {title}
        </div>
        <Badge band={band} />
      </div>
      {children}
    </div>
  );
}

export default function PlatformTrustValidator() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastRun, setLastRun] = useState("");

  const run = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/admin/platform-trust/validate");
      setData(res.data);
      setLastRun(formatPlatformTime());
    } catch (e) {
      const msg = (e?.response?.data?.detail || e?.message || "validation failed");
      setError(String(msg));
      toast.error(`Trust validator: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    run();
  }, [run]);

  if (loading && !data) {
    return (
      <div
        data-testid="platform-trust-loading"
        className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500"
      >
        <RotateCw className="inline-block animate-spin mr-2" size={14} />
        Running validation…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div
        data-testid="platform-trust-error"
        className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"
      >
        <strong>Trust validator unavailable:</strong> {error}
        <div className="mt-2">
          <Button
            size="sm"
            variant="outline"
            onClick={run}
            data-testid="platform-trust-retry"
          >
            <RotateCw size={14} className="mr-1" /> Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const finalBand = data.final_band || "amber";
  const wfRows = data.workflow_delivery_health || [];
  const sys = data.system || {};
  const er = data.email_routing || {};
  const ai = data.audit_status_integrity || {};
  const pmc = data.pm_email_coverage || {};
  const dl = data.dead_letter_health || {};
  const redReasons = data.red_reasons || [];
  const amberReasons = data.amber_reasons || [];

  return (
    <div data-testid="platform-trust-validator" className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Platform Trust Validator
            </h3>
            <Badge band={finalBand} />
          </div>
          <p className="text-xs text-slate-500">
            Admin-gated, read-only · {lastRun && `last run ${lastRun}`}
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={run}
          disabled={loading}
          data-testid="platform-trust-run"
        >
          <RotateCw size={14} className={`mr-1 ${loading ? "animate-spin" : ""}`} />
          Re-run validation
        </Button>
      </div>

      {finalBand === "red" && redReasons.length > 0 && (
        <div
          data-testid="platform-trust-red-reasons"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"
        >
          <div className="font-medium mb-1">RED reasons ({redReasons.length}):</div>
          <ul className="list-disc list-inside text-xs space-y-0.5">
            {redReasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {finalBand === "amber" && amberReasons.length > 0 && (
        <div
          data-testid="platform-trust-amber-reasons"
          className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800"
        >
          <div className="font-medium mb-1">AMBER reasons ({amberReasons.length}):</div>
          <ul className="list-disc list-inside space-y-0.5">
            {amberReasons.slice(0, 8).map((r, i) => (
              <li key={i}>{r}</li>
            ))}
            {amberReasons.length > 8 && <li>… and {amberReasons.length - 8} more</li>}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Card
          icon={Database}
          title="System"
          band={sys.ok ? "green" : "red"}
          testId="trust-card-system"
        >
          <ul className="text-xs text-slate-700 space-y-1">
            <li>env: <code className="text-slate-500">{sys.app_env}</code></li>
            <li>db: <code className="text-slate-500">{sys.db_name}</code></li>
            <li>mongo: {sys.mongo ? "✓" : "✗"}</li>
            <li>scheduler: {sys.scheduler === false ? "✗" : "✓"}</li>
            <li>backup recent: {sys.backup_recent === false ? "✗" : sys.backup_recent === null ? "—" : "✓"}</li>
          </ul>
        </Card>

        <Card
          icon={Mail}
          title="Email Routing"
          band={er.critical_empty_count === 0 && er.errors_last_24h === 0 ? "green" : "red"}
          testId="trust-card-routing"
        >
          <ul className="text-xs text-slate-700 space-y-1">
            <li>mode: <code className="text-slate-500">{er.mode === "v2" ? "modern" : er.mode === "v1" ? "legacy fallback" : er.mode}</code></li>
            <li>Modern routing: {er.v2_enabled ? "✓" : "—"}</li>
            <li>routes: {er.route_total}</li>
            <li>critical empty: {er.critical_empty_count}</li>
            <li>errors 24h: {er.errors_last_24h}</li>
          </ul>
        </Card>

        <Card
          icon={CheckCircle2}
          title="Audit Integrity"
          band={ai.pass ? "green" : "red"}
          testId="trust-card-audit"
        >
          <ul className="text-xs text-slate-700 space-y-1">
            <li>unknown statuses: {ai.unknown_status_count}</li>
            <li>observed: {(ai.observed_statuses || []).length}</li>
            <li>allowed: {(ai.allowed_statuses || []).length}</li>
            {(ai.unknown_statuses || []).length > 0 && (
              <li className="text-rose-800 font-medium">
                {ai.unknown_statuses.join(", ")}
              </li>
            )}
          </ul>
        </Card>

        <Card
          icon={Users}
          title="PM Coverage"
          band={pmc.active_missing_unresolved > 0 ? "amber" : "green"}
          testId="trust-card-pm-coverage"
        >
          <ul className="text-xs text-slate-700 space-y-1">
            <li>active: {pmc.active_total ?? "—"}</li>
            <li>direct pm_email: {pmc.active_direct_pm_email ?? "—"}</li>
            <li>roster resolved: {pmc.active_roster_resolved ?? "—"}</li>
            <li>unresolved: {pmc.active_missing_unresolved ?? "—"}</li>
          </ul>
        </Card>
      </div>

      <div
        data-testid="trust-card-workflows"
        className="rounded-2xl border border-slate-200 bg-white"
      >
        <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
          <Activity size={16} className="text-slate-600" />
          <h4 className="text-sm font-semibold text-slate-900">
            Per-Workflow Delivery (last 24h)
          </h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wide bg-slate-50 text-slate-500">
              <tr>
                <th className="text-left px-3 py-2">workflow</th>
                <th className="text-right px-2 py-2">sent</th>
                <th className="text-right px-2 py-2">failed</th>
                <th className="text-right px-2 py-2">dead-letter</th>
                <th className="text-right px-2 py-2">submissions</th>
                <th className="text-left px-3 py-2">band</th>
                <th className="text-left px-3 py-2">reason</th>
              </tr>
            </thead>
            <tbody>
              {wfRows.map((w) => (
                <tr
                  key={w.calling_module}
                  data-testid={`trust-workflow-${w.calling_module}`}
                  className="border-t border-slate-100"
                >
                  <td className="px-3 py-2 font-mono text-xs text-slate-700">
                    {w.calling_module.replace("auto_email_dispatch:", "")}
                  </td>
                  <td className="px-2 py-2 text-right">{w.sent_24h}</td>
                  <td className={`px-2 py-2 text-right ${w.failed_24h ? "text-rose-700 font-semibold" : ""}`}>
                    {w.failed_24h}
                  </td>
                  <td className="px-2 py-2 text-right">{w.dead_letter_24h}</td>
                  <td className="px-2 py-2 text-right">{w.recent_submissions_24h}</td>
                  <td className="px-3 py-2"><Badge band={w.band} /></td>
                  <td className="px-3 py-2 text-xs text-slate-600">{w.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Card
        icon={Inbox}
        title="Dead-Letter Health"
        band={
          dl.dead_letter_unconfigured_total > 0 ||
          dl.shop_recipient_unconfigured_24h > 0
            ? "red"
            : dl.dead_letters_24h > 0
            ? "amber"
            : "green"
        }
        testId="trust-card-dead-letter"
      >
        <ul className="text-xs text-slate-700 space-y-1">
          <li>dead-letters 24h: {dl.dead_letters_24h ?? 0}</li>
          <li>dead-letter unconfigured (total): {dl.dead_letter_unconfigured_total ?? 0}</li>
          <li>shop unresolved 24h: {dl.shop_recipient_unconfigured_24h ?? 0}</li>
        </ul>
      </Card>
    </div>
  );
}
