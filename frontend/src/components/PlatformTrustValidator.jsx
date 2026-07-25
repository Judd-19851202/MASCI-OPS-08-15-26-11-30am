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
import { TruthOwnerPanel } from "@/components/admin/trust/TrustPrimitives";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const BAND = {
  green: { tone: "bg-emerald-50 border-emerald-200", pill: "bg-emerald-100 text-emerald-800 border-emerald-300", Icon: ShieldCheck, label: "Validated in scope" },
  amber: { tone: "bg-amber-50 border-amber-200", pill: "bg-amber-100 text-amber-800 border-amber-300", Icon: AlertTriangle, label: "Bounded gaps" },
  "amber-no-activity": { tone: "bg-slate-50 border-slate-200", pill: "bg-slate-100 text-slate-700 border-slate-300", Icon: Clock, label: "No recent evidence" },
  red: { tone: "bg-rose-50 border-rose-200", pill: "bg-rose-100 text-rose-800 border-rose-300", Icon: XCircle, label: "Contradiction detected" },
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

function boundedHeadline(ots) {
  const claim = ots?.permitted_claim || "UNKNOWN";
  const evaluation = ots?.truth_evaluation || "UNVERIFIABLE";

  if (evaluation === "MISMATCH") {
    return "Validator evidence found contradictions or failing signals in scope.";
  }
  if (evaluation === "DEGRADED") {
    return "Validator evidence is bounded by gaps, stale inputs, or unresolved questions.";
  }
  if (claim === "VALIDATED") {
    return "Validator evidence is validated in scope without claiming platform ownership.";
  }
  if (claim === "VERIFIED") {
    return "Validator evidence is verified in scope, with bounded gaps still disclosed.";
  }
  if (claim === "CORRELATED") {
    return "Validator evidence is correlated only because contradictions prevent a stronger claim.";
  }
  if (claim === "OBSERVED") {
    return "Validator evidence is only observed at this time; stronger claims are not supported.";
  }
  return "Validator evidence is available, but the claim remains intentionally bounded.";
}

function TruthDisclosure({ ots, testidPrefix = "platform-trust-ots-disclosure" }) {
  if (!ots) return null;
  const unknowns = ots.unknowns || [];
  const contradictions = ots.contradictory_evidence || [];

  return (
    <div className="space-y-2" data-testid={`${testidPrefix}-wrapper`}>
      <div
        className="grid gap-2 rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-700 sm:grid-cols-2 lg:grid-cols-4"
        data-testid={testidPrefix}
      >
        <div className="break-words" data-testid={`${testidPrefix}-subject`}>
          <span className="font-semibold text-slate-900">Truth subject:</span> {ots.truth_subject || "UNKNOWN"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-claim`}>
          <span className="font-semibold text-slate-900">Permitted claim:</span> {ots.permitted_claim || "UNKNOWN"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-ceiling`}>
          <span className="font-semibold text-slate-900">Claim ceiling:</span> {ots.claim_ceiling || "UNKNOWN"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-confidence`}>
          <span className="font-semibold text-slate-900">Confidence:</span> {ots.evidence_confidence || "UNKNOWN"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-state`}>
          <span className="font-semibold text-slate-900">Evidence state:</span> {ots.evidence_state || "unknown"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-quality`}>
          <span className="font-semibold text-slate-900">Evidence quality:</span> {ots.evidence_quality || "UNKNOWN"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-basis`}>
          <span className="font-semibold text-slate-900">Evidence basis:</span> {(ots.claim_basis || []).join(" · ") || "—"}
        </div>
        <div className="break-words" data-testid={`${testidPrefix}-audit`}>
          <span className="font-semibold text-slate-900">Audit reference:</span> {ots.audit_reference || "—"}
        </div>
      </div>
      {unknowns.length > 0 && (
        <div
          className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"
          data-testid={`${testidPrefix}-unknowns`}
        >
          <div className="font-semibold">Unknowns / gaps</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {unknowns.map((item, index) => (
              <li key={`${testidPrefix}-unknown-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      )}
      {contradictions.length > 0 && (
        <div
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900"
          data-testid={`${testidPrefix}-contradictions`}
        >
          <div className="font-semibold">Contradictions</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {contradictions.map((item, index) => (
              <li key={`${testidPrefix}-contradiction-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      )}
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

  const dispositionMeta = (
    <div
      data-testid="platform-trust-validator-disposition"
      className="hidden"
      data-trust-surface-id="platform_trust_validator"
      data-trust-disposition="ACTIVE_REPAIRED"
      data-trust-role="VALIDATOR"
      data-canonical-owner="platform_attestation"
    />
  );

  if (loading && !data) {
    return (
      <div
        data-testid="platform-trust-loading"
        className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500"
      >
        {dispositionMeta}
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
        {dispositionMeta}
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
  const ots = data.ots_truth || {};
  const headline = boundedHeadline(ots);

  return (
    <div data-testid="platform-trust-validator" className="space-y-4">
      {dispositionMeta}
      <TruthOwnerPanel
        title="Validation relationship"
        surface={data?.canonical_truth?.validation_surface}
        relationship={data?.truth_relationship}
        checkedAt={data?.generated_at || lastRun}
        testidPrefix="platform-trust-validator-owner-panel"
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 data-testid="platform-trust-validator-title" className="text-base font-semibold text-slate-900">
              Platform Trust Validator
            </h3>
            <Badge band={finalBand} />
          </div>
          <p data-testid="platform-trust-validator-subtitle" className="text-xs text-slate-500">
            Admin-gated, read-only validator · {lastRun && `last run ${lastRun}`}
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

      <div
        data-testid="platform-trust-bounded-headline"
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700"
      >
        <span className="font-semibold text-slate-900">Bounded validator disclosure:</span> {headline}
      </div>

      <TruthDisclosure ots={ots} />

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
        <div className="space-y-3 p-3 sm:hidden">
          {wfRows.map((w) => (
            <div
              key={w.calling_module}
              data-testid={`trust-workflow-mobile-${w.calling_module}`}
              className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] text-slate-900 break-words">
                    {w.calling_module.replace("auto_email_dispatch:", "")}
                  </div>
                  <div className="mt-1 text-slate-600 break-words">{w.reason}</div>
                </div>
                <Badge band={w.band} />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                <div data-testid={`trust-workflow-mobile-sent-${w.calling_module}`}>sent: {w.sent_24h}</div>
                <div data-testid={`trust-workflow-mobile-failed-${w.calling_module}`}>failed: {w.failed_24h}</div>
                <div data-testid={`trust-workflow-mobile-dead-${w.calling_module}`}>dead-letter: {w.dead_letter_24h}</div>
                <div data-testid={`trust-workflow-mobile-submissions-${w.calling_module}`}>submissions: {w.recent_submissions_24h}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="hidden overflow-x-auto sm:block">
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

      {data.compatibility && (
        <div
          data-testid="platform-trust-compatibility"
          className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 break-words"
        >
          <span className="font-semibold text-slate-900">Compatibility:</span>{" "}
          preserved {data.compatibility.preserved_fields} fields · additive {data.compatibility.new_additive_fields} fields · breaking changes {data.compatibility.breaking_api_changes}
        </div>
      )}
    </div>
  );
}
