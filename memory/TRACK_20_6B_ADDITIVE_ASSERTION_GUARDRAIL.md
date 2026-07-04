# TRACK 20.6B · Additive-Safe Assertion Guardrail (Doctrine)

**Purpose:** Prevent future strict-equality failures against intentionally evolving vocabularies (lanes, entity kinds, asset classes, record types, taxonomy classes).

**Filing:** Doctrine document · not a code enforcer. Complements the Zero-Drift + Tech-Debt Register discipline.

## Problem this doctrine solves

The MASCI Universal Thread architecture is **additively evolving by design**. Every promotion track adds one or more of:
- A new ownership lane (Track 19.59 added `vendor`)
- A new entity kind (Track 19.61 added `asset`)
- A new asset class (Track 19.62 added `Fire Protection`)
- A new record_type slug (multiple tracks)
- A new source in the Job Photos indexer
- A new certified role
- A new workflow kind

Strict-equality assertions against these evolving sets (`set(x) == {a, b, c}`) will re-break on every legitimate additive change, producing false-red regressions that either:
- Waste time in the next track (fix the assertion, re-run, re-certify), OR
- Hide real regressions when engineers ignore the noise, OR
- Delay deployment blocked on assertion drift.

Track 19.61 hit this exact issue (Track 19.59 vendor lane broke the Track 19.21 live-e2e test — see TD-20.6A-002).

## The doctrine

**Prefer superset containment over strict equality for evolving vocabularies.**

Instead of:
```python
assert set(x) == {"hr", "safety", "asset", "corporate_import"}   # brittle
```

Write:
```python
allowed  = set(x)
required = {"hr", "safety", "asset", "corporate_import"}
assert required <= allowed, f"missing required lane: {required - allowed}"

# Optional: also lock the CERTIFIED superset to catch rogue additions
certified = {"hr", "safety", "asset", "corporate_import", "vendor"}
assert not (allowed - certified), (
    f"uncertified lane(s): {allowed - certified}. "
    f"Add them here AND file a track."
)
```

**Two-side assertion:**
- **Bottom lock (`required <= allowed`)** — every mandatory element must be present. Prevents accidental removal.
- **Top lock (`allowed - certified` is empty)** — no rogue element may appear. Prevents typos, debug values, and additions without a track.

Adding a new legitimate element becomes a one-line update to the `certified` set inside the corresponding promotion track — a natural, intentional, reviewable change.

## Target vocabularies

The following are known-evolving vocabularies where strict-equality assertions are anti-pattern and additive-safe assertions must be used:

| Vocabulary | Source of truth | Known additions history |
|---|---|---|
| `ENTITY_KINDS` (`employee` · `vendor` · `asset`) | `backend/routes/employee_records.py` | vendor (19.59), asset (19.61) |
| `OWNERSHIP_LANES` (`hr` · `safety` · `asset` · `corporate_import` · `vendor`) | employee-records `LANE_RECORD_TYPES` | vendor (19.59), asset (19.61) |
| `ASSET_CLASSES` (via `services/asset_taxonomy.py`) | `TAXONOMY_VERSION` | Fire Protection (19.62 · v1.1.0) |
| `LANE_RECORD_TYPES[<lane>]` (record_type slugs) | employee-records | 5 fire-specific slugs (19.62) |
| Job Photos `sources` (`daily_report` · `inspection` · `qaqc`) | `backend/routes/job_photos.py` | additive-friendly by design |
| Universal Thread portal token portals (`admin` · `pm` · `hr` · `safety` · `shop` · `dispatch` · `field_leadership`) | multi-login response | additive-friendly |
| Trust-spine workflow kinds | `lib/trust_spine.py` | additive-friendly |
| Auto-email allowed record kinds | `_dispatch_auto_email` | additive-friendly |

## Anti-pattern examples

Where NOT to use additive-safe superset:

- **`certified` set of allowed image-upload MIME types** — this MUST be strict-equality (accidentally accepting a new type is a security risk).
- **`retired` set of removed endpoints** — this MUST be strict-equality (accidentally re-adding a retired endpoint is a regression).
- **Fixed-cardinality contracts** — response shape schema, PDF layout section count, etc.

Rule of thumb: additive-safe applies to **user-facing / operational vocabularies** that grow with the business. Not to security boundaries or wire contracts.

## Implementation checklist for future tracks

When landing a new element into an evolving vocabulary:

1. Grep the entire test tree for the strict-equality anti-pattern against the affected vocabulary:
   ```
   grep -rn 'assert set(.*allowed_lanes.*) == {' backend/tests/
   grep -rn 'assert set(.*ENTITY_KINDS.*) == {' backend/tests/
   ...
   ```
2. For every hit, replace with the two-side assertion.
3. Extend the `certified` set to include the new element AS PART OF the promotion track's diff.
4. Document the extension in the track's Executive Summary.

## Track 20.6B enforcement

Track 20.6B applied this doctrine in three places:
1. `test_track_19_21_e2e_live.py::test_vocabulary_hr_sees_all_lanes` — converted to two-side superset assertion (see `TRACK_20_6B_FIX_REPORT_TD_20_6A_002.md`).
2. `test_job_photos.py::test_admin_list` — converted forbidden-set check to additive-safe filter (excluding pre-op sources) rather than pinning the full source set.
3. `test_job_photos.py::test_raw_valid` — converted single-scheme `data:` check to additive-safe accept-list (`data:` OR `https://`).

The Track 20.6B lock test (`test_track_20_6b_test_hardening.py`) verifies that the anti-pattern is absent from these three files.

## No overbuilding

This doctrine is deliberately **documentation-first**. It does NOT include:
- A complex static analyzer.
- A pre-commit hook that scans every `assert set(...) == ` in the repo.
- A CI job that fails on unknown vocabularies.

Those would be false-red generators of their own. The doctrine relies on:
- Track-level review discipline (each promotion track author checks).
- The lock test's spot-check on the highest-signal files.
- The Tech Debt Register catching any drift as a Class-C entry.
