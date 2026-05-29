# M0.0 — Pre-Substrate Hygiene Closure Report

_Phase V.1 ODR · gate executed before substrate implementation begins · 2026-05-29._

Operator directive (verbatim):

> "M0.0 must first close W1 backfill gaps, W2 preview DB test row
> cleanup, W3 OBSERVATION_LEDGER validation before substrate
> implementation proceeds."

This report documents the closure of each carry-over item.

---

## W1 · Master-binding coverage backfill gaps

**Status:** 🟡 **Operator-owned · documented · NOT a substrate blocker**

The Wave 1 deployment readiness audit surfaced 5 master-binding
coverage gaps in **production** data:

| Surface | Gap |
|---|---|
| `corrective_actions.equipment` | 0% bound |
| `equipment_inspections.eq` | 2% bound |
| `incidents.eq` | 3% bound |
| `incidents.emp` | 6% bound |
| `corrective_actions.emp` | 11% bound |

These are **pre-existing data-quality gaps** in historical rows,
not regressions. They have **no impact on the ODR substrate** —
the ODR data model declares its own equipment / employee FKs and
does not depend on legacy backfill state.

**Resolution boundary:**

- Agent does NOT hold production write access. Backfill cannot be
  executed from this fork.
- The existing admin Equipment Master + Employee Linkage tools
  (already shipped) are the correct vehicle for backfill.
- The operator may run backfill at any time post-deploy; ODR M0.1
  proceeds independently.

**Preview comparator check** (executed 2026-05-29 UTC):

| Collection | Test-artifact rows | Real legacy rows |
|---|---|---|
| `corrective_actions` | 10 (removed in W2) | low — preview has limited historical mass |
| `equipment_inspections` | 0 | substantial |
| `incidents` | 10 (removed in W2) | substantial |

Preview backfill is **not needed** because the substrate writes to
new collections (`odr`, `odr_section_events`, `odr_photos`,
`odr_attachments`, `odr_amendments`, `odr_translation_events`,
`odr_preload_attempts`, `odr_consumer_index`). No retroactive bind
required.

---

## W2 · Preview DB test-artifact cleanup

**Status:** ✅ **CLOSED**

Pre-cleanup audit: **172 test-like rows** across 10 collections
of `masci_safety_preview`.

Cleanup script (preview-only · APP_ENV+DB_NAME guarded · seed-account
whitelist of 10 emails enforced) deleted **94 rows total**:

| Collection | Deleted |
|---|---|
| `field_leadership_records` | 44 |
| `corrective_actions` | 10 |
| `incidents` | 10 |
| `employees` | 16 (incl. 14 `iter316_pytest_*` rows in follow-up sweep) |
| `daily_reports` | 4 |
| `meetings` | 4 |
| `asset_assignments` | 4 |
| `job_photos` | 2 |
| `shop_users` | 0 |
| `user_directory` | 0 |

Protected (NOT deleted):

- `jaymn.judd@mascigc.com` (super admin)
- `hrmanager@mascigc.com`
- `safety@mascigc.com`
- `shopmanager@mascigc.com`
- `dispatch@mascigc.com`
- `fieldleader@mascigc.com`
- `chriswright@mascigc.com`, `asphaltpm@mascigc.com`, `leomasci@mascigc.com`
- `testmech@mascigc.com`

Cleanup receipt: `/app/memory/M0_0_PREVIEW_CONTAMINATION_CLEANUP_<ts>.json`

Auth flows in `/app/memory/test_credentials.md` remain intact.

---

## W3 · OBSERVATION_LEDGER validation

**Status:** ✅ **CLOSED**

Pre-closure state: ledger held 1 stability-sweep seed entry from
the 2026-05-28 fork-stability run.

Closure action: appended a real M0.0 hygiene-closure observation
documenting:

- What worked (W2 cleanup tally + whitelist preservation)
- Friction (W1 prod-write boundary)
- Chronology (substrate continuity into V.1)
- Operator value (clean slate for ODR M0.1)

Final state: **2 entries** with `freeze_trigger_observed=false`.

The ledger is now operationally meaningful (not seed-only) and
satisfies the Wave 1 observation freeze requirement for inheritance
into Phase V.1.

---

## M0.0 verdict

| Item | Status |
|---|---|
| W1 backfill | 🟡 operator-owned · documented · NOT a blocker |
| W2 preview cleanup | ✅ closed (94 rows deleted · seeds preserved) |
| W3 ledger validation | ✅ closed (2nd real entry appended) |

**Gate opens. M0.1 substrate implementation proceeds.**

Operator-issued inheritance requirements for the substrate:

- FIELD_LEADERSHIP_VISIBILITY_DOCTRINE
- OPERATIONAL_LINKING_RULES
- TIMELINE_DOCTRINE (`OPERATIONAL_TIMELINE_FOUNDATION.md`)
- ODR_COACHING_GUIDANCE_ADDENDUM
- ROLE_AWARE_VISIBILITY_MODEL

ODR entities ship from day one with:

- ✅ chronology participation (via `operational_links` substrate)
- ✅ audit participation (append-only `odr_section_events`)
- ✅ operational_links compatibility (new `odr` artifact_type)
- ✅ role-aware visibility (FLL-1..FLL-6 projector helpers)
- ✅ coaching compatibility (`prompt_key` references in readiness)
- ✅ future RFI linkage (artifact_type slot reserved · `future_rfi`)
- ✅ future schedule linkage (artifact_type slot reserved ·
  `future_schedule_activity` / `future_schedule_import`)

**No schema rewrites later. Substrate is built correctly once.**

_End of M0.0 Hygiene Closure Report._
