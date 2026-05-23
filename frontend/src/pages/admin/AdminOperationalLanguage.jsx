// AdminOperationalLanguage.jsx — Phase 2 P1+ · Operational Language Glossary
//
// Single source of truth for the operational vocabulary the platform uses.
// Materializes the "one operational language" platform principle. Every
// LifecycleGuide should eventually link here for term definitions.
//
// Each entry includes:
//   - EN + ES name
//   - Operational meaning (what it is)
//   - Lifecycle meaning (where it sits in a workflow)
//   - Accountability meaning (who owns it, who can change it)
//   - Downstream meaning (where it propagates / who consumes it)
//
// Admin-strict route — read-only reference. The glossary is intentionally
// versioned in code (not a CMS) so a Git commit IS the audit trail.

import React, { useMemo, useState } from "react";
import { Search, BookOpen } from "lucide-react";
import { Input } from "@/components/ui/input";
import AdminShell from "@/components/AdminShell";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";

// ──────────────────────────────────────────────────────────────────────
// Glossary entries (canonical operational vocabulary)
// Keep this list ordered by alphabetical EN name.
// When a new operational concept ships, add it here with all 5 sections
// filled. ES values are passed through useT(); the body strings here
// stay in EN with the t() wrapper applied at render time.
// ──────────────────────────────────────────────────────────────────────
const ENTRIES = [
  {
    id: "accountability_timeline",
    en: "Accountability Timeline",
    es: "Línea de Tiempo de Responsabilidad",
    operational: "Chronological record of every operationally-significant event tied to an employee — training, PPE issuance, CAPAs they own or are involved in, incidents, driver-qualification changes, and onboarding/archival events.",
    lifecycle: "Auto-assembled on every read. Never stored as a denormalized table — always derived from the live source-of-truth collections so it cannot drift.",
    accountability: "HR owns the canonical employee master that feeds the timeline. Safety, PM, FL, and Dispatch contribute records that appear on it. Admin has supervisory view.",
    downstream: "Surfaces inside HR Employee Detail, the HR Compliance Brief PDF, and the PM Crew Compliance lens (for project-scoped employees only).",
  },
  {
    id: "archive",
    en: "Archive",
    es: "Archivar",
    operational: "Soft-deletion of a record (employee, equipment, document, etc.). Sets deleted_at; never removes the document from MongoDB.",
    lifecycle: "Archived records leave most operational views but remain queryable for audit/legal continuity. They can be restored. Archive is reversible; hard-delete is not.",
    accountability: "Only Admin (and HR for employees) can archive. Safety / PM / FL / Dispatch never have archive authority — they have read-only visibility.",
    downstream: "Governance Health surfaces \"archived but still flagged active\" as a finding so operators can resolve the contradiction. Compliance Brief PDFs include archive timestamps when relevant.",
  },
  {
    id: "capa",
    en: "CAPA (Corrective & Preventive Action)",
    es: "CAPA (Acción Correctiva y Preventiva)",
    operational: "A discrete corrective action assigned to a named person with a due date. Spawned from incidents, audits, inspections, training findings, or safety meetings.",
    lifecycle: "Pipeline: Open → In Progress → Pending Review → Verified → Closed. Backend enforces every transition; illegal jumps return HTTP 422. Closing without Verified is impossible.",
    accountability: "Safety creates, advances, verifies, and closes. HR adds labor/accountability notes only — no Safety override. PM and FL get read-only visibility on CAPAs affecting their crews. Admin has supervisory authority.",
    downstream: "Surfaces in PM Crew Compliance, HR Accountability Timeline, Governance Health, Compliance Findings, and the Safety/HR digests. Status_history is append-only for OSHA/DOT/insurance review.",
  },
  {
    id: "closeout",
    en: "Closeout",
    es: "Cierre",
    operational: "Final closure of an operational record — most often a CAPA, but also incident closeout, project closeout, or training-cycle closeout.",
    lifecycle: "Closeout requires verification. For a CAPA: Verified by a second reviewer before Closed. For an incident: linked CAPAs must be at Verified or Closed before incident closeout.",
    accountability: "The actor who marks a record Closed is stamped on it (closed_by_name + completed_at). The verifier is separately stamped (verified_by_name + verified_at) — separation of duties.",
    downstream: "Closed records leave open dashboards but remain in the audit trail forever. They appear in Compliance Brief PDFs, Governance Health history, and the CAPA closed-cycle-time operational signal.",
  },
  {
    id: "compliance_finding",
    en: "Compliance Finding",
    es: "Hallazgo de Cumplimiento",
    operational: "A specific operational contradiction detected by the cross-portal Governance engine — e.g., active approved driver with an expired medical card, severe incident without a CAPA, employee name on records that doesn't match the master.",
    lifecycle: "Lifecycle: open → acknowledged → resolved. Findings auto-resolve when the underlying condition disappears (system_auto) and re-open when it returns. Manual acknowledge/resolve attaches a note + admin attribution.",
    accountability: "Admin owns review + resolution. Each finding has a stable id (sha1 of rule+entity) so re-scans don't duplicate. Detection is automatic; remediation is always human-authorized.",
    downstream: "Visible at /admin/governance and /admin/compliance-findings. Aggregated into the Admin and Safety notifications digests.",
  },
  {
    id: "convergence_score",
    en: "Convergence Score",
    es: "Puntuación de Convergencia",
    operational: "Single 0-100 number summarizing platform operational health. Penalized 20 per critical finding, 8 per high, 3 per medium, 1 per low.",
    lifecycle: "Recomputed every time the Governance Summary endpoint is called. Mapped to a label: ≥90 healthy, ≥70 fair, ≥40 degraded, <40 critical.",
    accountability: "Admin owns the convergence target. Each portal's role-scoped digest contributes findings that move the score. A score drop overnight is surfaced in the Admin digest as a Δ.",
    downstream: "Headlines the Governance Health dashboard and the Admin notifications digest. The first metric you should look at every morning.",
  },
  {
    id: "driver_qualified",
    en: "Driver Qualified",
    es: "Conductor Cualificado",
    operational: "An employee is considered qualified to drive when: approved_company_driver=true, medical_card_expiration_date in the future, and CDL (if cdl_holder=true) in the future.",
    lifecycle: "Recomputed live on every read. Never cached. Expirations are surfaced as detector findings (DRV_MED_EXPIRED, DRV_CDL_EXPIRED) the moment they occur.",
    accountability: "HR owns the master record. Dispatch and FL get read-only visibility. PM sees driver availability in their Crew Compliance lens.",
    downstream: "Drivers Available Right Now intelligence tile, Dispatch Driver Qualification view, FL DQ view, PM Crew Compliance lens, Dispatch + HR notifications digests.",
  },
  {
    id: "governance_score",
    en: "Governance Score",
    es: "Puntuación de Gobernanza",
    operational: "Synonym for Convergence Score. Used interchangeably in the Admin dashboard header. Always 0-100.",
    lifecycle: "See Convergence Score.",
    accountability: "See Convergence Score.",
    downstream: "See Convergence Score.",
  },
  {
    id: "lifecycle_guide",
    en: "Lifecycle Guide",
    es: "Guía de Ciclo de Vida",
    operational: "An inline coaching banner that every new operational surface must ship with — explains the workflow's roles, lifecycle, downstream visibility, and why it matters.",
    lifecycle: "Permanent platform architecture rule as of iter356. Every new feature, dashboard, form, or workflow must include a LifecycleGuide. No silent workflows.",
    accountability: "Anyone building a new surface owns the LifecycleGuide content for that surface. The 4 standard sections (Roles · Lifecycle gate · Downstream visibility · Why this matters) are required.",
    downstream: "Rendered inline (no modal interruption). Dismissible per-user via localStorage. ES parity is non-negotiable. Mobile-first.",
  },
  {
    id: "operational_readiness",
    en: "Operational Readiness",
    es: "Preparación Operativa",
    operational: "A crew/employee's fitness for field assignment — current training, PPE accountability, no open critical CAPAs, valid driver qualifications if driving.",
    lifecycle: "Computed live from the source-of-truth collections (no cached readiness scores). A single failure makes the employee \"not ready\" until resolved.",
    accountability: "FL owns operational readiness assessment for assignments. HR + Safety contribute the underlying data. PM sees readiness implications for their projects.",
    downstream: "FL DQ view, PM Crew Compliance, FL accountability widgets, FL notifications digest.",
  },
  {
    id: "verified",
    en: "Verified",
    es: "Verificada",
    operational: "A CAPA status meaning a second reviewer has inspected the corrective work and confirmed it actually happened. Mandatory before Closed.",
    lifecycle: "Inserted between Pending Review and Closed in the iter356 lifecycle upgrade. Stamps verified_at + verified_by_name + verified_by_email.",
    accountability: "Safety owns verification. Ideally a different person than the one who marked Pending Review (separation of duties). The platform stamps both actors onto the record for audit.",
    downstream: "Surfaces as a finding (CAPA_AWAITING_VERIFICATION) if a CAPA sits in Pending Review for >7 days. Visible in the CAPA register filter tabs and the Safety digest.",
  },
];

function GlossaryEntry({ entry }) {
  const { t } = useT();
  return (
    <article
      className="bg-white border border-slate-200 rounded-md overflow-hidden scroll-mt-24"
      id={entry.id}
      data-testid={`glossary-entry-${entry.id}`}
    >
      <header className="px-4 py-3 bg-slate-50 border-b border-slate-200">
        <div className="flex flex-wrap items-baseline gap-2">
          <h3 className="font-display text-lg font-black tracking-tight text-slate-900">
            {entry.en}
          </h3>
          <span className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500 font-bold">
            ES · {entry.es}
          </span>
        </div>
      </header>
      <dl className="px-4 py-3 space-y-3 text-sm">
        <div>
          <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">
            {t("Operational meaning")}
          </dt>
          <dd className="text-slate-800 leading-snug">{t(entry.operational)}</dd>
        </div>
        <div>
          <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">
            {t("Lifecycle meaning")}
          </dt>
          <dd className="text-slate-800 leading-snug">{t(entry.lifecycle)}</dd>
        </div>
        <div>
          <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">
            {t("Accountability")}
          </dt>
          <dd className="text-slate-800 leading-snug">{t(entry.accountability)}</dd>
        </div>
        <div>
          <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">
            {t("Downstream visibility")}
          </dt>
          <dd className="text-slate-800 leading-snug">{t(entry.downstream)}</dd>
        </div>
      </dl>
    </article>
  );
}

export default function AdminOperationalLanguage() {
  usePageTitle("Operational Language · Admin");
  const { t } = useT();
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return ENTRIES;
    return ENTRIES.filter((e) => {
      const hay = [e.en, e.es, e.operational, e.lifecycle,
                   e.accountability, e.downstream].join(" ").toLowerCase();
      return hay.includes(needle);
    });
  }, [q]);

  return (
    <AdminShell
      title="Operational Language"
      section="governance"
      intro={
        <p className="text-sm text-slate-700 leading-relaxed">
          {t("One vocabulary across the platform. \"Archive\" means the same thing in HR as in Safety; \"Closeout\" means the same thing on a CAPA as on an incident; \"Driver Qualified\" means the same thing in Dispatch as in FL. This page is the canonical reference — every LifecycleGuide should link to the relevant entry here.")}
        </p>
      }
    >
      <div className="space-y-5 mt-5" data-testid="admin-operational-language">
        <LifecycleGuide
          id="operational-language"
          icon={BookOpen}
          accent="slate"
          title={t("Why this glossary exists")}
          summary={t("Single source of operational truth · EN + ES parity · versioned in code.")}
          sections={[
            {
              label: t("What this is"),
              body: t("Every operational term the platform uses, with the same meaning in every portal. When in doubt, link here from a LifecycleGuide, an internal Slack thread, or a meeting deck."),
            },
            {
              label: t("How it's maintained"),
              body: t("Entries live in the codebase, not a CMS. Adding or changing a definition is a Git commit — the commit history IS the audit trail. ES parity is required for every entry."),
            },
            {
              label: t("How to use it"),
              body: t("Search the bar below. Or deep-link to a specific entry — every entry has an anchor like /admin/operational-language#capa."),
            },
            {
              label: t("Why this matters"),
              body: t("Vocabulary drift between departments is the cheapest source of operational chaos in a multi-portal platform. One word, one meaning, everywhere — every time."),
            },
          ]}
        />

        <div className="bg-white border border-slate-200 rounded-md p-3 flex items-center gap-2">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("Search any term, definition, or workflow concept")}
            className="border-none shadow-none focus-visible:ring-0 px-0"
            data-testid="glossary-search"
          />
          <span className="text-xs font-mono text-slate-500 shrink-0">
            {filtered.length}/{ENTRIES.length}
          </span>
        </div>

        {filtered.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500" data-testid="glossary-empty">
            {t("No glossary entries match. Try a broader term.")}
          </div>
        ) : null}

        <div className="space-y-3" data-testid="glossary-list">
          {filtered.map((e) => <GlossaryEntry key={e.id} entry={e} />)}
        </div>
      </div>
    </AdminShell>
  );
}
