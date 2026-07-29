import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw } from "lucide-react";

import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { TruthOwnerPanel, HealthCard, EvidenceDrawer, TrustStatusPill, worstStatus, sortCardsByAttention, useEvidenceDrawer } from "@/components/admin/trust/TrustPrimitives";
import { fetchOperationalHealthModule } from "@/lib/enterpriseGovernanceApi";
import { operationalError } from "@/lib/errors";
import { formatPlatformTime } from "@/lib/platformTime";

function countStatuses(sections) {
  const counts = { green: 0, yellow: 0, red: 0, unknown: 0 };
  (sections || []).forEach((section) => {
    (section.cards || []).forEach((card) => {
      const key = card?.status || "unknown";
      counts[key] = (counts[key] || 0) + 1;
    });
  });
  return counts;
}

function DriverCard({ driver, testId }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={testId}>
      <div className="flex flex-wrap items-center gap-2">
        <TrustStatusPill status={(driver.current_state || "unknown").toLowerCase()} testid={`${testId}-status`} />
        <div className="text-sm font-black text-slate-950">{driver.kpi_name}</div>
      </div>
      <div className="mt-2 text-sm text-slate-700">{driver.root_cause}</div>
      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
        <div data-testid={`${testId}-threshold`}><span className="font-semibold text-slate-800">Threshold:</span> {driver.threshold_crossed}</div>
        <div data-testid={`${testId}-owner`}><span className="font-semibold text-slate-800">Owner:</span> {driver.responsible_owner}</div>
        <div data-testid={`${testId}-impact`}><span className="font-semibold text-slate-800">Production impact:</span> {driver.production_impact}</div>
        <div data-testid={`${testId}-cert-impact`}><span className="font-semibold text-slate-800">Affects certification:</span> {driver.affects_wp15_constitutional_certification ? "Yes" : "No"}</div>
      </div>
    </div>
  );
}

export const OperationalHealthDashboardShell = ({ moduleId = "enterprise-governance" }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const { card: drawerCard, open: drawerOpen, setOpen: setDrawerOpen, openWith } = useEvidenceDrawer();

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const next = await fetchOperationalHealthModule(moduleId);
      setData(next || null);
    } catch (err) {
      setError(operationalError(err, "Could not load the operational health dashboard."));
    } finally {
      setLoading(false);
    }
  }, [moduleId]);

  useEffect(() => {
    load();
  }, [load]);

  const sections = data?.sections || [];
  const counts = useMemo(() => data?.counts || countStatuses(sections), [data, sections]);
  const overallStatus = useMemo(() => data?.overall_status || worstStatus(sections.flatMap((section) => section.cards || [])), [data, sections]);

  const filterCard = useCallback((card) => {
    if (statusFilter !== "all" && card.status !== statusFilter) return false;
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return [card.title, card.summary, card.root_cause_explanation, card.evidence_source_label, card.endpoint, card.producer]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q));
  }, [query, statusFilter]);

  return (
    <LegacyAdminModernShell
      title="Operational Health Dashboard"
      subtitle="Enterprise Governance is the first constitutional module on the shared health framework."
      breadcrumb={[{ label: "Governance & Trust", to: "/admin/governance-trust" }, { label: "Operational Health Dashboard" }]}
      testidPrefix="operational-health-dashboard"
      primaryActions={(
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          data-testid="operational-health-refresh"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      )}
    >
      <div className="space-y-6" data-testid="operational-health-dashboard-root">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-hero">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <TrustStatusPill status={overallStatus} testid="operational-health-overall-status" />
                <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-700" data-testid="operational-health-framework-label">
                  {data?.framework_label || "Operational Health Dashboard"}
                </span>
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-950" data-testid="operational-health-title">
                {data?.module?.label || "Enterprise Governance"}
              </h1>
              <p className="text-sm sm:text-base text-slate-700 leading-relaxed" data-testid="operational-health-authority-statement">
                {data?.module?.authority_statement || "This dashboard is a read-only consumer of canonical evidence. Unknown is shown whenever evidence is missing or stale."}
              </p>
            </div>
            <div className="grid min-w-[220px] grid-cols-2 gap-3" data-testid="operational-health-counts">
              {[["green", "Healthy"], ["yellow", "Attention"], ["red", "Critical"], ["unknown", "Unknown"]].map(([key, label]) => (
                <div key={key} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`operational-health-count-${key}`}>
                  <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-mono">{label}</div>
                  <div className="mt-2 text-2xl font-black text-slate-950">{counts[key] || 0}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2" data-testid="operational-health-module-catalog">
            {(data?.module?.future_modules || []).map((module) => (
              module.availability === "live" ? (
                <Link
                  key={module.id}
                  to={module.route}
                  className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-900"
                  data-testid={`operational-health-module-${module.id}`}
                >
                  {module.label} · live
                </Link>
              ) : (
                <span
                  key={module.id}
                  className="rounded-full border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600"
                  data-testid={`operational-health-module-${module.id}`}
                >
                  {module.label} · planned
                </span>
              )
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600" data-testid="operational-health-meta-row">
            <span className="rounded-full bg-slate-100 px-3 py-1">Generated {data?.generated_at ? formatPlatformTime(data.generated_at) : "—"}</span>
            <span className="rounded-full bg-slate-100 px-3 py-1">Primary route {data?.module?.route || "/admin/governance"}</span>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2" data-testid="operational-health-state-split">
          <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm" data-testid="operational-health-certification-card">
            <div className="text-[11px] uppercase tracking-[0.24em] text-emerald-700">Constitutional Certification</div>
            <div className="mt-2 text-3xl font-black text-emerald-950" data-testid="operational-health-certification-state">{data?.constitutional_certification?.state || "—"}</div>
            <div className="mt-3 grid gap-2 text-sm text-emerald-900">
              <div data-testid="operational-health-certification-certified-at"><span className="font-semibold">Certified:</span> {data?.constitutional_certification?.certified_at ? formatPlatformTime(data.constitutional_certification.certified_at) : "—"}</div>
              <div data-testid="operational-health-certification-commit"><span className="font-semibold">Commit:</span> {data?.constitutional_certification?.commit_sha || "—"}</div>
              <div data-testid="operational-health-certification-evidence"><span className="font-semibold">Evidence package:</span> {data?.constitutional_certification?.evidence_package || "—"}</div>
              <div data-testid="operational-health-certification-reasoning">{data?.constitutional_certification?.reasoning || "—"}</div>
            </div>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-live-card">
            <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Current Operational Health</div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <TrustStatusPill status={overallStatus} testid="operational-health-live-status" />
              <div className="text-3xl font-black text-slate-950" data-testid="operational-health-determination">{data?.determination || "—"}</div>
            </div>
            <div className="mt-3 grid gap-2 text-sm text-slate-700">
              <div data-testid="operational-health-evaluated-at"><span className="font-semibold text-slate-900">Evaluated:</span> {data?.current_operational_health?.evaluated_at ? formatPlatformTime(data.current_operational_health.evaluated_at) : "—"}</div>
              <div data-testid="operational-health-primary-reason"><span className="font-semibold text-slate-900">Primary reason:</span> {data?.current_operational_health?.primary_reason || "—"}</div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2" data-testid="operational-health-driver-inventory">
          <div className="rounded-3xl border border-rose-200 bg-rose-50 p-5 shadow-sm" data-testid="operational-health-red-drivers">
            <div className="text-[11px] uppercase tracking-[0.24em] text-rose-700">Exact RED drivers</div>
            <div className="mt-3 space-y-3">
              {(data?.red_drivers || []).map((driver) => <DriverCard key={driver.kpi_id} driver={driver} testId={`operational-health-red-driver-${driver.kpi_id}`} />)}
            </div>
          </div>
          <div className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm" data-testid="operational-health-amber-watchlist">
            <div className="text-[11px] uppercase tracking-[0.24em] text-amber-700">Amber watchlist</div>
            <div className="mt-3 space-y-3">
              {(data?.amber_watchlist || []).map((driver) => <DriverCard key={driver.kpi_id} driver={driver} testId={`operational-health-amber-driver-${driver.kpi_id}`} />)}
            </div>
          </div>
        </section>

        <TruthOwnerPanel
          title="Truth ownership"
          surface={data?.truth_surface}
          relationship={data?.truth_relationship}
          checkedAt={data?.generated_at ? formatPlatformTime(data.generated_at) : "—"}
          testidPrefix="operational-health-truth-owner"
        />

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-quick-links">
          <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Deep links</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {(data?.module?.quick_links || []).map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="rounded-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
                data-testid={`operational-health-link-${link.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </section>

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid="operational-health-error-banner">
            {error}
          </div>
        ) : null}

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-filter-panel">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter by KPI, evidence source, producer, or root cause…"
              className="w-full max-w-xl rounded-full border border-slate-300 bg-slate-50 px-4 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
              data-testid="operational-health-search"
            />
            <div className="flex flex-wrap gap-2" data-testid="operational-health-status-filters">
              {["all", "red", "yellow", "unknown", "green"].map((state) => (
                <button
                  key={state}
                  type="button"
                  onClick={() => setStatusFilter(state)}
                  className={`rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${statusFilter === state ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"}`}
                  data-testid={`operational-health-filter-${state}`}
                >
                  {state}
                </button>
              ))}
            </div>
          </div>
        </section>

        {loading && !data ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600" data-testid="operational-health-loading-banner">
            Loading enterprise governance evidence…
          </div>
        ) : null}

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-status-engine">
          <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Status engine verification</div>
          <div className="mt-2 text-sm text-slate-700" data-testid="operational-health-status-engine-policy">
            {data?.status_engine?.unknown_policy}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(data?.status_engine?.fixture_results || []).map((fixture) => (
              <div key={fixture.fixture_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`operational-health-fixture-${fixture.fixture_id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <TrustStatusPill status={fixture.pass ? "green" : "red"} testid={`operational-health-fixture-${fixture.fixture_id}-status`} />
                  <div className="text-sm font-black text-slate-950">{fixture.fixture_id}</div>
                </div>
                <div className="mt-2 text-xs text-slate-600">{fixture.policy}</div>
                <div className="mt-2 text-xs text-slate-800"><span className="font-semibold">Expected:</span> {fixture.expected.toUpperCase()} · <span className="font-semibold">Actual:</span> {fixture.actual.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-golden-path">
          <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Golden Path monitoring</div>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm" data-testid="operational-health-golden-path-table">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="pb-2 pr-4">Workflow</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Timestamp</th>
                  <th className="pb-2 pr-4">Failed step</th>
                  <th className="pb-2 pr-4">Last success</th>
                  <th className="pb-2 pr-4">Owner</th>
                </tr>
              </thead>
              <tbody>
                {(data?.golden_path?.results || []).map((row) => (
                  <tr key={row.workflow_id} className="border-t border-slate-100" data-testid={`operational-health-golden-path-${row.workflow_id}`}>
                    <td className="py-3 pr-4 font-semibold text-slate-900">{row.label}</td>
                    <td className="py-3 pr-4"><TrustStatusPill status={row.status} testid={`operational-health-golden-path-${row.workflow_id}-status`} /></td>
                    <td className="py-3 pr-4 text-slate-700">{row.timestamp ? formatPlatformTime(row.timestamp) : "—"}</td>
                    <td className="py-3 pr-4 text-slate-700">{row.failed_step || "—"}</td>
                    <td className="py-3 pr-4 text-slate-700">{row.last_successful_run ? formatPlatformTime(row.last_successful_run) : "—"}</td>
                    <td className="py-3 pr-4 text-slate-700">{row.current_owner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-exemptions">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Known exemptions</div>
            <TrustStatusPill status={data?.known_exemptions?.verified ? "green" : "unknown"} testid="operational-health-exemptions-status" />
          </div>
          <div className="mt-2 text-sm text-slate-700" data-testid="operational-health-exemptions-summary">
            {data?.known_exemptions?.count || 0} documented special-case infrastructure exemption(s). They remain visible evidence and do not silently count as healthy state.
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm" data-testid="operational-health-exemptions-table">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="pb-2 pr-4">Entry</th>
                  <th className="pb-2 pr-4">Reason</th>
                  <th className="pb-2 pr-4">Owner</th>
                  <th className="pb-2 pr-4">Review</th>
                </tr>
              </thead>
              <tbody>
                {(data?.known_exemptions?.entries || []).slice(0, 12).map((row) => (
                  <tr key={row.entry_id} className="border-t border-slate-100" data-testid={`operational-health-exemption-${row.entry_id}`}>
                    <td className="py-3 pr-4 font-mono text-xs text-slate-700">{row.entry_id}</td>
                    <td className="py-3 pr-4 text-slate-700">{row.reason}</td>
                    <td className="py-3 pr-4 text-slate-700">{row.architectural_owner}</td>
                    <td className="py-3 pr-4 text-slate-700">{row.review_requirement}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2" data-testid="operational-health-history-row">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-trends">
            <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Historical KPI transitions</div>
            <div className="mt-4 space-y-3">
              {Object.entries(data?.historical_kpi_trends || {}).slice(0, 8).map(([cardId, items]) => (
                <div key={cardId} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`operational-health-trend-${cardId}`}>
                  <div className="text-sm font-black text-slate-950">{cardId}</div>
                  <div className="mt-2 space-y-2 text-xs text-slate-700">
                    {(items || []).slice(-3).map((item, index) => (
                      <div key={`${cardId}-${index}`}>
                        <span className="font-semibold">{item.prior_state || "origin"}</span> → <span className="font-semibold">{item.new_state}</span> · {item.timestamp ? formatPlatformTime(item.timestamp) : "—"}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="operational-health-cert-history">
            <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Certification history</div>
            <div className="mt-4 space-y-3">
              {(data?.certification_history || []).slice(0, 8).map((row, index) => (
                <div key={`${row.event_key || row.timestamp}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4" data-testid={`operational-health-cert-history-${index}`}>
                  <div className="text-sm font-black text-slate-950">{row.determination}</div>
                  <div className="mt-2 text-xs text-slate-700">{row.timestamp ? formatPlatformTime(row.timestamp) : "—"} · commit {row.commit || "—"}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="space-y-6" data-testid="operational-health-sections">
          {sections.map((section) => {
            const filteredCards = sortCardsByAttention((section.cards || []).filter(filterCard));
            return (
              <section key={section.id} className="space-y-3" data-testid={`operational-health-section-${section.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500 font-mono">{section.label}</div>
                  <TrustStatusPill status={section.status || worstStatus(section.cards || [])} testid={`operational-health-section-${section.id}-status`} />
                  <div className="text-[11px] text-slate-400">{filteredCards.length}/{(section.cards || []).length} KPI(s)</div>
                </div>
                {filteredCards.length ? (
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {filteredCards.map((card) => (
                      <HealthCard key={card.id} card={card} onOpen={openWith} testidPrefix="operational-health-card" />
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-5 text-sm text-slate-500" data-testid={`operational-health-section-${section.id}-empty`}>
                    No KPI cards match the current filter.
                  </div>
                )}
              </section>
            );
          })}
        </div>

        <EvidenceDrawer card={drawerCard} open={drawerOpen} onOpenChange={setDrawerOpen} testidPrefix="operational-health-drawer" />
      </div>
    </LegacyAdminModernShell>
  );
};

export default OperationalHealthDashboardShell;