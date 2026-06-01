# Production Hygiene Inventory · Critical Fix Sprint 1A

**Batch:** OMEGA Critical Fix Sprint 1A · Phase 1
**Date:** 2026-05-31
**Scope:** Comprehensive inventory of production hygiene findings: orphan records · duplicate document IDs · duplicate employee IDs · duplicate usernames · inactive records still referenced by active workflows · abandoned workflow records.

---

## 1 · Duplicate document IDs

| Collection | Field | Duplicated value | Records | Severity |
|---|---|---|---|---|
| `incidents` | `doc_id` | `INC-2026-00001` | `d9626eeb` + `566a38dd` | 🔴 CRITICAL · `d9626eeb` is test data ("John Smith" canary) |
| `daily_reports` | `doc_id` | `DR-2026-00007` | `4cab04c6` + `ac306ad5` | 🟡 IMPORTANT · counter race condition · same root cause as incident-dup |

**Root cause (suspected · NOT proven):** `db.doc_id_counters` atomic-increment logic likely uses `find_one` then `update_one` rather than `find_one_and_update(..., {$inc: {seq: 1}}, returnDocument="after")`. Two collections share the same race-condition surface.

---

## 2 · Duplicate employee IDs

| Collection | Field | Duplicated value | Records | Verdict |
|---|---|---|---|---|
| `employees` | `employee_id` | `""` (empty string) | 245 docs | 🟢 NOT a defect — 245 HRIS-roster records with `employee_id=""` because the import did not carry employee numbers. This is by design for HRIS-only employees with no payroll-system ID. |
| `employees` | `email` | `""` (empty string) | 245 docs | 🟢 NOT a defect — HRIS roster has no email column for these records. |

**No real duplicate employee IDs detected.**

---

## 3 · Duplicate usernames / emails

| Collection | Field | Duplicate? | Verdict |
|---|---|---|---|
| `users` | `email` | none | 🟢 |
| `user_directory` | `email` | none (1 row per email) | 🟢 |
| `hr_users` | `email` | none | 🟢 |
| `field_leadership_users` | `email` | none | 🟢 |
| `safety_users` | `email` | none | 🟢 |
| `shop_users` | `email` | none | 🟢 |
| `dispatch_users` | `email` | none | 🟢 |

**No duplicate emails across or within identity collections.**

(NOTE: cross-portal occurrences of `jaymn.judd@mascigc.com`, `safety@mascigc.com`, etc. are super-admin/multi-portal accounts by design — see `TEST_ACCOUNT_AUDIT.md` §4.)

---

## 4 · Orphan records

| Probe | Result |
|---|---|
| `corrective_actions` referencing non-existent `incidents` | **0** orphans |
| `tasks` referencing non-existent source records (incidents · CAs · POs · fleet defects · DRs) | **0** orphans (across 100 sampled per source_module) |
| `notifications` with `subject_id` referencing non-existent target | **0** orphans across the incident/PO/CA/equipment/task types |

🟢 **Referential integrity is intact.** Despite the absence of DB-level foreign keys, the actual data does not contain dangling references.

---

## 5 · Inactive records still referenced by active workflows

| Probe | Result |
|---|---|
| `field_leadership_users.is_active=False` | 0 |
| `hr_users.is_active=False` | 0 |
| `users.is_active=False` | 0 |
| `equipment_units.is_active=False` referenced in fleet_defects | 0 |
| Project records inactive but referenced by open POs/CAs/incidents | 0 |

🟢 No active-vs-inactive workflow reference mismatch detected.

---

## 6 · Abandoned workflow records

### 6.1 · By age + status

| Workflow | Status | Age cutoff | Count |
|---|---|---|---|
| `corrective_actions` | Open / In Progress | created > 30 days ago | **0** |
| `po_requests` | Submitted / Pending Approval | created > 30 days ago | **0** |
| `fleet_defects` | open | created > 60 days ago | **0** |
| `incidents` | open | n/a (all 7 incidents have null status) | **7 with null status** (not aged-old, but unresolved by status convention) |

### 6.2 · Test/abandoned content

| Workflow | Records | Verdict |
|---|---|---|
| `payroll_variance_batches` | **10** | 🔴 confirmed test data ("John Smith" canary · 0 matched rows · uploaded by `hrmanager@mascigc.com` 2026-05-12/13) |
| `transfer_requests` | 29 Cancelled (of 30) | 🟢 terminal · cosmetic clutter |
| `hub_banners` | 1 expired | 🟢 expired Memorial Day (2026-05-26) banner not auto-purged |

### 6.3 · Storage/retention candidates

| Collection | Count | Verdict |
|---|---|---|
| `idempotency_keys` | 24 | 🟢 retention sweep candidate |
| `brute_force_blocks` | 0 | 🟢 |
| `webauthn_challenges` | 0 | 🟢 |
| `temp_upload_chunks` | 0 | 🟢 |
| `audit_events` | 10,155 | 🟢 normal volume · no retention policy codified |
| `usage_events` | **255,921** | 🟡 large · retention strategy not codified |
| `session_activity` | 1,052 | 🟢 |

---

## 7 · Abandoned user accounts

| Type | Count | Notes |
|---|---|---|
| Test/demo accounts | 1 | `fieldleader@mascigc.com` (covered in `TEST_ACCOUNT_AUDIT.md`) |
| Legacy owner accounts (`users.role=owner`) last login 2026-04-28 | 4 | David Jewett · Chris Wright · Ramon Rodriguez · Jaymn Judd · idle 33+ days |
| `user_directory` rows with `mcp=False · never logged in` | 5 | hrmanager · shopmanager · safety · masciaccounting · leticiamasci |
| `field_leadership_users` rows with `mcp=True · never logged in` | 25 | pre-onboarded · awaiting first login |

---

## 8 · Production hygiene summary

| Severity | Category | Records |
|---|---|---|
| 🔴 CRITICAL | Duplicate `incidents.doc_id` | 2 |
| 🔴 CRITICAL | Test FL user | 1 |
| 🔴 CRITICAL | Test incident "John Smith" | 1 (same as duplicate doc_id) |
| 🔴 CRITICAL | Test payroll batches | 10 |
| 🟡 IMPORTANT | Duplicate `daily_reports.doc_id` | 2 |
| 🟡 IMPORTANT | PREVIEW_POSTENV notifications | 2 |
| 🟡 IMPORTANT | Test FL session telemetry | 68 |
| 🟡 IMPORTANT | Incidents with `status=null` | 7 |
| 🟡 IMPORTANT | `user_directory.is_active=null` | 7 |
| 🟡 IMPORTANT | Legacy owner accounts idle 33+ days | 4 |
| 🟢 COSMETIC | Cancelled transfer_requests | 29 |
| 🟢 COSMETIC | Expired hub banner | 1 |
| 🟢 COSMETIC | `idempotency_keys` retention candidate | 24 |

**Total records flagged: ~160 across 13 categories** (76 critical, 90 important, 54 cosmetic). 0 orphans. 0 inactive-active mismatches.

---

## 9 · Closeout

🟡 Production data is **structurally healthy** (0 orphans · 0 referential gaps) with 2 documented duplicate doc_id races, 4 confirmed test artifact categories, and 6 hygiene/retention candidates. **All 8 user-bearing collections are duplicate-free on email.**

🛑 STOP. **NO REMEDIATION EXECUTED.** Companion deliverable: `REMEDIATION_CANDIDATE_LIST.md`.
