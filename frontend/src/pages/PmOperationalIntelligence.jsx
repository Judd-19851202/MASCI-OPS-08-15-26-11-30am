import React from "react";
import {
  fetchPmDashboard, fetchPmAttention, fetchAdminDelays,
  fetchPmProjectOperationalIntelligence,
} from "@/lib/odsIntelligenceApi";
import {
  PresetPicker, HorizonHeader, KpiTile, AttentionList,
  EmptyEvidence, EvidenceFooter,
} from "@/components/ods/HorizonPrimitives";
import { OperationalIntelligenceCard } from "@/components/ods/OperationalIntelligenceCard";
import { DrV2ApprovedReportsPanel } from "@/components/DrV2ApprovedReportsPanel";
import PmShell from "@/components/PmShell";
import { Activity } from "lucide-react";
import { DataTable } from "@/design-system";

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
  const [intel, setIntel] = React.useState(null);
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
        // TRACK 22.9C · Pull the accepted operational summary + photo
        // observation tags for the top project (by labor hours) from
        // canonical ODS facts. Skipped silently on any error — the
        // card component hides itself when both arrays are empty.
        const projects = d?.projects || [];
        const topProject = projects
          .slice()
          .sort((a1, b1) => (b1.labor_hours || 0) - (a1.labor_hours || 0))[0];
        if (topProject?.project_id) {
          try {
            const it = await fetchPmProjectOperationalIntelligence(
              topProject.project_id, { preset, limit: 5 },
            );
            if (alive) setIntel(it);
          } catch (_e) {
            if (alive) setIntel(null);
          }
        } else if (alive) {
          setIntel(null);
        }
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

  const projectColumns = React.useMemo(() => ([
    {
      key: "project",
      header: "Project",
      render: (p) => <span className="font-mono text-neutral-800">{p.project_id}</span>,
    },
    { key: "labor_hours", header: "Labor", align: "right", render: (p) => <span className="tabular-nums">{p.labor_hours}</span> },
    { key: "equipment_hours", header: "Equip", align: "right", render: (p) => <span className="tabular-nums">{p.equipment_hours}</span> },
    { key: "delay_hours", header: "Delay hrs", align: "right", render: (p) => <span className="tabular-nums">{p.delay_hours}</span> },
    { key: "safety_flag_count", header: "Safety", align: "right", render: (p) => <span className="tabular-nums">{p.safety_flag_count}</span> },
    { key: "readiness_blocker_count", header: "Blockers", align: "right", render: (p) => <span className="tabular-nums">{p.readiness_blocker_count}</span> },
    { key: "days_reported", header: "Days", align: "right", render: (p) => <span className="tabular-nums text-neutral-500">{p.days_reported}</span> },
  ]), []);

  return (
    <PmShell
      title="Operational Intelligence"
      section="operational-intelligence"
      intro={
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div className="text-sm text-slate-700 leading-relaxed">
            Three horizons over your assigned projects — What Happened,
            What Is Happening, What Needs Attention. Every KPI, delay,
            finding, and operational summary is backed by canonical ODS
            facts with source traceability.
          </div>
        </div>
      }
    >
      <div className="space-y-8" data-testid="pm-intel-page">
        <div className="flex items-baseline justify-between gap-4 flex-wrap">
          <div className="text-xs uppercase tracking-widest text-neutral-500">
            {loading ? "Loading operational evidence…" : "Range"}
          </div>
          <PresetPicker
            value={preset}
            onChange={setPreset}
            testid="pm-intel-preset-picker"
          />
        </div>

        {err ? (
          <div className="text-sm text-red-700" data-testid="pm-intel-error">
            {String(err)}
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
              <DataTable
                columns={projectColumns}
                rows={projects}
                rowKey={(p) => p.project_id}
                density="compact"
                tableMinWidth="760px"
                data-testid="pm-intel-projects-table"
                getRowTestId={(p) => `pm-project-row-${p.project_id}`}
              />
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
            {items.operational_summary && items.operational_summary.length > 0 ? (
              <AttentionList
                title="Recent operational summaries"
                items={items.operational_summary}
                kind="operational summary"
                testid="pm-attention-operational-summary"
              />
            ) : null}
          </div>
        </section>

        {/* TRACK 22.9C · Recent Operational Intelligence card (top project) */}
        {intel && intel.enabled ? (
          <OperationalIntelligenceCard
            summaries={intel.summaries}
            photoTags={intel.photo_observation_tags}
            title={
              intel.project_id
                ? `Recent Operational Intelligence · ${intel.project_id}`
                : "Recent Operational Intelligence"
            }
            testid="pm-operational-intelligence-card"
          />
        ) : null}

        {/* DR-UNIFY-002 · Approved Daily Reports PDF export (PM · project-scoped) */}
        <section data-testid="pm-approved-daily-reports">
          <HorizonHeader
            number={4}
            title="Approved Daily Reports"
            subtitle="Canonical English PDF export · management access only"
            testid="pm-horizon-4-header"
          />
          <DrV2ApprovedReportsPanel audience="pm" />
        </section>

        <EvidenceFooter />
      </div>
    </PmShell>
  );
}
