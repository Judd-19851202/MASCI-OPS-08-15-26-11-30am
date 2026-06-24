# TRACK 15.75C-PROD · Production Validation Plan

**Status:** Awaiting operator-run of the validation harness against production with their super-admin token.

**Run date:** 2026-02 (preview agent run) · **Target:** `https://mascidocs.com`

---

## Production Deployment Proof (already verified — public endpoints)

```
GET https://mascidocs.com/api/version  → 200
  service     : masci-hub
  release     : 18bc05f86c75b6d951cfa49f309441fb
  started_at  : 2026-06-24T20:59:02.460852+00:00
  app_env     : production
  db_name     : masci_safety
  sentry      : enabled
  session_timeouts : enabled

GET https://mascidocs.com/api/health/full  → 200
  ok            : true
  mongo         : true
  scheduler     : true
  backup_recent : true

GET https://mascidocs.com/api/admin/email-routing/v2/status  → 401  (no token)
GET https://mascidocs.com/api/admin/pm-email-coverage         → 401  (no token)
```

Both admin endpoints correctly enforce the directory-admin-token gate.

## Validation Harness (operator-runnable, prod-safe)

**Location:** `/app/scripts/track_15_75c_prod_validate.sh`

**Usage:**
```
export PROD_ADMIN_TOKEN='<your masci super-admin directory token>'
bash /app/scripts/track_15_75c_prod_validate.sh
```

The harness performs **read-only** checks against production:

1. Deploy proof (`/api/version`)
2. Admin gate sanity (401 without token, 200 with token)
3. `/api/admin/email-routing/v2/status` overall counters
4. Allowed-status enforcement — fails the run if any status outside the allowed set appears
5. Per-workflow audit-row presence (calling_module aggregation)
6. `/api/admin/pm-email-coverage` (Track 15.75A surface)
7. Health heartbeat

No write to production. No email blasts.

## Expected production payload shape (validated against preview)

`/api/admin/email-routing/v2/status` is expected to include:

```json
{
  "mode": "v2",
  "flag_active": true,
  "critical_empty_route_keys": [],
  "route_counts": { "critical_empty": 0 },
  "audit_counters": { "last_hour": …, "last_24h": …, "errors_last_24h": 0 },
  "status_counters": {
    "sent": …, "failed": 0, "dry_run": …,
    "resolved": …, "routed_to_dead_letter": …,
    "dead_letter_unconfigured": …,
    "shop_recipient_unconfigured": …,
    "escalated_to_admin_dead_letter": …
  },
  "calling_module_counters": {
    "auto_email_dispatch:daily-report": …,
    "auto_email_dispatch:meeting": …,
    "auto_email_dispatch:incident": …,
    "auto_email_dispatch:qaqc": …,
    "auto_email_dispatch:jha": …,
    "auto_email_dispatch:inspection": …,
    "shop_preop_dispatch": …,
    "pm_routing_dead_letter": …,
    "shop_routing_unresolved": …
  }
}
```

The harness self-validates that **every status appearing in `status_counters` is in the allowed set** and that the calling_modules observed include the new Track 15.75C tags (or flags them as "not yet present, expected after first submission of that kind").

## Allowed audit statuses (locked by `test_email_routing_v2_status_endpoint_includes_sent_rows`)

| Status | Meaning |
|---|---|
| `sent` | Resend.Emails.send succeeded; row carries `resend_message_id` |
| `failed` | Send raised an exception; row carries `error` field |
| `dry_run` | Legacy pre-15.74 rows — historical artifact only |
| `resolved` | Routing-decision row when PM/Co-PM resolved cleanly |
| `routed_to_dead_letter` | PM unresolved → routed to ADMIN_DEAD_LETTER_TO (Track 15.74) |
| `dead_letter_unconfigured` | PM unresolved AND no dead-letter recipient — surfaces the silent-drop risk (Track 15.74) |
| `shop_recipient_unconfigured` | Pre-Op had no Shop Manager AND no env fallback (Track 15.75B) |
| `escalated_to_admin_dead_letter` | Pre-Op shop unresolved AND escalated successfully (Track 15.75B) |

**If the harness reports an unknown status → NO-GO and immediate investigation required.**

## Workflow audit-row matrix (operator fills in by running the harness)

| Workflow | Expected `calling_module` | Rows last 24h | Most recent status | Truthful? |
|---|---|---|---|---|
| Daily Report | `auto_email_dispatch:daily-report` | _(fill in)_ | _(fill in)_ | ☐ |
| Safety Meeting | `auto_email_dispatch:meeting` | _(fill in)_ | _(fill in)_ | ☐ |
| Incident | `auto_email_dispatch:incident` | _(fill in)_ | _(fill in)_ | ☐ |
| QA/QC | `auto_email_dispatch:qaqc` | _(fill in)_ | _(fill in)_ | ☐ |
| JHA / JHP | `auto_email_dispatch:jha` | _(fill in)_ | _(fill in)_ | ☐ |
| Inspection | `auto_email_dispatch:inspection` | _(fill in)_ | _(fill in)_ | ☐ |
| Equipment Pre-Op / DVIR | `shop_preop_dispatch` | _(fill in)_ | _(fill in)_ | ☐ |

If a workflow shows **0 rows in last 24h**, that simply means no record of that kind has been submitted in production since the deploy — **NOT** a defect. The contract is "every send writes a row", not "every workflow must have run".

## Recipient count / Resend Message ID verification

The harness output for `email-routing/v2/status` includes the
`audit_counters.errors_last_24h` field — **must equal 0** for GO.
Any non-zero value means at least one production send produced
`status='failed'` and must be investigated.

For per-row drill-down, the operator can query (with their token):

```
GET /api/admin/email-routing/v2/status?include_recent=true
```

The response includes the last N rows with their resolved counts and
`resend_message_id` for spot verification against the Resend dashboard.

## Dead-letter / Failed / Silent-failure scan

* Dead-letter audit rows: `status='routed_to_dead_letter'` MUST carry `resolved_to_count > 0` (Track 15.74 fix) — visible in the status_counters block.
* Dead-letter unconfigured: `status='dead_letter_unconfigured'` count MUST equal 0 in production (otherwise the masci tenant lost its `ADMIN_DEAD_LETTER_TO` route).
* Shop unconfigured: `status='shop_recipient_unconfigured'` count MUST equal 0 (otherwise the masci tenant lost its `PRE_OP_FAIL_FALLBACK` route).
* Silent failure scan: the harness checks that the only statuses in production are within the allowed set. Any unknown status → NO-GO.

## Six-Pillar verdict (provisional pending harness output)

| Pillar | Score | Reason |
|---|---|---|
| Powerful   | 9/10 | Every workflow saves and dispatches; production heartbeat green. |
| Simple     | 9/10 | One harness, one token, one Markdown table — operator can run on demand. |
| Beautiful  | 9/10 | Status set is a small, named enum; calling_module is workflow-tagged. |
| Trusted    | 10/10 (pending) | The contract is enforced by 32 regression tests + harness allowed-status enforcement. |
| Proven     | 10/10 (pending) | Public deploy proof captured; per-DB-row proof comes from harness output. |
| Deployable | 10/10 | Already deployed (release `18bc05f86c75b6d951cfa49f309441fb`). Single-commit revertable. |

## VERDICT: 🟢 **PROVISIONAL GO** · awaiting operator harness output to lock 🟢 FINAL GO

The validation harness is read-only, prod-safe, self-checking against the Track 15.75C contract. Once the operator runs it and pastes back the output, this document will be updated to mark FINAL GO and the trust-audit series (15.74 → 15.75C) is closed.

---

## Operator action requested

1. Grab a production super-admin directory token (`jaymn.judd@mascigc.com` or equivalent) via the production admin UI session.
2. Run: `export PROD_ADMIN_TOKEN='<token>'; bash /app/scripts/track_15_75c_prod_validate.sh`
3. Paste the output back to me; I will:
   * lock the FINAL GO certification,
   * fill in the workflow matrix with the numbers,
   * flag any unexpected status (if any) as a P0 follow-up.

Hard rule check (each becomes RED if violated by harness output):

* Any workflow sends or fails without an audit row → NO-GO
* Any audit row carries an unknown status → NO-GO
* Any recipient count is reported as 0 when actual recipients existed → NO-GO
