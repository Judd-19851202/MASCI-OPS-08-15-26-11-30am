# PROJECT-IDENTITY-005 · Identity Health Report

**Scan date:** 2026-06-09 13:53–13:56 UTC  
**Environment:** preview (`masci_safety_preview`)  
**Detector version:** PROJECT-IDENTITY-005 initial release

---

## Identity Health Score

```
canonical_projects:           28
governance_queue (open):    1242
unmatched_records:          2105
normalized_matches:            0
intentional_variants:          1
projects_requiring_review:   405
last_governance_action:    2026-06-09T13:56:24 (Mark Intentional · #25-15 fixture)

identity_health_score:        0 / 100
```

> **Why 0?** The score formula penalises open Type A / B / D conflicts. Preview DB is heavily polluted with cert/test fixtures (see PROJECT-IDENTITY-001 §5 — 1,222 cert records across 19 collections). Almost every cert PN that doesn't exist in jobs_master generates a Type D item. On production data (5 cert records total per the audit), the score will be drastically higher.

> The score is intentionally **information-only** — it does not block any operational flow.

---

## Conflict Distribution by Type

| Type | Description                                                                                      | Unique items |
|------|--------------------------------------------------------------------------------------------------|-------------:|
| A    | PN matches a canonical row · name differs                                                        |            1 |
| B    | Name matches a canonical row · PN differs                                                        |            0 |
| C    | PN does not exact-match · normalizes uniquely to a canonical PN                                  |            0 |
| D    | PN populated · not found in jobs_master                                                          |        ≈ 990 |
| E    | Blank PN · non-blank name                                                                        |     present  |
| F    | Has PN · blank name                                                                              |     present  |

## Source Modules Touched (preview)

The detector ran against all 24 collections enumerated in `project_identity_governance.py:SCAN_COLLECTIONS`:

```
daily_reports · job_photos · incidents · inspections · meetings ·
equipment_inspections · qaqc_inspections · safety_equipment_issuances ·
safety_equipment_trainings · trench_excavations · trench_safety_deployments ·
po_requests · operations_actions · asset_assignments · corrective_actions ·
field_leadership_records · haul_cycles · jhas · jha_acknowledgements ·
fire_extinguishers · job_hazard_files · operational_events ·
operational_locations · field_submitter_bindings · dispatch_assignments
```

---

## Notable Items Currently in Queue

### Type A · most-impactful single signature

```
key:                          A|25-15|test_qaqc e53f1 sr 404
submitted_project_number:     25-15
submitted_project_name:       TEST_QAQC E53F1 SR 404
suggested_canonical_number:   25-15
suggested_canonical_name:     E53F1 - SR 404, Brevard Co (Pineda)
source_modules:               ["Job Photos"]
record_count:                 18
status:                       intentional   ← resolved during sprint smoke test
```

### Top Type D generators (legacy test fixtures)

These are cert/test PNs that the cert filter in `JobFolderList` already hides from operational hubs. The Governance Center still surfaces them so an admin can bulk-dismiss them or migrate them to a dedicated sandbox project number.

```
TEST-4525        (85 daily_reports)
TEST-452         (60 daily_reports / 99 bindings)
JOB-MM-E5        (66 job_photos)
JOB-FIX1-PYTEST  (66 job_photos)
PROJ-TOP         (40 haul_cycles / 40 dispatch)
0000-TEST        (16 daily_reports)
```

---

## Production Forecast (`masci_safety`)

Based on the PROJECT-IDENTITY-001 audit data, prod will surface:

| Type | Forecast               | Detail                                                                                       |
|------|------------------------|----------------------------------------------------------------------------------------------|
| A    | 4 high-impact items    | The user-cited duplicates (`26-01 - CP`, `24-12`, `25-21`, `26-07`). 740 records total.      |
| B    | likely 0               | Canonical names are highly distinctive.                                                      |
| C    | small                  | A handful of legacy `26-01` (without ` - CP` suffix) entries in po_requests.                 |
| D    | ≈ 5                    | Cert artefacts already filtered from operational UIs by `JobFolderList.isCertOrTest`.         |
| E    | small                  | Blank-PN orphans from public-form submissions.                                               |
| F    | small                  | Pre-PN-master legacy rows.                                                                   |

Operator workflow when prod scan runs:

1. Open `/admin/project-identity`.
2. Filter by `Type A` → 4 items.
3. For each: review submitted vs canonical → click `Mark Intentional` (if the submitter free-text variant is desired in historical context) **or** `Dismiss` (if it's noise).
4. Bulk-dismiss the cert/test Type D items.

No data writes. No record mutations. Just a queue of human decisions.

---

## Future Drift Prevention

The **deployment blocker** at `backend/tests/test_project_identity_compliance.py` ensures:

1. No future PR can reintroduce `${number}::${name}` grouping.
2. No future `<JobFolderList>` callsite can ship without `jobsMaster`.
3. No future consumer can ship without `/jobs-master` fetch.
4. No future contributor can remove the resolver doctrine safeguard.
5. No future contributor can add an unauthorized resolution state.

CI runs this on every commit. Failure = deployment blocked.

---

## Health Score Trend (to be tracked across deploys)

| Date          | Score | Open Type A | Open Type D | Notes                                |
|---------------|------:|------------:|------------:|--------------------------------------|
| 2026-06-09    |     0 |           0 |       ≈ 990 | initial detection in preview         |

Future scans should be appended to this table by the running admin so the platform can show a trend over time.
