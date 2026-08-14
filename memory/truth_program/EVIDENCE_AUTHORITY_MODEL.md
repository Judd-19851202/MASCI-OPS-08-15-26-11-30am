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

## HARD ACCESS BOUNDARY (proven this run)
The preview runtime's Mongo credentials are scoped ONLY to `masci_safety_preview` and are
`not authorized on masci_safety` (production). This is the correct isolation — preview cannot
read production business data. Therefore the live master-data census (Class B) CANNOT be produced
from the preview environment. It requires either production-scoped read credentials or the
post-Deploy live-verification phase running in the production runtime. No fabrication permitted.

## RECLASSIFICATION OF PRIOR EVIDENCE
- Independent Acceptance (INDEPENDENT_ACCEPTANCE.json): reconstructions from the preview DB
  (employees 454/is_active 441/lifecycle 442; carriers 336; eligibility 267/336=79.46%) are
  RECLASSIFIED as CLASS-A behavior/contract evidence ONLY — NOT MASCI current business totals.
- Equipment preview counts 766 (equipment-master) and 951 (status board) are NON-AUTHORITATIVE
  PREVIEW DATA. Their live reconciliation (SAME_LIVE_POPULATION vs GOVERNED_DISTINCT_LIVE_POPULATIONS)
  must be done against production read-only truth during live verification, not from preview fixtures.
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
