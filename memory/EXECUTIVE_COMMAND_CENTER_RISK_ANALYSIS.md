# Executive Command Center — Risk Analysis (Pillar 2 · Pre-Implementation)

**Classification:** OMEGA Pillar 2 · RISK ANALYSIS ONLY · No code · No DB · No endpoints · No UI
**Generated:** 2026-05-31 UTC
**Author:** E1
**Scope:** Catalog every category of risk in the blueprint — missing executive questions, duplicate widgets, low-value widgets, noise generators, unreliable data sources, false positives, false negatives.
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_DESIGN_REVIEW.md` · `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` · `FINAL_PHASE_A_RECOMMENDATION.md`

---

## 1 · Missing executive questions

The blueprint answered the 10 operator-mandated questions. But a fully-honest design review must surface what the blueprint **omitted** that leadership of a construction company plausibly needs:

| # | Missing question | Why it matters | Phase fit |
|---|---|---|---|
| MX-1 | What customer / client communications are open? | RFIs · change orders · client complaints can sink projects faster than safety/equipment issues | Phase B (depends on collection that may not yet exist) |
| MX-2 | What financial signals are flashing? | AR aging · cash position · project margin trajectory drive go/no-go decisions on bids, hires, capex | Phase B/C (probably requires external data) |
| MX-3 | What certifications / licenses / insurance / training expirations are imminent? | A lapsed driver CDL or insurance certificate can halt operations in 1 day; lapsed safety training triggers regulatory exposure | Phase A candidate — `document_expirations` collection already exists (23 references in code) |
| MX-4 | What schedule / critical-path milestones are at risk? | The single biggest contractor risk; no surface today | Phase B+ (depends on schedule import architecture) |
| MX-5 | What weather is incoming vs work scheduled? | Construction is weather-bound; 48h forecast vs. crew assignments is high-value | Phase C+ (requires weather integration) |
| MX-6 | What is changing fast (vs. yesterday)? | A delta view ("yesterday GREEN, today RED on jobs") accelerates pattern recognition | Phase A cheap addition — single sparkline per card |
| MX-7 | What just resolved? | Closing the loop helps leadership know the system is working; reinforces dashboard trust | Phase A or B |
| MX-8 | What is the org doing well this week? | A small "Wins" panel prevents the dashboard from becoming a pure-pain instrument and improves daily morale of leadership using it | Phase B nice-to-have |

**Recommendation:** Add **MX-3 (Document/License/Training Expirations)** as a Phase A card — strong evidence base (`document_expirations` collection already wired) + critical operational risk + clean RAG semantics (X days to expiry). This becomes Card 5 in the revised blueprint and **replaces** PM Load (per design review).

---

## 2 · Duplicate widgets (already inside the blueprint)

The heatmap spec itself acknowledges several duplications. Mapped here for visibility:

| Duplication | Cards involved | Cause | Recommendation |
|---|---|---|---|
| Same `incidents.severity≥medium` record | JOBS-2 + SAF-1 | Card 1 looks at incidents linked to a project; Card 2 looks at the incident severity itself | Drop JOBS-2; let SAF-1 own this. Card 1 cites "open incidents" as a count but does NOT promote its own RAG from incident severity |
| Same `corrective_actions` past-due | SAF-2 + ACC-2 | Spec explicitly flags ACC-2 as duplicate of SAF-2 | Surface only on Safety card (SAF-2). Accountability card excludes CAs |
| Same OOS equipment | EQP-1 + EQP-4 + BNK-4 | OOS is the same underlying state across three rules | Consolidate to one rule on Equipment card (EQP-1) with subcategories; remove EQP-4 and BNK-4 |
| Same aging POs | APP-2/APP-3 + BNK-3 | Spec explicitly flags BNK-3 as duplicate of APP-2/APP-3 | Remove BNK-3 (already supports removing Card 9) |
| Same overdue tasks | ACC-1 + PML composite + Recommender | Tasks counted three times | Define `tasks` as Accountability-only signal; PM Load should NOT include `overdue_tasks_assigned_to_pm` |
| Same overdue notifications | ACC-3 (also fed into Card 4) | Notifications are an audit trail, not an action queue | Remove ACC-3 entirely (per design review) |

**Net duplication count in the original blueprint: 6 distinct overlaps. The slimmer Phase A removes all 6 by removing Cards 5, 6, 9 and de-duplicating cards 1–4.**

---

## 3 · Low-value widgets

Defined as: produces data leadership cannot act on, or duplicates data already available with comparable effort.

| Card / Rule | Low-value reason | Disposition |
|---|---|---|
| JOBS-3 (orphan PM project) | One-time data hygiene; ongoing RED is noise | Move to admin compliance scan (already exists at `/admin/compliance-findings`); remove from Command Center |
| ACC-3 (stale unack notifications) | Most platform notifications aren't ack-required; pure noise | Remove |
| PML-2 (PM not seen 5 days) | False-positive engine due to no PTO calendar | Remove |
| EQP-3 generic | Many asset holds are deliberate | Restrict to "active operations" reason whitelist |
| BNK-5 (`operations_events.status=stuck`) | Field may not consistently exist | Remove until field schema confirmed |
| All of Card 9 | 3/5 rules are duplicates; 2/5 have weak baselines | Remove entire card from Phase A |

---

## 4 · Noise generators (high false-positive rate)

Rules that produce RAG flips for reasons that do not change leadership behavior:

1. **JOBS-1 (no DR by 17:00 local):** weekends/holidays/no-work days fire RED. Without PTO/holiday calendar, multiple RED states are wrong every week.
2. **ACC-3 (notifications stale 7d):** by design, fires RED for every executive within a week.
3. **PML-2 (not seen 5 days):** PTO, sick leave, on-site work without laptop all trigger.
4. **EQP-3 broad (active asset holds >7d):** intentional holds (training, capital reserve) trigger.
5. **SAF-4 broad (no safety meeting 14d):** dormant projects with no DR activity trigger.

**Total noise sources in original blueprint: 5.** After design review's modifications, the count drops to **0** (each is removed or gated).

---

## 5 · Unreliable data sources

Sources whose quality cannot be trusted to drive a leadership RAG without first being audited:

| Source | Risk | Mitigation |
|---|---|---|
| `projects.pnl` field (Card 8 / PRJ-2) | Sparsely populated; many projects have no P&L data | OFF the rule when data missing; defer Card 8 to Phase B with explicit data-coverage gate |
| `incidents.severity` (Card 2) | Operator-entered; inconsistent calibration | Cross-check against keyword scan in `description` field; add audit trail for severity changes |
| `tasks.due_at` (Card 4) | Not consistently set across all task-creating workflows (per data source map row 2) | Filter accountability card to tasks-with-due_at-set only; document the visibility gap |
| `daily_reports.supervisor_email` (Card 6) | Free-form text; not validated against FL user roster | Phase A defers Card 6 entirely; Phase C must clean this before reactivating |
| `operations_events.status` (Card 9) | Field may not be uniformly populated; spec marked 🟡 | Phase A removes Card 9 |
| `project_managers.last_login_at` (Card 5) | Doesn't capture mobile/phone/email work | Phase A removes Card 5 |
| `asset_holds.reason` (Card 3 / EQP-3) | Free-form; needs whitelist | Define whitelist as part of Phase A config doc |
| `pm_review.status` on `daily_reports` (BNK-2) | Field exists but adoption is uneven | Card 9 removed |

**Net effect:** 8 unreliable sources flagged. Phase A reduces dependence to **2 with explicit mitigations** (incidents.severity audited; tasks.due_at filtered).

---

## 6 · False positives — RAG fires when no action needed

| Scenario | Card affected | Frequency estimate |
|---|---|---|
| Saturday morning login: no DRs because no work | Card 1 (JOBS-1) | every weekend |
| PM on PTO: looks "not seen" | Card 5 (PML-2) | weekly |
| Long-running asset hold for winter storage | Card 3 (EQP-3) | many units, all winter |
| Dormant project's missed safety meeting | Card 2 (SAF-4) | persistent |
| Low-dollar PO aging 5 days | Card 7 (APP-2) | weekly |
| Notification informational, unack 7+ days | Card 4 (ACC-3) | continuous |
| Acknowledged-but-unresolved safety finding (yellow) | Card 2 (gap — false NEGATIVE actually, see §7) | persistent |

After design-review modifications, the FP rate drops sharply because cards 5, 6, 9 are gone, rules JOBS-3 / ACC-3 / PML-2 are removed, and EQP-3 / SAF-4 are gated. Remaining FP risk: Card 7 dollar-weighting (pending operator SLA input).

---

## 7 · False negatives — actionable conditions the dashboard misses

| Scenario | Why missed | Mitigation |
|---|---|---|
| Severe incident acknowledged 2h ago but not resolved | SAF-1 looks at age >48h | Add SAF-1b: any unresolved incident with `severity=high` regardless of age |
| Critical defect raised 5 min ago | EQP-2 fires at 1, but only via simple count — no severity surfacing per-item ordering | Ensure card body sorts by recency + severity |
| Stuck workflow with no `tasks` artifact (e.g., emails-only handoffs) | No DB trace | Acknowledge as out-of-scope (handoff platform; surface separately if needed) |
| Compound failure (1 incident + 1 OOS + 1 missing DR all on same job) | Each fires its own card, but no card combines them | Phase B Projects-at-Risk card is designed for this; Phase A acknowledges the gap |
| Chronic yellow compliance finding (e.g., open 60 days) | SAF-3 only RED-when-severity=red | Add SAF-3b: any compliance finding open >60 days |
| Imminent license/cert expiration | Original blueprint had no expirations card | Add MX-3 (`document_expirations`) as new Phase A card |
| Backup health AMBER (already exists at `/admin/recovery`) | Not on Command Center | Intentional — link Pulse Strip to `/admin/recovery` rather than duplicate |

After modifications, the dashboard adds **3 new sub-rules (SAF-1b, SAF-3b, MX-3)** that close the most material false-negative gaps.

---

## 8 · Operational adoption risks

Beyond technical correctness, the Command Center introduces social/process risks:

| Risk | Description | Mitigation |
|---|---|---|
| **Alert fatigue** | Too many RED items train leadership to ignore them | Slim Phase A · tune thresholds via config not code · operator-led threshold review monthly |
| **Black-box trust** | If the recommender is opaque, leadership stops questioning it | Defer recommender to Phase B; require explainable per-item reason codes |
| **Surveillance perception** | PM/Supervisor load cards feel like a scoreboard, eroding trust | Remove from Phase A · re-introduce only as opt-in for that role's lens (Phase C) |
| **Dashboard-driven decision-making replaces site experience** | Leadership stops walking sites because "the dashboard says it's GREEN" | Frame dashboard as triage tool, not replacement for direct contact |
| **Single-screen tunnel vision** | Operations Director misses non-dashboard issues | Pulse Strip must link to `/admin/recovery` and `/admin/audit` so adjacent context is one click away |
| **Stale snapshot trust** | Operator views a 60-sec-old snapshot and acts on out-of-date data | Make `computed_at` prominent · manual refresh button required (no auto-refresh that hides staleness) |
| **Permission creep** | Future request to "let executive_leadership see HR-sensitive data" pollutes the role model | Hard separation: Command Center returns aggregate signals only · drill-downs respect existing RBAC |

---

## 9 · Architecture risks

| Risk | Description | Mitigation |
|---|---|---|
| **Compute cost** | Snapshot endpoint runs N+1 aggregations across 132 collections | Bound to ~6 collections in slim Phase A · profile during pilot · cache only if measured need |
| **OMEGA backup freeze violation** | Future agent might "improve" `recovery_dashboard.py` to share code | Phase A code lives in NEW `routes/command_center.py` file · explicit don't-touch rule in roadmap §A.4 |
| **`tasks` collection schema mutations** | Adding `priority` filter might tempt schema additions | If `priority` is missing, Phase A filters in-application not by index — no schema change |
| **N+1 in card 8 (when reintroduced)** | Per-project rollup naively iterates jobs | Phase B requires single aggregation pipeline, profiled before launch |
| **Threshold doc concurrency** | Two admins editing thresholds simultaneously | `command_center_thresholds` doc uses `version` field for optimistic locking · Phase A acceptance criterion |

---

## 10 · Net risk posture after design-review modifications

| Risk category | Original blueprint | After Phase-A slimming + modifications |
|---|---|---|
| Missing exec questions | 8 unaddressed | 1 added (MX-3 Expirations) · 7 acknowledged as future-phase |
| Duplicate widgets | 6 overlaps | **0** |
| Low-value widgets | 6 instances | **0** |
| Noise generators | 5 rules | **0** |
| Unreliable data sources | 8 sources critical | **2 with explicit mitigations** |
| False-positive scenarios | 7 high-frequency | 1 (low-dollar PO aging; gated on operator SLA) |
| False-negative scenarios | 7 unaddressed | 3 closed via SAF-1b, SAF-3b, MX-3 · 4 deferred |
| Operational adoption risks | 7 risks | All mitigated via slim scope + Phase B deferrals |
| Architecture risks | 5 risks | All mitigated in roadmap |

The slim Phase A is **substantially more defensible** than the original blueprint.

---

## 11 · Top 5 risks to surface to operator BEFORE Phase A is authorized

1. **PO turnaround SLA** — what is MASCI's actual norm? Phase A's Card 7 thresholds depend on this (see `EXECUTIVE_COMMAND_CENTER_OPERATOR_CHALLENGE.md` Q-7).
2. **PTO / holiday calendar** — is one available, or must the dashboard ignore weekends/holidays via static config?
3. **`incidents.severity` calibration** — is severity entered consistently, or do we need a side-by-side keyword audit before launch?
4. **`document_expirations` data coverage** — is this collection complete for licenses, insurance, training? If sparse, MX-3 cannot ship in Phase A.
5. **Pilot user set** — names of the 3–5 people who will use Phase A daily for 4 weeks. Their feedback is the gating evidence for Phase B authorization.
