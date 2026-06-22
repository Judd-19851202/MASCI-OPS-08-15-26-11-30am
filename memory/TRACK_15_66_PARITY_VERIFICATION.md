# TRACK 15.66 — Parity Verification (Phase 1)

**Date:** 2026-06-22 · post Phase-1 migrations  
**Harness:** `backend/scripts/track_15_65_parity_verify.py` (re-used unchanged from Track 15.65)

## 1. Result

```json
{
  "match": 19,
  "mismatch": 0,
  "skipped_no_legacy": 3,
  "critical_empty": 0
}
```

**19/19 routes match.** Zero mismatches. Zero critical routes resolving to an empty list under V2.

## 2. Why this matters after Phase 1 changes

Phase 1 added migration wrappers in three runtime modules (`outage_alerts.py`, `lib/field_submitter_identity.py`, `lib/operator_digest.py`) plus a new V2 admin endpoint surface in `server.py`. The wrappers each:

1. Construct a legacy_provider that returns the EXACT recipient the pre-Track-15.65 code returned.
2. Call `resolve_and_audit(...)` which short-circuits to the legacy provider when `EMAIL_ROUTING_V2=false`.
3. Wrap the resolver call in `try/except` so any resolver failure falls back to the legacy provider.

Parity proves the wrappers don't change recipients in either flag state.

## 3. Live endpoint smoke-test evidence

```
GET  /api/admin/email-routing/v2/routes        → tenant=masci count=19
GET  /api/admin/email-routing/v2/branding      → returns env-defaults doc
POST /api/admin/email-routing/v2/.../SAFETY_FORMS_TO/test {dry_run:true}
                                               → resolved.to=[safety@,jaymn@]
                                                 audit row written (status=dry_run)
GET  /api/admin/email-routing/v2/audit?route_key=SAFETY_FORMS_TO
                                               → count=1, first row matches the dry-run above
PUT  /api/admin/email-routing/v2/routes/SAFETY_FORMS_TO {description:"…"}
                                               → ok=true changed=true source=admin
```

## 4. What Phase 2 parity must additionally prove

* Admin UI edits propagate through the resolver (cache invalidation).
* Branding panel changes affect sender resolution at send time.
* Audit drawer shows the audit rows the API returns.
* Critical-route disable attempt is rejected by the PUT endpoint (already enforced server-side; UI must surface the error).

## 5. Hard-rule compliance (Phase 1 parity)
* ✅ No live emails sent during this verification.
* ✅ No critical route empty.
* ✅ Legacy behaviour preserved with flag OFF.
* ✅ V2 behaviour with flag ON matches DB doc.
* ✅ Track parity remains 19/19 after Phase 1 wrappers added.
