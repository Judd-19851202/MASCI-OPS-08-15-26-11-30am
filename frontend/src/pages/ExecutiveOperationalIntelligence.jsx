import React from "react";
import { api } from "@/lib/api";
import {
  fetchAdminDashboard, fetchExecutiveHealth, fetchAdminAttention,
} from "@/lib/odsIntelligenceApi";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import {
  PresetPicker, HorizonHeader, KpiTile, AttentionList,
  EmptyEvidence, EvidenceFooter,
} from "@/components/ods/HorizonPrimitives";
import { formatPlatformTime } from "@/lib/platformTime";

function humanizeToken(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function fmtTs(value) {
  if (!value) return "Not reported";
  try {
    return formatPlatformTime(value);
  } catch {
    return String(value);
  }
}

function briefingStatusLabel(status) {
  if (!status) return "Not generated yet";
  return humanizeToken(status);
}

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
  const approvalHistory = briefing?.approval_history || [];

  const runBriefingAction = async (path) => {
    try {
      const res = await api.post(`/oppc/enterprise/monday-briefing/${path}`, {});
      setBriefing(res.data?.briefing || null);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Briefing action failed");
    }
  };

  return (
    <LegacyAdminModernShell
      title="Executive Operational Intelligence"
      subtitle="Portfolio-wide operating picture for leadership decisions, briefing readiness, and resource risk."
      breadcrumb={[{ label: "Executive Oversight", to: "/admin/executive-overview" }, { label: "Executive Operational Intelligence" }]}
      testidPrefix="exec-intel"
    >
      <div className="space-y-8" data-testid="exec-intel-page">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl space-y-2">
              <div className="text-[10px] uppercase tracking-[0.22em] text-slate-500 font-mono">
                Executive operational intelligence
              </div>
              <h1 className="text-2xl font-black text-slate-950">
                Portfolio snapshot in plain English
              </h1>
              <p className="text-sm text-slate-700 leading-relaxed">
                Use this page to understand what landed in the selected period, which projects need leadership attention, and whether the enterprise briefing is ready for distribution. OPPC is shown here as the enterprise operations center, not as unexplained backend shorthand.
              </p>
            </div>
            <PresetPicker value={preset} onChange={setPreset} testid="exec-intel-preset-picker" />
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Projects reporting</div>
              <div className="mt-1 text-2xl font-black text-slate-950">{totalProjects}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Resource conflicts</div>
              <div className="mt-1 text-2xl font-black text-slate-950">{oppcSummary.resource_conflicts ?? 0}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Briefing status</div>
              <div className="mt-1 text-sm font-semibold text-slate-950">{briefingStatusLabel(briefing?.status)}</div>
            </div>
          </div>
        </section>

        {err ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" data-testid="exec-intel-error">
            {String(err)}
          </div>
        ) : null}
        {loading ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500" data-testid="exec-intel-loading">
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
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3" data-testid="exec-intel-kpis">
            <KpiTile
              label="Total labor hours"
              value={kpis.labor_hours ?? 0}
              unit="hrs"
              testid="exec-kpi-labor"
              footnote="Crew time captured from operational reporting."
            />
            <KpiTile
              label="Total equipment hours"
              value={kpis.equipment_hours ?? 0}
              unit="hrs"
              testid="exec-kpi-equipment"
              footnote="Live equipment use recorded in the selected period."
            />
            <KpiTile
              label="Projects reporting"
              value={totalProjects}
              testid="exec-kpi-projects"
              footnote="Projects with usable reporting evidence in range."
            />
            <KpiTile
              label="Photos captured"
              value={kpis.photo_count ?? 0}
              testid="exec-kpi-photos"
              footnote="Field evidence added by crews and supervisors."
            />
            <KpiTile
              label="Open executive variances"
              value={oppcSummary.open_variances ?? 0}
              testid="exec-kpi-oppc-variances"
              footnote="Variance items still open in the enterprise operations center."
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
                        <td className="py-1.5 text-neutral-800">
                          <div className="font-semibold">{p.project_name || "Project name not reported"}</div>
                          <div className="text-xs text-neutral-500">{p.project_number || p.project_id || "Project reference not reported"}</div>
                        </td>
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
              subtitle="Variance, recovery, and resource coordination from the canonical enterprise operations center"
              testid="exec-horizon-oppc-header"
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-risk">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">Projects needing leadership review</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.what_is_at_risk || []).slice(0, 6).map((item) => (
                    <div key={item.project_number} className="flex items-center justify-between gap-3">
                      <span>{item.project_name || item.project_number}</span>
                      <span className="text-xs text-neutral-500">Recovery overdue {item.recovery_overdue || 0}</span>
                    </div>
                  ))}
                  {!(oppc.what_is_at_risk || []).length ? <EmptyEvidence label="No portfolio projects are currently escalated for leadership review." /> : null}
                </div>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-conflicts">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">Resource conflicts</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.resource_conflicts || []).slice(0, 6).map((item, idx) => (
                    <div key={`${item.resource_key}-${idx}`}>
                      <div className="font-semibold">{humanizeToken(item.conflict_type)}</div>
                      <div className="text-xs text-neutral-500">{item.project_number} · {item.why}</div>
                    </div>
                  ))}
                  {!(oppc.resource_conflicts || []).length ? <EmptyEvidence label="No active resource conflicts are reported right now." /> : null}
                </div>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-recovery">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">Recovery plans that slipped</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.recovery_overdue || []).slice(0, 6).map((item) => (
                    <div key={item.variance_key || item.project_number}>
                      <div className="font-semibold">{item.project_number} · {item.strategy || "strategy pending"}</div>
                      <div className="text-xs text-neutral-500">{humanizeToken(item.recovery_status)} · {humanizeToken(item.recovery_priority)}</div>
                    </div>
                  ))}
                  {!(oppc.recovery_overdue || []).length ? <EmptyEvidence label="No overdue recovery plans are reported right now." /> : null}
                </div>
              </div>
            </div>
          </section>
        ) : null}

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
                  <div className="text-lg font-semibold text-neutral-900" data-testid="exec-briefing-status">{briefingStatusLabel(briefing?.status)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold" onClick={() => runBriefingAction("generate")} data-testid="exec-briefing-generate">Generate latest</button>
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold" onClick={() => runBriefingAction("approve")} data-testid="exec-briefing-approve">Approve</button>
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold" onClick={() => runBriefingAction("freeze")} data-testid="exec-briefing-freeze">Freeze</button>
                  <a className="rounded-md border border-neutral-900 bg-neutral-900 px-3 py-2 text-xs font-semibold text-white" href={`${process.env.REACT_APP_BACKEND_URL}/api/oppc/enterprise/monday-briefing/pdf`} target="_blank" rel="noreferrer" data-testid="exec-briefing-pdf">Open PDF</a>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-3 text-sm">
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-week-ending">Week ending: {briefing?.week_ending || "Not selected yet"}</div>
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-generated">Generated: {fmtTs(briefing?.generated_at)}</div>
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-history">Approvals and freezes recorded: {approvalHistory.length}</div>
              </div>
              <div className="space-y-2 text-sm text-neutral-700" data-testid="exec-briefing-summary-lines">
                {(briefing?.summary_lines || []).map((line, idx) => <div key={`${line}-${idx}`}>{line}</div>)}
                {!(briefing?.summary_lines || []).length ? <div className="text-neutral-500">No executive narrative is published yet. Generate the latest briefing to build the summary from current operating evidence.</div> : null}
              </div>
              <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-xs text-neutral-600" data-testid="exec-briefing-warnings">Warnings: {(briefing?.warnings || []).join(" · ") || "No warning text was returned"}</div>
            </div>
          </section>

        {/* DR-UNIFY-002 · Executive surface deferred until real Executive Portal exists.
            The Approved Daily Reports panel lives on the PM + Admin dashboards. */}

        <EvidenceFooter />
      </div>
    </LegacyAdminModernShell>
  );
}
