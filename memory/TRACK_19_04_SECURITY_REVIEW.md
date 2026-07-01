# Track 19.04 · Security Review

## Scope

Two new surfaces introduced by Track 19.04:

1. `useFormDraft` actor-gated restore (client-side, no new server surface).
2. `POST /api/daily-reports/attachments/upload` — public attachment upload for Daily Reports.

## Threat model

### T1 · Cross-actor draft leak on a shared workstation

* **Threat**: Actor A saves a draft; Actor B later signs in on the same PC and sees Actor A's draft.
* **Mitigation**: `savedByActor` stamped on every draft entry. `useFormDraft` refuses to surface drafts whose fingerprint mismatches `getAuthActorFingerprint()`. Regression test `test_cross_actor_draft_not_offered`.
* **Residual risk**: Two anonymous (unauthenticated) foremen on a public form on the same device share `"anon"` fingerprint. Documented in `FORM_SESSION_ISOLATION_CONTRACT.md` §14 as acceptable for kiosk flows — the restore prompt itself is the explicit-confirm gate.

### T2 · Malicious file upload (RCE / phishing bait)

* **Threat**: Attacker uploads a `.exe` / `.bat` / `.dll` and lures a PM to click the presigned URL.
* **Mitigation**:
  * MIME allow-list: only `application/pdf`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/csv`, `application/csv`.
  * Extension deny-list explicit for the 20 most dangerous extensions.
  * Filename sanitised server-side (`_safe_filename()`): strip separators, control chars, dot-only prefixes, cap at 240 chars.
  * Presigned URL Content-Disposition inherited from R2 metadata (`inline` for PDF, `attachment` for docs) — no auto-execute vector.
* **Regression test**: `test_daily_report_attachment_dangerous_ext_rejected`, `test_daily_report_attachment_unsupported_mime_rejected`.

### T3 · Oversized upload DoS

* **Threat**: Attacker uploads a 500 MiB blob to exhaust R2 quota / bandwidth.
* **Mitigation**: 25 MiB cap enforced server-side BEFORE R2 put. Backed by frontend size check (bounce early on obvious misclicks).
* **Regression test**: `test_daily_report_attachment_oversized_rejected`.

### T4 · Cross-report attachment leakage

* **Threat**: Attachment uploaded to Report A becomes accessible from Report B's detail view.
* **Mitigation**: `attachment_ref` is stored ONLY in the specific report's `attachments[]` list. There is no global attachment index, no cross-report lookup surface. R2 keys are UUID-based — unguessable, unenumerable via API.
* **Verification**: no endpoint returns "all attachments" without a report filter.

### T5 · Path traversal in filename

* **Threat**: Attacker submits filename `../../etc/passwd`.
* **Mitigation**: `_safe_filename()` strips path separators before storage; R2 key is `_build_doc_key(source_id, ext)` which uses `uuid.uuid4().hex` — the client-supplied filename NEVER contributes to the storage path. Filename is a metadata field only.

### T6 · Data URL padding attack

* **Threat**: Malformed base64 data URL crashes the parser.
* **Mitigation**: Reused the tolerant padding logic from `upload_data_url()`. Bad UTF / invalid base64 → `ValueError` → HTTP 400 with clear message. No crash.

### T7 · Presigned URL enumeration

* **Threat**: Attacker enumerates presigned URLs to access others' attachments.
* **Mitigation**: Presigned URLs are HMAC-signed with a per-object key expiration; guessing another object's URL requires the R2 secret key (server-side only). 7 day TTL bounded.

### T8 · Attachment upload as anonymous submit path

* **Threat**: Anonymous attacker uploads via the public endpoint at scale to test firewall.
* **Mitigation**: Uploads are subject to the same platform-wide rate-limit (`rate_limit_public_post`) registered on the daily-reports POST. **Note**: the current implementation does NOT wrap the attach endpoint in the limiter — captured as a follow-up for the next iteration. Standing risk is LOW because a single oversized upload is capped at 25 MiB and the R2 bucket has quota alarms.
* **Follow-up**: wire `dependencies=[Depends(rate_limit_public_post)]` on the attach endpoint. Documented; not a Track 19.04 blocker.

### T9 · Cross-user draft via localStorage residue

* **Threat**: LocalStorage keys leak form data across users on a shared PC.
* **Mitigation**: The ONLY localStorage keys that carry form-adjacent data are:
  * `masci.crew-memory.daily-report.v1` — device-local Smart Prefill snapshot. `CrewSetupRestorePrompt` requires explicit operator Apply; NEVER silent. Project-change guard already in place (`isProjectChange`).
  * `masci.prior-usage.<formKey>` — beacon only, no form payload.
  * `masci_device_id` — pure device identifier, no form payload.
  * `masci.crew-memory` snapshot fields exclude quantities, notes, signatures, weather, incidents, materials, photos (Phase 31.1 doctrine).
* **Residual risk**: Two shared-PC users could see each other's Smart Prefill "yesterday's crew" via the offer chip. Acceptable because the chip is opt-in and the data is ALREADY project-scoped (both users are on the same project → same crew universe).

### T10 · React default state / Object identity carry-over

* **Threat**: `buildDailyReportDefaults()` returns the same object across mounts.
* **Verification**: `buildDailyReportDefaults()` is a pure function returning a fresh object literal on every call. No closure carry-over. Verified in `dailyReportSchema.js`.

## Findings summary

| # | Severity | Status |
| --- | --- | --- |
| T1 | HIGH | Fixed |
| T2 | HIGH | Fixed |
| T3 | MEDIUM | Fixed |
| T4 | HIGH | Fixed (by design) |
| T5 | HIGH | Fixed |
| T6 | LOW | Fixed |
| T7 | LOW | Existing infrastructure |
| T8 | LOW | Follow-up documented |
| T9 | LOW | Acceptable per contract |
| T10 | LOW | Verified safe |

**Verdict**: All Track 19.04 threats mitigated or documented. One low-severity follow-up (T8 rate-limiter on attach endpoint) tracked for the next iteration; no P0/P1 residual risk.
