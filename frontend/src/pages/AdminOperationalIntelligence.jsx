import React from "react";
import {
  fetchAdminDashboard, fetchAdminDelays, fetchAdminAttention,
} from "@/lib/odsIntelligenceApi";
import {
  PresetPicker, HorizonHeader, KpiTile, AttentionList,
  EmptyEvidence, EvidenceFooter,
} from "@/components/ods/HorizonPrimitives";

/**
 * DR-ROI-001E · Admin Operational Intelligence (company-wide).
 *
 * Three horizons:
 *   1. What Happened     — company totals for labor / equipment / photos / projects.
 *   2. What Is Happening — project health roll-up + delay category breakdown.
 *   3. What Needs Attention — safety / quality / delay / readiness facts
 *                             with fact-id + source traceability.
 */
export default function AdminOperationalIntelligence() {
  const [preset, setPreset] = React.useState("this_week");
  const [dash, setDash] = React.useState(null);
  const [delays, setDelays] = React.useState(null);
  const [attention, setAttention] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);
        const [d, dl, a] = await Promise.all([
          fetchAdminDashboard({ preset }),
          fetchAdminDelays({ preset }),
          fetchAdminAttention({ preset }),
        ]);
        if (!alive) return;
        setDash(d);
        setDelays(dl);
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
  const health = dash?.projects_health || [];
  const delayCats = delays?.by_category || [];
  const items = attention?.items || {};

  return (
    <div className="min-h-screen bg-neutral-50" data-testid="admin-intel-page">
      <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-8">
        <header className="flex items-baseline justify-between gap-4 flex-wrap">
          <div>
            <div className="text-[10px] uppercase tracking-widest text-neutral-500">
              Company operational intelligence
            </div>
            <h1 className="text-2xl font-semibold text-neutral-900">
              Admin & Executive View
            </h1>
          </div>
          <PresetPicker value={preset} onChange={setPreset} testid="admin-intel-preset-picker" />
        </header>

        {err ? (
          <div className="text-sm text-red-700" data-testid="admin-intel-error">
            {String(err)}
          </div>
        ) : null}
        {loading ? (
          <div className="text-sm text-neutral-500" data-testid="admin-intel-loading">
            Loading operational evidence…
          </div>
        ) : null}

        {/* ============================================================ */}
        {/* HORIZON 1 · What Happened                                     */}
        {/* ============================================================ */}
        <section data-testid="admin-horizon-1">
          <HorizonHeader
            number={1}
            title="What Happened"
            subtitle="Confirmed company-wide totals in range"
            testid="admin-horizon-1-header"
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="admin-intel-kpis">
            <KpiTile
              label="Labor hours"
              value={kpis.labor_hours ?? 0}
              unit="hrs"
              testid="admin-kpi-labor"
              footnote="labor_fact"
            />
            <KpiTile
              label="Equipment hours"
              value={kpis.equipment_hours ?? 0}
              unit="hrs"
              testid="admin-kpi-equipment"
              footnote="equipment_fact"
            />
            <KpiTile
              label="Photos"
              value={kpis.photo_count ?? 0}
              testid="admin-kpi-photos"
              footnote="photo_evidence_fact"
            />
            <KpiTile
              label="Projects reporting"
              value={(kpis.projects_included || []).length}
              testid="admin-kpi-projects"
              footnote="from operational_kpi_snapshots"
            />
          </div>
        </section>

        {/* ============================================================ */}
        {/* HORIZON 2 · What Is Happening                                 */}
        {/* ============================================================ */}
        <section data-testid="admin-horizon-2">
          <HorizonHeader
            number={2}
            title="What Is Happening"
            subtitle="Project health roll-up + delay categories"
            testid="admin-horizon-2-header"
          />
          <div
            className="rounded-lg border border-neutral-200 bg-white p-4"
            data-testid="admin-projects-health"
          >
            <div className="text-xs uppercase tracking-widest text-neutral-500 mb-3">
              Project health · sorted by delay + safety
            </div>
            {health.length === 0 ? (
              <EmptyEvidence label="No projects reported in this range." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-[10px] uppercase text-neutral-500">
                    <tr>
                      <th className="text-left py-1.5">Project</th>
                      <th className="text-right py-1.5">Labor hrs</th>
                      <th className="text-right py-1.5">Equip hrs</th>
                      <th className="text-right py-1.5">Delay hrs</th>
                      <th className="text-right py-1.5">Safety</th>
                      <th className="text-right py-1.5">Blockers</th>
                      <th className="text-right py-1.5">Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {health.map((p) => (
                      <tr
                        key={p.project_id}
                        className="border-t border-neutral-100"
                        data-testid={`admin-project-row-${p.project_id}`}
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

          <div
            className="mt-4 rounded-lg border border-neutral-200 bg-white p-4"
            data-testid="admin-delay-breakdown"
          >
            <div className="text-xs uppercase tracking-widest text-neutral-500 mb-2">
              Top delay categories
            </div>
            {delayCats.length === 0 ? (
              <EmptyEvidence label="No delays recorded in this range." />
            ) : (
              <ul className="text-sm divide-y divide-neutral-100">
                {delayCats.slice(0, 8).map((r) => (
                  <li
                    key={r.category}
                    className="flex justify-between py-1.5"
                    data-testid={`admin-delay-${r.category}`}
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
        </section>

        {/* ============================================================ */}
        {/* HORIZON 3 · What Needs Attention                              */}
        {/* ============================================================ */}
        <section data-testid="admin-horizon-3">
          <HorizonHeader
            number={3}
            title="What Needs Attention"
            subtitle={`${attention?.total || 0} evidence-linked items`}
            testid="admin-horizon-3-header"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AttentionList
              title="Safety findings"
              items={items.safety}
              kind="safety"
              testid="admin-attention-safety"
            />
            <AttentionList
              title="Quality findings"
              items={items.quality}
              kind="quality"
              testid="admin-attention-quality"
            />
            <AttentionList
              title="Active delays"
              items={items.delay}
              kind="delay"
              testid="admin-attention-delay"
            />
            <AttentionList
              title="Readiness blockers"
              items={items.readiness}
              kind="readiness"
              testid="admin-attention-readiness"
            />
          </div>
        </section>

        <EvidenceFooter />
      </div>
    </div>
  );
}
