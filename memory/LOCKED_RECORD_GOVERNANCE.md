# Locked Record Governance

_Phase V.4 · 2026-05-29 · governance · NOT implementation._

## 1 · The LOCKED_RECORD contract

Once a Daily Report reaches `APPROVED` status, it transitions (immediately or after an operator-configured grace period of 0–24 h) to `LOCKED_RECORD`. The LOCKED_RECORD contract is:

| Property | Doctrine |
|---|---|
| Mutability | ❌ never · DR fields are frozen byte-for-byte |
| Photos | ❌ no add · no remove |
| Production / Constraints | ❌ |
| Approval fields | ❌ never re-stamped |
| Audit envelope hash | recomputes one final time when the LOCKED transition fires · stamped as `final_audit_envelope_sha256` |
| Amendments | ✅ allowed only via the amendment workflow (see §3) |
| Read access | per `APPROVAL_PERMISSION_MATRIX.md §6` |
| PDF rendering | continues forever · audit footer carries the `final_audit_envelope_sha256` |
| DELETE | returns HTTP 410 (M1 Option C continues) |
| Historical projection | legacy DRs project as LOCKED_RECORD by default · zero migration |

## 2 · Continuity surfaces (all preserved)

| Surface | Behavior under LOCKED_RECORD |
|---|---|
| **Continuity ID** (DR-YYYY-NNNNN) | minted at first SUBMITTED · never reissued · stays valid forever |
| **Audit Footer** | every PDF page carries `Official Record · DR-YYYY-NNNNN · sha256=<16 hex> · rendered <UTC>` · the sha256 is the `final_audit_envelope_sha256` once locked |
| **Hash Chain** | each `daily_report_review_events` row carries `audit_envelope_sha256_before` + `_after` · final row's `_after` matches the LOCKED hash · drift = tamper signal |
| **Operational Timeline** | `operational_links` continues projecting the DR alongside related records (incidents · photos · inspections · meetings) per `OPERATIONAL_LINKING_RULES.md` |
| **Unified Records Projector** | LOCKED records appear with `status=LOCKED_RECORD` · `frozen_archive=true` in the `/api/operational-records` envelope |

## 3 · Amendment workflow (planned · NOT implemented today)

When a LOCKED_RECORD must change (operator error · regulatory correction · post-review discovery), an **amendment** is created:

```
DR-2026-00123 (LOCKED_RECORD, immutable)
  └── amended_by ──► DR-2026-00123-A1 (amendment, NEW record)
                       └── amended_by ──► DR-2026-00123-A2 (amendment, NEW record)
```

| Property | Doctrine |
|---|---|
| Amendment is a NEW record | original DR untouched · never mutated |
| Amendment carries a back-reference | `amends_dr_id` field + an `operational_links` row with `relationship="amends"` |
| Amendment continuity ID | `<original-continuity-id>-A<n>` · monotonically increasing |
| Amendment author | always logged · always super-tier OR admin |
| Amendment audit footer | links back to original via `amends_dr_id` |
| Amendment cannot delete original | original is immutable forever |
| Amendment cycle cap | none enforced server-side, but the operator can set a soft warning |
| External-auditor experience | PDF of original + each amendment is a complete forensic stack |

## 4 · Hash continuity (drift = tamper signal)

```
EVENT 1 (submit):
  audit_envelope_sha256_before:  null  (first event)
  audit_envelope_sha256_after:   H1

EVENT 2 (start_review):
  audit_envelope_sha256_before:  H1  ◄── must equal previous _after
  audit_envelope_sha256_after:   H2

EVENT 3 (approve):
  audit_envelope_sha256_before:  H2  ◄── must equal previous _after
  audit_envelope_sha256_after:   H3 = final_audit_envelope_sha256

PDF rendering shows: sha256=H3
```

If any rendered PDF or any DB row breaks this chain, the audit fails. The pre-deploy gate's hash-continuity probe (extension of the Wave-1C `pdf_audit_footer` probe) MUST verify this contract on every release candidate.

## 5 · What LOCKED_RECORD does NOT change for the operator

- ❌ NO new dashboard.
- ❌ NO new alert / notification.
- ❌ NO new portal page.
- ❌ NO new permission required to *view* a LOCKED record (same as any non-locked DR per the scope matrix).
- ❌ NO new step in the foreman workflow.
- ❌ NO PM Exposure Tile routing.

## 6 · External-auditor experience (CEI · DOT · FAA · owner)

| Surface | What the external auditor sees |
|---|---|
| Signed PDF link | DR content + Review History appendix + amendment chain (if any) |
| Audit footer on every page | `Official Record · DR-2026-00123 · sha256=<16> · rendered <UTC>` |
| Universal across audiences | M0.4 Audience Projection preserved — no audience-specific redaction within the auditor's scope |
| Verifiability | external auditor can re-compute the sha256 from the rendered envelope and verify against the footer · drift = tamper signal |
| PII | none beyond the necessary names of approver / reviewer · `ip_hash` + `device_id_hash` never leave admin scope |

## 7 · Doctrine compliance

- ✅ **Frozen Archive (M1 Option C)** — extended into the locked-record contract.
- ✅ **No silent delete** — DELETE 410 forever.
- ✅ **No silent edit** — amendment is a new record.
- ✅ **Hash continuity** — final sha256 stamped at lock transition.
- ✅ **Continuity ID stable** — never re-minted.
- ✅ **Audit footer universal** — every audience sees the integrity contract.
- ✅ **No new foreman steps** — locking is invisible to the foreman.

## 8 · Stop condition

🛑 Governance only. No endpoint coded. Implementation begins only after operator review.

_End of LOCKED_RECORD_GOVERNANCE.md._
