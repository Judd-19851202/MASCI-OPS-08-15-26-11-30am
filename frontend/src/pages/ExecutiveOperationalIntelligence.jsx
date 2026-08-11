import React from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import {
  fetchAdminDashboard, fetchExecutiveHealth, fetchAdminAttention,
} from "@/lib/odsIntelligenceApi";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { DataTable } from "@/design-system";
import {
  PresetPicker, HorizonHeader, KpiTile, AttentionList,
  EmptyEvidence, EvidenceFooter,
} from "@/components/ods/HorizonPrimitives";
import { formatPlatformTime } from "@/lib/platformTime";
import { useT } from "@/lib/i18n";
import { isReleaseDeferred } from "@/lib/releaseScope";
import { formatOperatorJobLabel, sanitizeOperatorCopy, sanitizeOperatorProjectNumber, sanitizeOperatorProjectName } from "@/lib/operatorLanguage";

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

function briefingStatusLabel(status, t) {
  if (!status) return t("Not generated yet");
  return t(humanizeToken(status));
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
  const { t } = useT();
  const briefingPdfDeferred = isReleaseDeferred("executiveMondayBriefingPdf");
  const [preset, setPreset] = React.useState("month");
  const [dash, setDash] = React.useState(null);
  const [health, setHealth] = React.useState(null);
  const [attention, setAttention] = React.useState(null);
  const [oppc, setOppc] = React.useState(null);
  const [briefing, setBriefing] = React.useState(null);
  const [loadingState, setLoadingState] = React.useState({
    dashboard: false,
    health: false,
    attention: false,
    oppc: false,
    briefing: false,
  });
  const [err, setErr] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    setErr(null);
    setLoadingState({
      dashboard: true,
      health: true,
      attention: true,
      oppc: true,
      briefing: true,
    });

    const markLoaded = (key) => {
      if (!alive) return;
      setLoadingState((prev) => ({ ...prev, [key]: false }));
    };

    const captureError = (message) => {
      if (!alive || !message) return;
      setErr((prev) => prev || message);
    };

    fetchAdminDashboard({ preset })
      .then((data) => {
        if (alive) setDash(data);
      })
      .catch((e) => captureError(e?.message || t("Could not load dashboard totals.")))
      .finally(() => markLoaded("dashboard"));

    fetchExecutiveHealth({ preset })
      .then((data) => {
        if (alive) setHealth(data);
      })
      .catch((e) => captureError(e?.message || t("Could not load at-risk projects.")))
      .finally(() => markLoaded("health"));

    fetchAdminAttention({ preset, limit: 15 })
      .then((data) => {
        if (alive) setAttention(data);
      })
      .catch((e) => captureError(e?.message || t("Could not load attention items.")))
      .finally(() => markLoaded("attention"));

    api.get("/oppc/enterprise/executive-operations-center")
      .then((r) => {
        if (alive) setOppc(r.data || null);
      })
      .catch(() => {
        if (alive) setOppc(null);
      })
      .finally(() => markLoaded("oppc"));

    api.get("/oppc/enterprise/monday-briefing")
      .then((r) => {
        if (alive) setBriefing(r.data?.briefing || null);
      })
      .catch(() => {
        if (alive) setBriefing(null);
      })
      .finally(() => markLoaded("briefing"));

    return () => { alive = false; };
  }, [preset, t]);

  const kpis = dash?.company_kpis || {};
  const atRisk = health?.top_at_risk || [];
  const totalProjects = health?.total_projects || 0;
  const items = attention?.items || {};
  const oppcSummary = oppc?.summary || {};
  const approvalHistory = briefing?.approval_history || [];
  const loading = Object.values(loadingState).some(Boolean);
  const initialLoad = loading
    && dash === null
    && health === null
    && attention === null
    && oppc === null
    && briefing === null;
  const itemsSummaryLoading = loadingState.attention && !attention;
  const projectsSummaryLoading = loadingState.health && !health;
  const briefingSummaryLoading = loadingState.briefing && !briefing;
  const horizon1Loading = loadingState.dashboard || loadingState.health || loadingState.oppc;
  const horizon2Loading = loadingState.health;
  const horizon3Loading = loadingState.attention;
  const briefingLoading = loadingState.briefing;

  const atRiskColumns = React.useMemo(() => ([
    {
      key: "project",
          header: t("Project"),
      render: (p) => (
        <div>
              <div className="font-semibold text-neutral-900">{sanitizeOperatorProjectName(p.project_name, t("Project name not reported"))}</div>
              <div className="text-xs text-neutral-500">{sanitizeOperatorProjectNumber(p.project_number || p.project_id, t("Project reference not reported"))}</div>
        </div>
      ),
      wrap: true,
    },
    { key: "delay_hours", header: t("Delay hrs"), align: "right", render: (p) => <span className="tabular-nums">{p.delay_hours}</span> },
    { key: "safety_flag_count", header: t("Safety"), align: "right", render: (p) => <span className="tabular-nums">{p.safety_flag_count}</span> },
    { key: "readiness_blocker_count", header: t("Blockers"), align: "right", render: (p) => <span className="tabular-nums">{p.readiness_blocker_count}</span> },
    { key: "labor_hours", header: t("Labor hrs"), align: "right", render: (p) => <span className="tabular-nums">{p.labor_hours}</span> },
    { key: "days_reported", header: t("Days"), align: "right", render: (p) => <span className="tabular-nums text-neutral-500">{p.days_reported}</span> },
  ]), [t]);

  const runBriefingAction = async (path) => {
    try {
      const res = await api.post(`/oppc/enterprise/monday-briefing/${path}`, {});
      setBriefing(res.data?.briefing || null);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || t("Briefing action failed"));
    }
  };

  return (
    <LegacyAdminModernShell
      title={t("Executive Operations Dashboard")}
      subtitle={t("Portfolio-wide operating picture for leadership decisions, briefing readiness, and resource risk.")}
      breadcrumb={[{ label: t("Executive Oversight"), to: "/admin/executive-overview" }, { label: t("Executive Operations Dashboard") }]}
      testidPrefix="exec-intel"
    >
      <div className="space-y-8" data-testid="exec-intel-page">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl space-y-2">
              <div className="text-[10px] uppercase tracking-[0.22em] text-slate-500 font-mono">
                {t("Executive operations dashboard")}
              </div>
              <h1 className="text-2xl font-black text-slate-950">
                {t("What needs leadership attention right now")}
              </h1>
              <p className="text-sm text-slate-700 leading-relaxed">
                {t("Start with the issues that need leadership action, then review what changed in the selected period and whether the enterprise briefing is ready to send.")}
              </p>
              <div className="rounded-2xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-900" data-testid="exec-intel-portfolio-link-callout">
                {t("Use")} <Link to="/admin/executive-overview" className="font-semibold underline" data-testid="exec-intel-portfolio-link">{t("Portfolio Performance")}</Link> {t("for cross-project cost, schedule, commitments, and current reporting.")}
              </div>
            </div>
            <PresetPicker value={preset} onChange={setPreset} testid="exec-intel-preset-picker" />
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <SummaryStatCard
              label={t("Items needing review")}
              value={itemsSummaryLoading ? null : attention?.total || 0}
              testId="exec-summary-items"
            />
            <SummaryStatCard
              label={t("Projects reporting")}
              value={projectsSummaryLoading ? null : totalProjects}
              testId="exec-summary-projects"
            />
            <SummaryStatusCard
              label={t("Briefing status")}
              value={briefingSummaryLoading ? null : briefingStatusLabel(briefing?.status, t)}
              testId="exec-summary-briefing-status"
            />
          </div>
        </section>

        {err ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" data-testid="exec-intel-error">
            {String(err)}
          </div>
        ) : null}
        {loading ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500" data-testid="exec-intel-loading">
            {initialLoad ? t("Loading the current operating picture…") : t("Updating the remaining sections…")}
          </div>
        ) : null}

        {/* HORIZON 1 · What Happened */}
        <section data-testid="exec-horizon-1">
          <HorizonHeader
            number={1}
            title={t("What happened")}
            subtitle={t("Portfolio totals in range")}
            testid="exec-horizon-1-header"
          />
          {horizon1Loading && !dash && !health && !oppc ? (
            <SectionPlaceholder
              message={t("Waiting for portfolio totals, project counts, and current variance posture…")}
              testId="exec-horizon-1-loading"
            />
          ) : (
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
                footnote="Projects with current reporting in the selected period."
              />
              <KpiTile
                label="Photos captured"
                value={kpis.photo_count ?? 0}
                testid="exec-kpi-photos"
                footnote="Field photos added by crews and supervisors."
              />
              <KpiTile
                label="Open executive variances"
                value={oppcSummary.open_variances ?? 0}
                testid="exec-kpi-oppc-variances"
                footnote="Variance items still open in the enterprise operations center."
              />
            </div>
          )}
        </section>

        {/* HORIZON 2 · What Is Happening */}
        <section data-testid="exec-horizon-2">
          <HorizonHeader
            number={2}
            title={t("Which projects are carrying the most operating friction")}
            subtitle={t("Delay, safety, and readiness issues that are rising to the top")}
            testid="exec-horizon-2-header"
          />
          <div
            className="rounded-lg border border-neutral-200 bg-white p-4"
            data-testid="exec-at-risk"
          >
            {horizon2Loading && !health ? (
              <SectionPlaceholder
                message={t("Checking which projects are carrying the most delay, safety, and readiness friction…")}
                testId="exec-at-risk-loading"
              />
            ) : atRisk.length === 0 ? (
              <div data-testid="exec-at-risk-table">
                <EmptyEvidence label={t("No at-risk projects in this range.")} />
              </div>
            ) : (
              <DataTable
                columns={atRiskColumns}
                rows={atRisk}
                rowKey={(p) => p.project_id}
                density="compact"
                tableMinWidth="760px"
                data-testid="exec-at-risk-table"
                getRowTestId={(p) => `exec-atrisk-row-${p.project_id}`}
              />
            )}
          </div>
        </section>

        {/* HORIZON 3 · What Needs Attention */}
        <section data-testid="exec-horizon-3">
          <HorizonHeader
            number={3}
            title={t("What needs attention")}
            subtitle={horizon3Loading && !attention ? t("Checking current attention queues") : `${attention?.total || 0} ${t("items need review")}`}
            testid="exec-horizon-3-header"
          />
          {horizon3Loading && !attention ? (
            <SectionPlaceholder
              message={t("Loading the safety, quality, delay, and readiness queues…")}
              testId="exec-horizon-3-loading"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AttentionList
                title={t("Safety findings")}
                items={items.safety}
                kind="safety"
                testid="exec-attention-safety"
              />
              <AttentionList
                title={t("Quality findings")}
                items={items.quality}
                kind="quality"
                testid="exec-attention-quality"
              />
              <AttentionList
                title={t("Active delays")}
                items={items.delay}
                kind="delay"
                testid="exec-attention-delay"
              />
              <AttentionList
                title={t("Readiness blockers")}
                items={items.readiness}
                kind="readiness"
                testid="exec-attention-readiness"
              />
            </div>
          )}
        </section>

        {oppc ? (
          <section data-testid="exec-horizon-oppc">
            <HorizonHeader
              number="OPPC"
              title="Enterprise Operations Center"
              subtitle={t("Variance, recovery, and resource coordination that may require leadership intervention")}
              testid="exec-horizon-oppc-header"
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-risk">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">{t("Projects needing leadership review")}</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.what_is_at_risk || []).slice(0, 6).map((item) => (
                    <div key={item.project_number} className="flex items-center justify-between gap-3">
                      <span>{formatOperatorJobLabel(item.project_number, item.project_name)}</span>
                      <span className="text-xs text-neutral-500">{t("Recovery overdue")} {item.recovery_overdue || 0}</span>
                    </div>
                  ))}
                  {!(oppc.what_is_at_risk || []).length ? <EmptyEvidence label={t("No portfolio projects are currently escalated for leadership review.")} /> : null}
                </div>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-conflicts">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">{t("Resource conflicts")}</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.resource_conflicts || []).slice(0, 6).map((item, idx) => (
                    <div key={`${item.resource_key}-${idx}`}>
                      <div className="font-semibold">{humanizeToken(item.conflict_type)}</div>
                      <div className="text-xs text-neutral-500">{sanitizeOperatorProjectNumber(item.project_number, t("Project reference not reported"))} · {sanitizeOperatorCopy(item.why, item.why || t("Details pending"))}</div>
                    </div>
                  ))}
                  {!(oppc.resource_conflicts || []).length ? <EmptyEvidence label={t("No active resource conflicts are reported right now.")} /> : null}
                </div>
              </div>
              <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid="exec-oppc-recovery">
                <div className="text-[10px] uppercase tracking-widest text-neutral-500">{t("Recovery plans that slipped")}</div>
                <div className="mt-3 space-y-2 text-sm text-neutral-700">
                  {(oppc.recovery_overdue || []).slice(0, 6).map((item) => (
                    <div key={item.variance_key || item.project_number}>
                      <div className="font-semibold">{sanitizeOperatorProjectNumber(item.project_number, t("Project reference not reported"))} · {sanitizeOperatorCopy(item.strategy, item.strategy || t("strategy pending"))}</div>
                      <div className="text-xs text-neutral-500">{humanizeToken(item.recovery_status)} · {humanizeToken(item.recovery_priority)}</div>
                    </div>
                  ))}
                  {!(oppc.recovery_overdue || []).length ? <EmptyEvidence label={t("No overdue recovery plans are reported right now.")} /> : null}
                </div>
              </div>
            </div>
          </section>
        ) : null}

        <section data-testid="exec-horizon-briefing">
            <HorizonHeader
              number="BRIEF"
              title="Monday Morning Briefing"
              subtitle={t("Briefing readiness, approval state, and current summary lines")}
              testid="exec-horizon-briefing-header"
            />
            <div className="rounded-lg border border-neutral-200 bg-white p-4 space-y-4" data-testid="exec-briefing-panel">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-neutral-500">Status</div>
                  <div className="text-lg font-semibold text-neutral-900" data-testid="exec-briefing-status">{briefingLoading && !briefing ? t("Loading current briefing status…") : briefingStatusLabel(briefing?.status, t)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold disabled:opacity-50" onClick={() => runBriefingAction("generate")} data-testid="exec-briefing-generate" disabled={briefingLoading && !briefing}>{t("Generate latest")}</button>
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold disabled:opacity-50" onClick={() => runBriefingAction("approve")} data-testid="exec-briefing-approve" disabled={briefingLoading && !briefing}>{t("Approve")}</button>
                  <button className="rounded-md border border-neutral-300 px-3 py-2 text-xs font-semibold disabled:opacity-50" onClick={() => runBriefingAction("freeze")} data-testid="exec-briefing-freeze" disabled={briefingLoading && !briefing}>{t("Freeze")}</button>
                  {briefingPdfDeferred ? <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900" data-testid="exec-briefing-pdf-deferred">{t("PDF is not available on this page yet.")}</div> : <a className="rounded-md border border-neutral-900 bg-neutral-900 px-3 py-2 text-xs font-semibold text-white" href={`${process.env.REACT_APP_BACKEND_URL}/api/oppc/enterprise/monday-briefing/pdf`} target="_blank" rel="noreferrer" data-testid="exec-briefing-pdf">{t("Open PDF")}</a>}
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-3 text-sm">
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-week-ending">{t("Week ending")}: {briefingLoading && !briefing ? t("Loading…") : briefing?.week_ending || t("Not selected yet")}</div>
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-generated">{t("Generated")}: {briefingLoading && !briefing ? t("Loading…") : fmtTs(briefing?.generated_at)}</div>
                <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3" data-testid="exec-briefing-history">{t("Approvals and freezes recorded")}: {briefingLoading && !briefing ? "—" : approvalHistory.length}</div>
              </div>
              <div className="space-y-2 text-sm text-neutral-700" data-testid="exec-briefing-summary-lines">
                {briefingLoading && !briefing ? <div className="text-neutral-500">{t("Loading the latest briefing summary lines…")}</div> : null}
                {!(briefingLoading && !briefing) ? (briefing?.summary_lines || []).map((line, idx) => <div key={`${line}-${idx}`}>{line}</div>) : null}
                {!(briefingLoading && !briefing) && !(briefing?.summary_lines || []).length ? <div className="text-neutral-500">{t("No executive summary lines are published yet. Generate the latest briefing to build the current summary from operating records.")}</div> : null}
              </div>
              <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-xs text-neutral-600" data-testid="exec-briefing-warnings">{t("Warnings")}: {briefingLoading && !briefing ? t("Loading…") : (briefing?.warnings || []).join(" · ") || t("No warning text was returned")}</div>
            </div>
          </section>

        {/* DR-UNIFY-002 · Executive surface deferred until real Executive Portal exists.
            The Approved Daily Reports panel lives on the PM + Admin dashboards. */}

        <EvidenceFooter />
      </div>
    </LegacyAdminModernShell>
  );
}

function SummaryStatCard({ label, value, testId }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={testId}>
      <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">{label}</div>
      <div className="mt-1 text-2xl font-black text-slate-950">{value == null ? "—" : value}</div>
      {value == null ? <div className="mt-2 text-xs text-slate-500">Loading current records…</div> : null}
    </div>
  );
}

function SummaryStatusCard({ label, value, testId }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={testId}>
      <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">{label}</div>
      <div className="mt-1 text-sm font-semibold text-slate-950">{value || "Loading current records…"}</div>
    </div>
  );
}

function SectionPlaceholder({ message, testId }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600" data-testid={testId}>
      {message}
    </div>
  );
}
