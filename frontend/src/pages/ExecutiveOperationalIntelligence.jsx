import React from "react";
import { api } from "@/lib/api";
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
  const [oppc, setOppc] = React.useState(null);
  const [briefing, setBriefing] = React.useState(null);
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
        const [oppcRes, briefingRes] = await Promise.all([
          api.get("/oppc/enterprise/executive-operations-center").then((r) => r.data).catch(() => null),
          api.get("/oppc/enterprise/monday-briefing").then((r) => r.data).catch(() => null),
        ]);
        const oppcJson = oppcRes || null;
        const briefingJson = briefingRes || null;
        if (!alive) return;
        setDash(d);
        setHealth(h);
        setAttention(a);
        setOppc(oppcJson);
        setBriefing(briefingJson?.briefing || null);
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
  const oppcSummary = oppc?.summary || {};

  const runBriefingAction = async (path) => {
    try {
      const res = await api.post(`/oppc/enterprise/monday-briefing/${path}`, {});
      setBriefing(res.data?.briefing || null);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Briefing action failed");
    }
  };

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
            <KpiTile
              label="OPPC open variances"
              value={oppcSummary.open_variances ?? 0}
              testid="exec-kpi-oppc-variances"
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

        {oppc ? (
          <section data-testid="exec-horizon-oppc">
            <HorizonHeader
              number="OPPC"
              title="Enterprise Operations Center"
              subtitle="Canonical variance, recovery, and resource coordination"
              testid="exec-horizon-oppc-header"
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-risk">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">Projects at risk</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.what_is_at_risk || []).slice(0, 6).map((item) => (
                    <div key={item.project_number} className="flex items-center justify-between gap-3">
                      <span>{item.project_number}</span>
                      <span className="text-xs text-neutral-500">Recovery {item.recovery_overdue || 0}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-conflicts">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">Resource conflicts</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.resource_conflicts || []).slice(0, 6).map((item, idx) => (
                    <div key={`${item.resource_key}-${idx}`}>
                      <div className="font-semibold">{item.conflict_type.replaceAll("_", " ")}</div>
                      <div className="text-xs text-neutral-500">{item.project_number} · {item.why}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-recovery">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">Recovery overdue</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.recovery_overdue || []).slice(0, 6).map((item) => (
                    <div key={item.variance_key}>
                      <div className="font-semibold">{item.project_number} · {item.strategy || "strategy pending"}</div>
                      <div className="text-xs text-neutral-500">{item.recovery_status} · {item.recovery_priority}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        ) : null}

        {briefing ? (
          <section data-testid="exec-horizon-briefing">
            <HorizonHeader
              number="BRIEF"
              title="Monday Morning Briefing"
              subtitle="Portfolio briefing lifecycle, freeze state, and executive narrative"
              testid="exec-horizon-briefing-header"
            />
            <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-4" data-testid="exec-briefing-panel">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-neutral-500">Status</div>
                  <div className="text-lg font-semibold text-neutral-900" data-testid="exec-briefing-status">{briefing.status || "draft"}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold" onClick={() => runBriefingAction("generate")} data-testid="exec-briefing-generate">Generate</button>
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold" onClick={() => runBriefingAction("approve")} data-testid="exec-briefing-approve">Approve</button>
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold" onClick={() => runBriefingAction("freeze")} data-testid="exec-briefing-freeze">Freeze</button>
                  <a className="rounded-md border border-neutral-900 bg-neutral-900 px-3 py-2 text-xs font-semibold text-white" href={`${process.env.REACT_APP_BACKEND_URL}/api/oppc/enterprise/monday-briefing/pdf`} target="_blank" rel="noreferrer" data-testid="exec-briefing-pdf">Open PDF</a>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-3 text-sm">
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-week-ending">Week ending: {briefing.week_ending || "—"}</div>
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-generated">Generated: {briefing.generated_at || "—"}</div>
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-hash">Hash: {briefing.content_hash || "—"}</div>
              </div>
              <div className="space-y-2 text-sm text-neutral-700" data-testid="exec-briefing-summary-lines">
                {(briefing.summary_lines || []).map((line, idx) => <div key={`${line}-${idx}`}>{line}</div>)}
              </div>
              <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-xs text-neutral-600" data-testid="exec-briefing-warnings">Warnings: {(briefing.warnings || []).join(" · ") || "None"}</div>
            </div>
          </section>
        ) : null}

        {/* DR-UNIFY-002 · Executive surface deferred until real Executive Portal exists.
            The Approved Daily Reports panel lives on the PM + Admin dashboards. */}

        <EvidenceFooter />
      </div>
    </div>
  );
}
