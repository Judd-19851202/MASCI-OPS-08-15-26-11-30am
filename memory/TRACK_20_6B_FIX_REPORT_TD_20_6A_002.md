# TRACK 20.6B · Fix Report · TD-20.6A-002

**Debt ID:** TD-20.6A-002
**Title:** `test_vocabulary_hr_sees_all_lanes` uses strict-equality assertion that broke after Track 19.59 additively added the `vendor` lane
**Original class:** C · P3 · target Track 20.6B
**Status:** ✅ **CLOSED** (2026-08-04)

## Original failure

```python
# Original assertion (Track 19.21)
assert set(body.get("allowed_lanes_for_actor") or []) == {
    "hr", "safety", "asset", "corporate_import"
}
```

The endpoint legitimately returns `{"hr", "safety", "asset", "corporate_import", "vendor"}` since Track 19.59 (vendor lane). Strict-equality assertions on evolving vocabularies are an anti-pattern documented in the Track 20.6B additive-safe assertion guardrail.

## Live reproduction

```
backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_hr_sees_all_lanes FAILED
E   AssertionError: assert {'asset', 'corporate_import', 'hr', 'safety', 'vendor'}
                    == {'asset', 'corporate_import', 'hr', 'safety'}
E   Extra items in the left set: 'vendor'
```

Reproduced 1/1 before fix.

## Fix applied

Replaced strict equality with an **additive-safe superset check** plus a **certified-vocabulary guardrail** that catches rogue lanes (typos, debug values, unapproved additions) without breaking on legitimate additive growth.

**Diff summary** (`backend/tests/test_track_19_21_e2e_live.py`):

```python
def test_vocabulary_hr_sees_all_lanes(hr_hdr):
    r = requests.get(f"{API}/employee-records/vocabulary", headers=hr_hdr, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("actor_role") == "hr"
    # Additive-safe SUPERSET check — original four core lanes MUST remain.
    allowed = set(body.get("allowed_lanes_for_actor") or [])
    required = {"hr", "safety", "asset", "corporate_import"}
    assert required <= allowed, (
        f"HR must see the original four core lanes; got: {sorted(allowed)}"
    )
    # Certified-vocabulary Zero-Drift assertion — every returned lane must
    # belong to the certified vocabulary. Rogue additions must land a track.
    certified = {"hr", "safety", "asset", "corporate_import", "vendor"}
    unexpected = allowed - certified
    assert not unexpected, (
        f"unexpected lanes not certified in the current vocabulary: "
        f"{sorted(unexpected)}. If this is intentional, add them to the "
        f"certified set here AND file the corresponding track."
    )
```

## Verification

```
backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_hr_sees_all_lanes PASSED
```

Adding a hypothetical future sixth lane (e.g. `contractor`) via a legitimate track will not re-break this test — the tester merely extends `certified` to `{..., "contractor"}` as part of that track's diff. Meanwhile a typo or debug-value lane will be caught immediately.

## Zero-drift

- Endpoint behavior unchanged.
- Vocabulary contents unchanged.
- Test-only change.
- No skip added.
- No permission weakening.

## Register entry

Status updated to **CLOSED** in `memory/TECHNICAL_DEBT_REGISTER.md` (2026-08-04).

## Doctrine reference

This fix embodies the Track 20.6B Additive-Safe Assertion Guardrail (see `TRACK_20_6B_ADDITIVE_ASSERTION_GUARDRAIL.md`).
