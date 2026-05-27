# Phase IV Roadmap — Operational UX Governance & Admin Unification

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 ROADMAP LOCKED · EXECUTION INCREMENTAL · ZERO-DATA-LOSS DOCTRINE
**Companions:** All 9 Phase IV deliverables (see below)

This is the single execution plan that sequences every Phase IV work item across 7 sub-phases. Each sub-phase is an independent PR-able unit. Regression must be green between every sub-phase.

---

## Sub-phase order & cadence

| Sub-phase | Title | Effort (est.) | Risk | Blocks deploy? |
|---|---|---|---|---|
| **IV.0** | Governance docs locked (this iteration) | DONE | none | no |
| **IV.A.1** | AdminShell two-tier nav scaffold | M | low | no |
| **IV.A.2** | Domain migration · Governance + System Health | M | low | no |
| **IV.A.3** | Domain migration · Data & Storage + Communications | M | low | no |
| **IV.A.4** | Domain migration · Identity & Access + Safety | L | medium | no |
| **IV.A.5** | Domain migration · HR & Workforce | L | medium | YES — HR Time Verification SLA must hold |
| **IV.A.6** | Domain migration · Fleet + Operations | L | medium | YES — daily-report submission must hold |
| **IV.A.7** | Domain migration · Dispatch & Logistics | L | high | YES — full dispatch board smoke required |
| **IV.B.1** | Extract `lib/email_shell.py` from `po_digest.py` | M | low | no |
| **IV.B.2** | Migrate 7 email callers (one PR each) | L per caller | medium | YES per caller |
| **IV.B.3** | Email shell conformance test + lint rule | S | low | no |
| **IV.C** | UX governance lint rule + spacing audit | M | low | no |
| **IV.D** | Terminology lint rule + canonical verbs sweep | M | low | no |
| **IV.E.1** | Pre-deploy stage 9 · attachment integrity probe | S | low | YES — adds blocking gate |
| **IV.E.2** | Pre-deploy stage 10 · mobile/iPad smoke | M | low | YES — adds blocking gate |
| **IV.E.3** | Live production post-deploy smoke script | S | low | no |

Effort: S = ≤ 1 dev-day · M = 1-3 dev-days · L = 3-7 dev-days. Sequential, not parallel, to keep regression risk bounded.

---

## Deliverables produced in this iteration (Sub-phase IV.0)

| # | Path | Purpose |
|---|---|---|
| 1 | `/app/memory/ADMIN_INFORMATION_ARCHITECTURE.md` | 10-domain map + current-state inventory |
| 2 | `/app/memory/ADMIN_DOMAIN_MAP.json` | Machine-readable domain map (used by nav scaffolding in IV.A.1) |
| 3 | `/app/memory/COMMUNICATION_UNIFICATION_DOCTRINE.md` | Email + notification doctrine |
| 4 | `/app/memory/EMAIL_TEMPLATE_STANDARD.md` | Pixel-exact shell spec for `lib/email_shell.py` |
| 5 | `/app/memory/UX_GOVERNANCE_STANDARD.md` | Buttons · forms · cards · tables · modals · spacing · severity |
| 6 | `/app/memory/COMPONENT_STANDARDIZATION_MATRIX.md` | Current-vs-canonical drift inventory |
| 7 | `/app/memory/TERMINOLOGY_DOCTRINE.md` | Wording, verbs, statuses, error messages |
| 8 | `/app/memory/NAVIGATION_REARCHITECTURE_PLAN.md` | Per-domain migration sequence |
| 9 | `/app/memory/PHASE_IV_DEPLOY_SAFETY.md` | 10-stage gate spec |
| 10 | `/app/memory/PHASE_IV_ROADMAP.md` | This document |

All 10 land in this iteration. **Zero code changed. Zero data touched.**

---

## Execution rhythm

For every sub-phase from IV.A.1 onward:

1. **Branch:** `iv-<subphase>-<slug>` (e.g., `iv-a-2-governance-system-health`)
2. **Implement:** the smallest possible change to land that sub-phase
3. **Test:** `bash /app/scripts/pre_deploy_check.sh` must be 8/8 green (later 10/10)
4. **Test:** `pytest backend/tests/pw_suite/` must be 35/35 green
5. **Smoke:** Mobile (375×812) + iPad (820×1180) screenshot of every page touched
6. **Document:** Append outcomes to `/app/memory/NAV_MIGRATION_LOG.md` (or domain-specific log)
7. **Deploy:** Operator triggers · runs `verify_production_identity.sh` + `verify_no_contamination.py`
8. **Verify:** 7-portal smoke from `mascidocs.com`
9. **Close:** Update PRD.md changelog and roadmap status

If any step fails, ROLL BACK before proceeding. Phase IV does not advance until the failing step is green.

---

## Success criteria (operator-stated · restated for tracking)

| Criterion | Measurement | Acceptance |
|---|---|---|
| Easier navigation | Number of clicks to reach top 10 admin tasks | ≤ 2 clicks from `/admin` |
| Lower cognitive load | Sidebar entries visible at any time | ≤ 12 |
| Cleaner operational hierarchy | Routes grouped under exactly one of 10 domains | 100% |
| Unified communications | Distinct email shells in production | 1 |
| Consistent behavior | Component variants per UX standard | 1 canonical per pattern |
| Calmer UX | Forbidden patterns in production code | 0 |
| Stronger operator trust | Production contamination events post-Phase-IV | 0 |
| Easier onboarding | Time-to-first-task for a new admin user | ≤ 5 min |
| Safer deploys | Production crash-loops per quarter | 0 |
| Zero production contamination | `verify_no_contamination.py` runs in gate | always pass |
| Zero live data loss | Production rows deleted outside operator-approved cleanup | 0 |

---

## What this roadmap explicitly defers

| Item | Why deferred | Trigger to revisit |
|---|---|---|
| Backend route restructuring (`/api/admin/*` → `/api/<domain>/*`) | High-risk · low-reward · breaks every iPad shortcut | Phase V |
| Frontend bundle split per domain | Bundle is ≤ 1.5 MB — not yet a problem | When bundle > 3 MB |
| Custom theme tokens / design-token library | Tailwind config is the source of truth | Phase V |
| Real-device certification with crews | Requires field coordination | Quarterly schedule |
| Legacy Base64 media migration to R2 | Planning doc exists · execution gated on operator approval | Operator authorisation |

---

## Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Nav refactor breaks bookmarked URLs | HIGH | No URL is deleted. Old paths shim to new domain shell with a one-time visual notice. |
| Email shell migration breaks scheduled cron sends | HIGH | Migrate one caller at a time. Each migration includes a side-by-side rendered comparison. |
| Lint rules block legitimate work | MEDIUM | Lint rules ship as warnings first, escalate to errors after 1 week of green. |
| Terminology sweep introduces translation drift | LOW | EN/ES pairs all land in `/admin/operational-language` before production. |
| Phase IV.A.7 (Dispatch) goes wrong mid-shift | HIGH | Schedule that PR to merge on a weekend morning UTC. |

---

## Verdict

🟡 **PHASE IV-0 — COMPLETE.**
✅ 10 governance deliverables produced
✅ Zero code changed
✅ Zero data touched
✅ Production unaffected
🔜 Phase IV.A.1 (AdminShell scaffold) is the next implementation iteration

The platform now has a complete, written, machine-readable governance baseline. Every subsequent piece of operational/admin/UX work has a single source of truth to align against. Future contributors can read the 10 documents and immediately know what shape new work must take.
