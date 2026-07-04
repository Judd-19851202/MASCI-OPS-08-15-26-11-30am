# TRACK 20.6B · Zero-Drift Matrix

**Verdict:** ✅ **Zero drift on real records.** One additive, well-audited, test-only guardrail added to `_dispatch_auto_email`. Everything else is test-file changes.

## Structural invariants

| Invariant | Before Track 20.6B | After Track 20.6B | Result |
|---|---|---|---|
| Backend route inventory | Unchanged | Unchanged | ✅ Same |
| Endpoint permissions | Unchanged | Unchanged | ✅ Same |
| Payload shapes (`photos: List[str]`, `_full_payload`, etc.) | Unchanged | Unchanged | ✅ Same |
| MIME allow-lists | Unchanged | Unchanged | ✅ Same |
| Size limits | Unchanged | Unchanged | ✅ Same |
| Auth model (`require_admin`, `require_admin_pm_or_hr_read`, etc.) | Unchanged | Unchanged | ✅ Same |
| `AUTO_EMAIL_REPORTS` semantics for real records | Unchanged | Unchanged | ✅ Same |
| Real-record email dispatch pipeline | Full send | Full send | ✅ Same |
| TEST_-prefixed record email dispatch pipeline | Full send (dangerous) | Short-circuit + audit | ✅ **Improved** (Class-A fix TD-20.6B-A01) |
| Number of `_dispatch_auto_email` functions in codebase | 1 | 1 | ✅ Same |
| Number of test files that hit retired shared-password admin login | 2 | 0 | ✅ **Improved** |
| Number of test files with strict-equality on evolving vocabularies | ≥1 | 0 (in touched files) | ✅ **Improved** |

## What was NOT changed (must not be built)

- ❌ No new backend route.
- ❌ No new collection.
- ❌ No new email transport.
- ❌ No new permission role.
- ❌ No new portal token.
- ❌ No new scheduler.
- ❌ No new OI product.
- ❌ No new upload behavior.
- ❌ No new UI component.
- ❌ No new modules.
- ❌ No new workflows.
- ❌ No feature.

## What was changed (surgical, additive)

- ✅ One `if` clause + trust-spine skip audit at the top of `_dispatch_auto_email` in `backend/server.py`.
- ✅ Three test-file hardenings:
    - `test_track_19_21_e2e_live.py` — fresh session + superset assertion.
    - `test_daily_reports.py` — canonical multi-login auth.
    - `test_job_photos.py` — canonical multi-login auth + additive R2/data-URL accept-list.
- ✅ New Tech Debt Register entry for TD-20.6B-A01.
- ✅ Status flips (OPEN → CLOSED) for TD-20.6A-001, TD-20.6A-002, TD-20.7-C01.
- ✅ 9 markdown deliverables under `memory/TRACK_20_6B_*.md`.
- ✅ New lock test `backend/tests/test_track_20_6b_test_hardening.py`.

## Production-behavior proof (real records unchanged)

Test:
1. Real record submit: `POST /api/daily-reports` with `project_name = "I-95 Widening"` and full crew/materials payload.
2. Expected: `_dispatch_auto_email` runs the FULL pipeline — routing → recipients → Resend → completion.
3. Verified via trust-spine event stream: `STAGE_ROUTING_RESOLVED → STAGE_RECIPIENTS_BUILT → STAGE_NOTIFICATION_QUEUED → STAGE_PROVIDER_ACCEPTED → STAGE_COMPLETED` all with `status="ok"` (assuming `AUTO_EMAIL_REPORTS=true`).

Contrast:
1. Test record submit: `POST /api/daily-reports` with `project_name = "TEST_DR_Project A1A"`.
2. Expected: `_dispatch_auto_email` short-circuits at the top; trust-spine emits `STAGE_NOTIFICATION_QUEUED` with `status="skipped", failure_reason="synthetic_test_record"`; no downstream code runs; no Resend call.
3. Verified via test-suite live run.

Both paths are individually correct. Zero drift on real records.

## No parallel systems

- Exactly ONE `_dispatch_auto_email` function.
- Exactly ONE trust-spine event schema.
- Exactly ONE canonical login endpoint (`POST /api/auth/multi-login`).
- Exactly ONE ownership-lane vocabulary source.
- Exactly ONE asset taxonomy.

## Continuity with prior tracks

- **Track 15.32 (auth retirement)** — Track 20.6B completes the migration of legacy test files off the retired shared-password admin login. Consistent with the doctrine.
- **Track 19.59 (vendor lane)** — Track 20.6B closes the last strict-equality assertion that broke on the vendor lane. Consistent with the additive doctrine.
- **Track 19.61 (asset lane)** — Track 20.6B tolerates the asset lane in every touched assertion.
- **Track 19.62 (fire protection)** — untouched.
- **Track 20.5 / 20.6 (audit tracks)** — untouched.
- **Track 20.6A (tech-debt discipline)** — Track 20.6B is the first pass at closeout under this doctrine. New Class-A discovery (TD-20.6B-A01) was fixed inline per doctrine, not deferred.
- **Track 20.7 (photo capture)** — unaffected.

## Conclusion

Track 20.6B is Zero-Drift-compliant. Real production behavior is byte-identical for every real record. The one additive production hunk (synthetic-test-record short-circuit) is scoped, audited, and defensively coded. All other changes are strictly test-file hardening.
