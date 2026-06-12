# MASCI Reality Gap Priority List

**Track 13.5B · Ranked gaps from the consolidated reality matrices**
**Mode:** Analysis only — no new findings, no new discovery, no implementation.
**Generated:** 2026-06-12 (UTC)

> Single source list. Every entry below is already documented in `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`, the rebuild list, or the Track 13.4D/E executive summary. This document only **ranks** them against the Five Pillars and the operator's stated outcome target ("move toward 10/10 Powerful, 10/10 Simple, 10/10 Beautiful, 10/10 Trusted, 10/10 Proven").

> Ranking dimensions: Operations · Safety · Trust · Adoption · Productization.

---

## 1. Critical (P0) — block the platform from claiming "Trusted" or "Proven"

| Rank | Gap | Source | Pillars impacted | Operator decision needed | Owner authorization required? |
| --- | --- | --- | --- | --- | --- |
| **C-1** | **Production Motive feed verification (D-01 + 7-point checklist)** | Track 13.4D | Trusted · Proven · Operations | Authorize execution against `mascidocs.com` | YES |
| **C-2** | **Production GPS coverage rate** (D-03 in preview shows 100/190 missing; live unknown) | Track 13.4D | Trusted · Proven · Operations | Same as C-1 | YES |
| **C-3** | **806 untranslated UI strings (R-08, T-01..T-07) — safety-critical bucket T-01 is 75.8%** | Track 13.4B Phase 3 | Trusted · Safety · Adoption | Authorize ES translation sprint | YES |
| **C-4** | **Engine status literals not wrapped in `t()` (T-12 / R-11)** | Track 13.4B Phase 3 | Trusted · Safety | Authorize engine-level wrap | YES |
| **C-5** | **Backend EN-only PDFs / emails / Excel (T-08, T-09, T-10, R-10)** | Track 13.4B Phase 3 | Trusted · Safety · Adoption | Authorize i18n for outbound docs | YES |

**Why these are P0:** every single C-rank item directly blocks Trusted=10 and/or Proven=10. They are also the most quoted concerns in the existing audit corpus.

---

## 2. High (P1) — block Simple from rising above ~7

| Rank | Gap | Source | Pillars impacted | Note |
| --- | --- | --- | --- | --- |
| **H-1** | **Collapse AdminCommandCenter ↔ OperationsCenterCommand** | V-09 / R-03 / R-05 + Command Center matrix §7 | Simple · Beautiful · Productization | Share the same `/api/operations-center/*` endpoint family; one of them is redundant. |
| **H-2** | **Rename non-role "Center" surfaces** (OperationalGuidanceCenter · AdminIntegrationCenter · TrenchSafetyOpsCenter · OdrCenter) | V-09 / Command Center matrix §3 | Simple · Beautiful | Restore "Center" to one meaning. |
| **H-3** | **Unify status vocabulary (V-10/V-11/V-12)** by migrating one pilot portal to the Phase B1 `StatusChip` + registry | Phase B1 done; Phase B3 BLOCKED | Simple · Beautiful · Trusted | Operator must authorize a pilot. |
| **H-4** | **Wire `tokens.css` consumers** — currently only one portal (the internal demo) reads them | V-04 / W-06 / W-19 / Phase A done | Beautiful · Productization | Phase B3 pilot migration is the action. |
| **H-5** | **Collapse 4 admin health pages (R-04)** | R-04 | Simple · Powerful | One Platform Health surface with sub-tabs. |
| **H-6** | **Collapse AdminCompliance vs AdminComplianceFindings (R-05)** | R-05 | Simple | Two pages doing one job. |
| **H-7** | **Daily Report / Site Inspection / Incident shared sub-form** (R-02) | R-02 | Simple · Adoption · Field re-entry | Field re-entry is the operator pain. |
| **H-8** | **Unified holds aggregation for PM** | PM reality matrix §2.3 | Powerful · Simple · Trusted | "Open Holds" is the #1 PM question; today it's derived per-engine. |
| **H-9** | **PM-scoped CAPA list view (U-01)** | Track 13.4E usability audit | Simple · Trusted | API exists (`/api/pm/crew/capas`); view is missing. |
| **H-10** | **Driver Hub static landing (V-15 / R-13)** | Rebuild list R-07 | Simple · Adoption · Field | Driver gets the lowest score in the platform (5.2). |

---

## 3. Medium (P2) — incremental moves to push Beautiful past 8

| Rank | Gap | Source | Pillars impacted |
| --- | --- | --- | --- |
| **M-1** | Shop header amber-vs-orange drift (V-01) | V-01 | Beautiful |
| **M-2** | PM tile-CTA amber-vs-indigo drift (V-02) | V-02 | Beautiful |
| **M-3** | Field Leadership red-700 overlap with Admin/Leadership brand-red (V-03) | V-03 | Beautiful · Adoption (role recognition) |
| **M-4** | Hub size variance 145 → 668 lines (V-05) | V-05 | Beautiful · Productization |
| **M-5** | ≥ 4 portal-header strategies (V-06) | V-06 | Beautiful · Simple |
| **M-6** | 15 status-chip components (V-07) | V-07 | Beautiful · Simple |
| **M-7** | OA-1 tile leakage on 6 of 7 portals (V-08 / R-06) | V-08 | Simple · Adoption |
| **M-8** | Cross-portal status case drift `Open`/`open` (V-10) | V-10 | Trusted · Simple |
| **M-9** | Closure verb drift `closed`/`done`/`signed_off`/... (V-12) | V-12 | Trusted · Simple |
| **M-10** | Public form chrome drift across 22 surfaces (V-14) | V-14 | Beautiful · Productization |
| **M-11** | PO digest + per-action delivery overlap (R-07) | R-07 | Trust (low-grade) · Adoption |
| **M-12** | iPad/phone capture deferred for Safety · Leadership · FL · Driver (V-13 partial) | V-13 | Proven · Adoption |
| **M-13** | `guidance_search_misses` invisible to operators (R-15) | R-15 | Productization · Coaching loop |

---

## 4. Low (P3) — quality-of-life moves to push Powerful from 9 to 10

| Rank | Gap | Source |
| --- | --- | --- |
| **L-1** | Excel export filenames prefix `MASCI_` (W-11) | W-11 |
| **L-2** | `forgedops-logo.png` unused (W-16) | W-16 |
| **L-3** | Dead ES entries (R-09 — 1,146 unused) | R-09 |
| **L-4** | Per-workflow status engines hardcoded (W-13) — only relevant when productizing | W-13 |
| **L-5** | Email templates Python-coded (W-20) — only relevant when productizing | W-20 |

---

## 5. White-label / Productization track (separate stack — not a P0/P1 for MASCI ops)

`MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md` §D catalogues 20 White-Label items (W-01..W-20). Per the Track 13.4C governance decision, these are kept as a **separate priority stack** to avoid mingling MASCI-operations urgency with productisation urgency. They are not duplicated here.

If/when operator authorizes ForgedOps productisation, the order is:
1. W-01 / W-02 (tenant model + scoping)
2. W-08 / W-09 (hardcoded recipients + MASCI legal phrases)
3. W-12 (tenant onboarding surface)
4. W-03 / W-04 (MASCI brand leak in 497 source files)

---

## 6. First-implementation priority (Track 13.5B's single answer)

The directive asks: *"What do we fix first to move MASCI OPS toward 10/10 Powerful, 10/10 Simple, 10/10 Beautiful, 10/10 Trusted, and 10/10 Proven?"*

### 6.1 Answer

**Execute the C-1 / C-2 production verification checklist first** (Track 13.4D, 7 points, no code change required). This raises Trusted by ≥ 1 point and Proven by ≥ 1 point in a single move and is the cheapest action on the entire list.

Then **authorize Phase B3 — Pilot Portal Migration of HR or PM** to the Phase B1 design-system primitives. HR is the lowest-risk migration target (`MASCI_HUMAN_USABILITY_AUDIT.md` rates it cleanest); PM is the highest-impact migration target (most routes, most operator hours). Either choice closes 4 H-rank gaps simultaneously (H-3 vocabulary unification, H-4 token consumer wiring, H-5/H-6 health/compliance collapse if HR is chosen, H-8/H-9 holds + CAPA if PM is chosen).

### 6.2 Why this order

- **C-1 / C-2 cost ~nothing** (analysis + log-checking against production) but **directly closes** the Trusted / Proven gap that no amount of code can close.
- **B3 pilot migration** then **proves** the design-system in production without crossing the "Operator Screenshot Wins" boundary (each surface goes side-by-side first).
- Every other H-rank item gets easier once one pilot has migrated, because the migration playbook becomes copy-paste for the next portal.

---

## 7. What this list does NOT do

- Does not create a new finding.
- Does not propose a recovery plan.
- Does not propose a new design system.
- Does not propose a new audit branch.
- Does not authorize any code change.

It is the **single ranked output** of Track 13.5B, ready for the operator to pick one or more items to authorize.

Standing rules: No deploy. No GitHub save. No merge.
