# TRACK 20.6B · Fix Report · TD-20.6A-001

**Debt ID:** TD-20.6A-001
**Title:** `test_vocabulary_unauth_401` returns 200 instead of 401 (live-e2e fixture leak)
**Original class:** C · P3 · target Track 20.6B
**Status:** ✅ **CLOSED** (2026-08-04)

## Original failure

Under the live-e2e runner, `test_vocabulary_unauth_401` in `backend/tests/test_track_19_21_e2e_live.py` was reported to return HTTP 200 (instead of the expected 401) because the shared `requests.Session()` was inheriting portal tokens from prior authenticated fixtures within the same test process.

## Reproduction attempt

Before applying any fix, ran the current codebase against the live preview backend:

```bash
$ curl -s -o /dev/null -w "%{http_code}\n" \
    "https://safety-audit-mobile-1.preview.emergentagent.com/api/employee-records/vocabulary"
401

$ REACT_APP_BACKEND_URL=... python -m pytest \
    backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_unauth_401 -v
PASSED
```

The endpoint itself is correctly gated in production. The failure described in the one-pager reflected an intermittent fixture leak that either:
1. Was resolved by a downstream cleanup between the one-pager filing (2026-08-02) and Track 20.6B execution (2026-08-04), OR
2. Only reproduces under a very specific ordering of tests that we no longer trigger by default.

Either way, the underlying test as written was NOT robust: it used the module-global `requests` (which reuses a default connection pool) rather than an explicit fresh session, so a future fixture change could re-introduce the leak silently.

## Fix applied

Rewrote `test_vocabulary_unauth_401` to use an explicit fresh `requests.Session()`. This closes the leak surface for all time — even if a future fixture change reintroduces token injection at module scope, this test cannot inherit it.

**Diff summary** (`backend/tests/test_track_19_21_e2e_live.py`):

```python
def test_vocabulary_unauth_401():
    # Track 20.6B · TD-20.6A-001 hardening — use a FRESH requests.Session()
    # explicitly so no stale header from a previous test can leak in and
    # accidentally satisfy the auth gate.
    fresh = requests.Session()
    r = fresh.get(f"{API}/employee-records/vocabulary", timeout=15)
    assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"
```

## Verification

```
backend/tests/test_track_19_21_e2e_live.py::test_vocabulary_unauth_401 PASSED
```

Live curl confirms production behavior:
```
$ curl -s -o /dev/null -w "%{http_code}\n" \
    "https://safety-audit-mobile-1.preview.emergentagent.com/api/employee-records/vocabulary"
401
```

## Zero-drift

- Endpoint behavior unchanged.
- `_gate` in `backend/routes/employee_records.py` unchanged.
- Test-only change confined to one function in one file.
- No production security weakening.
- No skip added.

## Register entry

Status updated to **CLOSED** in `memory/TECHNICAL_DEBT_REGISTER.md` (2026-08-04).
