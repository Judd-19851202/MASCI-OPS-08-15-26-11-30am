# Executive Heat Map — Scoring Specification (Pillar 2)

**Classification:** OMEGA Pillar 2 · DESIGN / SPEC ONLY · No code · No DB · No endpoints · No UI · No notifications · No workflow changes
**Generated:** 2026-05-31 UTC
**Author:** E1
**Audience:** Operations Leadership · Executive Leadership Team
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_AUDIT.md` · `EXECUTIVE_COMMAND_CENTER_SPEC.md` · `EXECUTIVE_DATA_SOURCE_MAP.md` · `EXECUTIVE_IMPLEMENTATION_ROADMAP.md`

---

## 1 · Goal

Define a single, objective, auditable Red / Yellow / Green scoring methodology that drives **every** RAG pill on the Command Center. The scorer must be:
1. **Deterministic** — same inputs → same colour, no opinion.
2. **Auditable** — every colour cites the rule that produced it (`warnings[]` pattern from `/admin/recovery/snapshot`).
3. **Tunable** — thresholds live in config, not in code.
4. **Composable** — the overall Pulse Strip pill is `max(severity)` across all card pills (worst wins).

---

## 2 · Global colour doctrine

| Colour | Meaning | Operator action |
|---|---|---|
| 🟢 GREEN | Within normal operational tolerance. No leadership attention required today. | None |
| 🟡 AMBER | Trending toward a problem. Leadership should be aware. | Inspect this card · drill into the listed items |
| 🔴 RED | Active operational issue requiring leadership decision or escalation now. | Act this morning · the Priority Stack will surface the worst RED items |

Three colours only. No yellow-amber sub-shades. No purples. No "blue = info." The colour space is binary-decisive: GREEN means leave it alone, RED means act now, AMBER is the bridge that says "you have time but not much."

---

## 3 · Scoring rule grammar

Every domain card's RAG is computed as:

```
score = max(rule_severity for rule in card_rules if rule.fires)
```

Where each rule has the shape:

```
{
  "id":          "<unique-rule-id>",
  "domain":      "<card-id>",
  "predicate":   "<plain-English-condition>",
  "data_source": "<collection-or-aggregation>",
  "amber_when":  "<threshold>",
  "red_when":    "<threshold>",
  "tunable_via": "<env-var-or-config-doc>"
}
```

A card returns:
- 🔴 if any rule fires `red_when`.
- 🟡 else if any rule fires `amber_when`.
- 🟢 else.

The card's `warnings[]` list contains one entry per fired rule, mirroring `/admin/recovery/snapshot.warnings`. Each warning carries `{severity, kind, message, rule_id, item_count}`.

This pattern is **already proven in production** (`recovery_dashboard.py` produces `warnings[{kind, severity, message}]`). The Command Center adopts it verbatim.

---

## 4 · Per-domain scoring rules

The thresholds below are **starting defaults** — every threshold MUST be operator-tunable via a config document (proposal: `db.command_center_thresholds`, single doc with one field per rule, see `EXECUTIVE_DATA_SOURCE_MAP.md` §6).

### 4.1 Card 1 · Jobs Today

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| JOBS-1 | Active jobs with **no DR filed today** by 17:00 local | ≥ 2 jobs | ≥ 5 jobs |
| JOBS-2 | Active jobs with **open incident severity≥medium** unaddressed >24h | ≥ 1 job | ≥ 3 jobs |
| JOBS-3 | Active jobs with **no PM assigned** (orphaned project) | ≥ 1 | ≥ 1 (always RED) |

### 4.2 Card 2 · Safety Today

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| SAF-1 | Open `incidents` with `severity ∈ {medium, high}` and `status=open` and `created_at > 48h ago` | ≥ 1 | ≥ 3 |
| SAF-2 | Open `corrective_actions` past `due_date` | ≥ 1 | ≥ 3 |
| SAF-3 | Open `compliance_findings` severity=red (acknowledged but not resolved) | ≥ 1 | ≥ 1 |
| SAF-4 | High-severity safety meeting/JHA gap (PM scope without meeting in last 14 days) | ≥ 2 | ≥ 4 |

### 4.3 Card 3 · Equipment Today

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| EQP-1 | `equipment_inspections.out_of_service=yes` AND no Shop sign-off | ≥ 1 | ≥ 3 |
| EQP-2 | `fleet_defects.status=open AND severity=critical` | ≥ 1 | ≥ 1 |
| EQP-3 | `asset_holds.active=true` aging > 7 days | ≥ 1 | ≥ 3 |
| EQP-4 | DVIR defect-OOS with no shop task in last 24h | ≥ 1 | ≥ 1 |

### 4.4 Card 4 · Accountability Overdue

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| ACC-1 | `tasks.status=open AND due_at < now` | 5–14 items | ≥ 15 items |
| ACC-2 | `corrective_actions` past `due_date` (also feeds SAF-2) | duplicate flag — surface once | — |
| ACC-3 | `notifications.acknowledged=false AND created_at > 7d ago` per executive user | ≥ 5 | ≥ 15 |

### 4.5 Card 5 · PM Load

Per-PM score = `(open_DRs_to_review × 1) + (open_incidents_in_pm_scope × 3) + (open_POs_for_pm_jobs × 1) + (overdue_tasks_assigned_to_pm × 2)`.

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| PML-1 | PM with composite load score | ≥ 12 | ≥ 24 |
| PML-2 | PM not seen (`last_login_at < 5 days`) AND has open items | ≥ 1 | ≥ 1 |

### 4.6 Card 6 · Supervisor Load

Per-FL-user score = `(daily_reports_signed_in_last_7d × 0.2) + (open_field_leadership_records × 1) + (dispatch_crew_day_count_this_week × 0.5)`.

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| SUP-1 | FL user with composite load score | ≥ 15 | ≥ 25 |
| SUP-2 | FL user with open field_leadership_records past due | ≥ 1 | ≥ 3 |

### 4.7 Card 7 · Approvals Aging

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| APP-1 | `po_requests.status=pending` AND age 3–4 days | ≥ 1 | — |
| APP-2 | `po_requests.status=pending` AND age 5–6 days | — | ≥ 1 |
| APP-3 | `po_requests.status=pending` AND age ≥ 7 days | (already RED via APP-2) | ≥ 1 (always RED) |
| APP-4 | `po_requests.receipt_required=true AND receipt_uploaded=false` past `due_at` | ≥ 1 | ≥ 3 |

### 4.8 Card 8 · Projects at Risk

Per-project composite RAG = worst of:
- Card 1 (Jobs) restricted to project
- Card 2 (Safety) restricted to project
- Card 3 (Equipment) restricted to project's assigned assets
- DR cadence rule: PRJ-1 — project with no DR in last 3 working days (AMBER ≥ 1 / RED ≥ 5 days no-DR)
- Cost rule: PRJ-2 — project P&L variance > 10% (AMBER) / > 25% (RED) (when `projects.pnl` data is available; OFF when missing)

A project is RED if any of the above rules fire RED for that project_number.

### 4.9 Card 9 · Operational Bottlenecks

| Rule ID | Predicate | Amber when | Red when |
|---|---|---|---|
| BNK-1 | `dispatch_assignments` stuck in same state > 24h | ≥ 1 | ≥ 5 |
| BNK-2 | `daily_reports` submitted but unreviewed > 48h | ≥ 3 | ≥ 10 |
| BNK-3 | `po_requests` in approval queue > 5d (also via APP-2/APP-3) | duplicate | — |
| BNK-4 | OOS equipment without work-order > 24h | ≥ 1 | ≥ 3 |
| BNK-5 | `operations_events.status=stuck` (if such field exists) | ≥ 1 | ≥ 5 |

### 4.10 Card 10 · Recommender (composite reducer)

The recommender does **not** define new rules. It is a reducer over every fired rule across cards 1–9, plus the priority weights below.

```
priority_score(item) = severity_weight × age_weight × domain_weight × ownership_weight
```

Where:
- `severity_weight` = RED:10, AMBER:3, GREEN:0 (GREEN items never appear in recommender)
- `age_weight` = log10(age_hours_open) + 1
- `domain_weight` = 1.5 for safety/equipment/jobs, 1.0 for accountability/approvals, 0.7 for load
- `ownership_weight` = 1.2 if owner role ∈ {operations_director, executive_leadership}, 1.0 otherwise

The top 5 by `priority_score` populate the Priority Stack. The top 20 populate the Recommender card's drilldown list.

---

## 5 · Overall Pulse Strip pill

```
overall = max(card.pill for card in [1..9])
```

If any card is RED → Pulse is RED.
Else if any card is AMBER → Pulse is AMBER.
Else GREEN.

The Pulse Strip's headline number is `count(RED_items) + count(AMBER_items)` across all cards.

---

## 6 · Audit trail per RAG decision

Every fired rule MUST emit a `warnings[]` entry of the shape:

```json
{
  "severity": "red|amber",
  "kind":     "<rule_id>",
  "message":  "<plain-English explanation>",
  "rule_id":  "<rule_id>",
  "item_ids": ["<id1>", "<id2>", "..."],
  "item_count": 7,
  "domain":   "<card-id>",
  "owner":    "<role>",
  "drill_to": "/admin/<page>?…"
}
```

This is the **same structure** the operator already trusts on `/admin/recovery/snapshot`. Adoption guarantees auditability without inventing a new convention.

---

## 7 · Tunability contract

No threshold may be hardcoded in JSX. All thresholds live in **one** of:
1. A single config document `db.command_center_thresholds` (admin-strict CRUD, future Phase A).
2. Environment variables prefixed `EXEC_CC_*` (for thresholds that must change without DB writes).
3. `EXECUTIVE_DATA_SOURCE_MAP.md` §6 lists the full proposed config schema.

Tuning a threshold must NEVER require a code deploy. (Mirrors how `BACKUP_R2_HOURLY` and `OOM_WATERMARK_MB` are operator-tunable today.)

---

## 8 · Non-scoring elements (must NOT influence RAG)

- ❌ User opinion ("this feels bad")
- ❌ Cosmetic conditions (typos, layout drift)
- ❌ Backup/recovery health (already lives in `/admin/recovery` — link from Pulse Strip instead of merging)
- ❌ Login analytics (lives in `/admin/analytics`)
- ❌ Anything outside the 10 mandated operator questions

If a future request would add a rule outside these 10 domains, the request must first be re-scoped against the four OMEGA pillars.

---

## 9 · Evidence of pattern viability

The RAG + warnings pattern proposed here is **already production-proven** for one domain:

| Pattern element | Already running in production | Evidence |
|---|---|---|
| RAG pill | yes — `recovery/snapshot.pill = AMBER` | `BACKUP_RECOVERABILITY_EPIC_CLOSEOUT.md` §2.4 |
| `warnings[]` array with severity+kind+message | yes — `recovery/snapshot.warnings` | same evidence |
| `computed_at` freshness stamp | yes — `recovery/snapshot.computed_at` | same evidence |
| Threshold tunable via env var | yes — `OOM_WATERMARK_MB`, `BACKUP_R2_HOURLY` | `OMEGA_PRE_DEPLOYMENT_CERTIFICATION_REPORT.md` §9 |
| Drill from pill to detail | yes — `/admin/recovery` UI | `AdminRecovery.jsx` |

The Command Center is, doctrinally, "the recovery dashboard pattern applied to the entire operational surface." No new architecture required.
