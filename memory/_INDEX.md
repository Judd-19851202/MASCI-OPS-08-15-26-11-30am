# `/app/memory/` — Governance Doc Index

_30-second orientation map for future agents and forks · 2026-05-28._

**Read this first.** Use the section headings to find the doctrine
domain you need, then open the file(s) under it. Do NOT grep blindly
across 500 docs — the platform has strict domain boundaries.

> **Status legend:** ✅ active · 📐 planning · 🟢 implemented ·
> 🟡 deferred · ⛔ read-before-touching

---

## 1 · Platform Governance Core

The substrate that protects the platform from itself.

| File | Purpose | Status |
|---|---|---|
| `PRD.md` | Master product requirements + phase log (always read first) | ✅ |
| `FINAL_DEEP_PRE_DEPLOY_CERTIFICATION.md` | Last canonical pre-deploy gate · 15 dimensions | ✅ |
| `POST_DEPLOY_LIVE_CERTIFICATION.md` | Last production verification · post-cutover | ✅ |
| `POST_DEPLOY_VERIFICATION_REPORT.md` | TRUST-TIME-1 + 1B post-deploy verification | ✅ |
| `AUTHORITY_MISMATCH_REPORT.md` | Authority Mismatch Probe last run | ✅ auto-gen |
| `TIMESTAMP_DOCTRINE_PROBE_REPORT.md` | Timestamp Doctrine Probe last run | ✅ auto-gen |
| `TIMESTAMP_UTILITY_STANDARD.md` | Store-UTC / transmit-tz-aware / render-local / label-UTC | ✅ ⛔ |
| `TRUST_TIME_1_CERTIFICATION.md` | +4h PO bug fix · 3-layer remediation | ✅ |
| `TIMESTAMP_DOCTRINE_SELF_PROTECTION_CERTIFICATION.md` | TRUST-TIME-1B self-protection probe | ✅ |
| `TRUST_SURFACES.md` / `.json` | Registry of every trust surface · 10 entries | ✅ |
| `TRUTHFUL_STATE_GOVERNANCE.md` / `.json` | 12 contracts of "what is displayed = what is true" | ✅ |
| `OPERATIONAL_TELEMETRY_DOCTRINE.md` / `.json` | Allowed telemetry events + PII rules | ✅ ⛔ |
| `CONTEXT_GOVERNANCE_STANDARD.md` | Cross-portal context inheritance doctrine | ✅ |
| `SHARED_SURFACE_CONTEXT_MATRIX.json` | Per-surface compliance matrix · 5 governed · 0 TBD | ✅ |
| `DEPLOYMENT_HISTORY.json` | OPS-1 deployment stanza · auto-tracked | ✅ |
| `GOVERNANCE_PRIMITIVES_STANDARD.md` | Capability-primitive doctrine | ✅ |

## 2 · Cross-Portal UX Governance

Visual + interaction discipline across Admin / PM / HR / Safety /
Dispatch / Shop / Field Leadership.

| File | Purpose | Status |
|---|---|---|
| `CROSS_PORTAL_OPERATOR_ATLAS.md` | Master map of every operator surface | ✅ |
| `CROSS_PORTAL_CONSISTENCY_STANDARD.md` | UX consistency contract | ✅ |
| `CROSS_PORTAL_COACHING_STANDARD.md` | Coaching copy doctrine | ✅ ⛔ |
| `CROSS_PORTAL_VOCABULARY_GLOSSARY.md` | Canonical operator vocabulary | ✅ |
| `ADMIN_UX_GOVERNANCE.md` | Admin console rendering rules | ✅ |
| `ADMIN_INFORMATION_ARCHITECTURE.md` | Admin nav doctrine | ✅ |
| `ADMIN_DOMAIN_MAP.json` | Admin domain boundaries | ✅ |
| `PM_TRANSITION_INVENTORY.md` | PM portal scope | ✅ |
| `HR_PORTAL_GOVERNANCE.md` (if present) | HR portal rules | ✅ |
| `SAFETY_PORTAL_GOVERNANCE.md` (if present) | Safety portal rules | ✅ |
| `DISPATCH_INVENTORY.md` (if present) | Dispatch surface inventory | ✅ |
| `VISUAL_LOUDNESS_DOCTRINE.md` (or `CALM_OBSERVABILITY_UI.md`) | Calmness rules · single-red doctrine | ✅ ⛔ |
| `COACHING_AND_VERBIAGE_AUDIT.md` | Audit of operator-facing copy | ✅ |
| `COMMUNICATION_TONE_STANDARD.md` | Tone doctrine (calm · operational · non-corporate) | ✅ |
| `CONTEXTUAL_RETURN_PATH_AUDIT.md` | Back-link inheritance audit | ✅ |

## 3 · Operational Records / Phase V

Doctrine for the next major phase. NONE of these are implemented yet.

| File | Purpose | Status |
|---|---|---|
| `CONSTRAINT_BOARD_VISUAL_MODEL.md` | Constraint UI doctrine (V-Prelude Wave 1) | 📐 |
| `OPERATIONAL_CONSTRAINT_FOUNDATION.md` | Constraint schema + scope | 📐 |
| `OPERATIONAL_LINKING_RULES.md` | **Read before any cross-artifact link is built** | 📐 ⛔ |
| `OPERATIONAL_TIMELINE_FOUNDATION.md` | `operational_links` substrate doctrine | 📐 |
| `PHOTO_GOVERNANCE_STANDARD.md` | Photo-as-evidence doctrine | 📐 |
| `OPERATIONAL_SEARCH_ARCHITECTURE.md` | Field-first search doctrine | 📐 |
| `FIELD_MEMORY_FOUNDATION.md` | Deterministic recurring-pattern surface | 📐 |
| _(Future)_ `RFI_DOCTRINE.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `RFI_LIFECYCLE.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `SCHEDULE_DOCTRINE.md` | Phase V.3+ · not yet drafted | 🟡 |
| _(Future)_ `P6_IMPORT_ARCHITECTURE.md` | Phase V.4+ · not yet drafted | 🟡 |
| _(Future)_ `RFI_PDF_STANDARD.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `DOT_FAA_TEMPLATES.md` | Phase V.1+ · not yet drafted | 🟡 |

## 4 · V-Prelude Planning (current phase)

All planning artifacts for the pre-RFI substrate work.

| File | Purpose | Status |
|---|---|---|
| `PHASE_V_PRELUDE_IMPLEMENTATION_PLAN.md` | 4-wave master sequence | 📐 ⛔ |
| `OPERATIONAL_CONSTRAINT_FOUNDATION.md` | Wave 1 substrate | 📐 |
| `PHOTO_GOVERNANCE_STANDARD.md` | Wave 1 substrate | 📐 |
| `OPERATIONAL_TIMELINE_FOUNDATION.md` | Wave 1 substrate | 📐 |
| `OPERATIONAL_LINKING_RULES.md` | Wave 1 substrate (this directive) | 📐 ⛔ |
| `OPERATIONAL_SEARCH_ARCHITECTURE.md` | Wave 2 | 📐 |
| `FIELD_MEMORY_FOUNDATION.md` | Wave 2 | 📐 |
| `OFFLINE_DRAFT_RESILIENCE_MODEL.md` | Wave 3 | 📐 |
| `MOBILE_UX_REFINEMENT_AUDIT.md` | Wave 3 | 📐 |
| `ROLE_AWARE_VISIBILITY_MODEL.md` | Wave 1-3 | 📐 |
| `GOVERNANCE_SELF_HEALING_ROADMAP.md` | Wave 4 | 📐 |
| `V_PRELUDE_WAVE_READINESS_CERTIFICATION.md` | Pre-Wave-1 gate | 🟢 |

### Wave 1 — Substrate (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_IMPLEMENTATION_SUMMARY.md` | Wave 1 master summary | 🟢 |
| `OPERATIONAL_CONSTRAINT_CERTIFICATION.md` | Wave 1 constraint cert | 🟢 |
| `OPERATIONAL_LINKS_CERTIFICATION.md` | Wave 1 links cert · §10 probes | 🟢 ⛔ |
| `OPERATIONAL_TIMELINE_CERTIFICATION.md` | Wave 1 timeline cert | 🟢 |
| `PHOTO_GOVERNANCE_CERTIFICATION.md` | Wave 1 photo governance cert | 🟢 |
| `WAVE1_OBSERVATION_GUIDE.md` | 24-hr observation window guide | 🟡 active |

### Wave 1.1 — Timeline Sidecar (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_1_TIMELINE_SIDECAR_SUMMARY.md` | Wave 1.1 master summary | 🟢 |
| `TIMELINE_CALMNESS_CERTIFICATION.md` | Visual calmness contract | 🟢 |
| `MOBILE_CHRONOLOGY_CERTIFICATION.md` | Mobile ergonomic contract | 🟢 |
| `TIMELINE_ROLE_VISIBILITY_CERTIFICATION.md` | Cross-portal role gate | 🟢 |
| `OPERATIONAL_TIMELINE_OBSERVATION_REPORT.md` | Observation window log | 🟡 active |

### Wave 1.1A — Calmness Telemetry (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_1A_CALMNESS_TELEMETRY_SUMMARY.md` | Wave 1.1A master summary | 🟢 |
| `TIMELINE_LOUDNESS_PROBE_CERTIFICATION.md` | Probe cert · heuristic targets | 🟢 |
| `CHRONOLOGY_DENSITY_HEURISTICS_REPORT.md` | Density / dup heuristics | 🟢 |
| `GOVERNANCE_TRENDLINE_EXTENSION.md` | Trendline doctrine + inventory | 🟢 |
| `OPERATIONAL_TIMELINE_STABILITY_REPORT.md` | End-of-pass stability picture | 🟡 active |
| `TIMELINE_LOUDNESS_TRENDLINE.json` | Append-only calmness trendline | 🟢 auto-gen |

### Wave 1.1B — Governance Memory Self-Protection (implemented 2026-05-28)

| File | Purpose | Status |
|---|---|---|
| `WAVE1_1B_GOVERNANCE_MEMORY_SUMMARY.md` | Wave 1.1B master summary | 🟢 |
| `TRENDLINE_SELF_PROTECTION_CERTIFICATION.md` | Probe cert · 8-axis matrix | 🟢 |
| `GOVERNANCE_MEMORY_INTEGRITY_REPORT.md` | Live snapshot state · guarantees | 🟢 |
| `APPEND_ONLY_MEMORY_CERTIFICATION.md` | Append-only doctrine | 🟢 |
| `OBSERVATION_FREEZE_HARDENING_REPORT.md` | 18 freeze triggers · pre-Wave-2 gate | 🟢 |
| `TIMELINE_LOUDNESS_TRENDLINE.snapshot.json` | Trendline integrity anchor | 🟢 auto-gen |
| `LOUDNESS_TRENDLINE.snapshot.json` | Portal-wide trendline anchor | 🟢 auto-gen |

## 5 · Route Decomposition / Backend Architecture

How `server.py` is being split into `routes/`.

| File | Purpose | Status |
|---|---|---|
| `ROUTE_DECOMPOSITION_*.md` (if present) | Per-route extraction notes | ✅ |
| `ARCHITECTURAL_RISK_REDUCTION.md` | High-risk zones to defer | ✅ |
| `AUTH_CONSOLIDATION_PROGRESS.md` | Auth route extraction status | ✅ |
| _(See)_ `backend/routes/` directory | Live extracted routes | ✅ |
| _(See)_ `server.py` | Remaining monolith — still primary surface | ✅ ⛔ |

## 6 · Field / Mobile Doctrine

Superintendent + foreman + iPad rules.

| File | Purpose | Status |
|---|---|---|
| `FIELD_WALK_CHECKLISTS/FL.md` | Foreman walk | ✅ |
| `FIELD_WALK_CHECKLISTS/PM.md` | PM walk | ✅ |
| `FIELD_WALK_CHECKLISTS/Safety.md` | Safety walk | ✅ |
| `FIELD_WALK_CHECKLISTS/HR.md` | HR walk | ✅ |
| `FIELD_WALK_CHECKLISTS/MobileSafari.md` | iOS Safari walk | ✅ |
| `DAILY_REPORT_FIELD_TRUST_REVIEW.md` | Daily-report field doctrine | ✅ |
| `DAILY_REPORT_DEVICE_MEMORY_MODEL.md` | Crew memory + preload doctrine | ✅ ⛔ |
| `DATA_SURVIVABILITY_AUDIT.md` | TRUST-1 doctrine root | ✅ ⛔ |
| `MOBILE_UX_REFINEMENT_AUDIT.md` | V-Prelude mobile polish list | 📐 |

## 7 · Legal / Audit / Retention

Locked snapshots, soft-delete, archive doctrine, audit defensibility.

| File | Purpose | Status |
|---|---|---|
| `AUDIT_GUARDRAILS.md` | Audit-trail discipline | ✅ ⛔ |
| `DATA_PORTABILITY.md` | Export + retention rules | ✅ |
| _(See)_ TRUST-1 archive-on-delete behavior in `idbDraft.js` + Mongo soft-delete | ✅ |
| _(Future)_ `RFI_RETENTION.md` | Phase V.1+ · not yet drafted | 🟡 |
| _(Future)_ `EXTERNAL_ACCESS_AUDIT.md` | Phase V.2+ · not yet drafted | 🟡 |
| _(Future)_ `PDF_SHA256_FOOTER_STANDARD.md` | Phase V.1+ · not yet drafted | 🟡 |

---

## Cross-cutting "read before touching" list

- ⛔ `TIMESTAMP_UTILITY_STANDARD.md` — every timestamp surface
- ⛔ `OPERATIONAL_LINKING_RULES.md` — every cross-artifact link
- ⛔ `OPERATIONAL_TELEMETRY_DOCTRINE.md` — every new client/server event
- ⛔ `DATA_SURVIVABILITY_AUDIT.md` — every draft / queue / IDB change
- ⛔ `AUDIT_GUARDRAILS.md` — every change to records that may be referenced legally
- ⛔ `CROSS_PORTAL_COACHING_STANDARD.md` — every operator-facing copy change
- ⛔ `VISUAL_LOUDNESS_DOCTRINE.md` (or `CALM_OBSERVABILITY_UI.md`) — every color / pill / badge addition

---

## Where to find the live state

- 🟢 Live OPS-1 status: `GET /api/admin/governance/self-protection`
- 🟢 Probe state: `python3 scripts/authority_mismatch_probe.py --gate`
- 🟢 Timestamp probe: `python3 scripts/timestamp_doctrine_probe.py --gate`
- 🟢 Pre-deploy gate: `bash scripts/pre_deploy_check.sh`

---

_If a doc you need is not listed here, grep `/app/memory/` for the
topic — but document its addition to this index when you next
touch it. Goal: 500 docs · 1 map · 30 seconds._
