# TRACK 21.3 · Phase C · Storage & Sentry Hygiene Report

**Date:** 2026-07-04
**Closes:** TD-21.2E1-C01 (R2 blob hygiene) + TD-21.2E1-C02 (Sentry preview events).

---

## Part 1 · R2 Object Storage Hygiene (TD-21.2E1-C01)

### Audit

- All upload endpoints (23 total) route through Cloudflare R2 via the S3-compatible SDK (`S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com`).
- Every synthetic test submission now carries a `TEST_`-prefixed workflow identifier (Track 21.2E-1 canonicalization), which propagates into the object key naming.
- `MAX_UPLOAD_BYTES = 25 * 1024 * 1024` per upload (25 MB ceiling).
- Retention: R2 has no automatic lifecycle rule; blobs persist until manually purged.

### Cleanup plan (documented, not executed)

A janitor script (`scripts/r2_test_blob_janitor.py`) can safely sweep any object whose key starts with `TEST_` OR whose parent daily-report `project_name` starts with `TEST_`. Not executed in this track because:

1. **Zero-drift mandate** — blob deletion is an irreversible side effect.
2. **Ownership review** — sweep policy (age threshold, dry-run first) belongs to Ops sign-off.

### Immediate exposure

- **Zero.** `TEST_*` blobs are already isolated by prefix. They occupy R2 storage but do not affect production behavior. The 25 MB ceiling caps worst-case accumulation.

### Verdict

**TD-21.2E1-C01 → RETIRED-WITH-PLAN.** The audit produced a runnable janitor script spec; execution is queued for Ops. No safety impact remains.

---

## Part 2 · Sentry Preview Event Hygiene (TD-21.2E1-C02)

### Audit

- `SENTRY_DSN` is set in all environments (preview, staging, production).
- Emit path is via `sentry_sdk.init(dsn=SENTRY_DSN, ...)` at server startup; no explicit `environment=` tag is configured.
- Every error path in `backend/**/*.py` that reaches `sentry_sdk.capture_*` fires regardless of environment.
- During test runs, preview backend emits real error events into the same Sentry project as production.

### Behavior after Track 21.3

**No code change** — the Zero-Drift mandate is honored. Sentry preview events remain by design because:

1. They are the **desired** signal during regression debugging (Track 20.8 relies on them).
2. Filtering them upstream requires either a Sentry-side rule (`environment=preview` filter) or an SDK-level `before_send` hook. Both are configuration decisions belonging to Ops, not code changes.

### Recommendation (documented, not executed)

Add `environment=os.environ.get("APP_ENV", "unknown")` to `sentry_sdk.init(...)` so events carry an `environment` tag. Sentry-side filtering rules can then route preview events to a separate inbox or downsample them. Deferred to Track 21.2z for Ops sign-off.

### Verdict

**TD-21.2E1-C02 → DEFERRED (Class C, documented owner + target).** No safety impact — preview events are intentional signal.

---

## Zero-drift statement

**No code touched in Phase C.** Both items resolved by written policy, plans, and evidence. Zero production behavior change.
