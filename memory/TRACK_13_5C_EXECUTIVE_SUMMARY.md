# Track 13.5C · Executive Summary — MASCI Target State Architecture

**Mode:** Architecture only — no code, no migration, no deploy.
**Generated:** 2026-06-12 (UTC)

---

## 1. What this track produced

Six documents that, together, define the **finish line** for MASCI Operations Platform. Every future implementation decision must measure itself against these documents.

| # | Document | Lines | Purpose |
| --- | --- | --- | --- |
| 1 | `MASCI_TARGET_STATE_ARCHITECTURE.md` | 261 | Platform-wide architecture across 15 dimensions (visual identity · header · nav · shell · public surface · KPIs · cards · status · tables · empty states · notifications · coaching · Command Center · mobile · iPad) |
| 2 | `MASCI_PORTAL_TARGET_STATE_MATRIX.md` | 145 | Per-portal target (Admin · Dispatch · PM · Safety · Shop · HR · Field Leadership · Leadership · Driver) |
| 3 | `MASCI_COMMAND_CENTER_TARGET_STATE.md` | 113 | Definitive "Command Center" specification: 5 role-landings + 1 cross-portal aggregator |
| 4 | `MASCI_PM_TARGET_STATE.md` | 134 | All 12 PM surfaces classified Must Exist · Nice To Have · Does Not Belong + "complete PM" definition |
| 5 | `MASCI_HUMAN_USABILITY_TARGET.md` | 134 | The under-5-minute first task contract, per role, with measurable pass criteria |
| 6 | This summary | — | Final verdict + projected pillar scores + minimum implementation tracks |

---

## 2. The finish line in one paragraph

A 10/10 MASCI Operations Platform has **one visual language** across all portals, **18 canonical statuses** and zero ad-hoc badges, **5 (+1) Command Centers** with one meaning each, **8 Must-Exist PM surfaces** all bound to real APIs with provenance tooltips, **a first-time operator able to complete one real task in under five minutes per role** with zero training, and **per-surface visual guardrails + 3-viewport screenshot baselines** that prevent drift between releases. Production data freshness is independently verified. No safety string is EN-only. No event is notified twice. No screen presents stale data as live.

---

## 3. Final verdict — projected Five-Pillar score

If MASCI achieves this exact target state:

| Pillar | Today (13.5B) | Target (13.5C) | Honest ceiling | Why not 10? |
| --- | :-: | :-: | :-: | --- |
| **Powerful** | 8.2 | **9.7** | 10 | Reaches 10 once Risks/RFIs/Submittals operator decisions are recorded and the chosen ones ship |
| **Simple** | 6.5 | **9.5** | 10 | Last 0.5 requires operator-validated usability testing with real first-time operators |
| **Beautiful** | 7.0 | **9.5** | 10 | Last 0.5 requires Leadership executive surface design — partially regulator-shaped |
| **Trusted** | 7.2 | **9.8** | 10 | 10 requires zero stale-data incidents over a trailing 30-day window — measurable only post-launch |
| **Proven** | 7.1 | **9.6** | 10 | 10 requires guardrails AND third-party security/penetration audit pass |
| **Aggregate** | **7.2** | **9.6** | 10.0 | Honest target |

> The honest claim is **9.6 / 10 aggregate** at the moment the target is reached. The remaining 0.4 closes only through real-world operation: zero stale-data incidents, an external audit, and operator-validated usability testing. The platform should not pretend to be a 10/10 until those external signals exist.

---

## 4. Minimum implementation tracks to reach the target

Sequenced **one at a time**. None of them happen in 13.5C. Each requires explicit operator authorization to begin. Cited from `MASCI_REALITY_GAP_PRIORITY_LIST.md`.

### 4.1 Pre-flight (zero code)

| Track | Output | Pillar impact |
| --- | --- | --- |
| **T0** — Track 13.4D 7-point Production Verification Checklist | Webhook arrival · GPS coverage · feed_status · geofence render count · ops-summary independent rederivation · stale-data incident baseline · operational uptime baseline | Trusted +1.0 · Proven +1.0 |
| **T1** — Operator decisions on PM scope (Risks/RFIs/Submittals in or out) | Written audit-ledger entry | Powerful +0.5 |

### 4.2 Foundation (already complete)

| Track | Status | Pillar impact |
| --- | --- | --- |
| **13.5A Phase A — tokens.css wiring** | ✅ Complete | Beautiful +0.5 |
| **13.5A Phase B1 — Design-system primitives** | ✅ Complete | Beautiful +0.5 · Simple +0.5 |
| **13.5A Phase B2 — PM V2 preview lane** | ✅ Complete | Operator preview only |
| **13.5B — Reality Matrix + 5-Pillar scorecard** | ✅ Complete | — (governance) |
| **13.5C — Target State Architecture** | ✅ Complete | — (governance) |

### 4.3 Pilot migration

| Track | Output | Pillar impact |
| --- | --- | --- |
| **T2** — Phase B3 Pilot Portal Migration (HR or PM) | One portal fully on B1 primitives; side-by-side `*_v2` swap with operator visual sign-off | Beautiful +1.0 · Simple +1.0 · Proven +0.5 |

### 4.4 Engine work (in any order; each is small)

| Track | Output | Pillar impact |
| --- | --- | --- |
| **T3** — PM CAPA list view (U-01) | One new `/pm/capas` screen; existing API | Simple +0.3 |
| **T4** — Unified Holds aggregation | `/api/holds` endpoint or materialized view | Powerful +0.5 · Simple +0.5 · Trusted +0.3 |
| **T5** — Due-Today cross-engine aggregation | `/api/due-today` endpoint | Powerful +0.3 · Simple +0.3 |
| **T6** — Daily Report / Site Inspection / Incident shared sub-form (R-02) | One shared sub-form component | Simple +0.5 · Adoption |
| **T7** — Driver Hub static landing (V-15 / R-13) | One new page | Simple +0.5 · Adoption +1.0 |
| **T8** — Command Center naming collapse (R-05) | Rename non-role Centers; collapse Admin↔Operations duplication | Simple +1.0 |
| **T9** — 4-page admin health collapse (R-04) | One health surface with sub-tabs | Simple +0.5 |
| **T10** — AdminCompliance dedupe (R-05) | One compliance page | Simple +0.2 |

### 4.5 Trust + i18n

| Track | Output | Pillar impact |
| --- | --- | --- |
| **T11** — 806 untranslated UI strings + engine `t()` wraps (R-08 / R-11 / T-01..T-07 / T-12) | ES round-trip 100% | Trusted +1.0 · Safety · Adoption |
| **T12** — EN-only PDFs / emails / Excel locale-aware (R-10 / T-08..T-10) | Outbound documents honor recipient locale | Trusted +0.5 |
| **T13** — Notification deduplication (R-07) | One event → one channel | Trusted +0.3 · Simple +0.3 |

### 4.6 Mobile + offline

| Track | Output | Pillar impact |
| --- | --- | --- |
| **T14** — Field Leadership + Safety Forms offline-capable | Queued sync ≤ 30 s | Powerful +0.5 · Trusted +0.3 |
| **T15** — Three-viewport baseline screenshots for every operator surface | Living evidence archive | Proven +1.0 |
| **T16** — Per-surface Playwright visual guardrails | One guardrail per portal · runs on every commit | Proven +1.0 |

### 4.7 Long-tail polish (cumulative <0.5 impact each)

Items M-1 through M-13 in `MASCI_REALITY_GAP_PRIORITY_LIST.md`. Authorized after T0–T16.

---

## 5. Critical-path map

```
T0 (production verify) ──┐
                         ├──► T2 (B3 pilot migration) ──► T11/T12 (trust/i18n) ──► T15/T16 (proven)
T1 (PM scope decisions) ─┘
                         │
                         ├──► T3 (PM CAPA) ────────► T4 (Holds) ─► T5 (Due-today)
                         │
                         ├──► T7 (Driver Hub) ────► Driver portal climbs to 9.4
                         │
                         └──► T8 (Center naming) ─► T9 (Admin health) ─► T10 (Compliance)
```

T0 and T1 unblock everything else. T2 unblocks Beautiful + Simple at scale. T16 unblocks the operator-trust climb to ≥ 9.8.

---

## 6. What this track did NOT do

- Did not write code.
- Did not create a new design system (referenced the existing one).
- Did not create new findings (referenced the existing 77).
- Did not propose a new audit branch.
- Did not authorize any deploy / GitHub save / merge.

It produced **6 reference documents** that act as the platform's North Star for every future implementation track.

---

## 7. Single-question answer

> "If MASCI OPS achieved this target state exactly, what Five-Pillar score would be expected?"

**Powerful 9.7 · Simple 9.5 · Beautiful 9.5 · Trusted 9.8 · Proven 9.6 — aggregate 9.6 / 10.**

The remaining 0.4 closes through 30 days of real-world operation: zero stale-data incidents, one external security/penetration audit pass, and operator-validated usability testing with real first-time operators.

> "What are the minimum implementation tracks required to get there?"

**Sixteen tracks (T0–T16)** as listed in §4. T0 and T1 cost zero code; the remaining 14 are sequenced by impact and authorized one at a time.

---

## 8. Standing rules

No deploy. No GitHub save. No merge. No code in 13.5C. The next move is operator authorization to begin T0 (production verification) or T2 (Phase B3 pilot migration) — both already scoped and ready.
