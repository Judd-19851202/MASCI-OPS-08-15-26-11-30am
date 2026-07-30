// SelfProtection.jsx — Phase GOVERNANCE-OPS-1 · 2026-05-28.
//
// /admin/governance/self-protection
//
// Calm, monochrome, aircraft-systems-style operational visibility into
// the platform's own governance protections. Read-only. Admin-only.
// No charts, no widgets, no animations beyond the polling refresh.
//
// The page answers ONE question in five seconds:
//   "Is the platform governance healthy right now?"

import React from "react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { api } from "@/lib/api";

const POLL_MS = 60_000;

const STATUS_META = {
  green: {
    label: "Healthy",
    classes: "border-emerald-200 bg-emerald-50 text-emerald-800",
  },
  amber: {
    label: "Needs review",
    classes: "border-amber-200 bg-amber-50 text-amber-800",
  },
  red: {
    label: "At risk",
    classes: "border-rose-200 bg-rose-50 text-rose-800",
  },
  unknown: {
    label: "Not instrumented",
    classes: "border-slate-200 bg-slate-100 text-slate-700",
  },
  unavailable_in_runtime_image: {
    label: "Unavailable in preview",
    classes: "border-slate-200 bg-slate-100 text-slate-700",
  },
};

function humanizeToken(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function StateBadge({ status, testId }) {
  const meta = STATUS_META[status] || STATUS_META.unknown;
  return (
    <span
      data-testid={testId}
      data-status={status}
      className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold ${meta.classes}`}
    >
      {meta.label}
    </span>
  );
}

function _fmtAgo(epoch_s) {
  if (!epoch_s) return "No timestamp recorded";
  const ms = epoch_s * 1000;
  const sec = Math.max(0, Math.floor((Date.now() - ms) / 1000));
  if (sec < 60)   return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60)   return `${min}m ago`;
  const hr  = Math.floor(min / 60);
  if (hr < 24)    return `${hr}h ago`;
  const d   = Math.floor(hr / 24);
  return `${d}d ago`;
}

function displayValue(value, fallback = "Not recorded") {
  if (value === null || value === undefined || value === "") return fallback;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function explainStatus(status, fallback = "No status reported") {
  if (!status) return fallback;
  if (status === "unknown") return "This signal is not wired in the preview runtime yet.";
  if (status === "unavailable_in_runtime_image") return "This runtime image does not include that evidence package.";
  return humanizeToken(status);
}

function SectionCard({ title, status, summary, children, testId }) {
  return (
    <section
      data-testid={testId}
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <header className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div className="space-y-2">
          <h2 className="text-lg font-black text-slate-950">{title}</h2>
          <p className="text-sm text-slate-700 leading-relaxed">{summary}</p>
        </div>
        <StateBadge status={status} testId={`${testId}-pill`} />
      </header>
      <div className="space-y-2 text-sm text-slate-700">
        {children}
      </div>
    </section>
  );
}

function FactRow({ label, value, testId }) {
  return (
    <div className="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:grid-cols-[14rem_1fr]" data-testid={testId}>
      <span className="text-slate-500 uppercase tracking-wider text-[10px] font-mono">
        {label}
      </span>
      <span className="text-slate-900 break-words">{displayValue(value)}</span>
    </div>
  );
}

export default function SelfProtection() {
  const [data, setData] = React.useState(null);
  const [err, setErr] = React.useState(null);
  const [loadedAt, setLoadedAt] = React.useState(null);
  const [refreshing, setRefreshing] = React.useState(false);

  const fetchOnce = React.useCallback(async () => {
    setRefreshing(true);
    setErr(null);
    try {
      const r = await api.get("/admin/governance/self-protection");
      setData(r.data || null);
      setLoadedAt(Date.now());
    } catch (e) {
      setErr(e?.message || "failed to load");
    } finally {
      setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    fetchOnce();
    const id = setInterval(fetchOnce, POLL_MS);
    return () => clearInterval(id);
  }, [fetchOnce]);

  if (err) {
    return (
      <LegacyAdminModernShell
        title="Governance · Self-Protection"
        subtitle="Read-only operational visibility into the platform's own governance protections."
        breadcrumb={[
          { label: "Identity & Security", to: "/admin/identity-security" },
          { label: "Self-Protection" },
        ]}
        testidPrefix="self-protection"
      >
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800" data-testid="self-protection-error">
          <div className="font-semibold text-rose-900 mb-1">Self-protection status is unavailable.</div>
          <p>
            {err}
          </p>
        </div>
      </LegacyAdminModernShell>
    );
  }

  if (!data) {
    return (
      <LegacyAdminModernShell
        title="Governance · Self-Protection"
        subtitle="Read-only operational visibility into the platform's own governance protections."
        breadcrumb={[
          { label: "Identity & Security", to: "/admin/identity-security" },
          { label: "Self-Protection" },
        ]}
        testidPrefix="self-protection"
      >
        <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600" data-testid="self-protection-loading">
          Reading governance state…
        </div>
      </LegacyAdminModernShell>
    );
  }

  const a = data.authority || {};
  const t = data.trust_surfaces || {};
  const c = data.context_governance || {};
  const ts = data.truthful_state || {};
  const tm = data.telemetry || {};
  const rg = data.regression_suite || {};
  const fw = data.field_walks || {};
  const dr = data.drift || {};
  const dp = data.deployment || {};
  const warningBreakdown = a.warning_classification || {};

  const heroSummary = a.new_violations > 0
    ? `${a.new_violations} new authority violation${a.new_violations === 1 ? " needs" : "s need"} immediate attention.`
    : a.new_warnings > 0
      ? `${a.new_warnings} warning${a.new_warnings === 1 ? " was" : "s were"} detected, but none are currently classified as active failures.`
      : "No new authority violations or warnings were detected in the latest pass.";

  const trustSummary = t.registered > 0
    ? `${t.registered} trust surfaces are registered, with ${t.live || 0} currently live and ${t.planned || 0} still planned.`
    : "Trust-surface registry evidence is not available in this preview runtime yet.";

  const contextSummary = c.context_governed > 0
    ? `${c.context_governed} surfaces are context-governed, with ${c.tbd || 0} still awaiting governance coverage.`
    : "No context-governed surfaces were reported in this runtime snapshot.";

  const truthfulSummary = ts.contracts > 0
    ? `${ts.contracts} truthful-state contracts are declared across ${ts.surfaces_covered?.length || 0} surfaces.`
    : "No truthful-state contract records were shipped in this runtime image.";

  const telemetrySummary = tm.client_signals || tm.server_signals
    ? `${tm.client_signals || 0} client signals and ${tm.server_signals || 0} server signals are currently declared.`
    : "Telemetry doctrine details are not available in this preview runtime yet.";

  const regressionSummary = rg.status === "unavailable_in_runtime_image"
    ? "Regression artifacts are not shipped in the preview runtime image, so this page cannot independently quote the latest test report."
    : rg.last_iteration
      ? `Latest recorded regression run: ${rg.last_iteration}.`
      : "No regression run metadata is available right now.";

  const fieldWalkSummary = fw.walks?.length
    ? `${fw.walks.length} field walk checklist${fw.walks.length === 1 ? " is" : "s are"} registered for verification.`
    : "No field walk checklist evidence was returned in this runtime snapshot.";

  const driftSummary = dr.open_gaps > 0
    ? `${dr.open_gaps} open governance gap${dr.open_gaps === 1 ? " remains" : "s remain"}.`
    : "No open governance gaps are currently reported; remaining warnings are historical or tolerated baseline items.";

  const deploymentSummary = dp.deployed_at
    ? `Current runtime was recorded ${_fmtAgo(dp.deployed_at)} and keeps ${dp.history_size || 0} release history entries for comparison.`
    : "Deployment lineage has not been recorded for this runtime yet.";

  return (
    <LegacyAdminModernShell
      title="Governance · Self-Protection"
      subtitle="Read-only operational visibility into the platform's own governance protections."
      breadcrumb={[
        { label: "Identity & Security", to: "/admin/identity-security" },
        { label: "Self-Protection" },
      ]}
      testidPrefix="self-protection"
    >
      <div className="space-y-6" data-testid="self-protection-page">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl space-y-2">
              <div className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-700">
                Platform self-protection
              </div>
              <h1 className="text-2xl font-black text-slate-950" data-testid="self-protection-title">
                Governance guardrails for the platform itself
              </h1>
              <p className="text-sm text-slate-700 leading-relaxed">
                {heroSummary} This page explains whether the platform&apos;s own governance controls are wired, current, and behaving as expected.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <StateBadge status={data.page_status} testId="self-protection-overall-pill" />
              <button
                type="button"
                onClick={fetchOnce}
                disabled={refreshing}
                data-testid="self-protection-refresh"
                className="inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {refreshing ? "Refreshing…" : "Refresh"}
              </button>
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Page status</div>
              <div className="mt-1 text-sm font-semibold text-slate-950">{explainStatus(data.page_status)}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Loaded in browser</div>
              <div className="mt-1 text-sm font-semibold text-slate-950">{loadedAt ? _fmtAgo(loadedAt / 1000) : "Not loaded yet"}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Generated by backend</div>
              <div className="mt-1 text-sm font-semibold text-slate-950">{data.generated_at ? _fmtAgo(data.generated_at) : "Not reported"}</div>
            </div>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          <SectionCard title="Authority protection" status={a.status} summary={heroSummary} testId="self-protection-authority">
            <FactRow label="Probe status" value={explainStatus(a.status)} testId="auth-status" />
            <FactRow label="New violations" value={a.new_violations} testId="auth-violations" />
            <FactRow label="New warnings" value={a.new_warnings} testId="auth-warnings" />
            <FactRow label="Baselined patterns" value={a.baselined} testId="auth-baselined" />
            <FactRow label="Current actionable warnings" value={warningBreakdown.current_actionable} testId="auth-current-actionable" />
            <FactRow label="Probe runtime" value={a.scan_ms != null ? `${a.scan_ms} ms` : "No runtime reported"} testId="auth-runtime" />
            <FactRow label="Last run" value={a.last_run_at ? _fmtAgo(a.last_run_at) : "Not run yet"} testId="auth-last-run" />
          </SectionCard>

          <SectionCard title="Trust surfaces" status={t.status} summary={trustSummary} testId="self-protection-trust">
            <FactRow label="Registered surfaces" value={t.registered} testId="trust-registered" />
            <FactRow label="Live now" value={t.live} testId="trust-live" />
            <FactRow label="Still planned" value={t.planned} testId="trust-planned" />
            <FactRow label="Doctrine fields tracked" value={(t.doctrine_fields || []).length || "No doctrine fields reported"} testId="trust-fields" />
          </SectionCard>

          <SectionCard title="Context governance" status={c.status} summary={contextSummary} testId="self-protection-context">
            <FactRow label="Governed with context rules" value={c.context_governed} testId="ctx-governed" />
            <FactRow label="Still to be governed" value={c.tbd} testId="ctx-tbd" />
            <FactRow label="Planned for later phases" value={c.planned} testId="ctx-planned" />
          </SectionCard>

          <SectionCard title="Truthful-state contracts" status={ts.status} summary={truthfulSummary} testId="self-protection-truthful">
            <FactRow label="Contracts declared" value={ts.contracts} testId="truthful-contracts" />
            <FactRow label="Covered surfaces" value={(ts.surfaces_covered || []).length || "No covered surfaces reported"} testId="truthful-surfaces" />
          </SectionCard>

          <SectionCard title="Telemetry doctrine" status={tm.status} summary={telemetrySummary} testId="self-protection-telemetry">
            <FactRow label="Client signals" value={tm.client_signals} testId="telemetry-client" />
            <FactRow label="Server signals" value={tm.server_signals} testId="telemetry-server" />
            <FactRow label="Forbidden patterns documented" value={tm.forbidden_patterns} testId="telemetry-forbidden" />
          </SectionCard>

          <SectionCard title="Regression suite" status={rg.status} summary={regressionSummary} testId="self-protection-regression">
            <FactRow label="Latest report" value={rg.last_iteration || "No report reference returned"} testId="reg-iteration" />
            <FactRow label="Last run" value={rg.last_iteration_at ? _fmtAgo(rg.last_iteration_at) : "No run timestamp returned"} testId="reg-last" />
          </SectionCard>

          <SectionCard title="Field walks" status={fw.status} summary={fieldWalkSummary} testId="self-protection-walks">
            {(fw.walks || []).length ? (fw.walks || []).map((w) => (
              <FactRow
                key={w.role}
                label={humanizeToken(w.role)}
                value={w.exists ? `Checklist current · updated ${_fmtAgo(w.last_modified_at)}` : "Checklist missing"}
                testId={`walk-${String(w.role).toLowerCase()}`}
              />
            )) : <FactRow label="Walk coverage" value="No field walk checklist evidence returned" testId="walks-empty" />}
          </SectionCard>

          <SectionCard title="Open governance gaps" status={dr.status} summary={driftSummary} testId="self-protection-drift">
            <FactRow label="Open gaps" value={dr.open_gaps} testId="drift-total" />
            <FactRow label="Context gaps" value={dr.context_tbd} testId="drift-ctx-tbd" />
            <FactRow label="Authority violations" value={dr.authority_violations} testId="drift-auth-v" />
            <FactRow label="Authority warnings under review" value={dr.authority_warnings} testId="drift-auth-w" />
          </SectionCard>

          <SectionCard title="Deployment lineage" status={dp.status} summary={deploymentSummary} testId="self-protection-deployment">
            <FactRow label="Current release fingerprint" value={dp.source_hash ? dp.source_hash.slice(0, 12) : "Not recorded"} testId="deploy-current" />
            <FactRow label="Recorded at" value={dp.deployed_at ? _fmtAgo(dp.deployed_at) : "Not recorded yet"} testId="deploy-recorded" />
            <FactRow label="Previous release fingerprint" value={dp.prior_source_hash ? dp.prior_source_hash.slice(0, 12) : "No prior fingerprint"} testId="deploy-prior" />
            <FactRow label="Previous recorded at" value={dp.prior_deployed_at ? _fmtAgo(dp.prior_deployed_at) : "No earlier deployment recorded"} testId="deploy-prior-recorded" />
            <FactRow label="History entries retained" value={dp.history_size != null ? dp.history_size : "No history count returned"} testId="deploy-history-size" />
          </SectionCard>
        </div>

        <footer className="text-[10px] text-slate-400 pt-3 border-t border-slate-200 font-mono">
          Read-only operational status · no PII · no analytics · no charts.
          Sources: authority probe · TRUST_SURFACES.json ·
          SHARED_SURFACE_CONTEXT_MATRIX.json · TRUTHFUL_STATE_TEST_MATRIX.json ·
          TELEMETRY_SIGNAL_MATRIX.json · FIELD_WALK_CHECKLISTS/.
        </footer>
      </div>
    </LegacyAdminModernShell>
  );
}
