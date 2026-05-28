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
import { Link } from "react-router-dom";
import AdminShell from "@/components/AdminShell";
import { api } from "@/lib/api";

const POLL_MS = 60_000;

function StatusPill({ status, testId }) {
  const map = {
    green:   { label: "OK",      cls: "border-emerald-700 text-emerald-700 bg-emerald-50" },
    amber:   { label: "WATCH",   cls: "border-amber-700 text-amber-800 bg-amber-50" },
    red:     { label: "FAIL",    cls: "border-rose-700 text-rose-700 bg-rose-50" },
    unknown: { label: "UNKNOWN", cls: "border-slate-400 text-slate-500 bg-slate-50" },
  };
  const m = map[status] || map.unknown;
  return (
    <span
      data-testid={testId}
      data-status={status}
      className={`inline-block px-2 py-0.5 rounded-sm border font-mono text-[10px] uppercase tracking-[0.18em] ${m.cls}`}
    >
      {m.label}
    </span>
  );
}

function _fmtAgo(epoch_s) {
  if (!epoch_s) return "—";
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

function Section({ title, status, children, testId }) {
  return (
    <section
      data-testid={testId}
      className="border-t border-slate-300/60 first:border-t-0 py-4"
    >
      <header className="flex items-baseline gap-3 mb-2">
        <h2 className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-700">
          {title}
        </h2>
        <StatusPill status={status} testId={`${testId}-pill`} />
      </header>
      <div className="font-mono text-[12px] text-slate-700 space-y-1">
        {children}
      </div>
    </section>
  );
}

function Row({ label, value, testId }) {
  return (
    <div className="grid grid-cols-[14rem_1fr] gap-2" data-testid={testId}>
      <span className="text-slate-500 uppercase tracking-wider text-[10px]">
        {label}
      </span>
      <span className="text-slate-800 break-all">{value ?? "—"}</span>
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
      <AdminShell active="governance">
        <div className="p-6 max-w-3xl">
          <h1 className="font-mono text-[12px] uppercase tracking-[0.25em] text-slate-700 mb-2">
            Governance · Self-Protection
          </h1>
          <p className="text-slate-700 text-sm" data-testid="self-protection-error">
            {err}
          </p>
        </div>
      </AdminShell>
    );
  }

  if (!data) {
    return (
      <AdminShell active="governance">
        <div className="p-6 max-w-3xl" data-testid="self-protection-loading">
          <h1 className="font-mono text-[12px] uppercase tracking-[0.25em] text-slate-700 mb-2">
            Governance · Self-Protection
          </h1>
          <p className="text-slate-500 text-sm">Reading governance state…</p>
        </div>
      </AdminShell>
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

  return (
    <AdminShell active="governance">
      <div
        className="p-6 max-w-3xl bg-slate-50 min-h-screen"
        data-testid="self-protection-page"
      >
        <header className="mb-4 pb-3 border-b border-slate-300/80">
          <div className="flex items-baseline justify-between gap-4">
            <div>
              <h1
                className="font-mono text-[12px] uppercase tracking-[0.3em] text-slate-700"
                data-testid="self-protection-title"
              >
                Governance · Self-Protection
              </h1>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Operational integrity of the platform's own governance layer ·{" "}
                <Link to="/admin/governance"
                      className="underline hover:text-slate-700">
                  back to governance
                </Link>
              </p>
            </div>
            <div className="flex items-center gap-2">
              <StatusPill status={data.page_status} testId="self-protection-overall-pill" />
              <button
                type="button"
                onClick={fetchOnce}
                disabled={refreshing}
                data-testid="self-protection-refresh"
                className="font-mono text-[10px] uppercase tracking-wider text-slate-500 hover:text-slate-800 border border-slate-300 px-2 py-1 rounded-sm"
              >
                {refreshing ? "refreshing…" : "refresh"}
              </button>
            </div>
          </div>
          <p className="text-[10px] text-slate-400 mt-1 font-mono">
            loaded {loadedAt ? _fmtAgo(loadedAt / 1000) : "—"} ·
            generated {data.generated_at ? _fmtAgo(data.generated_at) : "—"}
          </p>
        </header>

        <Section title="Authority Protection" status={a.status} testId="self-protection-authority">
          <Row label="Probe status" value={a.status} testId="auth-status" />
          <Row label="New violations" value={a.new_violations} testId="auth-violations" />
          <Row label="New warnings" value={a.new_warnings} testId="auth-warnings" />
          <Row label="Baselined patterns" value={a.baselined} testId="auth-baselined" />
          <Row label="Probe runtime" value={a.scan_ms != null ? `${a.scan_ms} ms` : "—"} testId="auth-runtime" />
          <Row label="Last run" value={a.last_run_at ? _fmtAgo(a.last_run_at) : "—"} testId="auth-last-run" />
        </Section>

        <Section title="Trust Surfaces" status={t.status} testId="self-protection-trust">
          <Row label="Registered surfaces" value={t.registered} testId="trust-registered" />
          <Row label="Live" value={t.live} testId="trust-live" />
          <Row label="Planned" value={t.planned} testId="trust-planned" />
          <Row label="Doctrine fields" value={(t.doctrine_fields || []).length} testId="trust-fields" />
        </Section>

        <Section title="Context Governance" status={c.status} testId="self-protection-context">
          <Row label="Context-governed" value={c.context_governed} testId="ctx-governed" />
          <Row label="TBD (Wave 3)" value={c.tbd} testId="ctx-tbd" />
          <Row label="Planned (Phase V)" value={c.planned} testId="ctx-planned" />
        </Section>

        <Section title="Truthful-State Contracts" status={ts.status} testId="self-protection-truthful">
          <Row label="Contracts declared" value={ts.contracts} testId="truthful-contracts" />
          <Row label="Surfaces covered" value={(ts.surfaces_covered || []).length} testId="truthful-surfaces" />
        </Section>

        <Section title="Telemetry Doctrine" status={tm.status} testId="self-protection-telemetry">
          <Row label="Client signals" value={tm.client_signals} testId="telemetry-client" />
          <Row label="Server signals" value={tm.server_signals} testId="telemetry-server" />
          <Row label="Forbidden patterns documented" value={tm.forbidden_patterns} testId="telemetry-forbidden" />
        </Section>

        <Section title="Regression Suite" status={rg.status} testId="self-protection-regression">
          <Row label="Last iteration report" value={rg.last_iteration || "—"} testId="reg-iteration" />
          <Row label="Last run" value={rg.last_iteration_at ? _fmtAgo(rg.last_iteration_at) : "—"} testId="reg-last" />
        </Section>

        <Section title="Field Walks" status={fw.status} testId="self-protection-walks">
          {(fw.walks || []).map((w) => (
            <Row
              key={w.role}
              label={w.role}
              value={w.exists
                ? `checklist current · updated ${_fmtAgo(w.last_modified_at)}`
                : "checklist missing"}
              testId={`walk-${w.role.toLowerCase()}`}
            />
          ))}
        </Section>

        <Section title="Open Governance Gaps" status={dr.status} testId="self-protection-drift">
          <Row label="Total open gaps" value={dr.open_gaps} testId="drift-total" />
          <Row label="Context TBD" value={dr.context_tbd} testId="drift-ctx-tbd" />
          <Row label="Authority violations" value={dr.authority_violations} testId="drift-auth-v" />
          <Row label="Authority warnings (review)" value={dr.authority_warnings} testId="drift-auth-w" />
        </Section>

        <footer className="text-[10px] text-slate-400 mt-6 pt-3 border-t border-slate-200 font-mono">
          Read-only operational status · no PII · no analytics · no charts.
          Sources: authority probe · TRUST_SURFACES.json ·
          SHARED_SURFACE_CONTEXT_MATRIX.json · TRUTHFUL_STATE_TEST_MATRIX.json ·
          TELEMETRY_SIGNAL_MATRIX.json · FIELD_WALK_CHECKLISTS/.
        </footer>
      </div>
    </AdminShell>
  );
}
