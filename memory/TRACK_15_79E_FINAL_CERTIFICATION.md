# TRACK 15.79E — CONTINUOUS PRODUCTION CERTIFICATION · FINAL CERTIFICATION

**Status:** ✅ COMPLETE — 🟢 GO (preview-side · awaiting one redeploy)
**Date:** 2026-06-25
**Scope:** Convert the Trust Center from a snapshot into a continuous,
self-certifying operational instrument. Every workflow automatically
gets a PROVEN / NOT-YET-EXERCISED / FAILED verdict derived from real
production lifecycle events. Operators never have to inject synthetic
records or run DevTools to know whether notifications are working.

---

## EXECUTIVE SUMMARY (plain English)

The platform now answers four questions automatically, with no
operator action:

* *Which workflows have been PROVEN end-to-end by real production
  traffic since the deploy?*
* *Which workflows haven't been used yet?* (informational — not a
  defect)
* *Which workflows failed?* (RED — and never auto-clears)
* *What's the exact remediation?* (operator-facing + engineering-facing
  per failure reason)

The verdict is derived from a single source of truth — the existing
`trust_spine_events` collection — so there is no dual-write, no
drift, and no separate "certification" state machine to maintain.
A workflow becomes VERIFIED **only** when its dispatcher actually
emits `completed/ok`. A workflow is RED **only** when its most
recent `completed` event is `status=failed`, and the RED never
auto-clears — a subsequent natural successful submission is the
only way to flip back to GREEN. This is the explicit anti-fake-green
guarantee.

---

## DELIVERABLES

| Artefact | Path | Purpose |
|---|---|---|
| Cert builder | `backend/lib/production_certification.py` | Pure-read function that aggregates `trust_spine_events` and returns per-workflow status + counters + remediation. |
| Cert endpoint | `backend/routes/admin_production_certification.py` | `GET /api/admin/production-certification` · admin-gated · read-only. |
| Server wiring | `backend/server.py` | Single `include_router` call after the deployment ledger + DR forensics routers. |
| Regression suite | `backend/tests/test_track_15_79e_production_certification.py` | 8 named gates (matrix below). |
| Gate integration | `scripts/deployment_gate.py` + `.github/workflows/sigma3-deploy-gate.yml` | New regression file added; no deploy can ship without it passing. |

---

## STATUS STATE MACHINE (closed set · 3 values)

| Status | When | Auto-clears? |
|---|---|---|
| **VERIFIED** | Most recent `completed` event for this workflow is `status=ok` | flips to FAILED on next `completed/failed` event |
| **FAILED** | Most recent `completed` event for this workflow is `status=failed` | **NEVER** — only a subsequent `completed/ok` flips back to VERIFIED |
| **NOT_YET_EXERCISED** | No `completed` event exists for this workflow | flips to VERIFIED or FAILED on first natural submission |

The RED-never-auto-clears rule is the hard guarantee. A defect that
once caused a failure stays surfaced until the platform PROVES it
was fixed through a fresh, real production submission. Gate 4 of
the regression suite (`test_failed_never_auto_clears_without_new_ok`)
locks this rule with synthetic events.

---

## ENDPOINT CONTRACT

```http
GET /api/admin/production-certification
X-Admin-Token: <super-admin>     # required (401/403 anonymous)
```

### Response

```jsonc
{
  "ok": true,
  "track": "15.79E",
  "generated_at": "2026-06-25T…",
  "platform_band": "red" | "amber" | "green",
  "counters": {
    "verified": 1, "failed": 0, "not_yet_exercised": 10, "total": 11
  },
  "workflows": [
    {
      "workflow": "daily-report",
      "status": "VERIFIED",
      "first_verified_at": "2026-06-25T10:12:29Z",
      "last_verified_at":  "2026-06-25T10:12:29Z",
      "successful_deliveries": 7,
      "failed_deliveries": 0,
      "last_failure": null,
      "last_failure_reason": null,
      "last_failure_record_id": null,
      "operator_remediation": null,
      "engineering_remediation": null,
      "regression_protected": true,
      "audit_row_observed": true
    },
    …
  ]
}
```

### Platform band rule

* `red`   — any workflow is FAILED
* `green` — at least one workflow is VERIFIED and none are FAILED
* `amber` — every workflow is NOT_YET_EXERCISED (fresh deploy)

Locked by Gate 8 of the regression suite.

---

## GATE MATRIX — `test_track_15_79e_production_certification.py`

| # | Gate | What it locks |
|---|---|---|
| 1 | `test_endpoint_requires_admin` | Anonymous returns 401/403. |
| 2 | `test_payload_shape` | Top-level `ok`, `track`, `counters{verified,failed,not_yet_exercised,total}`, `workflows[]`. Every workflow row carries the 12 required fields. Status is one of the closed-set 3. |
| 3 | `test_status_verified_requires_completed_ok` | Synthetic `completed/ok` + matching `audit_written/ok` event MUST produce `VERIFIED` and `audit_row_observed=true`. |
| 4 | `test_failed_never_auto_clears_without_new_ok` | **The core anti-fake-green rule.** An OLD `completed/ok` followed by a NEWER `completed/failed` MUST produce `FAILED` (older OK does NOT clear the newer failure). |
| 5 | `test_subsequent_ok_flips_failed_to_verified` | A `completed/failed` followed by a NEWER `completed/ok` MUST flip the workflow back to `VERIFIED`. |
| 6 | `test_not_yet_exercised_for_unused_workflow` | Every `WORKFLOW_EXPECTED_STAGES` key MUST appear in the response. Every status MUST be in the closed-set 3 (no accidental green). |
| 7 | `test_no_secrets_in_certification_payload` | No Mongo URIs · no `re_*` Resend keys · no Bearer tokens leak. |
| 8 | `test_platform_band_rules` | `red` iff any FAILED · `green` iff any VERIFIED and no FAILED · else `amber`. |

---

## OPERATOR REMEDIATION MAP

When a workflow is `FAILED`, the endpoint returns both an
operator-facing remediation (action they can take in the UI) and an
engineering-facing remediation (where to look in code). The map
covers the failure_reason patterns we know about today and falls
back to a generic message pointing at the DR Delivery Forensics
endpoint for anything new.

| failure_reason pattern | operator action | engineering action |
|---|---|---|
| `no recipients` | Assign a PM in Admin → People & Access (or set `ADMIN_DEAD_LETTER_TO`) | Inspect `pm_routing.resolve_pm_for_record_async` |
| `resend returned no message id` | Verify Resend API key + status page | Check `resend.Emails.send` return; verify SPF/DKIM |
| `auto-email disabled` | Set `RESEND_API_KEY` + `AUTO_EMAIL_REPORTS=true` in env | env var presence check at startup |
| `shop_recipient_unconfigured` / `pre_op_fail_fallback` | Assign Shop Manager role or set `PRE_OP_FAIL_FALLBACK` | Inspect `shop_users.list_shop_users` |
| `name '_wl' is not defined` | (none — engineering bug) | Inspect `pdf_render.py`; companion regression in `test_track_15_76_email_render_wl_regression.py` |
| anything else | Open Admin → DR Delivery Forensics for the matching report | Inspect backend logs around `failure_reason` ts |

---

## PREVIEW VERIFICATION

```
$ curl -H "X-Admin-Token: $TOK" \
    https://safety-audit-mobile-1.preview.emergentagent.com/api/admin/production-certification
HTTP 200
ok=true · track=15.79E · band=amber
counters={verified:0, failed:0, not_yet_exercised:11, total:11}

  daily-report           status=NOT_YET_EXERCISED  ok=0  fail=0
  meeting                status=NOT_YET_EXERCISED  …
  inspection             status=NOT_YET_EXERCISED  …
  incident               status=NOT_YET_EXERCISED  …
  jha                    status=NOT_YET_EXERCISED  …
  qaqc                   status=NOT_YET_EXERCISED  …
  equipment-inspection   status=NOT_YET_EXERCISED  …
  dvir                   status=NOT_YET_EXERCISED  …
  hr-request             status=NOT_YET_EXERCISED  …
  dispatch-assignment    status=NOT_YET_EXERCISED  …
  shop-defect            status=NOT_YET_EXERCISED  …

Anonymous probe: HTTP 401
Regression suite: 8 / 8 PASS in 5.24 s
Full Track 15.76-15.79E family: 112 / 112 PASS in 106.92 s
Trust Gate: decision=pass · exit_code=0 · 0 blocking · 0 advisory
```

(Preview has no `completed/ok` events yet — every workflow correctly
reports `NOT_YET_EXERCISED`, not green. No fake-green.)

---

## PRODUCTION RUN INSTRUCTIONS

The endpoint is in preview. To activate continuous certification
on `https://mascidocs.com`:

1. **Save → GitHub → Redeploy** the platform.
2. Call:
   ```bash
   curl -H "X-Admin-Token: $TOK" \
     https://mascidocs.com/api/admin/production-certification
   ```
3. Expected immediately post-redeploy:
   * `daily-report` → `VERIFIED` (the 10:12Z natural submission already
     completed end-to-end)
   * Every other workflow → `NOT_YET_EXERCISED`
4. As each remaining workflow gets its first natural production
   submission, it auto-flips to `VERIFIED` (or, if a defect surfaces,
   to `FAILED` with a named remediation). No operator action.

---

## ANSWERS TO THE FOUR PLATFORM-RULE QUESTIONS

> 1. **What has actually been proven in production?**
> Returned in `workflows[].status == VERIFIED`. As of preview build,
> production will report `daily-report = VERIFIED` immediately on
> redeploy (the 10:12Z natural submission). Every other workflow
> will report `NOT_YET_EXERCISED` until naturally exercised.
>
> 2. **What has not yet been exercised?**
> `workflows[].status == NOT_YET_EXERCISED`. Informational — not a
> defect.
>
> 3. **What failed?**
> `workflows[].status == FAILED`. RED never auto-clears.
>
> 4. **What was fixed?**
> The transition is observable: a workflow that was once FAILED and
> is now VERIFIED has both `last_failure` (historical timestamp +
> reason) AND `last_verified_at` (newer than the failure). The
> evidence chain is self-explanatory.

---

## SIX PILLARS

| Pillar | Status | Evidence |
|---|---|---|
| **Powerful** | ✅ | Continuous, real-evidence certification across all 11 workflows. Zero operator burden. |
| **Simple** | ✅ | One endpoint. Three statuses. No dual-write — derived purely from the existing `trust_spine_events` collection. |
| **Beautiful** | ✅ | Operator gets a one-glance table; each FAILED row carries a plain-English operator remediation + engineering remediation. No DevTools, no jargon. |
| **Trusted** | ✅ | 8 regression gates including the RED-never-auto-clears rule and the no-secrets rule. Closed-set status values. |
| **Proven** | ✅ | 112/112 family tests pass. Live preview endpoint returns the correct shape. Trust Gate exits 0. |
| **Deployable** | ✅ | Pure-read, additive, two new files + one server.py wiring line. Rollback = remove the include_router call. Wired into the Trust Gate as a required regression. |

---

## VERDICT

**🟢 GO — Track 15.79E continuous production certification is shipped
to preview, regression-locked at 8 gates, gate-passing, and ready
for one production redeploy.**

The platform is now self-certifying: as natural production traffic
flows through each workflow, the Trust Center automatically reports
which workflows have been PROVEN end-to-end versus which haven't yet
been exercised. Failures are surfaced loudly with named remediation
steps and **never auto-clear** until a fresh successful submission
proves the fix.

— end of Track 15.79E —
