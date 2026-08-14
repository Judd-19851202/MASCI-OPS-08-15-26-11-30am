// Track 13.6H · Phase 4 — Safety Recovery (live hub).
//
// MOUNTED AT: /safety-portal/hub_v2 (behind RequireSafety — same gate
// as /safety-portal). Classic /safety-portal hub preserved unchanged.
//
// REAL DATA ONLY: pulls every count from /api/safety/overview which
// already aggregates the real Safety engines (incidents, CAPAs, fire
// extinguishers, training records, safety documents, trench safety).
//
// Every card opens an existing Safety route — no placeholders, no
// future buttons. Trench Safety is the benchmark and stays untouched.
//
// One question this surface answers:
//   "What safety work requires attention right now?"

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getDirectoryToken } from "@/lib/directoryAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import SafetyOperationalKpisCard from "@/components/SafetyOperationalKpisCard";
import SafetyTrenchIntelligenceCard from "@/components/SafetyTrenchIntelligenceCard";
import {
  PortalShell,
  StatusChip,
  Card,
  EmptyState,
} from "../design-system";
import SafetySideNavV2 from "@/components/safety/sidebar/SafetySideNavV2";
import OiAttentionStrip from "@/components/operational_intelligence/OiAttentionStrip";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
import { useT } from "@/lib/i18n";
import { KpiInlineHelp } from "@/components/KpiInlineHelp";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const d = getDirectoryToken();
  const s = getSafetyToken();
  if (a) h["X-Admin-Token"] = a;
  if (d) h["X-Directory-Token"] = d;
  if (s) h["X-Safety-Token"] = s;
  return h;
}

async function safeJson(path) {
  try {
    const r = await fetch(`${API}${path}`, { headers: authHeaders() });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body };
  } catch {
    return { ok: false, status: 0, body: null };
  }
}

function useSafetySignals() {
  const [s, setS] = useState({
    loaded: false,
    refreshedAt: null,
    capas_open: null,
    capas_overdue: null,
    fire_ext_overdue: null,
    training_expired: null,
    training_expiring_30d: null,
    incidents_last_7d: null,
    safety_documents_total: null,
    // TRACK 22.4a · Canonical Trench Safety active-asset count wired
    // to the same source /trench-safety uses (see F22-4-006).
    trench_active_assets: null,
    trench_loaded: false,
    metadata: null,
  });

  useEffect(() => {
    let cancelled = false;
    safeJson("/api/safety/overview").then((r) => {
      if (cancelled) return;
      const b = r.body || {};
      setS((prev) => ({
        ...prev,
        loaded: true,
        refreshedAt: new Date().toISOString(),
        metadata: r.ok ? (b.kpi_metadata || null) : null,
        capas_open:             r.ok ? (b.corrective_actions_open ?? null) : null,
        capas_overdue:          r.ok ? (b.corrective_actions_overdue ?? null) : null,
        fire_ext_overdue:       r.ok ? (b.fire_extinguishers_overdue ?? null) : null,
        training_expired:       r.ok ? (b.training_expired ?? null) : null,
        training_expiring_30d:  r.ok ? (b.training_expiring_30d ?? null) : null,
        incidents_last_7d:      r.ok ? (b.incidents_last_7d ?? null) : null,
        safety_documents_total: r.ok ? (b.safety_documents_total ?? null) : null,
      }));
    });
    // Track 22.4a — separately load canonical Trench Safety count so
    // the Safety Portal tile is honest, not a hard-coded null.
    safeJson("/api/trench-safety/dashboard").then((r) => {
      if (cancelled) return;
      const b = r.body || {};
      setS((prev) => ({
        ...prev,
        trench_loaded: true,
        trench_active_assets: r.ok ? (b.total_active_assets ?? null) : null,
      }));
    });
    return () => { cancelled = true; };
  }, []);

  return s;
}

function SectionHeader({ kicker, title, caption, action }) {
  const { t } = useT();
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
      <div>
        <div style={{ fontSize: "var(--kicker-size)", letterSpacing: "var(--kicker-tracking)", fontWeight: "var(--kicker-weight)", textTransform: "uppercase", color: "var(--ink-faint)" }}>{t(kicker)}</div>
        <h2 style={{ margin: "2px 0 0", fontSize: 18, fontWeight: 700, color: "var(--ink-strong)", fontFamily: "var(--font-display)" }}>{t(title)}</h2>
        {caption && <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>{t(caption)}</p>}
      </div>
      {action}
    </div>
  );
}

function RealLink({ to, testid, children, intent = "default" }) {
  const { t } = useT();
  const tone = intent === "primary"
    ? { bg: "var(--brand-primary)", color: "var(--brand-on-primary)", border: "var(--brand-primary)" }
    : { bg: "var(--paper-card)", color: "var(--ink-strong)", border: "var(--border-bold)" };
  return (
    <Link to={to} data-testid={testid} style={{
      display: "inline-block", padding: "6px 12px", background: tone.bg, color: tone.color,
      border: `1px solid ${tone.border}`, borderRadius: "var(--radius-card)",
      fontSize: 12, fontWeight: 600, textDecoration: "none",
    }}>{typeof children === "string" ? t(children) : children}</Link>
  );
}

function QueueCard({ to, testid, title, why, source, value, loaded, variantWhenAttention = "warning" }) {
  const { t } = useT();
  const isAttention = loaded && typeof value === "number" && value > 0;
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <Card
        title={t(title)}
        description={t(why)}
        metric={loaded ? (value === null ? "—" : value) : "…"}
        variant={isAttention ? variantWhenAttention : "default"}
        status={
          !loaded ? <StatusChip severity="neutral" compact label={t("Loading")} />
          : value === null ? <StatusChip statusKey="offline_feed" compact />
          : isAttention ? <StatusChip statusKey="pending_verification" compact />
          : <StatusChip statusKey="verified" compact />
        }
      >
        <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
          {t(source)}
        </p>
      </Card>
    </Link>
  );
}

export default function SafetyHubV2() {
  const { t } = useT();
  const s = useSafetySignals();

  const allZero = s.loaded && [
    s.capas_open, s.capas_overdue, s.fire_ext_overdue,
    s.training_expired, s.training_expiring_30d, s.incidents_last_7d,
  ].every((v) => v === null || v === 0);

  return (
    <div data-testid="safety-hub-page" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Safety Operations"
        pageTitle={t("What safety work requires attention right now?")}
        subtitle={t("Every queue is a live count — open it to see what Safety needs to act on today. Trench Safety workflows live under Trench Safety.")}
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/safety/trench-safety" testid="safety-hub-v2-action-trench" intent="primary">Trench Safety</RealLink>
          </div>
        }
        sideNav={<SafetySideNavV2 />}
        lastActivity={
          <span data-testid="safety-hub-v2-last-activity">
            {s.loaded ? t("Refreshed {time}").replace("{time}", formatPlatformTimeOnly(s.refreshedAt)) : t("Loading live signals…")}
          </span>
        }
      >
        <section className="wp17-mission-banner" data-testid="safety-hub-v2-mission-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">Today’s focus</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">Reduce field risk by turning incidents, corrective actions, and compliance gaps into the next visible action.</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                See incidents, corrective actions, and gaps early so the field gets answers fast.
              </p>
            </div>
          </div>
        </section>

        {/* Track 19.52 · P1 #1 — OI Attention Strip.
           Consumes GET /api/operational-intelligence/summary and
           surfaces the safety_morning_digest signal (score · attention
           level · top attention label) at the top of the Safety Hub.
           Zero-drift: no new backend, no new score model. */}
        <OiAttentionStrip
          portal="safety"
          productIds={["safety_morning_digest"]}
          title="Safety focus right now"
          testId="safety-hub-v2-oi-strip"
        />

        {/* TRACK 23.8 · Company-wide Safety Operational KPIs.
            Consumes shared Track 23.7 aggregator spine · one identity
            for numbers · safety-first framing · project drilldown. */}
        <div data-testid="safety-kpi-strip" style={{ margin: "16px 0 20px 0" }}>
          <SafetyOperationalKpisCard />
        </div>

        {/* TRACK 23.10-D · Safety Portal Trench & Excavation Intelligence.
            Consumes 23.10-B Qualifications Engine + 23.10-C project
            linker/facts. Read-only. Zero cost. Honest source
            classification (LIVE/PARTIAL/MISSING per linkage). */}
        <div style={{ margin: "0 0 28px 0" }}>
          <SafetyTrenchIntelligenceCard />
        </div>

        {/* Section 1 — Corrective Actions (CAPAs). */}
        <section data-testid="safety-hub-v2-section-capas" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="01 · Corrective Actions · live"
            title="Open and overdue corrective actions"
            caption="These live counts show what Safety needs to close, verify, or push today."
            action={<KpiInlineHelp metadata={s.metadata?.sections?.corrective_actions} fallbackLabel="Safety corrective actions" testId="safety-hub-v2-capas-help" />}
          />
          <div data-testid="safety-hub-v2-queue-grid-capas"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/corrective-actions?focus_filter=open"
              testid="safety-hub-v2-queue-capas-open"
              title="Open corrective actions"
              why="Corrective actions are still open, in progress, or waiting for review"
              source="Live count · open or in-progress"
              value={s.capas_open}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/corrective-actions?focus_filter=overdue"
              testid="safety-hub-v2-queue-capas-overdue"
              title="Overdue corrective actions"
              why="Corrective actions are past due and need immediate follow-up"
              source="Live count · past due date"
              value={s.capas_overdue}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 2 — Compliance: fire extinguishers + training. */}
        <section data-testid="safety-hub-v2-section-compliance" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="02 · Compliance · live"
            title="Expirations and inspections"
            caption="These dates show what has expired, what is overdue, and what needs to be scheduled next."
            action={<KpiInlineHelp metadata={s.metadata?.sections?.compliance} fallbackLabel="Safety compliance snapshot" testId="safety-hub-v2-compliance-help" />}
          />
          <div data-testid="safety-hub-v2-queue-grid-compliance"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/fire-extinguishers?focus_filter=overdue"
              testid="safety-hub-v2-queue-fire-ext-overdue"
              title="Fire extinguishers overdue"
              why="These units are past their next required inspection date"
              source="Live count · past inspection date"
              value={s.fire_ext_overdue}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/training?focus_filter=expired"
              testid="safety-hub-v2-queue-training-expired"
              title="Training expired"
              why="These records are expired and need recertification"
              source="Live count · past expiration"
              value={s.training_expired}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/training?focus_filter=expiring_30d"
              testid="safety-hub-v2-queue-training-expiring"
              title="Training expiring in 30 days"
              why="These records expire soon and should be scheduled now"
              source="Live count · expiring inside 30 days"
              value={s.training_expiring_30d}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 3 — Incidents (read-only context). */}
        <section data-testid="safety-hub-v2-section-incidents" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="03 · Incidents · recent activity"
            title="Incidents reported in the last 7 days"
            caption="Use these counts to decide where Safety follow-up is needed first."
            action={<KpiInlineHelp metadata={s.metadata?.sections?.incidents} fallbackLabel="Safety incident activity" testId="safety-hub-v2-incidents-help" />}
          />
          <div data-testid="safety-hub-v2-queue-grid-incidents"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/incidents"
              testid="safety-hub-v2-queue-incidents-7d"
              title="Incidents in the last 7 days"
              why="Documented incidents reported in the past week"
              source="Live count · documented this week"
              value={s.incidents_last_7d}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety/trench-safety"
              testid="safety-hub-v2-queue-trench-safety"
              title="Active trench-safety assets"
              why="Track daily inspections, permits, and competent-person signoffs"
              source="Live count · trench-safety records"
              value={s.trench_active_assets}
              loaded={s.trench_loaded}
            />
            <QueueCard
              to="/safety-portal/documents"
              testid="safety-hub-v2-queue-documents"
              title="Safety documents on file"
              why="Reference docs — JHAs · SDS · regulatory posters"
              source="Live count · safety document library"
              value={s.safety_documents_total}
              loaded={s.loaded}
              variantWhenAttention="default"
            />
          </div>
        </section>

        {/* TRACK 14.0-DISCOVERABILITY · Wave B (2026-02-15)
           Section 4 — Field Records & Plans. Three Safety records were
           Wave A discoverability defects: tailgate / toolbox meetings,
           site inspections, JHA plans. Surfacing them here puts them
           one click away from the Safety Hub. Each tile deep-links
           into the SF-guarded list page (added in this track). */}
        <section data-testid="safety-hub-v2-section-field-records" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="04 · Field records · plans on file"
            title="Toolbox talks, site inspections, and JHA plans"
            caption="Open the records Safety teams use every day without digging through menus."
          />
          <div data-testid="safety-hub-v2-queue-grid-field-records"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/meetings"
              testid="safety-hub-v2-queue-meetings"
              title="Safety Meetings"
              why="Toolbox talks · pre-shift huddles · jobsite topic reviews"
              source="Live count · safety meetings on file"
              value={null}
              loaded={true}
              variantWhenAttention="default"
            />
            <QueueCard
              to="/safety-portal/inspections"
              testid="safety-hub-v2-queue-inspections"
              title="Site Inspections"
              why="Job-site walkthroughs · hazard observations · grading"
              source="Live count · inspections on file"
              value={null}
              loaded={true}
              variantWhenAttention="default"
            />
            <QueueCard
              to="/safety-portal/jha-plans"
              testid="safety-hub-v2-queue-jha-plans"
              title="JHA plans"
              why="Job hazard analyses · crew sign-offs · revisions"
              source="Live count · JHA plans on file"
              value={null}
              loaded={true}
              variantWhenAttention="default"
            />
          </div>
        </section>

        {allZero && (
          <EmptyState
            testId="safety-hub-v2-all-clear"
            title="Safety is all clear."
            explanation="No corrective actions are open, no inspections are overdue, no training is expired, and no incidents were logged in the last 7 days."
            severity="good"
          />
        )}

      </PortalShell>
    </div>
  );
}
