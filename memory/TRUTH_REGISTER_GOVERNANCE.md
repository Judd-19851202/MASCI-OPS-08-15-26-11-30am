# TRUTH REGISTER · GOVERNANCE

**Authority**: FOCP MASTER PROGRAM · Phase 1
**Status**: Active

---

## Why this document exists

The Sprint 1 + Sprint 2 closeouts proved that any process which lets unverified findings drive engineering wastes engineer-cycles against phantom defects. This governance document codifies the rules that prevent that failure mode from recurring.

---

## Rule 1 · Single source of truth

`TRUTH_REGISTER.md` is the **only** valid finding container. Sprint planning, OKR commitments, and engineering work may only reference findings by `TR-####` ID. No `ITER500_*`, `ITER501_*`, `OMEGA_*`, or arbitrary `*_REGISTER.md` finding may be referenced as the basis for code work.

## Rule 2 · No finding without verification

A finding may not be added to the Truth Register unless it carries at minimum:

* `verified_source_date` — a date the finding was checked against `/app/` JSX or Python
* `evidence` — a file path + line numbers, screenshot reference, or operator quote

Findings missing either field shall not be sprint-eligible. They may sit in DEFERRED status, awaiting verification.

## Rule 3 · No sprint without all four verification dates

A finding may only enter a sprint when its status is ACTIVE AND it carries at least:

* `verified_source_date` (mandatory)
* `verified_ui_date` OR `verified_preview_date` (at least one of)

If the finding has business-critical impact (severity CRITICAL or HIGH) AND will be deployed to production, then prior to merge a `verified_production_date` is also required (operator-led).

## Rule 4 · Migration discipline

A finding inherited from a legacy register (ITER500, ITER501, etc.) is **not** automatically valid. To migrate:

1. Re-read the original finding text.
2. Check current `/app/` source against the finding (grep, view_file).
3. Decide: ACTIVE / RETIRED / SUPERSEDED / DEFERRED / REJECTED.
4. Record the verification with file paths + line numbers OR screenshot reference.
5. Assign a `TR-####` ID.
6. Write the row to `TRUTH_REGISTER.md`.

If step 2 cannot complete (e.g., requires operator input), the finding is DEFERRED with a precise statement of what the operator must provide to unblock verification.

## Rule 5 · Retirement discipline

A finding may only move to RETIRED when its evidence shows the gap no longer exists. The retiring entry must cite the resolving file + line numbers or commit / PR ID.

## Rule 6 · Supersession discipline

A finding may only move to SUPERSEDED when another `TR-####` ID has been created that subsumes or replaces it. The `superseded_by` field must point to the replacement.

## Rule 7 · Rejection discipline

A finding may only move to REJECTED when verification proves it was never a real defect OR when it explicitly conflicts with codified platform doctrine. The rejection entry must cite the doctrine document.

## Rule 8 · No silent edits

Status changes must be reflected by appending an entry to `TRUTH_REGISTER_CHANGELOG.md` (or, if absent, by inline date-stamped notation in the row). Status flips without dated audit-trail are non-compliant.

## Rule 9 · Operator-only fields

`verified_production_date` may only be filled by the operator (or a delegate with production credentials). AI agents must never set this field. If an AI agent needs production verification, it shall flag the finding DEFERRED until the operator records the date.

## Rule 10 · Audit cadence

Every 90 days a full Truth Register sweep is performed: ACTIVE findings re-verified against current source; RETIRED findings spot-checked; DEFERRED findings reviewed for operator action.

---

## Enforcement

* Sprint plans, retros, and finish summaries that reference findings without a `TR-####` ID are non-compliant. Reject the sprint plan, not the finding.
* Code commits closing a finding shall include the `TR-####` ID in the commit message footer (`Closes TR-####`).
* The Truth Register is the read-side for every status review, executive briefing, and customer-facing audit response.

---

End of governance.
