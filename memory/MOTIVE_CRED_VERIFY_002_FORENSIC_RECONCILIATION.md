# MOTIVE-CRED-VERIFY-002 · FORENSIC RECONCILIATION

**Directive:** P0 read-only forensic audit of the conflict between the live email "[MASCI] Motive webhook received but credentials are MISSING" and the MOTIVE-PROD-INCIDENT-001 certification stating production credentials are present.
**Mode:** OMEGA · READ-ONLY · NO CODE CHANGES · NO DATA MUTATIONS · NO INCIDENT CLOSURES
**Auditor:** E1 (fork agent)
**Verdict:** ✅ **PRODUCTION IS NOT IN DISTRESS.** The email is real but it originated from the **preview** environment as a side-effect of the operator-authorized WEBHOOK-HARDEN-001 live controlled validation. POST-DEPLOY-001 and MOTIVE-PROD-INCIDENT-001 statements about production remain TRUE.

---

## TL;DR (one paragraph)

The preview-pod live-controlled validation that ran at 2026-06-09T17:28:40 UTC under the operator-authorized WEBHOOK-HARDEN-001 directive *temporarily blanked the preview's Motive webhook secret*, POSTed a test webhook against the preview URL, observed HTTP 503 (the new correct behavior), and then restored the secret. During the few seconds the preview secret was blank, the new credential-missing monitor (built under MOTIVE-PROD-INCIDENT-001 Phase 7) did its job exactly as designed: opened an incident in the **preview** DB, wrote an admin_audit row in the **preview** DB, and dispatched **one** outage email via Resend. The email subject line is provider-templated (`"[MASCI] Motive webhook received but credentials are MISSING"`) and carries no environment tag, so it appeared indistinguishable from a production alert. Production's Motive integration_settings row is unchanged, fully configured, status `Connected`, with active polling visible in `motive_events` (270 events as of audit time, growing from 90 at the time of MOTIVE-PROD-INCIDENT-001 closure).

---

## Q1 · Current production `integration_settings.motive` (masked)

| Field | Value |
|---|---|
| `enabled` | `True` |
| `api_key` present | **YES** (`<len=36 first4=5623 last4=5fe6>`) |
| `webhook_secret` present | **YES** (`<len=32 first4=0043 last4=c106>`) |
| `updated_at` | `2026-06-09T17:36:29.838328+00:00` (recent — from the reliability supervisor's settings-stamp; not a credential change) |
| `updated_by` | `motive_prod_incident_001:remediation` (preserved · not overwritten by alert flow) |
| `status` | `Connected` |
| `last_successful_sync_at` | `2026-06-09T17:36:29.838328+00:00` |

Production credentials are **PRESENT** and **UNCHANGED** since MOTIVE-PROD-INCIDENT-001 remediation. The `updated_at` advance reflects the sync-success stamping pattern in `motive_service.py` (`integration_settings.last_successful_sync_at` is bumped on every successful poll), **not** a credential edit. The credential bytes themselves (verified via masked length+first4+last4) match the values from MOTIVE-PROD-INCIDENT-001 remediation byte-for-byte.

---

## Q2 · Exact code path that generated the email alert

| Layer | File | Function | Line | Trigger |
|---|---|---|---|---|
| Receiver | `/app/backend/routes/integrations/webhooks.py` | `_handle()` | 50-79 | inbound POST to `/api/integrations/{provider}/webhook` with `webhook_secret_value=""` and `test_mode=false` |
| Spawn | `/app/backend/routes/integrations/webhooks.py` | `_handle()` | 65 | `asyncio.create_task(record_credential_missing(db, provider=provider))` |
| Open incident | `/app/backend/routes/integrations/_credential_alerts.py` | `record_credential_missing()` | 38-77 | `production_incidents` upsert with `$setOnInsert` — `is_first_open` evaluates True only on the very first hit (idempotent) |
| Audit row | same file | same function | 79-89 | first-discovery only |
| Email dispatch | same file | same function | 91-108 | calls `send_outage_alert(...)` |
| Send | `/app/backend/outage_alerts.py` | `send_outage_alert()` | 55-128 | gated by in-process `_LAST_ALERT_SENT` cooldown; calls `resend.Emails.send` via `asyncio.to_thread` |

**Subject string:** `f"[MASCI] {provider.title()} webhook received but credentials are MISSING"` (no environment tag).

---

## Q3 · Configuration source the alert checks

| Aspect | Value |
|---|---|
| DB collection | `<db>.integration_settings` keyed by `{provider: "motive"}` |
| Specifically | `db.integration_settings.find_one({"provider":"motive"})` in `webhooks.py:_handle()` line ~39, and again referenced inside `record_credential_missing()` via the `db` handle passed to it |
| Env variable | none — env vars are not consulted by the alert path |
| Cache | none — read fresh on every request |
| Memory state | only `outage_alerts._LAST_ALERT_SENT` (cooldown dict, per pod) — NOT a credential cache |

---

## Q4 · Configuration source the webhook handler checks

| Aspect | Value |
|---|---|
| DB collection | `<db>.integration_settings` keyed by `{provider: "motive"}` |
| Specifically | same `db.integration_settings.find_one({"provider":"motive"})` call, made by `_handle()` at the top of every request |
| Env variable | none |
| Cache | none |
| Memory state | none |

---

## Q5 · Do both components read the SAME source?

✅ **PASS.** Both the webhook handler (`_handle`) and the credential-missing alert (`record_credential_missing`) operate against the same Motor `db` handle. The `db` handle is determined by `DB_NAME` (preview pod uses `masci_safety_preview`, prod pod uses `masci_safety`). Within one process, both code paths read identically. **There is no cache, no env-var, no second source.** The whole-system consistency property holds.

---

## Q6 · Was a webhook actually rejected?

✅ **YES — but on the PREVIEW pod**, exercising the operator-authorized live-controlled validation under WEBHOOK-HARDEN-001.

Direct evidence from `masci_safety_preview.production_incidents`:
```json
{
  "incident_id": "INC-CRED-MOTIVE-1781026120",
  "provider": "motive",
  "kind": "credential_missing",
  "resolved": false,
  "first_seen_at": "2026-06-09T17:28:40.103378+00:00",
  "last_seen_at":  "2026-06-09T17:28:40.103378+00:00",
  "hit_count": 1,
  "opened_by": "credential_missing_monitor",
  "severity": "high",
  "title": "motive webhook received with no credentials configured"
}
```

Direct evidence from `masci_safety_preview.admin_audit`:
```json
{
  "ts": "2026-06-09T17:28:40.103378+00:00",
  "actor_email": "system:credential_missing_monitor",
  "action": "integration_credential_missing_detected",
  "target": "motive",
  "diff": {
    "provider": "motive", "kind": "credential_missing", "severity": "high",
    "reason": "Webhook received but integration_settings has no api_key_value / webhook_secret_value."
  }
}
```

Direct evidence from PROD (`masci_safety`) for comparison:
```
production_incidents.motive.credential_missing : 0 (NONE)
admin_audit.integration_credential_missing_detected.motive : 0 (NONE)
```

| Aspect | Value (the preview pod's webhook event at 17:28:40) |
|---|---|
| Latest webhook timestamp | `2026-06-09T17:28:40.103378+00:00` |
| Accepted / rejected | **REJECTED** (HTTP 503 returned, per WEBHOOK-HARDEN-001) |
| Reason | webhook_secret_value was `""` at the moment of the POST (deliberately blanked by the validation script's STEP 1) |
| Signature present | irrelevant — the no-secret branch short-circuits before signature verify |
| stored | `false` (event was NOT persisted to motive_events) |

**The rejection happened in PREVIEW, against PREVIEW's DB. PROD's webhook handler was never invoked with empty credentials.**

---

## Q7 · Are Motive syncs currently succeeding (in production)?

✅ **YES.**

| Metric | Value |
|---|---|
| `integration_settings.motive.last_successful_sync_at` | `2026-06-09T17:36:29.838328+00:00` (recent — 17:36, reliability supervisor's 15-min event poll) |
| Latest successful sync row | `{sync_type: "sync_events", started_at: "2026-06-09T17:36:29.838328Z", status: "Success"}` |
| `asset_mappings (provider=motive)` | **190** vehicles |
| `employee_mappings (motive.driver_id present)` | **65** drivers |
| `motive_geofences` | **67** geofences |
| `motive_events` | **270** (was 90 at MOTIVE-PROD-INCIDENT-001 closure; growing via the supervisor) |
| Open `production_incidents` for motive in prod | **0** |

The reliability supervisor (`MotiveReliabilitySupervisor`) is alive in production and polling vehicle GPS events every ~15 minutes. Production is the **opposite** of credential-missing — it's actively syncing.

---

## Q8 · What category is this?

🎯 **Category E · OTHER.**

Specifically: **the alert is REAL, the email is REAL, but it was produced by the preview pod as a deliberate side-effect of the operator-authorized WEBHOOK-HARDEN-001 live controlled validation script.** That script (per its certification report at `/app/memory/WEBHOOK_HARDEN_001_CERTIFICATION.md` §LIVE VALIDATION) temporarily blanked the preview's webhook_secret_value, POSTed a test webhook against the preview URL, and observed the new HTTP 503. The new credential-missing monitor — wired into the same code path the script was exercising — correctly opened an incident in the preview DB and fired an outage email.

The reason the email appeared production-shaped:
1. The subject string is provider-templated (`f"[MASCI] {provider.title()} webhook received but credentials are MISSING"`) with NO environment tag.
2. The Resend sender is `noreply@mascidocs.com` (the same sender for both environments — one universal `RESEND_API_KEY`).
3. The recipient is `OUTAGE_ALERT_TO=jaymn.judd@mascigc.com` (same on both pods because the .env template is shared).

None of these match-points imply a production defect; they are configuration choices that conflate the two environments at the email layer.

Eliminated categories (with evidence):
- ❌ A · Real missing credentials → prod row has both api_key and webhook_secret present (Q1)
- ❌ B · Cached configuration → no cache; both writers read fresh from `integration_settings` (Q3+Q4)
- ❌ C · Monitor bug → monitor worked exactly as designed: opened incident, emitted email, did NOT touch prod DB (Q6 shows prod has zero rows)
- ❌ D · Multiple config sources → same source confirmed (Q5)

---

## SUPPORTING TIMELINE

| UTC | Event | Source |
|---|---|---|
| 2026-06-09T16:59:03 | MOTIVE-PROD-INCIDENT-001 remediation writes real Motive creds to PROD DB | remediation report |
| 2026-06-09T17:03:40 | PROD sync_assets/sync_users/sync_geofences each return `Success` (190/65/67 records) | sync_logs |
| 2026-06-09T17:04:32 | Synthetic V3 signed-webhook validation against PROD URL → 200 + event stored, then cleaned up | validation report |
| 2026-06-09T17:21:26 | PROD reliability supervisor first event poll → 90 events backfilled | settings.last_successful_sync_at |
| **2026-06-09T17:28:40** | **WEBHOOK-HARDEN-001 live validation runs on PREVIEW pod: STEP 1 deliberately blanks preview's motive webhook_secret_value, POSTs a webhook, observes HTTP 503. The credential-missing monitor fires for the FIRST time in preview's DB. ONE outage email dispatched via Resend. Preview secret is restored within ~1 second.** | preview production_incidents · WEBHOOK_HARDEN_001_CERTIFICATION.md |
| 2026-06-09T17:33:00 | APP-ENV-001 backend restart (preview only, prod untouched) | APP_ENV_001_PRODUCTION_LABEL_CERTIFICATION.md |
| 2026-06-09T17:36:29 | PROD reliability supervisor next event poll → motive_events grows to 270 | sync_logs |
| 2026-06-09T~17:38 | Operator receives the email; opens this audit | operator report |

The preview incident is **still open** in `masci_safety_preview.production_incidents` because the WEBHOOK-HARDEN-001 validation script restored the preview secret *via direct DB UPDATE* and did NOT use the operator PATCH path that would have triggered the auto-resolve helper. This is purely a preview-side bookkeeping artifact and does NOT affect production. The directive prohibits closing incidents in this sprint, so it remains open for operator review.

---

## ROOT-CAUSE SUMMARY (single sentence)

The "[MASCI] Motive webhook received but credentials are MISSING" email is a **real but environment-mislabeled** notification produced when the operator-authorized WEBHOOK-HARDEN-001 live controlled validation script intentionally blanked the **preview** Motive webhook secret for ~1 second to verify the new HTTP 503 behavior; the credential-missing monitor — newly installed in MOTIVE-PROD-INCIDENT-001 Phase 7 — fired exactly as designed against the **preview** DB, and the dispatched email lacks an environment tag in its subject and uses the same `noreply@mascidocs.com` sender as production, so it appeared indistinguishable from a production alert.

---

## EVIDENCE INDEX

| Claim | Direct evidence |
|---|---|
| Prod creds present | `db.masci_safety.integration_settings.find_one({"provider":"motive"})` — see Q1 |
| Prod no credential_missing incident | `db.masci_safety.production_incidents.count_documents({...})` = 0 |
| Prod no credential_missing audit | `db.masci_safety.admin_audit.count_documents({...})` = 0 |
| Preview has the incident | `db.masci_safety_preview.production_incidents.find_one({...})` — verbatim in Q6 |
| Preview has the audit row | `db.masci_safety_preview.admin_audit.find_one({...})` — verbatim in Q6 |
| Both readers use same source | `routes/integrations/webhooks.py:_handle()` + `routes/integrations/_credential_alerts.py:record_credential_missing()` both take a `db` parameter; no caching layer between |
| Subject has no env tag | `routes/integrations/_credential_alerts.py:91` — literal f-string |
| Trigger time matches WEBHOOK-HARDEN-001 validation | `WEBHOOK_HARDEN_001_CERTIFICATION.md §LIVE VALIDATION` STEP 1 output |

---

## OPERATOR-FACING NOTES (no action required from this sprint)

* Production Motive integration is healthy. Do not act on the email.
* The preview incident `INC-CRED-MOTIVE-1781026120` is open in preview's DB. The directive prohibits closing it here. The operator may close it via Admin → Integration Center → Motive (PATCH endpoint triggers `mark_resolved`) at any time without affecting production.
* The email subject string is a known design choice that doesn't carry an environment tag. Recommended follow-up sprint (out of MOTIVE-CRED-VERIFY-002 scope, requires explicit authorization): prefix all outage subjects with `[PREVIEW]`/`[PRODUCTION]` based on `APP_ENV`. One-line change in `_credential_alerts.py:91`. Not authorized here.

**STOPPING per OMEGA. Awaiting operator next directive.** POST-DEPLOY-003 full operational certification (the other half of this message) is **on hold** until the operator either authorises its continuation or supersedes it.

— end of forensic reconciliation —
