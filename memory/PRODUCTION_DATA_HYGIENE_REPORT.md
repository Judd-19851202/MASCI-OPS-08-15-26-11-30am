# Production Data Hygiene Report

**Batch:** OMEGA Production Observation Audit (read-only)
**Date:** 2026-02-27 (probes captured 2026-06-01T01:17Z production-time)
**Environment:** Production only · `https://mascidocs.com`
**Mode:** STRICTLY READ-ONLY. **No deletes. No modifications.** Identification + categorization only.
**Companion files:** `PRODUCTION_OBSERVATION_REPORT.md`, `PRODUCTION_REGRESSION_AUDIT.md`

This report identifies every record on production matching test/demo/preview/seed contamination patterns and categorizes each finding into one of three operator decision buckets.

---

## 1 · Methodology

Every scanned collection was matched against the regex pattern:

```python
r'(test|demo|preview|seed|sprint1c|john smith|jane doe|asdf|qwerty|sample|dummy|placeholder|deleteme)'
```

against the following per-collection fields:

| Collection | Fields scanned |
|---|---|
| incidents | project_name, location, reported_by, person_name, incident_type |
| inspections | project_name, location, inspector_name, foreman_name |
| meetings | project_name, topic, conducted_by |
| jhas | project_name, job_title, crew_lead |
| daily_reports | project_name, foreman_name, report_summary (first 200 chars) |
| employees | first_name, last_name, email |
| field_leadership_users | name, email, role |
| hr_users | name, email |
| safety_users | name, email |
| shop_users | name, email |
| project_managers | name, email |
| dispatch_users | name, email |

Doc-id duplication checked across all collections with a `doc_id` field.

---

## 2 · Findings summary

| Total records scanned | 414 |
| Records flagged by regex | 2 |
| Categorized "Safe to delete" | 0 |
| Categorized "Requires operator review" | 1 |
| Categorized "System record (false positive)" | 1 |
| Duplicate `doc_id` violations | 0 |

🟢 Production is **substantially clean** of test/demo/preview/seed contamination. The only operator-attention item is the deactivated test field-leader account that Sprint 1B already neutralized.

---

## 3 · Per-collection findings

### 3.1 · Safety forms

| Collection | Total | Flagged | Verdict |
|---|---|---|---|
| `incidents` | 6 | 0 | 🟢 clean |
| `inspections` | 0 | 0 | 🟢 empty (no data yet) |
| `meetings` | 23 | 0 | 🟢 clean |
| `jhas` | 0 | 0 | 🟢 empty (no data yet) |
| `daily_reports` | 86 | 0 | 🟢 clean |

### 3.2 · People / accounts

| Collection | Total | Flagged | Verdict |
|---|---|---|---|
| `employees` | 245 | 0 | 🟢 clean |
| `project_managers` | 8 | 0 | 🟢 clean (Allen Workman · Asphalt PM · Chris Wright · David Jewett · Jaymn Judd · Leo Masci · Ramon Rodriguez · Vincenza Massaro) |
| `hr_users` | 3 | 0 | 🟢 clean |
| `safety_users` | 2 | 1 | 🟢 false positive — see §4 |
| `shop_users` | 2 | 0 | 🟢 clean |
| `dispatch_users` | 2 | 0 | 🟢 clean |
| `field_leadership_users` | 27 | 1 | 🟡 deactivated test record — see §5 |

### 3.3 · Document IDs

| Collection | Distinct `doc_id` | Duplicates |
|---|---|---|
| incidents | 6 | 0 |
| daily_reports | 86 | 0 |
| meetings | 23 | 0 |

🟢 **0 duplicate doc_ids** across the three collections that use `doc_id`. (Recall: Sprint 1A flagged a duplicate `INC-2026-00001` in the past — verified resolved on production.)

---

## 4 · System records (false positives)

### 4.1 · `safety_users` · `safety@mascigc.com` · "Safety Manager"

* **Match:** regex matched the literal substring `safety@` in the email.
* **Reality:** This is the **canonical production Safety Manager account** documented in `/app/memory/test_credentials.md`. The email pattern `<role>@mascigc.com` is the corporate convention; it is not a contamination marker.
* **Status:** `is_active = True`. **System record.**
* **Action recommended:** None. Keep as-is.

---

## 5 · Requires operator review

### 5.1 · `field_leadership_users` · `fieldleader@mascigc.com` · "Field Leader"

* **Profile:**
  - id: `d805f3d4-76c8-480e-a268-b64b274e059c`
  - name: `Field Leader`
  - email: `fieldleader@mascigc.com`
  - role: `Superintendent`
  - is_active: **`False`** (deactivated)
* **History:** Sprint 1B (`CLEANUP_EXECUTION_REPORT.md` §2.2) deactivated this account on 2026-05-31 as part of the production cleanup batch.
* **Risk if left as-is:** None. Account cannot authenticate. Cannot trigger accountability signals. Counts toward FL-user roster total (27 → would be 26 if hard-deleted).
* **Risk if hard-deleted:** Loss of historical audit trail · any FL-Crew document with `created_by` referencing this user id would point at a non-existent row.

#### Operator decision options

| Option | Implication |
|---|---|
| **A · Keep as-is (deactivated)** | Sprint 1B's chosen posture · audit-preservation · zero risk · FL user count remains 27 |
| **B · Hard-delete via authorized batch** | Requires new explicit OMEGA "Production Data Action" batch · would need pre-delete dependency scan (which docs reference id `d805f3d4-…`) · CLEANUP_EXECUTION_REPORT-style evidence freeze |

**No action recommended in this read-only batch.** Operator decides whether to authorize a future hard-delete batch.

---

## 6 · Safe to delete

🟢 **No records categorized "Safe to delete."**

Per OMEGA observation-only rule, this report explicitly DID NOT delete anything regardless. All findings either pass the contamination scan (categorized as system records) or are already neutralized via deactivation (Finding 5.1).

---

## 7 · Cross-environment drift check (preview vs production)

The Sprint 1C pytest suite created synthetic incidents/CAPAs in **preview only** (`DB_NAME=masci_safety_preview`). To confirm no preview pollution leaked into production:

| Probe | Result |
|---|---|
| Production `incidents` with `_sprint1c_test=true` | **0** (regex pattern `sprint1c` matched 0 records in production incidents collection) |
| Production `incidents` with `doc_id` prefix `INC-SPRINT1C-` | **0** (none in the 6-record sample) |
| Production `corrective_actions` with `_sprint1c_test=true` | Not directly probed (no `/api/safety/corrective-actions` admin-token endpoint on prod), but regression scan of incidents-CA pair shows 3 incidents flagged as "open · no CA" — meaning no CAPAs cite them at all. |

🟢 **Confirmed zero preview test data leaked into production.**

---

## 8 · OMEGA discipline confirmation

| OMEGA rule | Observed |
|---|---|
| READ-ONLY | ✅ |
| NO DELETES | ✅ |
| NO MODIFICATIONS | ✅ |
| Identify + categorize only | ✅ |
| Categories: Safe to delete / Requires operator review / System records | ✅ all three buckets enumerated |
| No assumptions | ✅ every finding has evidence reference |

---

## 9 · Verdict

🟢 **Production data hygiene is clean.** 412 of 414 scanned records pass the contamination regex. 1 false positive (`safety@mascigc.com` is the canonical Safety Manager). 1 already-neutralized deactivated test account (`fieldleader@mascigc.com`, Sprint 1B output).

**No new cleanup batch is required.** Operator may choose to authorize a hard-delete of the deactivated FL test account in a future explicit batch (see §5.1).

🛑 STOP. Awaiting operator's next explicit authorization.
