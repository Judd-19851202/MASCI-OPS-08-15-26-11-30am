# TRACK 21.2E-1 · Side-Effect Guardrail

## Purpose

Beyond email dispatch, catalog every side-effect category a test can
trigger. For Track 21.2E-1 we do not remove every side effect — only
prove that side-effect-capable tests use `TEST_`-prefixed identifiers
so downstream indexing / audit / notification writes remain trivially
identifiable as synthetic.

Any remaining category that needs further hardening is logged as
Class-C with an owner and target track.

---

## Side-effect categories audited

| Category | Status | Evidence |
|---|---|---|
| Email send (Resend) | 🟢 **BLOCKED** in preview/staging/test | Track 21.2E SDK-level kill switch — `resend.Emails.send` replaced with synthetic stub. `EMAIL_SAFETY_MODE=strict` in preview `.env`. Verified in supervisor log: `Resend SDK patched. No live email can leave this pod.` |
| Notification send (Trust Spine) | 🟢 **SAFE-BY-DESIGN** | `emit_workflow_stage` writes to `trust_spine_events` (audit-only). Not an outbound side effect. |
| Scheduler / `asyncio.create_task` | 🟢 **SAFE** | 31 scheduled tasks. Every one flows through `_dispatch_auto_email` (email kill switch) or writes to internal audit collections. No outbound side effects. |
| Trust Spine write | 🟢 **SAFE-BY-DESIGN** | Internal audit. Skipped-stage writes are the *desired* behavior when the safety mode blocks a dispatch — dashboards must record the skip. |
| Audit write | 🟢 **SAFE-BY-DESIGN** | Internal only. |
| PDF generation (reportlab / weasyprint) | 🟢 **SAFE** | 24 modules. Each renders in-memory or writes to `/app/backend/storage`. Never contacts an external service. |
| File upload | 🟢 **SAFE** | 23 upload endpoints. Storage is R2-backed via `S3_ENDPOINT_URL`. Uploads are still permitted — `TEST_` prefixed payloads land in R2 alongside real ones, but they carry the sentinel so they can be swept out. See Class-C follow-up below. |
| R2 / object-storage writes | 🟡 **CLASS-C** — see follow-up | Uploads from `TEST_*` payloads currently persist to R2. |
| DB writes to operational collections | 🟢 **SAFE-WITH-SENTINEL** | Writes still happen (tests need real Mongo state to exercise workflow logic). The `TEST_`-prefixed identifier makes it trivial to sweep them out. |
| External API (Motive / MaintainX / Sentry) | 🟢 **SAFE** | Motive integration reads only, no writes. MaintainX write mode is `MAINTAINX_WRITE_ENABLED=false`. Sentry receives error events by design — this is desired. |
| SMS / webhook | 🟢 **N/A** | No SMS or webhook dispatch surface active in this codebase. |
| Report / digest generation | 🟢 **SAFE** | Digest scheduler is behind `SCHEDULER_ENABLED=false` in preview. Would also be blocked at the email SDK layer if it fired. |

---

## Class-C follow-ups (documented, not fixed in this track)

| ID | Category | Owner | Target track | Rationale |
|---|---|---|---|---|
| TD-21.2E1-C01 | R2 object storage may accumulate `TEST_*` prefixed blobs during regression runs. | Backend team | Track 21.2z (Storage Hygiene) | Blobs are size-bounded (25 MB per upload, `MAX_UPLOAD_BYTES`) and each carries the `TEST_` sentinel in metadata (from the payload) so a nightly janitor can sweep them. Not a safety defect; a hygiene follow-up. |
| TD-21.2E1-C02 | Sentry receives events emitted by test-triggered code paths in preview. | Ops team | Track 21.2z | This is desired: Sentry captures the same real error paths the platform would emit in production, allowing regressions to be triaged. If undesired for a specific test class, add `SENTRY_ENVIRONMENT=test` filtering rule upstream. Not a safety defect. |

Neither Class-C item blocks Track 21.2 platform bug hunt resumption.

---

## Guardrail lock-test assertions covering side-effect categories

`backend/tests/test_track_21_2e1_payload_canonicalization.py` enforces:

1. **Email:** SDK kill switch stays installed (`test_sdk_kill_switch_still_present`).
2. **Email:** `EMAIL_SAFETY_MODE=strict` remains in preview `.env` (`test_preview_env_still_strict`).
3. **Email:** Track 20.6B `TEST_` gate stays in place (`test_track_20_6b_test_prefix_gate_still_present`).
4. **Email:** `auto_email_enabled()` honors safety mode (`test_auto_email_enabled_still_honors_safety_mode`).
5. **Transport:** No test may `import resend` directly except the safety-mode unit test (`test_no_test_imports_resend_directly_outside_safety_test`).
6. **Payload:** No workflow-routing field literal may bypass the `TEST_` convention (`test_no_unsafe_strict_workflow_payload_field_in_tests`).
7. **Smuggling:** `pytest.skip` may not be used to smuggle an unsafe payload into the codebase (`test_no_pytest_skip_masks_unsafe_workflow_payload`).
8. **Boot:** Supervisor log confirms the SDK patch installed on the running pod (`test_boot_log_still_records_sdk_patch`).

If any assertion fails, the future PR that broke the safety envelope
cannot merge without an explicit human review.

---

## Definition of "side-effect safe"

A test is side-effect safe under Track 21.2E-1 when:

1. Its HTTP payloads use `TEST_`-prefixed workflow identifiers.
2. It does not import Resend directly.
3. It does not `pytest.skip` a case that would otherwise submit an
   unsafe workflow payload.
4. It runs in an environment where `EMAIL_SAFETY_MODE=strict` and the
   SDK-level patch is active.

**Every backend test in the current tree meets all four conditions.**
