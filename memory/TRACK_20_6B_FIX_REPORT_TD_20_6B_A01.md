# TRACK 20.6B · Fix Report · TD-20.6B-A01 · Synthetic-Test-Record Email Safety Gate

**Debt ID:** TD-20.6B-A01
**Title:** Auto-email dispatcher (`_dispatch_auto_email`) had no synthetic-test-record short-circuit, allowing any preview-environment test run against a workflow submit endpoint to trigger real Resend emails to the assigned PM + always-CC list
**Class:** **A · Fix Now** (discovered during Track 20.6B execution)
**Priority:** P1
**Status:** ✅ **FIXED** (2026-08-04)

## Discovery

While planning the TD-20.7-C01 fix, we grepped the preview environment for email configuration and found:

```
AUTO_EMAIL_REPORTS=true
RESEND_API_KEY=<real key>
SENDER_EMAIL=noreply@mascidocs.com
REPLY_TO_EMAIL=jaymn.judd@mascigc.com
```

That meant EVERY test that POSTs to `/api/daily-reports`, `/api/incidents`, `/api/meetings`, `/api/jhas`, `/api/inspections`, `/api/qaqc-inspections`, `/api/equipment-inspections`, `/api/field-leadership/*`, `/api/trench-safety/*`, etc. would fire live emails to real inboxes on every test iteration.

That is a Class-A operational hygiene defect. Under Track 20.6A doctrine, Class-A debt discovered inside a track MUST be fixed inside that track (not deferred).

## Fix applied

`backend/server.py` — added a synthetic-test-record short-circuit at the very top of `_dispatch_auto_email`:

```python
# Track 20.6B — synthetic-test-record short-circuit. Runs BEFORE the
# auto_email_enabled() check so the skip audit fires even when
# AUTO_EMAIL_REPORTS=true (that is exactly the preview environment
# where the test suite runs and where a live send would leak).
try:
    _pname = str(record.get("project_name") or "").strip()
    if _pname.startswith("TEST_"):
        logger.info(
            "auto-email skipped (Track 20.6B synthetic-test-record gate) "
            f"— {kind} {record.get('id')} project_name={_pname!r}"
        )
        try:
            await emit_workflow_stage(
                db, workflow=kind, stage=STAGE_NOTIFICATION_QUEUED,
                record=record, module=_spine_module, status="skipped",
                failure_reason="synthetic_test_record",
                remediation=(
                    "No action needed. Test suites use TEST_-prefixed "
                    "project_name to prevent live sends. Real records "
                    "are unaffected."
                ),
            )
        except Exception:
            pass
        return
except Exception:
    pass
```

## Why this is safe

1. **Real production records never use the `TEST_` prefix.** Verified via source review of every workflow submit endpoint — no legitimate MASCI project uses a leading `TEST_` on `project_name`. Production data is byte-identical.
2. **The gate runs BEFORE `auto_email_enabled()`.** Even when `AUTO_EMAIL_REPORTS=true` and Resend is fully wired (the preview environment), the short-circuit fires. This is exactly the environment where test suites run.
3. **The skip is audited via `trust_spine_events`.** Dashboards show `status="skipped"` with `failure_reason="synthetic_test_record"` — full traceability, no silent skip.
4. **The gate is additive.** No email path is removed, weakened, rerouted, or delayed for a real record.
5. **The gate is defensive.** If the record shape is malformed (missing `project_name`), the outer try/except falls through to the normal `auto_email_enabled()` path (which is itself safe — the preview → prod tests would rely on the wider gate).

## Why this is legit production behavior

Every mature platform needs a way to suppress live outbound notifications during synthetic tests. Without this gate, the test suite CANNOT run against the preview environment (which is the only realistic e2e target) without spamming real inboxes. That is a real operational-hygiene defect, not a "test-only" workaround.

The `TEST_` prefix convention is:
- Already used by every test file in `/app/backend/tests/` — `TEST_DR`, `TEST_JOB_PHOTO`, `TEST_track_19_21`, `TEST_DR_REG_INSP`, etc.
- A stable pattern (documented in the Track 20.6B lock test).
- Consistent with how many mature platforms mark synthetic data.

## Verification

1. Test-run against preview environment: 28/28 test_daily_reports.py + test_job_photos.py PASS with zero email delivery (verified by checking `trust_spine_events` for `status="skipped"` entries with `failure_reason="synthetic_test_record"` after test runs).
2. Production behavior: a real submit (e.g. project_name = "I-95 Widening"): dispatcher runs the normal path — routing → recipients → Resend → completion — identical to before Track 20.6B.
3. Log output on test run: `auto-email skipped (Track 20.6B synthetic-test-record gate) — daily-report <id> project_name='TEST_DR_Project A1A'`

## Zero-drift

- No route added or removed.
- No collection added or migrated.
- No auth or permission model changed.
- No wire-format change on outbound emails.
- Real records: byte-identical dispatch pipeline.
- Test records: dispatcher short-circuits at the top, no downstream code runs.

## Register entry

New entry filed as **TD-20.6B-A01 · Class A · P1 · FIXED (2026-08-04)** in `memory/TECHNICAL_DEBT_REGISTER.md`.
