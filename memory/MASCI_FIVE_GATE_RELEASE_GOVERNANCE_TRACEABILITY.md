# MASCI Five-Gate Release Governance Traceability

## 1. Authority and scope

This report is the sole standalone traceability artifact created for the
Five-Gate Release Governance amendment.

It maps the permanent five-gate law into the existing canonical MASCI
governing artifacts without duplicating those artifacts.

## 2. Five-gate definition

The mandatory release-governance gates are:

1. `CONTRACT_LOCKED`
2. `LOCAL_ENGINEERING_VERIFIED`
3. `INDEPENDENT_ADVERSARIAL_CERTIFIED`
4. `IMMUTABLE_RELEASE_CANDIDATE_VERIFIED`
5. `DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED`

`DONE` is reserved for the state in which all five gates are VERIFIED.

## 3. Cross-artifact traceability matrix

| Requirement ID | Gate / Rule | MASCI_DEFINITION_OF_DONE.md | MASCI_OPERATIONAL_EXECUTION_CONSTITUTION.md | MASCI_OPERATIONAL_EXECUTION_REGISTER.md | MASCI_OPERATIONAL_EXECUTION_CERTIFICATION_PLAN.md | MASCI_OPERATIONAL_EXECUTION_CONSTITUTIONAL_APPENDIX.md | MASCI_OPERATIONAL_EXECUTION_REQUIREMENT_TRACEABILITY_MATRIX.md |
|---|---|---|---|---|---|---|---|
| FG-001 | `CONTRACT_LOCKED` is mandatory Gate 1 | §4 | §23.4 | T1, T13, §20 | §2A, §34 | §10.3 | FG-001 row |
| FG-002 | `LOCAL_ENGINEERING_VERIFIED` is mandatory Gate 2 | §4 | §23.4 | T13, §20 | §2A, §34 | §10.3 | FG-002 row |
| FG-003 | `INDEPENDENT_ADVERSARIAL_CERTIFIED` is mandatory Gate 3 | §4 | §23.4–§23.5 | T13, §20 | §2A, §34 | §10.3 | FG-003 row |
| FG-004 | `IMMUTABLE_RELEASE_CANDIDATE_VERIFIED` is mandatory Gate 4 | §4 | §23.4, §23.6 | T13, §20 | §2A, §34 | §10.3 | FG-004 row |
| FG-005 | `DEPLOYED_OPERATIONAL_ACCEPTANCE_VERIFIED` is mandatory Gate 5 | §4 | §23.4, §23.7 | T13, §20 | §2A, §34 | §10.3 | FG-005 row |
| FG-006 | `DONE` requires all five gates VERIFIED | §4–§5 | §23.4 | §20 | §2A, §32, §34 | §10.3 | FG-006 row |
| FG-007 | Gate order is sequential and non-substitutable | §4 | §23.4 | §20 | §34 | §10.3 | FG-007 row |
| FG-008 | Builder may not self-declare Gate 3 / Gate 5 / `DONE` | §4 | §23.5 | T13 | §2A | §10.3 | FG-008 row |
| FG-009 | Skipped required tests need `skip_classification`, reason, owner | §4–§5 (through gated completion vocabulary) | §23 release governance | T1 evidence / T13 evidence | §2B, §33 | §10.3 | FG-009 row |
| FG-010 | Permitted `skip_classification` values are `BLOCKING` / `NON_BLOCKING` | §5 | §23 release governance | T1 / T13 | §2B | §10.3 | FG-010 row |

## 4. Conflict resolution summary

- The prior legacy completion shorthand was removed as a governing
  completion status and replaced with the reserved constitutional `DONE`
  state.
- Local verification language was re-scoped so local proof maps to
  `LOCAL_ENGINEERING_VERIFIED`, not to `DONE`.
- Release-readiness language was narrowed so handoff readiness does not
  silently imply deployed operational acceptance.
- Skipped-test evidence now requires explicit classification rather than
  loose narrative mention.

## 5. Deterministic enforcement coverage

The backend regression suite enforces the following deterministic checks:

- all five gate tokens exist in the governing artifacts
- `DONE` is explicitly defined as all five gates VERIFIED
- builder self-declaration prohibition exists in governing text
- skipped required test evidence must include `skip_classification`
- only `BLOCKING` and `NON_BLOCKING` are permitted skipped-test
  classifications
- banned casual approval shorthand is rejected in the amended governing
  artifacts under test

## 6. Intended interpretation rule

This traceability report explains where the Five-Gate law lives.

It does not replace the amended canonical governing artifacts.