# Test Census

- **Test files:** 634 under `backend/tests/`.
- **Test functions:** 9183 (grep for `def test_` and `    def test_` in test classes).
- **Regression envelope:** 385+ passed · 0 skipped · 0 failed (Track 20.8 · Track 20.9 confirmed).

## Classification
- **KEEP** — 634 lock/regression files. Every recent track (19.54 → 21.0) adds its own lock test.
- **RETIRE candidates (post-deploy audit)** — ~40 iter### test files pre-15.30 with retired shared-password admin login patterns (see Track 20.6B TD-20.7-C01 for the doctrine; per-file audit is Track 21.x scope).
- **FIX** — 0 real failing tests at deployment gate (Track 20.6B closed all known · Track 20.8 closed the last skip).
- **DELETE** — 0 in Track 21.0. Batch audit for delete candidates is Track 21.x.

## Skips
Zero skips in the Track-20.8 primary envelope after Track 20.8 TD-20.8-A01 fix.
