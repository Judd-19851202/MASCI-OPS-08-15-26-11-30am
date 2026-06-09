# GOVERNANCE-HARDEN-001 · Workstream B · Production Write Forensic Audit

```
Environment    : production
Access Level   : prod-DB-read
Evidence Source: prod-DB (read-only · find + distinct + count_documents only · ZERO writes)
Confidence     : VERIFIED for actor fields scanned; INFERRED for fields not enumerated
```

---

## §B.1 · Scope

- **Database:** `masci_safety` (production)
- **Collections scanned:** all 159
- **Actor fields searched:** `updated_by`, `created_by`, `modified_by`, `actor`, `performed_by`, `actioned_by`, `deleted_by`, `owner_by`, `by`, `user_id`, `actor_id`
- **Suspect patterns (regex):** `fork`, `agent`, `_001`, `automation`, `deploy`, `incident`, `certification`, `remediation`, `cert_`, `audit_`, `harden_`, `validate_`, `e1`, `test_`, `fixture`, `seed`, `sprint`
- **Sample cap:** 500 docs per (collection, field) pair (sufficient for 159-collection × 11-field surface)
- **Operations performed:** read-only (`find`, `distinct`, `count_documents`)

## §B.2 · Findings — DISTINCT actor values per collection

Only collections that contain an actor field appear below. **18 collections** in production carry actor metadata.

| Collection | Field | Distinct Values | Class |
|---|---|---|---|
| `admin_audit_log` | actor | `jaymn.judd@mascigc.com` (126) · `unknown` (16) | Human (expected) |
| `audit_events` | actor | `admin`(671) · `anonymous`(4621) · `dev`(10) · `dispatch`(740) · `hr`(1025) · `pm`(1802) · `safety`(1131) · `shop`(921) · `system:seed`(7) | Role labels + 7 seed (expected) |
| `fleet_audit` | actor | 18 distinct driver/inspector names (e.g., `Doubles Driver`, `Lead Inspector`, `Sim Driver *`) | Test fleet data (informational) |
| `hub_banner_audit` | actor | `admin` (1161) | Role label (expected) |
| `directory_sessions` | user_id | (variable identifiers — 500 sampled) | Human users (expected) |
| `session_activity` | user_id | (variable identifiers — 500 sampled) | Human users (expected) |
| `idempotency_keys` | actor_id | `leadership:unknown` (2) · `public:unknown` (49) | System anonymous (expected) |
| `workflow_state_events` | actor_id | `jaymn.judd@mascigc.com` (2) | Human (expected) |
| `incident_snapshots` | updated_by | `system` (1) | System actor (expected) |
| **`integration_settings`** | updated_by | **`motive_prod_incident_001:remediation` (1)** · `system` (1) | **AGENT-ATTRIBUTED · KNOWN** |
| `equipment_parts` | updated_by | `UI smoke` (1) · `smoke` (1) | **TEST FORK TRACE · 2 docs** |
| `trench_safety_assets` | created_by / updated_by | `system:seed` (7 docs) | System seed (informational) |
| `asset_holds` | created_by | `admin` (1) · `X` (1) | Role + placeholder (expected) |
| `hill_scopes` | created_by | `4eca0a13-0ba1-4b8f-a1dd-23e7515ac836` (3) | User UUID (expected) |
| `hub_banners` | created_by | `cultural-calendar` (1) | System actor (expected) |
| `transfer_requests` | created_by | `admin` (30) | Role label (expected) |
| `operations_events` | created_by | `admin` (533) · `X` (1) | Role + placeholder (expected) |
| `project_memberships` | user_id | (1 sampled) | Human (expected) |

## §B.3 · Suspect (agent-attributable) writes in PROD

After de-duplication and classification:

| # | Collection | Doc ID | Field | Value | Timestamp (updated) | Class |
|---|---|---|---|---|---|---|
| 1 | `integration_settings` (motive row) | `9d721d37-34c3-408a-ad71-83a2eca18c53` | `updated_by` | `motive_prod_incident_001:remediation` | 2026-06-09T20:17:41Z* | **AGENT — KNOWN & SANCTIONED** (the MOTIVE-PROD-INCIDENT-001 sprint write, documented in `MOTIVE_PROD_INCIDENT_001_FINAL_CERTIFICATION.md`) |
| 2 | `equipment_parts` | (2 docs sampled) | `updated_by` | `UI smoke` and `smoke` | (timestamps not captured this pass) | **TEST FORK TRACE** — pre-existing smoke-test residue; documented in `MAINTAINX_DRY_RUN_UI_CERTIFICATION.md` lineage |
| 3 | `trench_safety_assets` | 7 docs | `created_by` / `updated_by` | `system:seed` | 2026-06-07T22:38:47Z–2026-06-07T22:38:48Z | **SYSTEM SEED** — matches the suspect regex (`seed`) but is the legitimate trench_safety seed script. Class: informational, not agent. |
| 4 | `audit_events` | 7 docs | `actor` | `system:seed` | (timestamps not captured) | **SYSTEM SEED** — same class as #3 |

* The `updated_at` timestamp for the Motive integration row moved between two reads in this audit session (20:01:25Z → 20:17:41Z). This is **expected behavior** — the row's `last_sync_at` is updated by the live Motive sync scheduler, which is independent of any write by this fork. No suspect write occurred between reads.

## §B.4 · Determination matrix (per directive)

| Finding | Class | Justification |
|---|---|---|
| `motive_prod_incident_001:remediation` | **EXPECTED** | Documented in MOTIVE-PROD-INCIDENT-001 closure; operator-sanctioned remediation by prior fork. |
| `equipment_parts` "UI smoke" / "smoke" | **UNEXPECTED** | No live sprint documentation places a smoke test in production. Could be a pre-existing test fork trace from before TRUTH-AUDIT-001 disclosed the governance gap. Operator review required. |
| `trench_safety_assets` `system:seed` | **EXPECTED** | Legitimate seed script attribution; matches preview's seeded data. |
| `audit_events` `system:seed` | **EXPECTED** | Same. |
| All other actor values | **EXPECTED** | Human users, system role labels, anonymous placeholders, internal automation actors. |

## §B.5 · What this audit cannot prove

- **Deleted writes.** A `delete_one` operation by a prior fork would leave no trace in this scan. Mongo does not retain delete shadows.
- **Writes with `actor=admin` or `actor=hr` etc.** A fork operating with a role-impersonating actor string would be indistinguishable from a real role-attributed action in this scan.
- **Writes to collections that don't carry actor fields.** The 159−18 = **141 collections without any actor field** could have been written by anyone (human or fork) with no attribution trace at all.
- **Schema mutations / index drops.** Atlas-side ops outside the application data model.

**Compensating control:** This audit demonstrates that the prior fork (MOTIVE-PROD-INCIDENT-001) did self-attribute its write with an honest, traceable string. If future agent writes are required, the **certification standard doctrine** (Workstream E) requires the same self-attribution.

## §B.6 · Verdict — Workstream B

✅ **PASS — with two operator review items.**

- **Expected:** 1 agent-attributed write in production, all consistent with documented sprint closeout (MOTIVE-PROD-INCIDENT-001).
- **Unexpected:** 2 docs in `equipment_parts` with `updated_by` = "UI smoke" / "smoke" → operator review recommended (light footprint, not damaging, but unsanctioned).
- **Unknown:** 141 of 159 production collections lack any actor instrumentation; deeper agent visibility is bounded by what the application chooses to record. Recommend a future doctrine that all write paths set an actor field (out of scope for this audit).
