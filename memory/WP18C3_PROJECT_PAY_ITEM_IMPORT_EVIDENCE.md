# WP18C3 Project Pay-Item Import Evidence

Date: 2026-08-03

## Implemented import pipeline

The C3 import lane is implemented in `backend/services/project_budget_authority.py` and exposed through `/api/pm/project-controls/projects/{project_number}/budget/imports`.

### Supported source classes
- `schedule_of_values`
- `bid_tab`
- `pay_item_list`
- `engineer_bid_form`
- `csv`
- `excel` (`openpyxl` parser)
- `pdf_review` (`pdfplumber` table extraction with line-based fallback)

### Workflow enforced in code

`Import → advisory suggestions → PM review → PM approval → activation`

What the code prevents:
- no automatic activation;
- no silent approval;
- no silent normalization of ambiguous rows;
- no PDF extraction treated as authoritative without review.

## Runtime-certified import evidence

### Certification project
- Project: `ZZ-RUNTIME-CERT-2026`
- PM approver: `cert.pm@example.com`

### Import sessions created during certification

1. `budget-import:ZZ-RUNTIME-CERT-2026:63f83cc774eb`
   - file: `budget-cert-1.csv`
   - hash: `1e5badef952f026fa40d672fcccf5f1c686839ab222aa11682198c0229e0a3bc`
   - source kind: `csv`
   - target version stage: `current_approved_budget`
   - status: `activated`

2. `budget-import:ZZ-RUNTIME-CERT-2026:25c8c28f1309`
   - file: `budget-cert-2.csv`
   - hash: `c91f2f01fe7eba33060937dec054aa995beebecdfb02a3b112b84af6e38c037b`
   - source kind: `csv`
   - target version stage: `current_approved_budget`
   - status: `activated`

### Source preservation proof

Each import session stores:
- original filename
- file extension / content type
- SHA-256 hash
- parser name
- parser warnings
- preserved sample rows
- importer identity
- import timestamp

## Customer pay-item constitutional evidence

The certified source rows carried `Pay Item = C3-CERT-1785798640`. During governed PM review, the certification project reused its existing customer pay-item authority (`CERT-001`) while preserving the imported token as `project_cost_code = C3-CERT-1785798640` and keeping the raw source row in `source_preservation.sample_rows`.

This proves:
- customer truth stays distinct from MASCI work-type truth;
- imported source data is preserved;
- PM may approve reuse of existing customer pay items without rewriting source evidence.

## UI / operator evidence

PM page `/pm/project-controls/budget` includes:
- source-kind selector
- target-version selector
- file input
- version-name input
- staged-import list
- row-level review cards
- activation button disabled until review reaches an activation-ready state

`/app/test_reports/iteration_112.json` confirmed the full PM import workspace rendered correctly and accepted file uploads / review controls.
