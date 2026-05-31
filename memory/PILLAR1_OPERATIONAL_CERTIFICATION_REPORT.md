# Pillar 1 · Operational Certification Report

**Batch:** Pillar 1 · Pre-Deployment Operational Certification
**Date:** 2026-05-31
**Scope:** Read-only certification answering one question — **"Can leadership trust Pillar 1 in production?"** Covers data quality, ownership fidelity, executive actionability, supportability, white-label readiness, and customer-#2 readiness.
**Discipline:** OMEGA · evidence-only · zero code · zero UI · zero DB · zero endpoints · zero collections · zero deployment · zero work on Pillars 2/3/4 or future ForgedOps portal.

> **Master file.** Companion deliverables:
> - `PILLAR1_DEPLOYMENT_RECOMMENDATION.md` — final verdict + paths
> - `PILLAR1_EXECUTIVE_USABILITY_REPORT.md` — Phase 3
> - `PILLAR1_SUPPORTABILITY_AUDIT.md` — Phase 4
> - `PILLAR1_WHITE_LABEL_READINESS_REPORT.md` — Phase 5
> - Evidence: `/app/memory/pillar1_certification_evidence/`

---

## 0 · Executive verdict

🟡 **GO WITH KNOWN LIMITATIONS.**

The Accountability Engine (`lib/accountability_projection.py` + `routes/accountability_service.py`) is architecturally sound, exhibits zero functional defects on its own surface, and passes 128/128 combined pytests. Pillar 1 itself is **🟢 PASS**.

The known limitations sit one layer up:

1. **Pillar 2 Phase A defects D1/D2/D5** are still un-patched and continue to govern what leadership actually sees through the Command Center. These were certified as a 🟡 CONDITIONAL GO by `EXECUTIVE_COMMAND_CENTER_CERTIFICATION.md` and are not addressable inside Pillar 1.
2. **JOBS-ISSUE-NO-OWNER predicate / implementation mismatch** — the threshold doc claims it counts "open incident OR open corrective action with no assigned owner"; the code at `command_center.py:355-365` queries `corrective_actions` only. 19 ownerless incidents are not surfaced. This is a Pillar 2 rule defect, not a Pillar 1 projection defect.
3. **Owner placeholders are correct but inert on preview data** — 0/10 pending POs link to a `jobs_master` row with a populated PM; 0/44 OOS fleet defects have `acknowledged_by_name`; 4/5 open incidents have no linked CA assignee. The Audit established this empirically (`ACCOUNTABILITY_OWNER_RESOLUTION_AUDIT.md` §4). The mechanism is correct — the data simply does not unlock it today on the preview dataset.
4. **White-label readiness: 🔴 NOT READY.** 4,431 MASCI string occurrences across `backend/` + `frontend/src/`. Pillar 1 modules themselves contain only 2 MASCI strings (both inside `command_center.py`, not in the projection library or service router), but the surrounding platform is still single-tenant.

**Production deployment of Pillar 1 alone (the projection + service layer) carries low risk.** Production deployment of Pillar 1 _as consumed by the Command Center_ carries the same risk profile as Pillar 2 Phase A's 🟡 CONDITIONAL GO certification.

---

## 1 · Phase 1 — Executive Data Quality Review

### 1.1 · Live snapshot (2026-05-31 16:11 UTC)

| Pulse field | Value |
|---|---|
| Overall pill | RED |
| RED warnings | 6 |
| AMBER warnings | 1 |
| RED items | 8 |
| AMBER items | 10 |
| Reconciles (items=sum(cards.items)) | 🟢 yes |

### 1.2 · Per-card validation

| Card | Pill | Warnings | Items | DQ verdict |
|---|---|---|---|---|
| jobs | RED | 3 | 8 | 🟢 underlying signals real (29 stale-DR projects · 2 unowned · 7 stale incidents); see §1.3 caveat |
| safety | RED | 2 | 5 | 🟢 2 incidents > 48h H/Critical (`f9715e57` aged 4d, `c3c17bf2` aged 4d) · 4 CAs past due |
| equipment | RED | 1 | 0 | 🟢 44-unit OOS backlog real; 🟡 0 surfaced items (Phase A defect D3/D5 area · `command_center_phase_a.py` covers count-only path) |
| accountability | GREEN | 0 | 0 | 🟢 no aged unassigned tasks today |
| approvals | AMBER | 1 | 5 | 🟡 175 pending POs in 3-4d window — **6% are TEST_iter prefixed seed pollution** on preview only; production count would be lower |

### 1.3 · Rule-by-rule false-positive / false-negative scan

| Rule | Today's hit | FP risk | FN risk | Notes |
|---|---|---|---|---|
| JOBS-DR-MISSING | 29 jobs | LOW | LOW | Calendar-aware lookback 36 working hours. Pre-existing D3 (weekend FP) documented, not regressed. |
| JOBS-ISSUE-NO-OWNER | 2 CAs | LOW | 🔴 **HIGH** | Predicate text says "incident OR CA"; code queries CAs only. 19 ownerless incidents silently uncounted. Pre-existing Pillar 2 defect surface, not introduced by Pillar 1. |
| JOBS-ISSUE-NO-PATH | 7 incidents | LOW | MED | Counts incidents > 7d without a linked CA · severity-blind (FN-2 family from Phase A FN review). |
| SAF-CRITICAL-UNRESOLVED | 2 incidents | 🟡 MED | LOW | Phase A D1 (no resolution-state check) — aged H/Critical that get marked resolved with non-canonical status may still fire. 2 confirmed real hits today. |
| SAF-OSHA-OPEN | 0 today | 🟡 MED | LOW | Phase A D2 (no resolution-state check). Latent. |
| SAF-CA-OVERDUE | 4 CAs | LOW | LOW | 3 real owners shown (`Alec Perkins`, `iter364 Sub Vendor Owner`) — projection resolution working as designed. |
| EQP-BACKLOG | 44 units | LOW | LOW | Real count from `fleet_defects` open + OOS. |
| APP-AMBER | 175 POs | 🟡 MED | LOW | 6% TEST_iter pollution on preview dataset; production-side ratio will be lower. Rule itself sound. |

### 1.4 · Threshold behavior

`db.command_center_thresholds` version=3 is loaded, all 15 rules carry the 5-question contract (predicate · operational_risk · leadership_action · owner_role · expected_resolution). Thresholds are operator-tunable via `PATCH /api/admin/command-center/thresholds`. No threshold is unreasonable in isolation; the cumulative concern is that the warning-mix (6 RED) skews leadership attention away from genuinely-severe items.

### 1.5 · Verdict — Phase 1

🟡 **DATA QUALITY ACCEPTABLE WITH KNOWN LIMITATIONS.**

The data Pillar 1 projects is internally faithful to the underlying collections. The complaints — JOBS-ISSUE-NO-OWNER scope · weekend FPs · 6% test pollution — are all **upstream of Pillar 1** (rule definitions live in Pillar 2 Phase A; pollution lives in the preview seed dataset). The projection layer itself returns correct, defensible answers for every sampled record.

---

## 2 · Phase 2 — Ownership Fidelity Audit

### 2.1 · Sampled 25 records (5 per source)

| # | Source | ID | Status | Source-of-truth owner | Projected owner | Match |
|---|---|---|---|---|---|---|
| 1 | po_requests | 992f9ef2 | Submitted | jobs_master.PM=None | "Pending Approver" | 🟢 truthful fallback |
| 2 | po_requests | b93c3372 | Submitted | jobs_master.PM=None | "Pending Approver" | 🟢 truthful fallback |
| 3 | po_requests | 6d4979e1 | Submitted | jobs_master.PM=None | "Pending Approver" | 🟢 truthful fallback |
| 4 | po_requests | ed3bbe2a | Submitted | jobs_master.PM=None | "Pending Approver" | 🟢 truthful fallback |
| 5 | po_requests | 85dd8aff | Submitted | jobs_master.PM=None | "Pending Approver" | 🟢 truthful fallback |
| 6 | corrective_actions | b42b5985 | Open | assigned_to_name="iter368 Owner" | "iter368 Owner" | 🟢 named |
| 7 | corrective_actions | 90205677 | Open | "iter364 Sub Vendor Owner" | "iter364 Sub Vendor Owner" | 🟢 named |
| 8 | corrective_actions | 3a1c2c16 | Open | "Alec Perkins" | "Alec Perkins" | 🟢 named |
| 9 | corrective_actions | 2e6fab05 | Open | "" (empty) | "Safety" | 🟢 truthful fallback |
| 10 | corrective_actions | 46e3f79a | Open | "iter368 Owner" | "iter368 Owner" | 🟢 named |
| 11 | fleet_defects | 352607b7 | open · oos | ack_by=None | "Shop" | 🟢 truthful fallback |
| 12 | fleet_defects | 65218ad5 | open · oos | ack_by=None | "Shop" | 🟢 truthful fallback |
| 13 | fleet_defects | 602c6bea | open · monitor | ack_by=None | "Shop" | 🟢 truthful fallback |
| 14 | fleet_defects | 0d59131d | open · oos | ack_by=None | "Shop" | 🟢 truthful fallback |
| 15 | fleet_defects | 198cde3c | open · oos | ack_by=None | "Shop" | 🟢 truthful fallback |
| 16 | incidents | 8966ce3f | first_aid · open | no linked CA | "Safety" | 🟢 truthful fallback |
| 17 | incidents | 987af2e8 | Low · open | linked CA `iter368 Owner` (Open) | "iter368 Owner" | 🟢 named (1A-5 resolved) |
| 18 | incidents | 5f94568b | Low · open | no linked CA | "Safety" | 🟢 truthful fallback |
| 19 | incidents | 699617a9 | Low · open | no linked CA | "Safety" | 🟢 truthful fallback |
| 20 | incidents | 493dcf0f | Medium · open | no linked CA | "Safety" | 🟢 truthful fallback |
| 21 | tasks | 5f112422 | Open · role=safety | assignee_user_id present | role-derived label | 🟢 (role-based by design — Audit A-03) |
| 22 | tasks | be8f0ce2 | Open · role=safety | assignee_user_id present | role-derived label | 🟢 |
| 23 | tasks | 471cd031 | Open · role=safety | assignee_user_id present | role-derived label | 🟢 |
| 24 | tasks | e555e022 | Open · role=pm | assignee_user_id present | role-derived label | 🟢 |
| 25 | tasks | 61824775 | Open · role=pm | assignee_user_id present | role-derived label | 🟢 |

### 2.2 · Mismatch summary

**Mismatches: 0 / 25.**

Every sampled record's projected owner exactly matches the platform's authoritative routing data — or, where authoritative data is absent, the truthful placeholder (`Pending Approver`, `Safety`, `Shop`) is surfaced.

### 2.3 · Verdict — Phase 2

🟢 **OWNERSHIP FIDELITY CERTIFIED.**

The projection library reports who actually owns the work today. The placeholders that remain are legitimate gaps in the underlying routing data (no PM on the project · no CA on the incident · no shop acknowledgement on the defect) — not engine defects. Phase 1A-5's resolvers are active and correctly promote names whenever data exists; today on the preview dataset they activate on 1/10 incident slots and 0/10 PO slots (consistent with the Audit's empirical baseline).

---

## 3 · Phase 3 — Executive Actionability Review

See `PILLAR1_EXECUTIVE_USABILITY_REPORT.md` for per-card 6-AM walkthrough. Summary:

| Card | 6-AM verdict | Notes |
|---|---|---|
| jobs | 🟢 USEFUL | Names 29 unfiled DRs + 2 unowned issues. Operator-actionable. |
| safety | 🟢 USEFUL | 2 RED H-incidents > 48h are exactly the items leadership needs to know. |
| equipment | 🟡 MARGINAL | 44-unit backlog is a leading indicator; **0 surfaced items** under D5 means leadership cannot drill in from the card. |
| accountability | 🟡 MARGINAL | GREEN today; the card adds little signal because Pillar 1A-3 service is already the data source — duplication risk. |
| approvals | 🟡 MARGINAL | "Pending Approver" placeholders + 6% test data dilutes urgency; production data will resolve this. |

---

## 4 · Phase 4 — Supportability Review

See `PILLAR1_SUPPORTABILITY_AUDIT.md`. Summary:

| ForgedOps support question | Answerable from platform surfaces? | Source |
|---|---|---|
| Why is this red? | 🟢 YES | drilldown `why_red`, snapshot `rule_id`, `command_center_thresholds.predicate` |
| Who owns it? | 🟢 YES | drilldown `owner` + `accountability.owner_*` (4 fields) |
| Why is it overdue? | 🟡 PARTIAL | `accountability.due_at` + `last_activity_at` shown; **no explanation of why it slipped** — operator must read CA/incident detail |
| What changed? | 🔴 NO | timeline only contains audit/status_history events from source; no diff/before-after surface |
| When did it change? | 🟢 YES | `last_activity_at` + `timeline_events[*].at` |

---

## 5 · Phase 5 — White-Label Readiness Audit

See `PILLAR1_WHITE_LABEL_READINESS_REPORT.md`. Summary:

| Pillar 1 file | MASCI string count |
|---|---|
| `lib/accountability_projection.py` | 0 |
| `routes/accountability_service.py` | 0 |
| `routes/command_center.py` | 2 |
| Platform-wide (backend + frontend) | 4,431 |

The Accountability Engine modules themselves are **white-label-clean**. The Command Center retains 2 MASCI strings ("Within MASCI PO SLA") — trivially externalizable. The surrounding platform is single-tenant.

---

## 6 · Phase 6 — Customer #2 Readiness Review

| Dimension | Status | Notes |
|---|---|---|
| Projection library is collection-aware (uses `db.X`) | 🟢 READY | Database name is environment-driven (`DB_NAME`). A second tenant just needs a second DB. |
| Owner-role enum (`pm`, `safety`, `shop`, `hr`, `approver_per_routing`, `operations_leadership`) | 🟢 READY | Vocabulary is generic; not MASCI-specific. |
| Source-collection assumptions (`tasks`, `corrective_actions`, `po_requests`, `fleet_defects`, `incidents`, `jobs_master`) | 🟡 NEEDS CONFIG | Names are platform-standard but Customer #2 will need the same schemas — they're not optional. |
| Threshold doc (`db.command_center_thresholds`) | 🟢 READY | Per-tenant doc; rules + thresholds tunable per tenant. |
| Calendar doc (`db.command_center_calendar`) | 🟢 READY | Per-tenant doc; timezone + working hours tunable. |
| Field naming on routing sources (`jobs_master.primary_pm_name`, `corrective_actions.assigned_to_name`) | 🟡 NEEDS CONFIG | Hardcoded in the resolvers. Customer #2 with a different schema would require additional resolver variants or a routing-source adapter. |
| Hardcoded placeholders ("Pending Approver", "Safety", "Shop", "Unassigned PM", "UNASSIGNED") | 🟡 NEEDS CONFIG | English-only string literals. Need to be i18n-able for a non-English Customer #2. |
| MASCI-branded strings in Command Center rule docs ("Within MASCI PO SLA") | 🟡 NEEDS CONFIG | 2 occurrences in `command_center.py`; trivial fix. |
| Pillar 1 endpoints (`/api/admin/accountability/*`) | 🟢 READY | Admin-strict, tenant-scoped via `db`. |
| Pillar 1 governance docs (`/app/memory/ACCOUNTABILITY_*`) | 🟢 READY | No tenant-specific content. |

### 6.1 · Verdict — Phase 6

🟡 **READY WITH CONFIGURATION WORK.** The Accountability Engine architecture supports a second customer **without redesign**. It requires:

1. ~2 dev-days of resolver-source field aliasing (or a generic routing-source adapter)
2. ~1 dev-day of string i18n on owner placeholders
3. ~0.5 dev-day to scrub the 2 MASCI strings from `command_center.py`
4. Per-tenant config of `command_center_thresholds` and `command_center_calendar`

No schema migration · no projection rewrite · no service-layer rewrite. The library remains tenant-agnostic at its core.

---

## 7 · OMEGA discipline scorecard

| Discipline rule | Verdict |
|---|---|
| Zero code edits in this batch | 🟢 |
| Zero UI edits | 🟢 |
| Zero DB writes (reads only via probe scripts) | 🟢 |
| Zero new endpoints | 🟢 |
| Zero new collections | 🟢 |
| Zero refactors | 🟢 |
| Zero deployment | 🟢 |
| Zero Pillar 2 / 3 / 4 work | 🟢 |
| Zero Escalation Framework work | 🟢 |
| Zero Accountability Dashboard work | 🟢 |
| Zero Support Ticket System work | 🟢 |
| Zero ForgedOps portal work | 🟢 |
| Read-only certification only | 🟢 |
| STOP after reports | 🟢 (this report is one of 5 · agent stops after PRD / _INDEX update) |

---

## 8 · Files in this batch

| File | Purpose |
|---|---|
| `PILLAR1_OPERATIONAL_CERTIFICATION_REPORT.md` (this file) | Master report · Phases 1, 2, 6 · OMEGA scorecard |
| `PILLAR1_DEPLOYMENT_RECOMMENDATION.md` | Final verdict · 3 deployment paths |
| `PILLAR1_EXECUTIVE_USABILITY_REPORT.md` | Phase 3 · per-card 6-AM walkthrough |
| `PILLAR1_SUPPORTABILITY_AUDIT.md` | Phase 4 · ForgedOps support question matrix |
| `PILLAR1_WHITE_LABEL_READINESS_REPORT.md` | Phase 5 · MASCI inventory + backlog |
| `pillar1_certification_evidence/live_snapshot_2026-05-31.json` | Raw `/api/admin/command-center/snapshot` payload |
| `pillar1_certification_evidence/ownership_sampling_2026-05-31.txt` | Raw 25-record ownership probe output |
| `pillar1_certification_evidence/data_quality_probes_2026-05-31.txt` | Raw DQ aggregations |

---

## 9 · Closeout

🟡 **GO WITH KNOWN LIMITATIONS.** Pillar 1 itself is certified for production deployment. The limitations are inherited from Pillar 2 Phase A's documented defects (D1/D2/D5) and from underlying-data hygiene (preview seed pollution · sparse routing data), neither of which is within Pillar 1's scope to fix.

The deployment recommendation is in `PILLAR1_DEPLOYMENT_RECOMMENDATION.md`. **STOP. No code. No deploy. Awaiting operator review.**
