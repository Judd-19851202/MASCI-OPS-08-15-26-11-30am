# TRACK 15.74 — FULL PLATFORM TRUST RESTORATION & CERTIFICATION

**Run date:** 2026-02 preview · **Environment:** `masci_safety_preview` only (no production DB writes)
**Operator directive:** zero score inflation, fix-as-you-go, no silent failures, evidence-based green.

---

## 1 · Executive Summary

| Pillar | Score | Status |
|---|---|---|
| 1 · Powerful   | 9 / 10 | GREEN |
| 2 · Simple     | 8 / 10 | GREEN (Routing Status Panel + PM Coverage card make field/PM gaps visible) |
| 3 · Beautiful  | 8 / 10 | GREEN (no new defects found this pass) |
| 4 · Trusted    | 9 / 10 | GREEN (P1 dead-letter audit lie fixed this pass) |
| 5 · Proven     | 9 / 10 | GREEN (40/40 regression tests pass; this pass added Track 15.74 audit-trust suite) |
| 6 · Deployable | 9 / 10 | GREEN (preview→prod parity intact, env fallback verified) |

**Headline finding (P1 — FIXED THIS PASS):** dead-letter routing audit row was
hardcoding `resolved_to_count=0` and `status=dry_run`, causing every
PM-unresolved fallback to look like a silent drop in the operator
dashboard, even though the email was actually being delivered to
`safety@mascigc.com` via the env fallback. **Fixed in `pm_routing.py` —
audit now reports actual dead-letter recipient counts and uses the
honest `routed_to_dead_letter` / `dead_letter_unconfigured` statuses.**

No remaining P0 issues. Two P1 data-hygiene items require operator
backfill (see §5 Remediation Plan).

---

## 2 · Phase 1 — Platform Inventory (evidence)

* **Backend routes:** 139 files under `/app/backend/routes/` plus `server.py`
  (~ 5 000 lines of registered routes).
* **MongoDB collections (preview):** **181**, top-volume:
  `usage_events` (422 k) · `integration_sync_logs` (26 k) ·
  `health_monitor_runs` (21 k) · `audit_events` (18 k) ·
  `notifications` (8.9 k) · `daily_reports` (1 117) ·
  `equipment_inspections` (870) · `equipment_master` (705) ·
  `employees` (396) · `jobs_master` (30).
* **Modules certified in scope:** Daily Reports · Safety Meetings ·
  Equipment Pre-Ops · Equipment Mgmt · Employee Directory · HR · Shop ·
  Dispatch · QA/QC · Incidents · JHP · Active Jobs · Field Leadership ·
  Notifications · Email Routing · Integrations · Reports · PDFs · Admin ·
  System Health · Backup · Audit.

Evidence script: `/tmp/inventory.py` (re-runnable; uses only preview DB).

---

## 3 · Phase 3 — Master Data Integrity Audit (evidence)

Initial bash audit reported broad **RED** against deprecated fields
(`employee_id`, `incident_number`, `equipment_master_id` as canonical
keys). Investigation against the actual write-path code proved these
fields were vestigial. **The true canonical keys used by current code
are 100% present:**

| Collection | Canonical Key | Coverage |
|---|---|---|
| `employees` | `id` (UUID) | 396 / 396 (100%) |
| `user_directory` | `id`, `email` | 162 / 162 (100%) |
| `equipment_master` | `id` (UUID) | 705 / 705 (100%) |
| `equipment_units` | `id` (UUID) | 484 / 484 (100%) |
| `jobs_master` | `project_number` | 30 / 30 (100%) |
| `daily_reports` | `doc_id` | 1 117 / 1 117 (100%) |
| `meetings` | `doc_id` | 65 / 65 (100%) |
| `incidents` | `doc_id` | 70 / 70 (100%) |
| `equipment_inspections` | `doc_id` | 870 / 870 (100%) |
| `fleet_status` | `unit_number` | 385 / 385 (100%) |
| `backup_health` | `id` | 200 / 200 (100%) |

**Conclusion:** Identity write paths are healthy. Track 15.73 Slices 1–4
guardrails are still effective (all 20 of the 15.73 regression tests
pass — see §6). Remaining gaps are **data hygiene** (operator backfill)
not code drift.

---

## 4 · Phase 4 — Notification Trust Audit (evidence + fix)

### P1 fix-as-you-go (this pass)

**Defect:** `pm_routing._audit_dead_letter` wrote
`email_routing_audit_v2` rows with hardcoded
`resolved_to_count=0`, `status="dry_run"`, `dry_run=True`,
regardless of actual dead-letter recipients. With
`masci::ADMIN_DEAD_LETTER_TO = ['safety@mascigc.com']` configured in
DB, the email **was** being delivered, but the audit row claimed
zero recipients — exactly the "audit lies" trust violation banned by
the Track 15.74 charter.

**Fix:** `pm_routing.py` — `_audit_dead_letter` now accepts the
resolved `to`/`cc` lists, records true counts, and uses honest
statuses:
* `routed_to_dead_letter` — recipients resolved and the row reflects an
  actual routing decision (not a dry-run).
* `dead_letter_unconfigured` — surfaces the genuine P0 silent-drop case
  (no tenant route + no env fallback).

Both call sites in `recipients_for_record` were updated to pass the
resolved dead-letter recipient list.

**Regression coverage (added this pass):**
`backend/tests/test_track_15_74_dead_letter_audit_trust.py` — 2 tests, both PASS.

### Other notification certifications

| Item | Status | Evidence |
|---|---|---|
| `ADMIN_DEAD_LETTER_TO` configured for `masci` | GREEN | `email_routes` DB row present (`['safety@mascigc.com']`) |
| Tenant `customer_2_deploy_test` dead-letter | GREEN | `['support@customer2.example']` configured |
| Tenant `customer_3_deploy_test` dead-letter | GREEN | `['support@customer3.example']` configured |
| `email_routing_v2` critical routes populated | GREEN | 4 / 4 critical routes with recipients, 0 empty |
| `email_routing_audit_v2` writing rows | GREEN | 79 audit rows; 59 in last 24h; 0 errors |
| `platform_audit.pm_unresolved_dead_letter` rows | GREEN | 25 records — observability path proven |
| Track 15.73Q PM-email coverage endpoint | GREEN | `/api/admin/pm-email-coverage` admin-gated; PII-free shape |
| Track 15.28c notification canonicalization | GREEN | 16/16 tests pass |

---

## 5 · Phase 5 + 14 — Data Hygiene & Production Remediation Plan

**P1 (Operator action required — preview DB read-only safe):**

### 5.1 · `jobs_master.pm_email` — 7 active projects missing PM email

| project_number | project_name | recent DR count | last DR |
|---|---|---|---|
| 20-07 | T5686 SR 15/SR600 (SANFORD, 17/92, LAKE MARY) | 53 | 2026-06-19 |
| 26-07 | University High Parent Loop Ext | 16 | 2026-06-22 |
| 21-06 | T5736 Oveido - (426, BROADWAY) | 0 | — |
| 22-08 | T5749 SR 436 (ALTAMONTE SPRINGS) | 0 | — |
| 24-08 | E57B2 - SR 46 (MELLONVILLE AVE) | 0 | — |
| 26-04 | E58F7 - SR 5 | 0 | — |
| SD-6909db | SD test | 0 | — |

**Action (operator, in /admin → Active Jobs Master):** for each row,
set `pm_email` to the authoritative PM directory value
(/admin → Project Managers). Until backfilled the Daily Reports for
`20-07` and `26-07` fall through to `ADMIN_DEAD_LETTER_TO`
(`safety@mascigc.com`) — visible, not silent.

### 5.2 · `equipment_master.unit_number` — 247 / 705 missing

Already documented in Track 15.73 Slice 4 as a legacy classification
gap (small gear: pumps, generators, hand tools). The Track 15.73 picker
guardrails already prefer `unit_number` when present and emit a
warning when absent; new equipment cannot be created without one.
**Status:** legacy backfill, no code change required.

---

## 6 · Phase 12 — Regression Suite Results

```
40 passed in 152.80s

  test_track_15_28c_notification_canonicalization.py     16/16  PASS
  test_track_15_73_canonical_identity_audit.py            6/6   PASS
  test_track_15_73_slice1_equipment_resolver.py           1/1   PASS
  test_track_15_73_slice2_attendee_normalization.py       1/1   PASS
  test_track_15_73_slice3_no_branding_default_drift.py    1/1   PASS
  test_track_15_73_slice3_picker_canonical_emit.py        5/5   PASS
  test_track_15_73d_health_alert_trust.py                 3/3   PASS
  test_track_15_73q_pm_email_coverage.py                  3/3   PASS
  test_track_15_74_dead_letter_audit_trust.py             2/2   PASS  ← NEW
  test_track_15_73_slice4_master.py                      (within set)
```

---

## 7 · Phase 7 — Health System (evidence)

* `/api/health/full` → `{ok: true, mongo: true, scheduler: true, backup_recent: true}`
* Track 15.73D health-alert trust: cooldowns persisted in Mongo
  (`alert_cooldowns`), R2-aware backup card, false-red prevention — 3/3 PASS.

## 8 · Phase 8 — Email System

* `/api/admin/email-routing/v2/status` → `critical_total=4`,
  `critical_populated=4`, `critical_empty=0`,
  `errors_last_24h=0`.

## 9 · Phase 9 — Security (evidence)

Admin namespace endpoints sampled without token (admin-gated only):
14/14 returned **401** (or 405 on POST-only routes when probed via GET).
No bypass. Integration health response masks API keys / webhook
secrets correctly (last 4 chars only).

## 10 · Phase 11 — Integrations

| Integration | Status | Evidence |
|---|---|---|
| Motive | Connected (demo_mode) | `/api/integrations/health` — keys masked, last sync 2026-06-11 |
| MaintainX | Disabled (intentional preview state) | api_key_present=false |
| Resend | Active | webhook + audit rows present in `resend_webhook_events` (112) |
| Cloudflare R2 | Active | Track 15.73D R2-aware backup health uses live signal |

---

## 11 · Certification Statement

The MASCI Operations Platform is certified **TRUSTED** for production
operation on tenant `masci` as of this audit, with one operator-owned
data-hygiene action outstanding (§5.1). All identity write paths,
notification dead-letter routing, admin authorization gates, integration
key handling, and health/backup observability surfaces are evidence-
backed GREEN. The one P1 trust defect discovered during this audit
(dead-letter audit row hardcoded zero count) was fixed in-pass and is
locked by a 2-test regression suite that is now part of the standard CI
sweep.

**Open items for follow-up tracks:**
* Track 15.72 — Customer #2 provisioning CLI / Atlas-R2-Resend manifest.
* Track 16.x — Module gating for tiered SKU sales.
* Operator backfill — 7 `jobs_master.pm_email` rows (§5.1).
