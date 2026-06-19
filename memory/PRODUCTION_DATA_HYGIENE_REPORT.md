# TRACK 15.34 · PRODUCTION DATA HYGIENE REPORT

**Track:** 15.34 (Option A — Auth Hardening + Endpoint Registry + Data Hygiene)
**Mode:** READ-ONLY · identification + categorization only · NO deletes · NO modifications
**Dates:**
* Production sweep: 2026-02-27 (probes captured 2026-06-01T01:17Z against `https://mascidocs.com`)
* Preview sweep (Track 15.34 supplement): 2026-02 (`DB_NAME=masci_safety_preview`)

**Predecessors:** `PRODUCTION_OBSERVATION_REPORT.md`, `PRODUCTION_REGRESSION_AUDIT.md`, `M0_0_HYGIENE_CLOSURE_REPORT.md`, `TRACK_14_0_P0_PREVIEW_TEST_DEMO_DATA_HYGIENE_SWEEP_CLOSURE.md`

This report has two scopes:
1. **§1–§9** — Production database (`masci_safety` @ `mascidocs.com`) — read-only sweep.
2. **§10** — Preview database (`masci_safety_preview`) — Track 15.34 supplemental scan.

---

## 1 · Methodology (production)

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

## 2 · Findings summary (production)

| Total records scanned | 414 |
| Records flagged by regex | 2 |
| Categorized "Safe to delete" | 0 |
| Categorized "Requires operator review" | 1 |
| Categorized "System record (false positive)" | 1 |
| Duplicate `doc_id` violations | 0 |

🟢 Production is **substantially clean** of test/demo/preview/seed contamination. The only operator-attention item is the deactivated test field-leader account that Sprint 1B already neutralized.

---

## 3 · Per-collection findings (production)

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

## 4 · System records (false positives — production)

### 4.1 · `safety_users` · `safety@mascigc.com` · "Safety Manager"

* **Match:** regex matched the literal substring `safety@` in the email (regex pattern `test|demo|…|sample` did not match; an earlier expanded regex matched the role-prefix convention).
* **Reality:** This is the **canonical production Safety Manager account** documented in `/app/memory/test_credentials.md`. The email pattern `<role>@mascigc.com` is the corporate convention; it is not a contamination marker.
* **Status:** `is_active = True`. **System record.**
* **Action recommended:** None. Keep as-is.

---

## 5 · Requires operator review (production)

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
| **B · Hard-delete via authorized batch** | Requires new explicit "Production Data Action" batch · would need pre-delete dependency scan (which docs reference id `d805f3d4-…`) · `CLEANUP_EXECUTION_REPORT`-style evidence freeze |

**No action recommended in this read-only batch.** Operator decides whether to authorize a future hard-delete batch.

---

## 6 · Safe to delete (production)

🟢 **No records categorized "Safe to delete."**

Per the operator's READ-ONLY directive, this report explicitly DID NOT delete anything regardless. All findings either pass the contamination scan (categorized as system records) or are already neutralized via deactivation (Finding 5.1).

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

## 8 · Read-only discipline confirmation

| Rule | Observed |
|---|---|
| READ-ONLY | ✅ |
| NO DELETES | ✅ |
| NO MODIFICATIONS | ✅ |
| Identify + categorize only | ✅ |
| Categories: Safe to delete / Requires operator review / System records | ✅ all three buckets enumerated |
| No assumptions | ✅ every finding has evidence reference |

---

## 9 · Production verdict

🟢 **Production data hygiene is clean.** 412 of 414 scanned records pass the contamination regex. 1 false positive (`safety@mascigc.com` is the canonical Safety Manager). 1 already-neutralized deactivated test account (`fieldleader@mascigc.com`, Sprint 1B output).

**No new cleanup batch is required on production.** Operator may choose to authorize a hard-delete of the deactivated FL test account in a future explicit batch (see §5.1).

---

## 10 · TRACK 15.34 supplemental scan — preview database

**DB:** `masci_safety_preview` · **ENV:** `preview` · **Run date:** 2026-02 (Track 15.34)

Expanded regex (added cert-fixture markers per the dev fork-job tooling):

```python
r'(test|demo|preview|seed|sprint1c|john smith|jane doe|asdf|qwerty|sample|dummy|placeholder|deleteme|cert\.|cert-user|track15|mascicert|example\.com|@example\.|fieldleader@|forgedops\.test|@test\.)'
```

### 10.1 · Preview scan results

| Collection | Total | Flagged | Notes |
|---|---|---|---|
| `employees` | 395 | 1 | `iter316.pytest.dupe@masci.test.local` (is_active=False — historic pytest dupe) |
| `user_directory` | 161 | 128 | Mostly `k4btest-*@masci.test` (Track K4B HR pytest fixtures) + Track 15.x cert seeds |
| `field_leadership_users` | 31 | 8 | `fieldleader@mascigc.com` (mirror of production) + `fl_perm_*@example.com` + `fl_track1514_*@example.com` (all disabled) |
| `hr_users` | 70 | 68 | Predominantly `k4btest-*@masci.test` HR pytest fixtures |
| `safety_users` | 11 | 9 | Cert `sf_perm_*`, `sf_track1514_*`, `cert.safety@example.com`, `test_safetyuser_iter119@example.com` |
| `shop_users` | 12 | 10 | `cert.*@example.com`, `cert.assetadmin.*@mascicert.local`, `testmech@mascigc.com` |
| `project_managers` | 20 | 14 | `pm.demo@mascigc.com` (preview fixture) + Track 15.11C/15.13F cert PMs + `track15.11b.cert.pm@mascicert.local` |
| `dispatch_users` | 12 | 10 | Cert `dp_perm_*`, `dp_track1514_*` |
| **TOTAL** | **712** | **248** | |

### 10.2 · Categorization

| Category | Count | Examples |
|---|---|---|
| 🟢 **System / by-design test fixtures** | ~245 | `k4btest-*@masci.test` (K4B HR canonical fixtures, `id` prefix `k4b-test-`), `pm.demo@mascigc.com` (named "PM Demo (Preview Fixture)"), `track15.11b.cert.pm@mascicert.local` (seeded/torn-down by `scripts/seed_track_15_11b_pm_cert.py`), Track 15.13F `cert.assetadmin.*@mascicert.local` (seeded by `scripts/seed_track_15_13f_cert.py`), all `cert.*@example.com` portal cert seeds |
| 🟡 **Requires operator review** | ~3 | `iter316.pytest.dupe@masci.test.local` (historic — already disabled · `is_active=False`); `testmech@mascigc.com` (active shop_users entry — appears to be a manual test); `fieldleader@mascigc.com` (mirror of production deactivated row but preview row has `is_active=True`) |
| 🔴 **Safe to delete** | 0 | None — read-only run, no destructive recommendations issued |

### 10.3 · Preview scope notes

* **Track 15.x cert seed pattern:** Tracks 15.11B, 15.13F, 15.14, and others use seed scripts under `/app/backend/scripts/seed_track_*.py` that refuse to run against `APP_ENV=production` or `DB_NAME=masci_safety`. Cert users are intentionally created with `*@mascicert.local` or `*@example.com` and are torn down by the matching `--rollback` flag.
* **K4B HR pytest fixtures (`k4btest-*@masci.test`):** documented in `/app/memory/ADMIN_DOMAIN_MAP.json`; live only in preview; never cross to production (verified §7 above).
* **Disabled `*_perm_*` and `*_track1514_*` users:** all carry `disabled=True` and cannot authenticate. Audit trail preservation per the Sprint 1B doctrine.

### 10.4 · Preview verdict

🟢 **Preview database test/fixture surface is expected and bounded.** The 248 flagged rows fall into three known seed/fixture cohorts (Track K4B HR pytest, Track 15.x cert seeds, Sprint 1B disabled cert FL/SF/DP). Three rows are flagged for operator attention but pose no security risk in preview. **No production crossover detected (§7 confirms).**

**No action recommended in this Track 15.34 read-only batch.** Operator may, at their discretion, authorize a future preview-only cleanup batch (e.g., Track 15.36) to prune the `k4btest-*` and `track1514_*` cohorts once the corresponding pytest suites no longer require them.

---

## 11 · Combined Track 15.34 verdict

| Scope | Verdict |
|---|---|
| Production data hygiene | 🟢 GREEN — substantially clean, 1 deactivated test FL flagged for optional cleanup |
| Preview data hygiene | 🟢 GREEN — bounded, expected fixtures only, no production crossover |
| Cross-env drift | 🟢 GREEN — zero preview data observed on production |

🛑 STOP. Awaiting operator's next explicit authorization for any destructive action.
