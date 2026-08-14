# MASCI OPS — EVIDENCE AUTHORITY MODEL (owner correction, 2026-06)

Two explicit, separate truth classes. Never conflate them again.

## CLASS A — LOGIC / BEHAVIOR TRUTH  (authority = PREVIEW)
Formulas, state machines, zero/N-A/UNKNOWN, stale/future timestamps, authorization negative
tests, pagination/truncation, scale, cache/fallback, failure injection, responsive rendering.
Synthetic preview records are VALID here. All GD-0013..GD-0032 guards + Independent-Acceptance
ADVERSARIAL boundary checks are Class-A and remain valid.

## CLASS B — CURRENT MASCI BUSINESS-DATA TRUTH  (authority = PRODUCTION, read-only)
Real current populations: employees, equipment/assets, fleet units, trucks, trailers, drivers,
suppliers/vendors, subcontractors, projects/jobs, users, live certifications.
A PREVIEW COUNT MUST NEVER CERTIFY A PRODUCTION POPULATION.

## HARD ACCESS BOUNDARY (DB layer only)
The preview runtime's Mongo credentials are scoped ONLY to `masci_safety_preview` and are
`not authorized on masci_safety` (production). This DB isolation is correct and MUST remain.

## CORRECTION (2026-06): LIVE CENSUS IS NOT BLOCKED — IT WAS COMPLETED VIA THE LIVE APP
The prior conclusion ("Class B census CANNOT be produced from preview") was too broad. Direct
preview→production Mongo is intentionally denied, but the LIVE production application at
`https://mascidocs.com` is reachable through its legitimate authenticated Super Admin browser/API
READ path. The Class-B census WAS produced that way — NOT from preview Mongo, NOT from direct
production Mongo. See `LIVE_APPLICATION_MASTER_DATA_CENSUS.md` for the full result.
Live snapshot (current, dynamic): Employees 297 (active roster 240) · Equipment Master 604
(== Status Board 604 → SAME_LIVE_POPULATION) · Suppliers/Vendors/Subcontractors 167 · Trucks 96 ·
Trailers 53 · Transport-capable fleet 136 · Eligible CDL drivers 40 · Jobs 35/34-active · Users 44.
Production writes 0. Source repairs required NO. These are SNAPSHOTS; the permanent contract is the
canonical-master + governed-filter derivation documented in the census artifact.

## RECLASSIFICATION OF PRIOR EVIDENCE
- Independent Acceptance (INDEPENDENT_ACCEPTANCE.json): reconstructions from the preview DB
  (employees 454/is_active 441/lifecycle 442; carriers 336; eligibility 267/336=79.46%) are
  RECLASSIFIED as CLASS-A behavior/contract evidence ONLY — NOT MASCI current business totals.
- Equipment preview counts 766 (equipment-master) and 951 (status board) are NON-AUTHORITATIVE
  PREVIEW DATA. RESOLVED via live production (2026-06): production Equipment Master = Equipment
  Status Board = 604 → `SAME_LIVE_POPULATION`. The preview 766/951 gap was synthetic-row exclusion
  (list excludes synthetic; status board did not) — zero effect in production. See census artifact.
- Formula/scale/boundary testing that used preview remains VALID (Class A). This is an authority
  correction, NOT a reopening of closed logic.

## PREVIEW FIXTURE GOVERNANCE
All `masci_safety_preview` records are governed as PREVIEW_TEST_DATA — NON-AUTHORITATIVE FOR
BUSINESS POPULATION. They must never be cited as MASCI real counts in acceptance. Not deleted
(useful for behavior/scale testing).

## SOURCE IMPACT
No source defect implicated by this correction — the application computes over whatever DB it is
connected to; the error was in EVIDENCE INTERPRETATION (treating preview counts as production
truth). No tracked deployable source change required; fingerprint unchanged.
