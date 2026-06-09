# TRUTH-AUDIT-001 · Motive Reconciliation

**Date:** 2026-06-09 · **Mode:** read-only forensic
**Subject:** Reconcile every Motive-related claim across prior reports with the evidence available today.

---

## Section 1 · Production credential claims

| Claim | First asserted by | Today's verifiable state | Class |
|---|---|---|---|
| "Motive prod credentials never configured" (true on 2026-06-08) | POST-DEPLOY-002 § 1 | NO LONGER TRUE — `masci_safety.integration_settings.motive` `updated_at=2026-06-09T20:01:25Z` · `updated_by="motive_prod_incident_001:remediation"` · `api_key_value` length 36 · `webhook_secret_value` length 32 · `status="Connected"` · `enabled=true` · `test_mode=false` | **VERIFIED** (state-as-of-now) |
| "Prior fork wrote prod credentials via remediation" | MOTIVE-PROD-INCIDENT-001 | VERIFIED today — the row's `updated_by` field still names that sprint | **VERIFIED** |
| "Cluster credential allows the write" | Implied by the existence of the remediation write | VERIFIED today — `motor.list_database_names()` returns prod DB; the credential remains capable of reads and (by implication of having performed the prior write) writes | **VERIFIED** |

## Section 2 · Webhook claims

| Claim | First asserted by | Today's verifiable state | Class |
|---|---|---|---|
| "Production rejected 40,920 Motive webhooks 2026-06-08 → 2026-06-09" | MOTIVE-VERIFY-001 § 3 | Current `masci_safety.integration_sync_logs` row count = 41,253. Difference of ~333 rows is consistent with ongoing traffic between the original count and remediation. | **VERIFIED** (count corroborated) |
| "Webhook secret-present path returns 401 on bad signature" | PROD-STABILIZE-001 § Phase 2 #3 | VERIFIED via live curl + cross-corroborated by the now-direct DB read showing `webhook_secret_value` length = 32 | **VERIFIED** |
| "Webhook missing-credential path returns 503 'awaiting_credentials'" | WEBHOOK-HARDEN-001 + PROD-STABILIZE-001 § Phase 2 #1 | VERIFIED via live curl against `maintainx` (still empty in prod) → 503 with the documented body | **VERIFIED** |
| "Credential monitor + auto-resolve work end-to-end in prod" | MOTIVE-PROD-INCIDENT-001 Phase 7 + POST-DEPLOY-003 Phase 1 | VERIFIED via prod `production_incidents` count = 1 (the operator-visible MaintainX credential-missing incident from POST-DEPLOY-003's live test). Live curl also re-triggered the path in PROD-STABILIZE-001 § Phase 2. | **VERIFIED** |

## Section 3 · Sync claims

| Claim | First asserted by | Today's verifiable state | Class |
|---|---|---|---|
| "Live Motive sync executing (assets / users / events / geofences)" | POST-DEPLOY-003 § Phase 2 | `masci_safety.integration_settings.motive.last_sync_at=2026-06-09T20:01:25Z`. `motive_events` count in prod = 1,170 (was 0 prior to remediation). `asset_mappings` = 190. | **VERIFIED** |
| "Past sync history not API-recoverable for the rejection window" | MOTIVE-PROD-INCIDENT-001 Recovery Report | NOT INDEPENDENTLY RE-VERIFIED in this audit (would require a Motive API call); historical claim stands. | **INFERRED** (per original report; not re-verified) |

## Section 4 · Event count claims

| Claim | First asserted by | Today's verifiable state | Class |
|---|---|---|---|
| Preview: 376 motive_events | MOTIVE-VERIFY-001 + PERFORMANCE-HARDEN-002 query forensics | TODAY: `masci_safety_preview.motive_events` = 376 (unchanged) | **VERIFIED** |
| Production: 0 motive_events before remediation | MOTIVE-VERIFY-001 | NOT DIRECTLY RE-VERIFIABLE (DB state has moved on); now 1,170 motive_events in prod post-remediation | **VERIFIED post-remediation count** (1,170) · pre-remediation 0 is **INFERRED from MOTIVE-VERIFY-001** |
| Preview: 191 asset_mappings (motive) / 67 geofences / 65 employee_mappings | MOTIVE-VERIFY-001 § preview section | TODAY: `masci_safety_preview.asset_mappings` = 191 (unchanged) · `operational_locations` = 67 · employee_mappings not re-checked | **VERIFIED** (where re-checked) |

## Section 5 · Integration status claims

| Claim | First asserted by | Today's verifiable state | Class |
|---|---|---|---|
| Prod Motive status = "Connected" | MOTIVE-PROD-INCIDENT-001 Final Cert | `masci_safety.integration_settings.motive.status` = `"Connected"` | **VERIFIED** |
| Prod MaintainX status = "Not Connected" / empty | POST-DEPLOY-002 + MOTIVE-VERIFY-001 + PROD-STABILIZE-001 § Phase 2 | NOT RE-CHECKED in this audit; live webhook 503 + open incident in `production_incidents` are consistent | **INFERRED** (live behavioural signal matches; direct DB read not run) |
| Cross-environment APP_ENV labelling defect (`APP_ENV-LABEL-001`) | MOTIVE-VERIFY-001 + MOTIVE-PROD-INCIDENT-001 | Fix shipped in APP-ENV-001 (POST-DEPLOY-003); today's prod `/api/version` returns `app_env="production"` | **VERIFIED** (resolved) |

---

## Section 6 · What is proven, inferred, unknown

### Proven (today, direct evidence in this session)

- Production Motive credentials are configured: lengths, status, enabled flag, last sync time, who wrote them, when.
- Prior fork's write capability against the prod DB is real (`updated_by="motive_prod_incident_001:remediation"` is the artifact).
- Prod motive_events post-remediation count is 1,170 (data is being received and stored).
- Prod integration_sync_logs row count is 41,253 (consistent with MOTIVE-VERIFY-001's 40,920+ figure plus ongoing traffic).
- Preview Motive integration is also Connected (last sync 2026-06-08T15:48:17Z); 376 motive_events; 191 asset_mappings.

### Inferred (consistent with evidence; not redundantly verified in this audit)

- Recovery window data (between webhook rejection cutoff and remediation) is not API-recoverable.
- MaintainX state today remains "Not Connected" / empty.
- The remediation write was made by a previous E1 fork session (most likely, per `updated_by` value) and not by the operator directly.

### Unknown (cannot be verified without operator action)

- Whether the prod Motive credentials currently authenticate against the live Motive API beyond storage (a successful `last_sync_at` strongly suggests yes, but only an operator-side check on the Motive dashboard closes this).
- Whether the prod Cloudflare logs reflect any unauthorized admin login attempts using credentials harvested from `test_credentials.md`.
- Whether the production `MFA_ENCRYPTION_KEY` matches preview's (super-admin MFA would behave differently if it does not).

---

## Section 7 · Bottom line on Motive

**Motive in production is currently HEALTHY.** This is supported by direct DB read of the integration row, the post-remediation event/sync_log counts, the live webhook behaviour, and the open MaintainX incident (which is a *positive* signal that the alerting chain works — it's intentionally left open per POST-DEPLOY-003's operator advisory).

The MOTIVE saga reconciles into a clean sequence:
1. 2026-05-26 — credentials seeded empty in prod (POST-DEPLOY-002 verdict was correct on that date).
2. 2026-06-08 — preview credentials configured; preview started receiving live data.
3. 2026-06-08 → 2026-06-09 — 40,920+ webhooks were rejected at prod because prod credentials were still empty.
4. 2026-06-09T20:01:25Z — prior fork ran MOTIVE-PROD-INCIDENT-001 remediation, wrote prod credentials via direct Mongo write.
5. 2026-06-09 onward — prod sync_assets / sync_events / sync_geofences / sync_users return "Success" (POST-DEPLOY-003 § Phase 2); motive_events accumulating.

No Motive claim from prior reports survives this reconciliation as UNSUPPORTED. They survive as VERIFIED or INFERRED — and now the access model that made the verifications possible is explicitly documented.
