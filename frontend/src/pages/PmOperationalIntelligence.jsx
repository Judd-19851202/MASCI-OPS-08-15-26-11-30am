import React from "react";
import {
  fetchPmDashboard, fetchPmAttention, fetchAdminDelays,
} from "@/lib/odsIntelligenceApi";
import {
  PresetPicker, HorizonHeader, KpiTile, AttentionList,
  EmptyEvidence, EvidenceFooter,
} from "@/components/ods/HorizonPrimitives";

/**
 * DR-ROI-001E · PM Operational Intelligence
 *
 * Three horizons, every KPI backed by verified ODS data.
 *  1. What Happened      — total labor / equipment / production / loads.
 *  2. What Is Happening  — production mix + delay categories in range.
 *  3. What Needs Attention — safety / quality / delay / readiness facts
 *                            with fact-level source traceability.
 */
export default function PmOperationalIntelligence() {
  const [preset, setPreset] = React.useState("this_week");
  const [dash, setDash] = React.useState(null);
  const [attention, setAttention] = React.useState(null);
  const [delays, setDelays] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);
        const [d, a, dl] = await Promise.all([
          fetchPmDashboard({ preset }),
          fetchPmAttention({ preset }),
          fetchAdminDelays({ preset }),
        ]);
        if (!alive) return;
        setDash(d);
        setAttention(a);
        setDelays(dl);
      } catch (e) {
        if (alive) setErr(e?.message || "Load failed");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [preset]);

  const kpis = dash?.kpis || {};
  const projects = dash?.projects || [];
  const production = kpis.production_by_cost_code || {};
  const delayCats = delays?.by_category || [];
  const items = attention?.items || {};

  const daysReported = projects.reduce((n, p) => n + (p.days_reported || 0), 0);
  const projectsWithData = projects.length;

  return (
    <div className="min-h-screen bg-neutral-50" data-testid="pm-intel-page">
      <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-8">
        <header className="flex items-baseline justify-between gap-4 flex-wrap">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-neutral-500">
              PM operational intelligence
            </div>
            <h1 className="text-2xl font-semibold text-neutral-900">
              Project Health & Production
            </h1>
          </div>
          <PresetPicker value={preset} onChange={setPreset} testid="pm-intel-preset-picker" />
        </header>

        {err ? (
          <div className="text-sm text-red-700" data-testid="pm-intel-error">
            {String(err)}
          </div>
        ) : null}
        {loading ? (
          <div className="text-sm text-neutral-500" data-testid="pm-intel-loading">
            Loading operational evidence…
          </div>
        ) : null}

        {/* ============================================================ */}
        {/* HORIZON 1 · What Happened                                     */}
        {/* ============================================================ */}
        <section data-testid="pm-horizon-1">
          <HorizonHeader
            number={1}
            title="What Happened"
            subtitle="Confirmed operational totals in the selected range"
            testid="pm-horizon-1-header"
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="pm-intel-kpis">
            <KpiTile
              label="Labor hours"
              value={kpis.labor_hours ?? 0}
              unit="hrs"
              testid="pm-kpi-labor"
              footnote="labor_fact"
            />
            <KpiTile
              label="Equipment hours"
              value={kpis.equipment_hours ?? 0}
              unit="hrs"
              testid="pm-kpi-equipment"
              footnote="equipment_fact"
            />
            <KpiTile
              label="Photos"
              value={kpis.photo_count ?? 0}
              testid="pm-kpi-photos"
              footnote="photo_evidence_fact"
            />
            <KpiTile
              label="Days reported"
              value={daysReported}
              testid="pm-kpi-days"
              footnote={`${projectsWithData} project${projectsWithData === 1 ? "" : "s"}`}
            />
          </div>
        </section>

        {/* ============================================================ */}
        {/* HORIZON 2 · What Is Happening                                 */}
        {/* ============================================================ */}
        <section data-testid="pm-horizon-2">
          <HorizonHeader
            number={2}
            title="What Is Happening"
            subtitle="Production mix + delay categories in range"
            testid="pm-horizon-2-header"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              className="rounded-lg border border-neutral-200 bg-white p-4"
              data-testid="pm-intel-production"
            >
              <div className="text-xs uppercase tracking-widest text-neutral-500 mb-2">
                Production by cost code
              </div>
              {Object.keys(production).length === 0 ? (
                <EmptyEvidence label="No production recorded in this range." />
              ) : (
                <ul className="text-sm divide-y divide-neutral-100">
                  {Object.entries(production)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 8)
                    .map(([code, qty]) => (
                      <li
                        key={code}
                        className="flex justify-between py-1.5"
                        data-testid={`pm-prod-${code}`}
                      >
                        <span className="font-mono text-neutral-700 truncate">{code}</span>
                        <span className="tabular-nums text-neutral-900">{qty}</span>
                      </li>
                    ))}
                </ul>
              )}
            </div>

            <div
              className="rounded-lg border border-neutral-200 bg-white p-4"
              data-testid="pm-intel-delays"
            >
              <div className="text-xs uppercase tracking-widest text-neutral-500 mb-2">
                Delay categories
              </div>
              {delayCats.length === 0 ? (
                <EmptyEvidence label="No delays recorded in this range." />
              ) : (
                <ul className="text-sm divide-y divide-neutral-100">
                  {delayCats.slice(0, 8).map((r) => (
                    <li
                      key={r.category}
                      className="flex justify-between py-1.5"
                      data-testid={`pm-delay-${r.category}`}
                    >
                      <span className="capitalize text-neutral-700">
                        {String(r.category).replaceAll("_", " ")}
                      </span>
                      <span className="tabular-nums text-neutral-900">
                        {r.hours}h · {r.count} events
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div
            className="mt-4 rounded-lg border border-neutral-200 bg-white p-4"
            data-testid="pm-intel-projects"
          >
            <div className="text-xs uppercase tracking-widest text-neutral-500 mb-3">
              Project roll-up · sorted by delay + safety
            </div>
            {projects.length === 0 ? (
              <EmptyEvidence label="No projects reported in this range." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-[10px] uppercase text-neutral-500">
                    <tr>
                      <th className="text-left py-1.5">Project</th>
                      <th className="text-right py-1.5">Labor</th>
                      <th className="text-right py-1.5">Equip</th>
                      <th className="text-right py-1.5">Delay hrs</th>
                      <th className="text-right py-1.5">Safety</th>
                      <th className="text-right py-1.5">Blockers</th>
                      <th className="text-right py-1.5">Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((p) => (
                      <tr
                        key={p.project_id}
                        className="border-t border-neutral-100"
                        data-testid={`pm-project-row-${p.project_id}`}
                      >
                        <td className="py-1.5 font-mono text-neutral-800">{p.project_id}</td>
                        <td className="py-1.5 text-right tabular-nums">{p.labor_hours}</td>
                        <td className="py-1.5 text-right tabular-nums">{p.equipment_hours}</td>
                        <td className="py-1.5 text-right tabular-nums">{p.delay_hours}</td>
                        <td className="py-1.5 text-right tabular-nums">{p.safety_flag_count}</td>
                        <td className="py-1.5 text-right tabular-nums">
                          {p.readiness_blocker_count}
                        </td>
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

        {/* ============================================================ */}
        {/* HORIZON 3 · What Needs Attention                              */}
        {/* ============================================================ */}
        <section data-testid="pm-horizon-3">
          <HorizonHeader
            number={3}
            title="What Needs Attention"
            subtitle={`${attention?.total || 0} evidence-linked items`}
            testid="pm-horizon-3-header"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AttentionList
              title="Safety findings"
              items={items.safety}
              kind="safety"
              testid="pm-attention-safety"
            />
            <AttentionList
              title="Quality findings"
              items={items.quality}
              kind="quality"
              testid="pm-attention-quality"
            />
            <AttentionList
              title="Active delays"
              items={items.delay}
              kind="delay"
              testid="pm-attention-delay"
            />
            <AttentionList
              title="Readiness blockers"
              items={items.readiness}
              kind="readiness"
              testid="pm-attention-readiness"
            />
          </div>
        </section>

        <EvidenceFooter />
      </div>
    </div>
  );
}
