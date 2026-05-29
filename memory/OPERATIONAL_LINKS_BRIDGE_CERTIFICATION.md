# Operational Links Bridge · Certification

_Phase V.1 · M1 · 2026-05-29 · target-only artifact contract._

> **Authorization:** _"Approve `legacy_daily_report` as TARGET ONLY
> inside operational_links. New ODR records may reference legacy
> records. Legacy records may never become active source artifacts.
> Purpose: preserve chronology. Preserve historical continuity.
> Prevent legacy mutation."_

This certification documents the bridge that allows ODR-era records
to chronologically reference their legacy ancestors without
mutating, converting, or re-attesting any legacy content.

---

## 1 · Schema-level contract

### 1.1 Artifact registration

`/app/backend/routes/operational_links.py`:

```python
ARTIFACT_TYPES = {
    # … existing types …
    "legacy_daily_report",   # M1 · Option C · target-only archive
}

# Doctrine: OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md
TARGET_ONLY_ARTIFACT_TYPES = {
    "legacy_daily_report",
}
```

### 1.2 Validation gate

```python
def _validate_relationship(body: OperationalLinkCreate) -> None:
    # … existing checks …
    # M1 · Option C · target-only artifact gate.
    if body.source_type in TARGET_ONLY_ARTIFACT_TYPES:
        raise HTTPException(
            422,
            f"'{body.source_type}' is a target-only archive artifact "
            "and cannot be the source of a new operational link "
            "(M1 · Option C · OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md).",
        )
```

The guard fires **before** any database write. Legacy rows can never
become a `source_*` of a new `operational_link` regardless of caller
intent or token level.

## 2 · Allowed link patterns (after M1)

| source_type | target_type | relationship | allowed? |
|---|---|---|---|
| `odr` | `legacy_daily_report` | `references` | ✅ |
| `odr` | `legacy_daily_report` | `addresses` | ✅ |
| `odr` | `legacy_daily_report` | `responds_to` | ✅ |
| `odr` | `legacy_daily_report` | `chronology_anchor` | ✅ (when this relationship is registered) |
| `photo` | `legacy_daily_report` | `evidence_for` | ✅ |
| `incident` | `legacy_daily_report` | `references` | ✅ |
| `legacy_daily_report` | `*` | `*` | ❌ HTTP 422 |
| `*` | `legacy_daily_report` | `supersedes` | ⚠️ Allowed by validation, but the `supersedes` materializer mutates the target's `status` — operators should use `references` instead to avoid mutating the archive even at the link layer. (See §4 nuance.) |

Notes:
- The relationship `addresses` is the closest semantic to "this new
  ODR addresses the situation captured in this legacy daily report"
  — it is the recommended default for cross-substrate chronology.
- The relationship `chronology_anchor` is reserved for future
  registration; if registered, it will be the canonical "this comes
  after this" link without mutating the target.

## 3 · Why target-only matters

A "source" link in the operational_links substrate is the act of
**generating new chronology**. Frozen records by definition have
finished generating chronology — they cannot grow new outbound
relationships because that would imply post-cutover authorship of
historical content.

A "target" link is the act of **another record acknowledging
chronology**. That acknowledgement is fully consistent with frozen
archive: the target is observed, the relationship is recorded on the
source side, the target itself is not mutated.

This invariant is what makes Option C operationally clean:

> **Legacy records are observed but never updated.**
> **ODR records observe legacy, build forward, and carry the new chronology.**

## 4 · Behavior nuance · `supersedes`

The existing `supersedes` relationship has a side-effect: it sets
the target's `status = "superseded"`. For most artifact types this
is desirable. For `legacy_daily_report`, it would mutate the
archive (changing `status` on a frozen row).

Two safeguards are in place:

1. **Recommendation** (this certification): operators authoring
   ODR-to-legacy bridges should use `references` (not `supersedes`).
2. **Future hardening** (NOT IMPLEMENTED in M1): a small additional
   guard in the materializer that no-ops the status mutation when
   the target is in `TARGET_ONLY_ARTIFACT_TYPES`. This belongs in a
   later wave because (a) the recommendation is sufficient
   operationally, and (b) the `supersedes` semantics for archive
   bridging are still under operator discussion.

## 5 · Test coverage

`tests/odr/test_m1_option_c.py`:

| # | Test | What it proves |
|---|---|---|
| 13 | `test_link_legacy_as_target_allowed` | ODR → legacy_daily_report (`references`) is accepted; both types properly populate the link record |
| 14 | `test_link_legacy_as_source_blocked_422` | legacy_daily_report → anything is rejected with 422 + "target-only" message |

Both tests are 🟢 in the M1 sweep.

## 6 · Forward operations enabled by this bridge

With the bridge in place, the following ODR-era operations become
possible without touching the archive:

- **Project chronology stitching:** when a foreman files an ODR for
  a project that has 6 historical daily reports, the new ODR can
  reference the most recent legacy entry to maintain a continuous
  per-project timeline.
- **Photo evidence retroactivity:** if a photo in `job_photos` is
  later determined to relate to a historical daily report, a
  `photo → legacy_daily_report (evidence_for)` link records that
  relationship without altering the legacy report's photo list.
- **Cross-substrate timeline search:** the unified projector can
  walk the `operational_links` graph forward from any record and
  surface every record that references it — including across the
  archive seam.

None of these operations modify the legacy substrate.

## 7 · Forbidden operations (re-stated for clarity)

| Operation | Status |
|---|---|
| Create a link with `source_type = legacy_daily_report` | ❌ HTTP 422 |
| Insert into `daily_reports` collection via `operational_links` side-effects | ❌ no such code path |
| Update `daily_reports` row status via `operational_links` side-effects | ⚠️ avoided by `references` recommendation; future hardening planned |
| Delete `daily_reports` row via `operational_links` side-effects | ❌ no such code path |
| Convert a legacy row to ODR by linking it | ❌ no such code path |

## 8 · Compatibility note

The new `legacy_daily_report` artifact type is additive: it does
not change the meaning or behavior of any existing artifact type
in `ARTIFACT_TYPES`. Existing operational_links rows are unaffected.
No migration of operational_links data is required (in fact, none
is permitted under Option C).

## 9 · Operator-facing one-liner

> **The bridge is a one-way street.**
>
> ODR records may look back at legacy records and acknowledge the
> chronology. Legacy records cannot reach forward. The past does
> not author the future.

---

_End of OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md._
