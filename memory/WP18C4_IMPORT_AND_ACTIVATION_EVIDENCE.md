# WP-18C4 Import And Activation Evidence

## Runtime-certified lane
- Certified lane: `CSV`
- Runtime certification project: `ZZ-RUNTIME-CERT-2026`

## Workflow verified
1. Stage import
2. Preserve source rows and parser warnings
3. Produce advisory mapping suggestions
4. PM reviews and edits row-level relationships
5. PM approves rows explicitly
6. PM activates governed schedule version
7. Exports and work-package/activity views reflect the active version

## Architected but not runtime-certified in C4
- Primavera P6
- Microsoft Project
- Excel
- PDF review-assisted

## Non-destructive handling
- Staged imports remain reviewable before activation
- Version activation creates additive versioned schedule activity rows
- Work packages are versioned by `project_number + version_id + work_package_id`
- Compatibility backfill is queued and non-blocking

## Separation preserved
- Budget truth remains in C3 budget authority
- Project/pay-item/work-type truth remains in C2 authority
- Daily Report actuals remain authoritative field execution facts