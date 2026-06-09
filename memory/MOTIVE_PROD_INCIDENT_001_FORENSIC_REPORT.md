# MOTIVE-PROD-INCIDENT-001 · FORENSIC REPORT

**Incident:** MOTIVE-PROD-INCIDENT-001 · Production Motive integration unreachable
**Sprint:** P0 production incident response
**Mode:** OMEGA · evidence-first · multi-source forensic audit
**Status:** ✅ FORENSIC PHASE COMPLETE

---

## PHASE 1 · FORENSIC VALIDATION

### Q1 · Motive credentials in PREVIEW (`masci_safety_preview`)
| Field | Value |
|---|---|
| status | Connected |
| enabled | true |
| demo_mode | true |
| created_at | 2026-05-26T10:56:42.369877+00:00 |
| updated_at | 2026-06-09T14:53:46.027312+00:00 |
| last_sync_at | 2026-06-08T15:48:17.236621+00:00 |
| last_successful_sync_at | 2026-06-08T15:48:17.236621+00:00 |
| api_key_value | `<36 chars · first4=5623 · last4=5fe6>` |
| webhook_secret_value | `<32 chars · first4=0043 · last4=c106>` |
| api_base | `https://api.gomotive.com` |
| webhook_url | `https://mascidocs.com/api/integrations/motive/webhook` |

### Q2 · Motive credentials in PRODUCTION (`masci_safety`) — **PRE-REMEDIATION**
| Field | Value |
|---|---|
| status | Not Connected |
| enabled | false |
| demo_mode | false |
| created_at | 2026-05-26T10:56:42.369877+00:00 |
| updated_at | **2026-05-26T10:56:42.369900+00:00** (identical to created — never touched) |
| updated_by | system |
| last_sync_at | null |
| last_successful_sync_at | null |
| api_key_value | (empty) |
| webhook_secret_value | (empty) |
| api_base | null |
| webhook_url | null |

### Q3 · Drift summary
| Aspect | Preview | Production (pre) | Drift |
|---|---|---|---|
| api_key_value | 36 chars present | empty | 🔴 missing |
| webhook_secret_value | 32 chars present | empty | 🔴 missing |
| enabled | true | false | 🔴 differs |
| api_base | set | null | 🔴 missing |
| webhook_url | set | null | 🔴 missing |
| `updated_by` | system | system | (both seed) |

### Q4 · Were production credentials ever populated?
**NO.** Direct evidence:
- `created_at == updated_at` (2026-05-26T10:56:42) on the prod motive row — single insert, no subsequent UPDATE.
- `updated_by == "system"` — no operator account ever modified the row.
- Zero rows in `masci_safety.admin_audit` matching `target=motive` or `action ~ integration` (re-verified pre-remediation).
- Restore drill snapshots from 2026-05-30 (`masci_restore_drill_2026_05_30`) and 2026-06-01 (`masci_restore_drill_auto_20260601_015003`) BOTH show the same empty seed row — confirming the empty state predates any deployment activity.

---

## PHASE 2 · WEBHOOK LOSS ASSESSMENT

| Q | Metric | Value |
|---|---|---|
| Q5 | Total Motive webhooks received by production | **41,139** |
| Q6 | Accepted | **0** |
| Q7 | Rejected | **41,139** (100%) |
| Q8 | First rejection timestamp | 2026-06-08T15:54:58.787466Z |
| Q9 | Most recent rejection (pre-remediation) | 2026-06-09T16:59:01.674932Z |
| Q10 | Current rejection rate (last 60 min before remediation) | 1,580 / hour |
| Q11 | Rejection reasons | 100% `"Awaiting Credentials"` · notes: `"Webhook hit with no secret configured."` |
| Q12 | Payloads stored | **NO.** `webhooks.py:48-58` short-circuits BEFORE the payload reaches storage. Only metadata in `integration_sync_logs` is retained (timestamp + status + notes). The raw HTTP body is held in process memory and discarded on response. No retention. Recovery from MASCI-side is **impossible** for the 41,139 lost payloads. |

### Per-hour distribution (PROD `integration_sync_logs`)
```
2026-06-08T15:    96   (incident begins · 15:54:58 first hit)
2026-06-08T16: 1,539
2026-06-08T17: 1,462
2026-06-08T18:   197
2026-06-08T19: 3,102
2026-06-08T20: 1,713
2026-06-08T21: 1,634
2026-06-08T22: 1,752
2026-06-08T23: 1,691
2026-06-09T00:   141
2026-06-09T01: 3,459   (peak hour)
2026-06-09T02: 1,724
2026-06-09T03: 1,698
2026-06-09T04: 1,655
2026-06-09T05: 1,620
2026-06-09T06: 1,623
2026-06-09T07: 1,518
2026-06-09T08: 1,668
2026-06-09T09: 1,476
2026-06-09T10: 1,710
2026-06-09T11: 1,713
2026-06-09T12:   196
2026-06-09T13: 3,091
2026-06-09T14:    78
2026-06-09T15: 3,071
2026-06-09T16: 1,318  (incident closes mid-hour at 16:59:03 remediation)
```

### Post-remediation signature anomaly (critical finding)
Once the webhook secret was restored, the receiver moved past the "Awaiting Credentials" short-circuit and reached the signature-verification step. Inspecting the next 10 webhook arrivals in production:

```
integration_error_logs[motive][webhook]
  occurred_at                       message                          details
  2026-06-09T17:00:17.669686+00:00  Invalid or missing signature     {'signature_present': False}
  ... × 10 entries, ALL with signature_present=False ...
```

**Interpretation:** Every incoming "webhook" arrived **without** an `X-Motive-Signature` header. Genuine Motive deliveries are always signed (HMAC-SHA256 hex of the raw body using the webhook secret — confirmed by `MOTIVE_M1_ACTIVATION_CERTIFICATION.md:84-87`). The absence of any signature header on the first 10 post-remediation arrivals strongly suggests the bulk of the 41,139 pre-remediation hits were **NOT genuine Motive webhook deliveries** but rather an unsigned automated traffic source (security scanner, misconfigured monitor, or an unidentified bot). The traffic also dropped from ~1,500/h to silence within minutes of the receiver beginning to issue HTTP 401, consistent with an automated client backing off on rejection rather than retrying.

**Caveat:** Cannot rule out from MASCI-side that *some* fraction of the 41,139 hits were genuine Motive deliveries that simply got mixed in with the noise. Confirmation requires inspecting Motive's outbound webhook delivery log in Motive Admin Dashboard.

---

## TIMELINE (verified facts)

| UTC | Event |
|---|---|
| 2026-05-26T10:56:42 | `integration_settings.motive` row seeded in both prod and preview DBs (`updated_by=system`, empty creds). |
| 2026-06-08T12:42 | **Operator pasted real Motive credentials** into the Admin Integration Center while logged into PREVIEW. Writes landed in `masci_safety_preview.integration_settings.motive`. M-1 sprint exercised the live API: 190 vehicles, 65 drivers, 67 geofences, 90 GPS events. |
| 2026-06-08T~15:00 | Production deployment / Motive webhook URL update to `https://mascidocs.com/...`. |
| 2026-06-08T15:54:58 | **Incident begins.** First webhook arrival at production endpoint, rejected. |
| 2026-06-08 → 2026-06-09 | Sustained ~1,500-3,500/hour rejection rate. All entries `"Awaiting Credentials"`. No payloads stored. |
| 2026-06-09T16:59:03 | **Production credentials restored** by this incident response (see remediation report). |
| 2026-06-09T17:03:40 | Manual sync run against prod: 190 vehicles, 65 drivers, 67 geofences imported (zero errors). |
| 2026-06-09T17:06:26 | Reliability supervisor + remediation update flips `last_successful_sync_at`. |

---

## EVIDENCE CITATIONS

- `masci_safety.integration_settings.motive` (direct find_one, pre-remediation): see §Q2
- `masci_safety_preview.integration_settings.motive` (direct find_one): see §Q1
- `masci_safety.integration_sync_logs` aggregate by hour/status/sync_type: see §Q5–Q11
- `masci_restore_drill_2026_05_30.integration_settings.motive` and `masci_restore_drill_auto_20260601_015003.integration_settings.motive`: both empty — confirms pre-existing empty state
- `MOTIVE_M1_ACTIVATION_CERTIFICATION.md:84-87` — signature scheme
- `MOTIVE_PRODUCTION_ACTIVATION_AUDIT.md` — prior live audit confirming preview webhook plumbing
- `routes/integrations/webhooks.py:48-58` — short-circuit code path (no payload storage on rejection)

— end of forensic report —
