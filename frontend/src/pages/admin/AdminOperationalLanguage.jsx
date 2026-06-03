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
    lifecycle: "Pipeline: Open → In Progress → Pending Review → Verified → Closed. The platform enforces every transition; illegal jumps are refused. Closing without Verified is impossible.",
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
    lifecycle: "Recomputed every time the Governance Summary is loaded. Mapped to a label: ≥90 healthy, ≥70 fair, ≥40 degraded, <40 critical.",
    accountability: "Admin owns the convergence target. Each portal's role-scoped digest contributes findings that move the score. A score drop overnight is surfaced in the Admin digest as a Δ.",
    downstream: "Headlines the Governance Health page and the Admin notifications digest. The first number you should look at every morning.",
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
    id: "follow_up_required",
    en: "Follow-Up Required",
    es: "Requiere Seguimiento",
    operational: "Status a Safety reviewer sees on an incident the moment Tier-1 fast entry is submitted but no CAPA has been opened yet. Means: \"The crew got the immediate report — now somebody owns the corrective action.\"",
    lifecycle: "Auto-derived live, never stored. Computed from severity + osha_recordable + the count of linked CAPAs. Disappears the second the first CAPA is opened against the incident.",
    accountability: "Safety owns opening the follow-up CAPA. The incident submitter is NOT responsible for the CAPA — Tier-1 fast entry is intentionally lightweight to avoid blocking field reporting. PM and HR see the status; Admin has supervisory view.",
    downstream: "Surfaces inline on /incidents/{id} as a rose status banner with an \"Open Follow-Up CAPA\" CTA. Severe incidents (medical/restricted/lost_time/fatality or OSHA recordable) explicitly require follow-up; quieter incidents do not.",
  },
  {
    id: "governance_score",
    en: "Governance Score",
    es: "Puntuación de Gobernanza",
    operational: "Synonym for Convergence Score. Used interchangeably in the Admin Governance Health header. Always 0-100.",
    lifecycle: "See Convergence Score.",
    accountability: "See Convergence Score.",
    downstream: "See Convergence Score.",
  },
  {
    id: "investigation_open",
    en: "Investigation Open",
    es: "Investigación Abierta",
    operational: "Status on an incident that has at least one linked CAPA in motion but not yet verified. Means: \"Somebody has taken ownership — work is happening, not waiting.\"",
    lifecycle: "Auto-derived live from the linked CAPA pipeline. Flips to Operationally Complete the moment every linked CAPA reaches Verified or Closed. Re-opens if any verified CAPA is reverted.",
    accountability: "The CAPA assignees own the work. Safety owns moving CAPAs to Verified. PM and HR see the status; FL sees the same status via crew accountability views.",
    downstream: "Surfaces as an amber status banner on /incidents/{id} and as a tile on the Safety CAPA register filtered to Open + Pending Review.",
  },
  {
    id: "lifecycle_guide",
    en: "Lifecycle Guide",
    es: "Guía de Ciclo de Vida",
    operational: "An inline coaching banner that every new operational surface must ship with — explains the workflow's roles, lifecycle, downstream visibility, and why it matters.",
    lifecycle: "Permanent platform architecture rule. Every new feature, form, or workflow must include a LifecycleGuide. No silent workflows.",
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
    id: "operationally_complete",
    en: "Operationally Complete",
    es: "Operativamente Completo",
    operational: "Status on an incident when every linked CAPA has reached Verified or Closed. Means: \"The corrective work happened AND a second reviewer confirmed it.\"",
    lifecycle: "Auto-derived live, never stored. Re-opens if any of the linked CAPAs is reverted out of Verified. Distinct from a CAPA Closeout — operational completeness is per-incident, closeout is per-CAPA.",
    accountability: "Safety owns the final verification. Admin has supervisory view. The crew supervisor and the involved employee are stamped on the underlying CAPA audit trail via verified_by_name + verified_at.",
    downstream: "Surfaces as an emerald status banner on /incidents/{id}. Releases the incident from open dashboards while preserving the full audit trail forever.",
  },
  {
    id: "pending_review",
    en: "Pending Review",
    es: "Pendiente de Revisión",
    operational: "A CAPA status meaning the corrective work has been submitted by the owner and is waiting for a second reviewer (separation of duties). One step before Verified.",
    lifecycle: "Inserted between In Progress and Verified. The owner cannot self-verify; a different Safety reviewer must mark the CAPA Verified for it to advance toward Closed.",
    accountability: "The CAPA owner submits it into Pending Review. A different Safety reviewer (or admin) verifies. The CAPA_AWAITING_VERIFICATION finding fires if a CAPA sits here for >7 days — that's how the platform prevents stalled reviews.",
    downstream: "Visible in the Safety CAPA register's Pending Review tab, the Safety + Admin digests, and the Accountability Timeline for the assigned employee.",
  },
  {
    id: "roster_backed_selector",
    en: "Roster-backed Selector",
    es: "Selector respaldado por el roster",
    operational: "An input pattern that captures an employee reference by searching the active employee master, returning both a canonical employee_id AND a name snapshot in a single interaction. Falls back to free-text for subcontractors/non-employees with a visible unlinked warning.",
    lifecycle: "Used at data-entry time on every operational form (Incident, PPE, Training, Daily Report crew, etc.). Replaces the legacy pattern of free-text name + optional master-link as two separate fields — eliminates the silent path where users typed a name and skipped the link.",
    accountability: "Builder of any new form owns the EmployeeRosterField wiring. The component itself enforces the linkage contract — there is no \"forgot to link\" path because the same UI captures both values atomically.",
    downstream: "When the user picks from the roster, the record stores employee_id and the EMP_LINK_UNRESOLVABLE detector never fires for that record. When the user free-texts, the warning at entry time tells them the downstream finding will appear. Net effect: identity drift becomes impossible-by-accident.",
  },
  {
    id: "verified",
    en: "Verified",
    es: "Verificada",
    operational: "A CAPA status meaning a second reviewer has inspected the corrective work and confirmed it actually happened. Mandatory before Closed.",
    lifecycle: "Inserted between Pending Review and Closed during the CAPA lifecycle upgrade. Stamps verified_at + verified_by_name + verified_by_email.",
    accountability: "Safety owns verification. Ideally a different person than the one who marked Pending Review (separation of duties). The platform stamps both actors onto the record for audit.",
    downstream: "Surfaces as a finding (CAPA_AWAITING_VERIFICATION) if a CAPA sits in Pending Review for >7 days. Visible in the CAPA register filter tabs and the Safety digest.",
  },

  // ── iter396 · Dispatch Lifecycle System glossary block ───────────────
  // 22 entries: 1 umbrella + 13 lifecycle states + 8 wait reasons.
  // Calm operational language, matches existing platform tone. Each
  // id is anchorable so LifecycleGuide on the dispatch board can
  // deep-link (e.g. /admin/operational-language#dls_waiting_on_plant).
  {
    id: "dls",
    en: "Dispatch Lifecycle System (DLS)",
    es: "Sistema de Ciclo de Vida de Despacho (DLS)",
    operational: "Real-time operational flow engine for haul cycles. Every assignment moves through a small canonical set of lifecycle states; every transition is recorded; non-standard transitions are tagged but never blocked.",
    lifecycle: "Three collections: dispatch_assignments (current truth), dispatch_state_events (append-only audit), haul_cycles (derived summaries). All tenant-scoped. Forgiving validation — operations never get trapped by rigid rules.",
    accountability: "Dispatch owns assignment creation and lifecycle management. Drivers move their own truck through states via magic-link sessions. PM/Safety/Shop/FL receive read-only signals scoped to their domain.",
    downstream: "Feeds the Operational Board, Governance Findings, CSV exports, and PM/Shop role tiles. Future estimating intelligence, change-order defense, and production forecasting all derive from this single source of operational truth.",
  },
  {
    id: "dls_assigned",
    en: "ASSIGNED",
    es: "ASIGNADO",
    operational: "A truck has been assigned a haul cycle but has not yet left the yard. The driver knows what to do — the cycle has not started moving.",
    lifecycle: "Starting state for every dispatch_assignment. Standard next: ENROUTE_TO_LOAD. Pause states (WAITING / HOLD / BREAKDOWN) and OFF_SHIFT are also acceptable.",
    accountability: "Dispatch creates the assignment; the driver acknowledges by tapping the next state on their phone. No silent transitions.",
    downstream: "Counts toward 'active hauls' on the operational board until the driver advances. Assignment time anchors the cycle start on haul_cycles.csv.",
  },
  {
    id: "dls_enroute_to_load",
    en: "ENROUTE_TO_LOAD",
    es: "EN RUTA A CARGAR",
    operational: "The truck is on the road to the load site (plant, quarry, stockpile). No load on board yet.",
    lifecycle: "Standard next: AT_LOAD_SITE. Pause states acceptable. Skipping forward to LOADING or LOADED is forgiven but tagged NON_STANDARD_TRANSITION.",
    accountability: "Driver advances. Dispatcher sees the truck on the board with a minutes-in-state counter.",
    downstream: "Long durations here surface in ASSIGNMENT_STUCK if the truck stalls before reaching the load site.",
  },
  {
    id: "dls_at_load_site",
    en: "AT_LOAD_SITE",
    es: "EN SITIO DE CARGA",
    operational: "The truck has arrived at the load site and is queued or staged for loading.",
    lifecycle: "Standard next: LOADING. WAITING from this state usually means waiting on plant, loader, or queue. Wait reason must be canonical.",
    accountability: "Driver advances on arrival. Loader operator presence is informational only — not a separate state.",
    downstream: "If WAITING is selected here without progression, the WAIT_THRESHOLD_EXCEEDED detector eventually fires.",
  },
  {
    id: "dls_loading",
    en: "LOADING",
    es: "CARGANDO",
    operational: "Material is actively being loaded onto the truck.",
    lifecycle: "Standard next: LOADED. Brief duration in most cycles; extended LOADING usually means plant trouble — pause to WAITING with reason instead of staying in LOADING.",
    accountability: "Driver controls the transition. Loader operator name is captured on the assignment record for audit, not as a workflow approval.",
    downstream: "Loading duration aggregates into haul_cycles.operating_seconds.",
  },
  {
    id: "dls_loaded",
    en: "LOADED",
    es: "CARGADO",
    operational: "Loading complete · ticket secured · truck ready to depart.",
    lifecycle: "Standard next: ENROUTE_TO_JOB. The driver may optionally tap LOADED before pulling away to mark the load timestamp cleanly.",
    accountability: "Driver advances. Ticket-photo capture is parked for a future iteration — not required to advance today.",
    downstream: "Loaded-time marks the cycle midpoint and anchors plant-to-job analysis later.",
  },
  {
    id: "dls_enroute_to_job",
    en: "ENROUTE_TO_JOB",
    es: "EN RUTA AL TRABAJO",
    operational: "The loaded truck is on the road to the job site.",
    lifecycle: "Standard next: ARRIVED_JOB. Wait states still allowed (e.g., traffic, lane closure).",
    accountability: "Driver-driven transition.",
    downstream: "Long-distance hauls show their full ENROUTE_TO_JOB duration on haul_cycles.csv for future cycle-time analysis.",
  },
  {
    id: "dls_arrived_job",
    en: "ARRIVED_JOB",
    es: "LLEGÓ AL TRABAJO",
    operational: "Truck has arrived at the job site and is queued for dumping.",
    lifecycle: "Standard next: DUMPING. WAITING_ON_PAVER or WAITING_ON_DUMP are common from this state.",
    accountability: "Driver-driven. Paving crew presence does not need a separate state.",
    downstream: "Queue depth at the job is implicit in how many trucks sit in ARRIVED_JOB at once on the board.",
  },
  {
    id: "dls_dumping",
    en: "DUMPING",
    es: "DESCARGANDO",
    operational: "Material is actively being unloaded onto the job site.",
    lifecycle: "Standard next: COMPLETE. Brief duration.",
    accountability: "Driver-driven.",
    downstream: "Dump duration is part of haul_cycles.operating_seconds.",
  },
  {
    id: "dls_complete",
    en: "COMPLETE",
    es: "COMPLETO",
    operational: "Cycle finished. The truck is available for the next dispatch.",
    lifecycle: "Terminal for the cycle. Triggers automatic materialization of a haul_cycles row with total/wait/operating seconds and standard/non-standard transition counts.",
    accountability: "Driver advances. A new dispatch starts a new assignment — no reuse of COMPLETE rows.",
    downstream: "haul_cycles.csv is the foundation for future estimating, change-order defense, and production-rate intelligence.",
  },
  {
    id: "dls_waiting",
    en: "WAITING",
    es: "ESPERANDO",
    operational: "The truck is paused inside an operational state, blocked by something outside the driver's control.",
    lifecycle: "Requires a canonical wait reason (PLANT / LOADER / DUMP / PAVER / TRAFFIC / LANE_CLOSURE / NEXT_DISPATCH / STAGING). Free-text-only WAITING is forbidden by doctrine.",
    accountability: "Driver selects the reason in one tap. Dispatch sees the wait reason live on the operational board.",
    downstream: "WAIT_THRESHOLD_EXCEEDED governance finding fires after 20 min by default. haul_cycles.csv tracks wait_seconds separately from operating_seconds.",
  },
  {
    id: "dls_hold",
    en: "HOLD",
    es: "EN ESPERA",
    operational: "Truck is intentionally held — usually by truck boss or dispatch override — distinct from operational WAITING.",
    lifecycle: "Pause state. Returns to any operational state when released.",
    accountability: "Used when the cause is administrative, not operational (re-routing, paperwork, supervisor direction).",
    downstream: "HOLD time is recorded but does not trigger governance findings unless extended beyond the stuck threshold.",
  },
  {
    id: "dls_breakdown",
    en: "BREAKDOWN",
    es: "AVERÍA",
    operational: "Truck is mechanically out of service.",
    lifecycle: "Pause state — but operationally critical. The BREAKDOWN_ACTIVE governance finding fires immediately.",
    accountability: "Driver enters from any operational state. Shop sees BREAKDOWN_ACTIVE on its Shop Hub tile in real time.",
    downstream: "Shop's high-value signal. Patterns of repeat breakdowns by truck or driver feed maintenance planning.",
  },
  {
    id: "dls_off_shift",
    en: "OFF_SHIFT",
    es: "FUERA DE TURNO",
    operational: "Driver has ended their shift for the day.",
    lifecycle: "Terminal for the day. Reachable from any state — drivers may end shift mid-cycle if necessary (for instance, from BREAKDOWN).",
    accountability: "Driver advances. A new shift creates a new assignment.",
    downstream: "Shift duration aggregates into future fatigue-risk analysis (not yet built — out of scope).",
  },
  {
    id: "dls_waiting_on_plant",
    en: "WAITING_ON_PLANT",
    es: "ESPERANDO PLANTA",
    operational: "Truck is at a load site but the plant is not ready (silo line down, mix unavailable, queue depth).",
    lifecycle: "Sub-state of WAITING. Selected from the canonical list — never free text.",
    accountability: "Driver picks. Future Motive validation may confirm location automatically.",
    downstream: "Pattern of repeat WAITING_ON_PLANT on a project is a starvation-risk signal for the PM tile and FL tile.",
  },
  {
    id: "dls_waiting_on_loader",
    en: "WAITING_ON_LOADER",
    es: "ESPERANDO CARGADOR",
    operational: "Plant or quarry has material but the loader is unavailable.",
    lifecycle: "Sub-state of WAITING.",
    accountability: "Driver picks.",
    downstream: "Distinct from WAITING_ON_PLANT so loader-availability problems don't get blamed on plant operations.",
  },
  {
    id: "dls_waiting_on_dump",
    en: "WAITING_ON_DUMP",
    es: "ESPERANDO DESCARGA",
    operational: "Job-site dump queue is backed up; nowhere to unload yet.",
    lifecycle: "Sub-state of WAITING.",
    accountability: "Driver picks.",
    downstream: "Dump congestion patterns feed future operational planning intelligence.",
  },
  {
    id: "dls_waiting_on_paver",
    en: "WAITING_ON_PAVER",
    es: "ESPERANDO PAVIMENTADORA",
    operational: "Paving crew is not ready to receive the load.",
    lifecycle: "Sub-state of WAITING.",
    accountability: "Driver picks.",
    downstream: "Combined with WAITING_ON_DUMP, this is a paving-starvation signal for FL.",
  },
  {
    id: "dls_waiting_on_traffic",
    en: "WAITING_ON_TRAFFIC",
    es: "ESPERANDO TRÁFICO",
    operational: "Truck is delayed by general traffic conditions.",
    lifecycle: "Sub-state of WAITING.",
    accountability: "Driver picks. Operationally honest — traffic is real and worth recording.",
    downstream: "Aggregate traffic patterns feed future haul-time honesty for estimating.",
  },
  {
    id: "dls_waiting_on_lane_closure",
    en: "WAITING_ON_LANE_CLOSURE",
    es: "ESPERANDO CIERRE DE CARRIL",
    operational: "Active lane closure (often DOT) is blocking the haul route.",
    lifecycle: "Sub-state of WAITING.",
    accountability: "Driver picks. Distinct from generic traffic.",
    downstream: "Lane-closure pattern by project is a change-order-defense signal later.",
  },
  {
    id: "dls_waiting_on_assignment",
    en: "WAITING_ON_ASSIGNMENT",
    es: "ESPERANDO ASIGNACIÓN",
    operational: "Driver finished a cycle and is waiting for dispatch's next call.",
    lifecycle: "Sub-state of WAITING — but operationally distinct from in-cycle waits.",
    accountability: "Picked when there's no active cycle to be in. Surfaces dispatch-capacity issues honestly.",
    downstream: "Aggregate WAITING_ON_ASSIGNMENT time per shift is the cleanest 'dispatch friction' signal.",
  },
  {
    id: "dls_staging",
    en: "STAGING",
    es: "ESPERA PROGRAMADA",
    operational: "Truck is intentionally staged — pre-positioned in advance of paving start or shift start.",
    lifecycle: "Sub-state of WAITING. Recorded because pre-staging is operational reality and deserves operational honesty.",
    accountability: "Driver picks. Should not be confused with WAITING_ON_ASSIGNMENT.",
    downstream: "STAGING vs WAITING_ON_ASSIGNMENT distinction protects future estimating from double-counting.",
  },
  // ── OKCP / OPERATOR EXCELLENCE · Sprint B additions ────────────────
  // Directive-named operational vocabulary, EN + ES, field-terminology first.
  {
    id: "jha_jhp",
    en: "JHA / JHP (Job Hazard Analysis / Plan)",
    es: "JHA / JHP (Análisis / Plan de Riesgos del Trabajo)",
    operational: "The pre-task hazard plan for THIS site and THIS crew. Names the steps, the hazards each step exposes, and the controls. A poster format goes on the wall; a PDF goes in the audit chain.",
    lifecycle: "Authored before the work starts → posted at the toolbox → crew acknowledges → archived to the project record. New version replaces (does not delete) the prior. Acknowledgement chain is preserved per version.",
    accountability: "Safety authors. Foreman briefs the crew. Each crew member acknowledges via the public JHP Hub. The PM is on the project audit chain.",
    downstream: "Safety Meeting topic library cross-references the JHA. Incident reviews pull the JHA in the first hour — a JHA that does not match the day's work reads as 'this crew had no plan.'",
  },
  {
    id: "qaqc",
    en: "QA/QC (Quality Assurance / Quality Control Inspection)",
    es: "QA/QC (Inspección de Aseguramiento / Control de Calidad)",
    operational: "The structured field inspection that validates a constructed element meets the specification. Distinct from Site Inspection (safety-axis) — QA/QC is quality-axis.",
    lifecycle: "Open → DEFICIENCY_RAISED → PENDING_RE_INSPECTION → Closure via one of three paths: (A) re-inspect passed · (B) corrective action ≥ 20 chars · (C) exception with PM + Safety dual sign-off ≥ 10 chars. Closure without re-inspection is code-blocked.",
    accountability: "PM owns. Safety verifies on path C. Field foreman remediates. The dual sign-off on path C protects against single-actor exception-creep.",
    downstream: "Open deficiencies block project handoff. CAPA may spawn from a closure-path-B finding. Audit / owner reviews trace deficiency → corrective → verified.",
  },
  {
    id: "rts",
    en: "RTS (Return to Service)",
    es: "RTS (Retorno al Servicio)",
    operational: "The authorization that releases a fleet unit back to dispatch after a defect repair. The single highest-stakes decision in the Shop — a wrongly-released unit can hurt people.",
    lifecycle: "Defect logged → repair → test cycle → RTS authorization → unit re-enters the dispatch pool. RED-severity defects require dual sign-off (mechanic + supervisor). Driver receives a shift-start QR notification when the unit is dispatched again.",
    accountability: "Mechanic and shop supervisor jointly authorize. Original defect reporter has visibility but does not sign off (separation of duties). Driver acknowledges receipt before dispatch.",
    downstream: "Full chain-of-custody (defect → repair → parts → mechanic → supervisor → driver) is preserved for any subsequent incident review. RTS is never negotiable under schedule pressure.",
  },
  {
    id: "dvir",
    en: "DVIR (Daily Vehicle Inspection Report)",
    es: "DVIR (Reporte de Inspección Diaria del Vehículo)",
    operational: "The DOT-required pre-trip / post-trip inspection. The driver attests the unit's safety-critical systems are functional before and after the shift.",
    lifecycle: "Pre-trip → shift use → post-trip. Defects logged on either DVIR flow into the Fleet Repair pipeline. Post-trip with no defects becomes the next pre-trip's baseline.",
    accountability: "Driver authors. Shop reads the post-trip. Supervisor reviews if a defect crosses severity threshold.",
    downstream: "DOT roadside inspection will pull DVIRs first. A pattern of incomplete DVIRs is a CSA score event. The DVIR audit trail is non-negotiable retention.",
  },
  {
    id: "emr",
    en: "EMR (Experience Modification Rate)",
    es: "EMR (Tasa de Modificación por Experiencia)",
    operational: "The insurance-industry score that multiplies workers'-comp premium up or down based on the company's incident history. EMR < 1.00 = lower than industry average. EMR > 1.00 = higher.",
    lifecycle: "Annual. Calculated from the prior 3 years of claim experience. Every recordable incident affects EMR for at least 3 years after.",
    accountability: "Safety owns prevention. HR owns claims. Executive owns the EMR target. Operations indirectly via incident-rate impact.",
    downstream: "EMR feeds bid eligibility (many owners require EMR ≤ 1.00 to bid). Every Incident Report and CAPA is ultimately an EMR-defense document. EMR is not visible inside the platform — but every safety record contributes to it.",
  },
  {
    id: "root_cause",
    en: "Root Cause",
    es: "Causa Raíz",
    operational: "The underlying system, decision, or condition that allowed an incident or deficiency to occur. NOT the immediate trigger — the immediate trigger is the proximate cause. Root cause is the layer above.",
    lifecycle: "Identified during incident or CAPA investigation. A root-cause statement that names a person is usually wrong (people fail when systems let them); name the system.",
    accountability: "Safety leads the analysis. PM, HR, Shop, or Dispatch may co-investigate by domain. The CAPA addresses the root cause, not the proximate trigger.",
    downstream: "Closing a CAPA against a proximate trigger without addressing the root cause is the most common reason the same incident recurs. Root cause discipline is what makes the platform improve over time.",
  },
  {
    id: "near_miss",
    en: "Near Miss",
    es: "Casi-Incidente (Cuasi-Accidente)",
    operational: "An event that COULD have caused injury or property damage but did not — usually by chance, timing, or last-second action. The data goldmine of a safety program.",
    lifecycle: "Reported through the Incident Report form with severity = Near-Miss. Same investigation rigor as a Recordable, but no medical record. Closure tracks same path as any incident.",
    accountability: "The witness reports. Safety triages. The crew owns the lesson learned. Suppressing near-miss reports is the single fastest way to grow a serious incident rate.",
    downstream: "Near-miss frequency is the leading indicator of where the next Recordable will happen. A team with 10× the near-miss reporting rate of peers usually has 0.5× the Recordable rate — the math is real.",
  },
  {
    id: "severity",
    en: "Severity",
    es: "Severidad",
    operational: "The classification of an incident or defect by potential or actual impact. Drives recordability, escalation, retention, and audit scrutiny.",
    lifecycle: "Severity is selected at intake (Incident Report severity field; Fleet defect severity color). Severity may be revised during investigation with a documented reason — but only upward escalation is automatic, downward revision requires Safety sign-off.",
    accountability: "Reporter picks initial severity. Safety adjudicates final severity for incidents. Shop adjudicates for fleet defects. Wrong severity makes the OSHA log wrong — the consequence is auditable.",
    downstream: "Drives whether a CAPA is mandatory (Recordable usually yes). Drives whether DOT/OSHA report is required (Severity + class combination). Drives RED/YELLOW/GREEN board visibility for Fleet.",
  },
  {
    id: "escalation",
    en: "Escalation",
    es: "Escalación",
    operational: "The action of raising an issue above the current actor's authority — to a supervisor, to Safety, to HR, to PM, to Executive, or out of the company (to OSHA, DOT, insurance, owner).",
    lifecycle: "Every operational workflow has an escalation path. The HelpTip `escalate` kind documents the trigger; the platform records who escalated, when, to whom, and why.",
    accountability: "Escalating is a positive operator behavior, not a complaint. Not escalating something that should have been escalated is the most common audit finding after an incident.",
    downstream: "Escalation creates an audit row. Once escalated, the receiver's clock starts — escalation is a baton, not a complaint box.",
  },
  {
    id: "revision",
    en: "Revision",
    es: "Revisión",
    operational: "A documented change to a previously-submitted record (Daily Report edit, JHP version replacement, Incident narrative correction, Payroll Variance row adjustment).",
    lifecycle: "Original is preserved (immutable). Revision is appended with author, timestamp, and reason. Both versions are visible in the audit trail; the most recent is the operational source of truth.",
    accountability: "The original author or a supervisor can revise. Some records (Incident closure, JHP attestation) require the revising actor to attest the reason.",
    downstream: "Audit reviews the revision chain. Frequent revisions on a single record signal a quality problem in the original submission. Revision is forgiven; falsifying the original is not.",
  },
  {
    id: "verification",
    en: "Verification",
    es: "Verificación",
    operational: "The independent confirmation that a CAPA, corrective action, deficiency closure, or training record is genuinely closed — not just marked closed.",
    lifecycle: "Verification follows action — never precedes. CAPA: Pending Review → Verified → Closed. Training: deficiency → make-up class → verified-on-file. QA/QC: corrective → re-inspection → verified.",
    accountability: "Verifier is NOT the actor who completed the action (separation of duties). For CAPAs, Safety verifies. For training, HR verifies. For QA/QC, the original inspector or a peer verifies.",
    downstream: "Closure without verification is impossible by code. An unverified pile-up indicates verifier capacity gap — surfaces in Governance Health.",
  },
  {
    id: "owner",
    en: "Owner",
    es: "Dueño",
    operational: "The single named person accountable for the workflow outcome — not a role, not a team. Every operational workflow has an owner stamp.",
    lifecycle: "Owner is assigned at workflow creation and is preserved through closure. Owner may be reassigned only with a documented reason and timestamp. Multiple-owner records are forbidden — clarity over politeness.",
    accountability: "Owner answers in audit. Owner receives the next-action notification. Owner cannot delegate accountability — only execution.",
    downstream: "Cross-portal dashboards (PM Crew Compliance, HR Accountability Timeline) roll up by owner. 'Unowned' is a Governance Health finding that auto-creates a compliance row.",
  },
  {
    id: "approver",
    en: "Approver",
    es: "Aprobador",
    operational: "The named person authorized to advance a workflow past an approval gate (e.g., RTS sign-off, Payroll Variance attestation, Time-Off approval, QA/QC closure path C dual sign-off).",
    lifecycle: "Approver is distinct from Owner (separation of duties). Approver acts on a fully-completed input — never on a partially-completed one.",
    accountability: "Approver attests in audit. An approver who rubber-stamps without review is the platform's most-common audit defense failure.",
    downstream: "Approver name + timestamp + (where applicable) reason are preserved on the record forever. An empty approver field where one is expected blocks the workflow.",
  },
  {
    id: "retention",
    en: "Retention",
    es: "Retención",
    operational: "How long an operational record must remain queryable. Driven by record type — OSHA records 5 years, DOT 3 years, workers'-comp claims forever, payroll 4 years federal / 7 years state, accident reconstruction 7 years.",
    lifecycle: "Retention is determined at record creation by classification. Archive (soft-delete) does NOT shorten retention — archived records remain queryable for audit / legal continuity. Hard-delete is reserved for documented data-correction events.",
    accountability: "Admin owns retention configuration. Legal owns retention policy. Every workflow's classification step is also a retention decision — getting classification wrong gets retention wrong.",
    downstream: "Compliance Findings surface 'archived but still flagged active' contradictions. Retention drift is the kind of finding that surfaces only at audit — usually too late.",
  },
  {
    id: "audit_trail",
    en: "Audit Trail",
    es: "Rastro de Auditoría",
    operational: "The append-only sequence of operationally-significant events on a workflow — who did what, when, why. The platform's defense in any post-incident review or legal discovery.",
    lifecycle: "Every workflow with a state machine writes to the workflow_state_events collection on every transition. Append-only: events are never updated, never deleted. Reopen creates a new event; it does not erase the prior closure.",
    accountability: "The system writes the audit row automatically; the actor's identity is captured from the authenticated session. An actor cannot edit their own audit row.",
    downstream: "OSHA / DOT / insurance / owner reviews can subpoena the audit trail. A platform whose audit trail can be tampered with is not a platform; the append-only constraint is the audit defense.",
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
