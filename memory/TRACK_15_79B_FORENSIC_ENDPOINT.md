# TRACK 15.79B — DAILY REPORT DELIVERY FORENSICS · FORENSIC ENDPOINT

**Status:** ✅ ENDPOINT SHIPPED · 🟢 GO (preview proof) · awaiting one
operator call against production
**Date:** 2026-02-12
**Scope:** Build the admin-gated, read-only forensic endpoint demanded
by Track 15.79B. The endpoint traces — record by record — *why* the
PM/Co-PM email for any Daily Report did or did not send, classifying
every failure into a closed-set root-cause code.

---

## EXECUTIVE SUMMARY

The operator reported a P0 production incident: Daily Reports saved
tonight, but no PM/Co-PM emails were received despite valid PM/Co-PM
assignments visible in the UI. Direct production-DB access from this
preview pod is blocked at the Atlas user-permission layer (proper env
isolation), so I built the platform's own forensic instrument — an
admin-gated, read-only endpoint that the operator can call from
production with their existing session.

`GET /api/admin/daily-report-delivery/forensics` is now live in
preview. It:

* Pulls every Daily Report submitted in a configurable window.
* Re-implements the resolver code path **without** triggering any
  audit-row side effects (test-locked).
* Reads `jobs_master`, `project_team_assignments`,
  `trust_spine_events`, and `email_routing_audit_v2` and joins them
  per record.
* Classifies each report into one of 18 closed-set root-cause codes.
* Returns the operator's exact remediation step per record.

97 / 97 regression tests pass.

---

## DELIVERABLES

| Artefact | Path | Purpose |
|---|---|---|
| Forensic endpoint | `routes/admin_dr_delivery_forensics.py` | `GET /api/admin/daily-report-delivery/forensics` · admin-gated · read-only · per-record trace + closed-set classification. |
| Server wiring | `backend/server.py` (lines ~10851-…) | Registers the forensic router after the deployment ledger. |
| Regression suite | `tests/test_track_15_79b_dr_forensics.py` | 12 named gates (matrix below). |

---

## ENDPOINT CONTRACT

```http
GET /api/admin/daily-report-delivery/forensics
    ?since_hours={1..168}   default 36
    &project_number={str}   optional
    &limit={1..200}         default 50

X-Admin-Token: <super-admin token>   required
```

### Response (top-level)

```json
{
  "ok": true,
  "track": "15.79B",
  "generated_at": "2026-…",
  "since_hours": 36,
  "project_number_filter": null,
  "tenant_dead_letter_configured": true,
  "expected_stage_contract": [
    "record_created", "routing_resolved", "recipients_built",
    "notification_queued", "provider_accepted", "audit_written",
    "completed"
  ],
  "reports_found": …,
  "reports_with_pm_assignment": …,
  "reports_with_copm_assignment": …,
  "reports_with_pm_email_resolved": …,
  "reports_with_copm_email_resolved": …,
  "reports_with_recipients_built": …,
  "reports_with_send_attempt": …,
  "reports_with_provider_accept": …,
  "reports_dead_lettered": …,
  "reports_unconfigured": …,
  "reports_silent_failure": …,
  "reports": [ … ]
}
```

### Per-report row

* `report_id`, `doc_id`, `submitted_at`, `report_date`, `project_number`,
  `project_number_normalized`, `project_name`, `submitted_by`
* `job_master_match` — `{found, project_number, pm_email,
  project_manager, co_pm_emails}`
* `team_roster_match` — `{count_canonical, rows[], diagnostic_misses[]}`
  * `diagnostic_misses[]` flags `project_number_mismatch`,
    `role_name_mismatch`, `inactive_assignment` rows that exist but
    were silently excluded by the canonical query.
* `roster_query_used` — exact Mongo filter applied (for operator
  reproducibility)
* `pm_assignment`, `copm_assignments[]` — public-shape rows
* `pm_email_resolved`, `copm_emails_resolved[]` — after the email
  walk (email → user_directory → employees)
* `resolver_result` — `{pm_name, pm_email, co_pm_emails, to[], cc[],
  error}` — what the dispatcher would build right now
* `recipients_built` (bool), `expected_recipients[]`,
  `actual_recipients_count`
* `email_attempted`, `provider_accepted`,
  `resend_message_id_present`
* `email_routing_audit[]` — every matching audit row (ts, status,
  route_key, to_count, cc_count, subject, resend_message_id_present,
  error_present)
* `trust_spine_stages[]` — every Trust Spine event (ts, stage,
  status, module, failure_reason)
* `missing_stages[]` — stages from the contract that did not emit
* `failure_point` — single string for the dashboard
* **`root_cause_code`** — one of the closed-set codes below
* `operator_remediation` — exact action the operator should take
* `platform_fix_required` (bool) — whether the fault is in code,
  not data

---

## CLOSED-SET ROOT-CAUSE CODES (18)

| Code | Meaning |
|---|---|
| `ok_delivered` | Trust Spine `completed=ok` · `provider_accepted=ok` · audit row `status=sent` · ≥1 recipient · not dead-letter. |
| `dead_letter_only` | No PM resolved BUT `ADMIN_DEAD_LETTER_TO` configured — email went to office, not the assigned PM. (The likely production fault class.) |
| `project_number_mismatch` | Roster row exists but its `project_number` differs from the DR's after normalization. |
| `tenant_mismatch` | (Reserved · multi-tenant guard.) |
| `role_name_mismatch` | Roster row exists for the project but `assignment_role` is not `"pm"` or `"co_pm"`. |
| `inactive_assignment` | Roster row exists but `active=false`. |
| `primary_flag_mismatch` | PM row exists but `is_primary=false`. |
| `pm_identity_found_email_missing` | PM roster row exists but email walk (row → user_directory → employees) failed. |
| `copm_identity_found_email_missing` | Same, for Co-PMs. |
| `resolver_bypassed_roster` | `jobs_master.pm_email` returned a different address than the live Team Roster primary PM. |
| `recipients_empty` | Resolver returned zero recipients (no fallback). |
| `auto_email_not_scheduled` | `AUTO_EMAIL_REPORTS` disabled or `RESEND_API_KEY` missing — Trust Spine logged a `skipped` notification stage. |
| `dispatch_skipped` | `schedule_auto_email()` never invoked `_dispatch_auto_email`. |
| `provider_rejected` | Resend returned no `message_id`. |
| `audit_missing` | Trust Spine reported `provider_accepted=ok` but no audit row exists. |
| `trust_spine_missing_notification_stage` | `record_created` fired but the dispatcher never reached `recipients_built` (silent failure). |
| `dead_letter_unconfigured` | No PM resolved AND no `ADMIN_DEAD_LETTER_TO` — email went **nowhere**. |
| `unknown` | Cause not classifiable from available evidence. |

---

## GATE MATRIX — `test_track_15_79b_dr_forensics.py`

| # | Gate | What it locks |
|---|---|---|
| 1 | `test_endpoint_requires_admin` | Anonymous request returns 401/403. |
| 2 | `test_payload_shape_summary` | Response contains every required summary counter + `expected_stage_contract`. |
| 3 | `test_limit_max_enforced` | `since_hours` bounded `[1, 168]`, `limit` bounded `[1, 200]`. |
| 4 | `test_roster_pm_resolves_via_canonical_query` | Realistic schema PM assignment resolves to a recipient. |
| 5 | `test_roster_copms_resolve` | Two Co-PM rows are both surfaced + their emails resolved. |
| 6 | `test_role_name_mismatch_detected` | Diagnostic scan surfaces `assignment_role="Project Manager"` (wrong key) as `role_name_mismatch`. |
| 7 | `test_inactive_assignment_detected` | Diagnostic scan surfaces `active=false` rows as `inactive_assignment`. |
| 8 | `test_classifier_detects_missing_notification_stage` | When `record_created` fires but `recipients_built` is missing, classifier returns `trust_spine_missing_notification_stage`. |
| 9 | `test_classifier_provider_rejected` | When `provider_accepted=failed`, classifier returns `provider_rejected`. |
| 10 | `test_no_secrets_leak_in_payload` | Payload contains no `MONGO_URL`, `RESEND_API_KEY`, `re_*`, `ADMIN_PASSWORD`, `ADMIN_HMAC_SECRET`, `Bearer`, or `X-Admin-Token` substrings. |
| 11 | `test_endpoint_performs_no_writes` | Inserts one no-PM DR, counts documents in `email_routing_audit_v2`, `platform_audit`, `trust_spine_events`, `project_team_assignments`, `deployment_decisions` before + after one call — counts must be identical. |
| 12 | `test_classifier_dead_letter_only` | Closed-set `dead_letter_only` code is reachable from the classifier. |

---

## SECURITY REVIEW

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | admin auth required | ✅ | Gate 1 (anon → 401). |
| 2 | anonymous returns 401 | ✅ | Live preview probe `anon=401`. |
| 3 | no secrets leaked | ✅ | Gate 10 + live grep returned no marker hits. |
| 4 | no tokens leaked | ✅ | Gate 10 enumerates token markers. |
| 5 | no raw passwords | ✅ | Gate 10 enumerates `admin_password`. |
| 6 | no Mongo URLs | ✅ | Gate 10. |
| 7 | no Resend keys | ✅ | Gate 10. |
| 8 | no stack traces | ✅ | Resolver errors truncated to 200 chars; no Python tracebacks surfaced. |
| 9 | max limit enforced | ✅ | Gate 3 (`limit ≤ 200`, `since_hours ≤ 168`). |
| 10 | no writes | ✅ | Gate 11 counts five collections before/after; equal. |

---

## PREVIEW VERIFICATION

```bash
URL=https://safety-audit-mobile-1.preview.emergentagent.com
TOK=$(curl … multi-login … jaymn.judd@…)
curl -H "X-Admin-Token: $TOK" \
  "$URL/api/admin/daily-report-delivery/forensics?since_hours=72&limit=10"
```

**Result (preview pod):**
* `ok=true · track=15.79B`
* `reports_found=3 · all project 26-07 · root_cause_code=dead_letter_only`
* `pm_email_resolved=null` on all 3 (matches the operator-data
  advisory carried since Track 15.78).
* `reports_dead_lettered=3 · reports_unconfigured=0 ·
  reports_silent_failure=0`
* Anonymous probe → `HTTP 401`.
* Re-running the endpoint a second time produced no growth in
  `email_routing_audit_v2`, `platform_audit`, `trust_spine_events`,
  `project_team_assignments`, or `deployment_decisions`.

---

## PRODUCTION RUN INSTRUCTIONS

The endpoint is in the preview deploy now. To run it against
production:

1. **Save → Github → Redeploy** the platform so the endpoint is live
   at `https://mascidocs.com/api/admin/daily-report-delivery/forensics`.
2. Sign in at `https://mascidocs.com/sign-in` as the super admin.
3. Open a new tab → DevTools → Console → run:
   ```js
   fetch('/api/admin/daily-report-delivery/forensics?since_hours=36&limit=100', {
     headers: { 'X-Admin-Token': localStorage.getItem('masci.admin.token') }
   }).then(r => r.json()).then(d => console.log(JSON.stringify(d, null, 2)))
   ```
4. The JSON output names each tonight-submitted Daily Report with its
   `root_cause_code` and `operator_remediation`. Paste it back here
   and I will close out Phases 2 through 8 of Track 15.79B
   (root-cause confirmation, fix, regression locking).

No DevTools needed for daily ops once the operator wires the response
into the existing Operations Trust Center panel — the endpoint
returns structured JSON ready for the UI.

---

## SIX PILLARS

| Pillar | Status | Evidence |
|---|---|---|
| **Powerful** | ✅ | One endpoint joins five sources of truth and answers the exact incident question. |
| **Simple** | ✅ | GET + 3 query params. PASS/FAIL classification per record. |
| **Beautiful** | ✅ | Structured JSON ready for the OTC panel + operator_remediation per row. |
| **Trusted** | ✅ | Closed-set classifier · 12 named regression gates · no fake-green. |
| **Proven** | ✅ | Preview probe identified the 3 standing DRs and classified them as `dead_letter_only` — matches the operator's symptom precisely. |
| **Deployable** | ✅ | Additive · read-only · admin-gated · rollback = delete file + 4-line server.py block. |

---

## VERDICT

**🟢 GO (Phase 1 endpoint shipped)** — `GET /api/admin/daily-report-delivery/forensics`
is live in preview, regression-locked at 12 gates, admin-gated, read-
only, and surfacing the correct root-cause classification on the 3
existing preview DRs. Anonymous returns 401. Zero writes. Zero secret
leaks.

**Hard-rule compliance:**
* Endpoint admin-gated? ✅
* Endpoint mutates data? ✅ NO — Gate 11 proves zero writes.
* Endpoint leaks secrets? ✅ NO — Gate 10 + live grep.
* Endpoint can trace tonight's real Daily Reports after deploy? ✅
  Once redeployed to production, the operator runs one fetch call to
  obtain the per-report classification.

To proceed to Phases 2–8 (root-cause confirmation + fix +
regression-lock), the operator must redeploy production and paste the
production response JSON back into this thread.

— end of Track 15.79B Phase 1 —
