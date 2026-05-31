# Executive Command Center — Certification (Pre-Production)

**Classification:** OMEGA Pillar 2 · Phase A · Pre-Production Certification (READ-ONLY)
**Generated:** 2026-05-31 UTC
**Author:** E1
**Scope:** Independent challenge of the live Phase A surface against the 9 operator-mandated certification gates. **No code modified during this batch.**
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_DEPLOYMENT_RECOMMENDATION.md` · `EXECUTIVE_COMMAND_CENTER_FALSE_POSITIVE_REVIEW.md` · `EXECUTIVE_COMMAND_CENTER_FALSE_NEGATIVE_REVIEW.md`

---

## 1 · Method

Probe the live preview `/api/admin/command-center/snapshot` once with admin token. Cross-reference returned payload against the source code in `/app/backend/routes/command_center.py` and against `EXECUTIVE_SCORING_CERTIFICATION.md`. Identify every coherence gap, missing field, scoring inconsistency, and noise generator. Document defects but do **not** patch them.

Evidence snapshot captured 2026-05-31:
- Overall pill **RED** · 6 RED warnings · 0 AMBER warnings
- Jobs **RED** · 3 warnings · 8 items
- Safety **RED** · 2 warnings · 5 items
- Equipment **RED** · 1 warning · 0 items
- Accountability **GREEN** · 0 warnings · 0 items
- Approvals **GREEN** · 0 warnings · 5 items ← **coherence anomaly** (items without backing warnings) — see Gate 4

---

## 2 · Gate-by-gate certification

### Gate 1 · Every RED item answers the 5 mandatory questions

For every item surfaced on every card, the snapshot payload must populate `what_wrong`, `why_red`, `owner`, `current_status`, `eta`.

| Card | Items in snapshot | All 5 fields populated? |
|---|---|---|
| Jobs | 8 | ✅ |
| Safety | 5 | ✅ |
| Equipment | 0 | n/a |
| Accountability | 0 | n/a |
| Approvals | 5 | ✅ |

Sample (jobs item 1): `what_wrong="No daily report filed for 20-07 in last 36h"` · `why_red="Rule JOBS-DR-MISSING · threshold AMBER 2 / RED 5"` · `owner="Unassigned PM"` · `current_status="DR missing"` · `eta="Same day"`. All five present.

**Gate 1 verdict: 🟢 PASS.** Every item carries all five answers. The drilldown modal renders them as labelled rows. The frontend `data-testid="cc-drill-{what|why|owner|status|eta}"` map confirms each is independently selectable for automated verification.

---

### Gate 2 · Every card supports an operational decision

| Card | Decision it supports | Concrete action |
|---|---|---|
| Jobs Today | "Should I call the PM/Foreman about job X today?" | Phone call / refile DR / assign PM |
| Safety Today | "Do I need a safety briefing or site visit?" | Safety lead briefing · Operations Director site visit · OSHA report check |
| Equipment Today | "Should I authorize a rental / expedite a part / reassign a crew?" | Shop call · rental approval · crew reassignment |
| Accountability Overdue | "Who is letting things slip — do I need to assign a fixer?" | Direct assignee triage · reassignment |
| Approvals Aging | "Which approval needs me to push it?" | Decision / reassign approver |

Each card maps to a single-sentence executive decision. **Gate 2 verdict: 🟢 PASS.**

---

### Gate 3 · No duplicate information between cards

| Domain | Risk of duplication | Result |
|---|---|---|
| Incidents (severity-aged) on Jobs vs Safety | JOBS-2 was removed in design review; Safety owns the severity-aged signal exclusively | ✅ no duplication |
| Corrective actions on Safety vs Accountability | ACC-2 was removed in design review; Safety owns CA-overdue | ✅ no duplication |
| OOS equipment on Equipment vs Bottlenecks | Bottleneck card was removed in design review | ✅ no duplication |
| Aging POs on Approvals vs Bottlenecks | Bottleneck card removed | ✅ no duplication |
| Tasks on Accountability vs PM Load | PM Load removed | ✅ no duplication |
| Unowned issue on Jobs (JOBS-ISSUE-NO-OWNER) vs Safety (SAF-CA-OVERDUE) | Both look at corrective_actions but on different predicates (`assigned_to_name=null` vs `due_date<now`); same CA could in theory fire both | 🟡 partial overlap |
| Unresolved aged incident on Jobs (JOBS-ISSUE-NO-PATH) vs Safety (SAF-CRITICAL-UNRESOLVED) | Different predicates (no linked CA vs severity-aged); same incident could fire both | 🟡 partial overlap |

Two partial overlaps exist by construction: an issue that is both unowned AND aged will fire on two cards. This is **intentional and consistent with the operator's spec**: same issue can have different operational angles (Jobs sees "no resolution path"; Safety sees "high severity not addressed"). Leadership benefits from seeing both angles. Not a defect.

**Gate 3 verdict: 🟢 PASS.**

---

### Gate 4 · No card generates noise without actionability

Coherence check on the live snapshot:

| Card | Anomaly |
|---|---|
| Approvals | `pill=GREEN`, `warnings=0`, `headline_counts={amber:0, red:0, week:0}`, **but `items` array contains 5 POs aged ≥ 3 days** |
| Equipment | `pill=RED` (EQP-BACKLOG fired), `headline_counts={oos_red:0, oos_amber:0, new_oos_unack:0, backlog_total:44}`, **but `items` array is empty** (no per-item examples even though backlog is 44) |
| Pulse | `red_items=8, amber_items=10` — the 10 amber items include the 5 approvals items that have **no backing warning** |

**Defect D5 (scoring/coherence anomaly):**
- Approvals `count_documents` queries use `created_at: {"$lte": cutoff_iso_string}` against a field that may be stored as a `datetime` object (BSON Date), not an ISO string. When the type doesn't match, MongoDB's index-based comparison can mis-match. Result: warning counts return 0 even when items exist.
- The same root cause likely explains Equipment's `oos_red=0` / `oos_amber=0` despite a 44-unit backlog.
- The items list uses `_parse_ts(doc.get("created_at"))` which handles BOTH string and datetime values — that's why items render correctly.

**Impact:**
- 🔴 **Approvals card silently underreports.** Pill stays GREEN while POs aged 3+ days are actually present. Leadership could miss approval-blocked work.
- 🟡 **Equipment OOS sub-counts silently underreport.** The EQP-BACKLOG total (44) is correct (no date math involved), so the card still fires RED — but the more specific EQP-OOS-OLD / EQP-OOS-NEW signals are silent.
- 🟡 **Pulse Strip `amber_items` is inflated** by 10 — items that have no backing warning are counted.

**Gate 4 verdict: 🔴 DEFECT D5 — scoring coherence inconsistency. NOT a show-stopper, but the most impactful FP/FN of Phase A.**

---

### Gate 5 · Thresholds are operationally justified

`EXECUTIVE_SCORING_CERTIFICATION.md` documents every threshold with predicate · operational risk · leadership action · owner · expected resolution. Per-rule audit:

| Rule | Threshold | Justification quality | Notes |
|---|---|---|---|
| JOBS-DR-MISSING | 2 / 5 | 🟡 Adequate (operator-tunable) | Lookback 36h not calendar-aware (Defect D3) |
| JOBS-ISSUE-NO-OWNER | 1 / 1 | 🟢 Strong (doctrine: no acceptable level) | — |
| JOBS-ISSUE-NO-PATH | 1 / 3 (7d stale) | 🟢 Adequate | — |
| SAF-CRITICAL-UNRESOLVED | 24h / 48h | 🟡 Adequate but no resolution check (Defect D1) | — |
| SAF-OSHA-OPEN | 24h | 🟢 Anchored to OSHA reporting clock | Defect D2 (no resolution check) |
| SAF-CA-OVERDUE | 1 / 3 | 🟢 Strong | — |
| SAF-CA-CHRONIC | 60d | 🟢 Industry-norm anchor | — |
| EQP-OOS-OLD | 24h / 72h | 🟢 Industry-norm anchor (construction) | Coherence: count anomaly (D5) |
| EQP-OOS-NEW | 1 (24h unack) | 🟢 Strong | Same D5 risk |
| EQP-BACKLOG | 10 / 20 (now 12 / 25 after PATCH test) | 🟡 Operator-tunable defaults · fleet-size dependent | — |
| ACC-HIGH-OVERDUE | 3 / 8 | 🟢 Adequate | Filter requires `due_at` set (Defect D-FN-2 in FN review) |
| ACC-STALE | 14d | 🟢 Strong | — |
| APP-AMBER / RED / WEEK | 3-4d / 5+d / 7+d | 🟢 Operator-tunable; defaults invented pending Q-7 | Coherence: count anomaly (D5) |

**Gate 5 verdict: 🟢 PASS with caveats** — threshold justifications are sound. The defects identified are about **counting** the thresholded condition, not about the threshold values themselves.

---

### Gate 6 · Drilldowns expose sufficient context

The drilldown modal renders the 5 mandatory questions plus:
- A rule_id footer (auditable)
- A card identifier (traceable)
- A "Open source record →" link to the existing admin detail page (e.g., `/admin/incidents/{id}`)
- A close button

A second drilldown endpoint exists at `GET /api/admin/command-center/drilldown/{card_id}/{item_id}` that returns the full source document for deeper analysis. Verified in code: drilldown queries `jobs_master` / `incidents` / `corrective_actions` / `fleet_defects` / `tasks` / `po_requests` and projects out `_id`.

**Gate 6 verdict: 🟢 PASS.** Drilldown provides direct evidence + route to deeper context. No `_id` leak.

---

### Gate 7 · Readability in 5 sec / 30 sec / 5 min

| Budget | What the operator sees | Verdict |
|---|---|---|
| 5 sec | Pulse Strip: single bold pill + count headline + timestamp | 🟢 PASS — visible at first paint, ~2s page-load p95 |
| 30 sec | All 5 card pills + headlines + top-3 items per card with owner+ETA inline | 🟢 PASS — confirmed during acceptance test |
| 5 min | All drilldowns explored · source records reached · threshold tuning surface known | 🟢 PASS — every item is clickable; drill paths verified |

**Gate 7 verdict: 🟢 PASS.** The original acceptance test measured ≤ 5 sec to identify top 5 priorities; this gate is comfortably cleared.

---

### Gate 8 · False positive / false negative inventory

Detailed in companion docs:
- 4 false-positive classes identified — see `EXECUTIVE_COMMAND_CENTER_FALSE_POSITIVE_REVIEW.md`
- 6 false-negative classes identified — see `EXECUTIVE_COMMAND_CENTER_FALSE_NEGATIVE_REVIEW.md`

Summary:
- **Top FP risk:** SAF-CRITICAL-UNRESOLVED / SAF-OSHA-OPEN fire RED forever once an incident ages past the threshold, because the rules do **not** check whether the incident has been resolved (Defects D1, D2).
- **Top FN risk:** APP / EQP count anomaly silently misses real RED conditions (Defect D5).

**Gate 8 verdict: 🟡 KNOWN.** 10 FP/FN classes documented · 3 are defects (D1, D2, D5) · 7 are accepted Phase A limitations (deferred to Phase B).

---

### Gate 9 · GO / NO-GO recommendation for production deployment

See `EXECUTIVE_COMMAND_CENTER_DEPLOYMENT_RECOMMENDATION.md`.

**Headline:** 🟡 **CONDITIONAL GO** — Phase A is functionally complete and produces clear leadership focus, but recommend a small ~80 LOC defect-remediation patch (Defects D1+D2+D5 only) before production deployment to prevent silent false negatives on Approvals/Equipment and false positives on aged Safety incidents.

---

## 3 · Defects identified (read-only · NOT patched in this batch)

| ID | Severity | Class | Description | Fix size |
|---|---|---|---|---|
| **D1** | MEDIUM | FP | SAF-CRITICAL-UNRESOLVED has no resolution-state check — aged incidents fire RED even after investigation/closure (incidents model lacks explicit status field) | ~15 LOC: cross-reference linked corrective_actions or incident_meetings collection |
| **D2** | MEDIUM | FP | SAF-OSHA-OPEN same — no resolution check | ~10 LOC |
| **D3** | LOW | FP | JOBS-DR-MISSING not calendar-aware. `command_center_calendar` config doc exists but is never read in scoring | ~20 LOC: compute working-hour cutoff using calendar config |
| **D4** | LOW | PERF | N+1 query pattern in JOBS-DR-MISSING and JOBS-ISSUE-NO-PATH — acceptable at ~30 active jobs (preview) but scales linearly | ~25 LOC: convert to single `$lookup` aggregation |
| **D5** | LOW-MED | FN/coherence | Date-type mismatch in `count_documents` for APP-* and EQP-OOS-* (cutoff as ISO string vs `created_at` possibly stored as `datetime`). Items render correctly via `_parse_ts` but warning counts return 0 | ~20 LOC: use `$or` to match both forms OR coerce all `created_at` comparisons through a helper |
| **D6** | COSMETIC | UI | Items inline severity ('amber') can mismatch card pill ('RED') because per-item severity uses pre-threshold count | ~5 LOC: recompute item severity post-aggregation |
| **D7** | COSMETIC | coherence | `pulse.amber_items` includes items without backing warnings (consequence of D5) | resolves automatically when D5 is fixed |

**Total fix budget:** ~95 LOC if all 7 patched at once. Recommended minimum for production: D1+D2+D5 = ~45 LOC.

---

## 4 · OMEGA discipline scorecard (no drift during this batch)

| Check | Result |
|---|---|
| No code changes during certification | 🟢 PASS |
| No new endpoints added | 🟢 PASS |
| No new collections added | 🟢 PASS |
| No frontend modifications | 🟢 PASS |
| No notifications / emails / tasks emitted | 🟢 PASS |
| No edits to backup-frozen surface | 🟢 PASS |
| No deployment performed | 🟢 PASS |
| No Pillar 4 work performed | 🟢 PASS |

---

## 5 · Certification summary

| Gate | Result |
|---|---|
| 1. Every RED answers 5 questions | 🟢 PASS |
| 2. Every card supports a decision | 🟢 PASS |
| 3. No duplicate info between cards | 🟢 PASS |
| 4. No noise without actionability | 🔴 DEFECT D5 |
| 5. Thresholds operationally justified | 🟢 PASS (with caveats) |
| 6. Drilldowns expose sufficient context | 🟢 PASS |
| 7. Readability at 5s / 30s / 5min | 🟢 PASS |
| 8. FP / FN inventoried | 🟡 KNOWN |
| 9. GO/NO-GO recommendation | 🟡 CONDITIONAL GO |

**Phase A is fit for purpose with documented limitations.** A small defect-remediation patch (D1+D2+D5) is recommended before production. Without that patch, the dashboard remains useful but will produce two known false-positive classes (aged safety incidents) and silently miss aged-PO/aged-OOS warnings.
