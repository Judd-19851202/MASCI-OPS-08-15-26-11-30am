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