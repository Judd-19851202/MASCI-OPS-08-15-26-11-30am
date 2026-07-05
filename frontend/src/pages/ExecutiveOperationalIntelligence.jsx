import React from "react";
import {
  fetchAdminDashboard, fetchExecutiveHealth, fetchAdminAttention,
} from "@/lib/odsIntelligenceApi";
import {
  PresetPicker, HorizonHeader, KpiTile, AttentionList,
  EmptyEvidence, EvidenceFooter,
} from "@/components/ods/HorizonPrimitives";

/**
 * DR-ROI-001E · Executive Operational Intelligence.
 *
 * Executive-facing view. Same three horizons, tuned for portfolio-level
 * scanning: totals, top-at-risk projects, attention items grouped by
 * category. Every value backed by operational_facts and snapshots — no
 * decorative analytics, no placeholder charts, no AI branding.
 */
export default function ExecutiveOperationalIntelligence() {
  const [preset, setPreset] = React.useState("month");
  const [dash, setDash] = React.useState(null);
  const [health, setHealth] = React.useState(null);
  const [attention, setAttention] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);
        const [d, h, a] = await Promise.all([
          fetchAdminDashboard({ preset }),
          fetchExecutiveHealth({ preset }),
          fetchAdminAttention({ preset, limit: 15 }),
        ]);
        if (!alive) return;
        setDash(d);
        setHealth(h);
        setAttention(a);
      } catch (e) {
        if (alive) setErr(e?.message || "Load failed");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [preset]);

  const kpis = dash?.company_kpis || {};
  const atRisk = health?.top_at_risk || [];
  const totalProjects = health?.total_projects || 0;
  const items = attention?.items || {};

  return (
    <div className="min-h-screen bg-neutral-50" data-testid="exec-intel-page">
      <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-8">
        <header className="flex items-baseline justify-between gap-4 flex-wrap">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-neutral-500">
              Executive operational intelligence
            </div>
            <h1 className="text-2xl font-semibold text-neutral-900">
              Portfolio Snapshot
            </h1>
          </div>
          <PresetPicker value={preset} onChange={setPreset} testid="exec-intel-preset-picker" />
        </header>

        {err ? (
          <div className="text-sm text-red-700" data-testid="exec-intel-error">
            {String(err)}
          </div>
        ) : null}
        {loading ? (
          <div className="text-sm text-neutral-500" data-testid="exec-intel-loading">
            Loading portfolio evidence…
          </div>
        ) : null}

        {/* HORIZON 1 · What Happened */}
        <section data-testid="exec-horizon-1">
          <HorizonHeader
            number={1}
            title="What Happened"
            subtitle="Portfolio totals in range"
            testid="exec-horizon-1-header"
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="exec-intel-kpis">
            <KpiTile
              label="Total labor hours"
              value={kpis.labor_hours ?? 0}
              unit="hrs"
              testid="exec-kpi-labor"
            />
            <KpiTile
              label="Total equipment hours"
              value={kpis.equipment_hours ?? 0}
              unit="hrs"
              testid="exec-kpi-equipment"
            />
            <KpiTile
              label="Projects reporting"
              value={totalProjects}
              testid="exec-kpi-projects"
            />
            <KpiTile
              label="Photos captured"
              value={kpis.photo_count ?? 0}
              testid="exec-kpi-photos"
            />
          </div>
        </section>

        {/* HORIZON 2 · What Is Happening */}
        <section data-testid="exec-horizon-2">
          <HorizonHeader
            number={2}
            title="What Is Happening"
            subtitle="Top-at-risk projects by delay + safety"
            testid="exec-horizon-2-header"
          />
          <div
            className="rounded-lg border border-neutral-200 bg-white p-4"
            data-testid="exec-at-risk"
          >
            {atRisk.length === 0 ? (
              <EmptyEvidence label="No at-risk projects in this range." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-[10px] uppercase text-neutral-500">
                    <tr>
                      <th className="text-left py-1.5">Project</th>
                      <th className="text-right py-1.5">Delay hrs</th>
                      <th className="text-right py-1.5">Safety</th>
                      <th className="text-right py-1.5">Blockers</th>
                      <th className="text-right py-1.5">Labor hrs</th>
                      <th className="text-right py-1.5">Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {atRisk.map((p) => (
                      <tr
                        key={p.project_id}
                        className="border-t border-neutral-100"
                        data-testid={`exec-atrisk-row-${p.project_id}`}
                      >
                        <td className="py-1.5 font-mono text-neutral-800">{p.project_id}</td>
                        <td className="py-1.5 text-right tabular-nums">{p.delay_hours}</td>
                        <td className="py-1.5 text-right tabular-nums">{p.safety_flag_count}</td>
                        <td className="py-1.5 text-right tabular-nums">
                          {p.readiness_blocker_count}
                        </td>
                        <td className="py-1.5 text-right tabular-nums">{p.labor_hours}</td>
                        <td className="py-1.5 text-right tabular-nums text-neutral-500">
                          {p.days_reported}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {/* HORIZON 3 · What Needs Attention */}
        <section data-testid="exec-horizon-3">
          <HorizonHeader
            number={3}
            title="What Needs Attention"
            subtitle={`${attention?.total || 0} evidence-linked items`}
            testid="exec-horizon-3-header"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AttentionList
              title="Safety findings"
              items={items.safety}
              kind="safety"
              testid="exec-attention-safety"
            />
            <AttentionList
              title="Quality findings"
              items={items.quality}
              kind="quality"
              testid="exec-attention-quality"
            />
            <AttentionList
              title="Active delays"
              items={items.delay}
              kind="delay"
              testid="exec-attention-delay"
            />
            <AttentionList
              title="Readiness blockers"
              items={items.readiness}
              kind="readiness"
              testid="exec-attention-readiness"
            />
          </div>
        </section>

        {/* DR-UNIFY-002 · Executive surface deferred until real Executive Portal exists.
            The Approved Daily Reports panel lives on the PM + Admin dashboards. */}

        <EvidenceFooter />
      </div>
    </div>
  );
}
