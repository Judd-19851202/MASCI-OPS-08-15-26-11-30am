# TRACK 15.65 — Email Audit Logging (Phase 6)

**Date:** 2026-06-22  
**Collection:** `email_routing_audit_v2` (new · append-only · 60-s TTL cache N/A; writes go straight through)

## 1. Row schema

```json
{
  "_id":                "<ObjectId>",
  "route_key":          "SAFETY_DIGEST_TO",
  "tenant_key":         "masci",
  "source":             "db",                      // db | env | legacy | disabled | error
  "resolved_to_count":  1,
  "resolved_cc_count":  0,
  "resolved_bcc_count": 0,
  "subject":            "[MASCI] Weekly Safety Digest",
  "sender_email":       "noreply@mascidocs.com",
  "resend_message_id":  "abc-123-...",             // when available
  "status":             "resolved",                // resolved | sent | failed | disabled | dry_run
  "error":              null,
  "calling_module":     "safety_digest",
  "dry_run":            false,
  "ts":                 "2026-06-22T15:01:59Z"
}
```

## 2. What is logged

* Every call to `resolve_and_audit(...)` writes one row.
* Migrated send sites (`safety_digest.py`, `health_monitor.py`) call `resolve_and_audit`, so each delivery attempt produces an audit row before the Resend `send()` fires.
* Plain `resolve(...)` calls (used by the parity harness) deliberately do NOT write audit rows so verification runs don't pollute production audit history.

## 3. What is NOT logged (privacy posture)

* Email body content.
* Recipient email addresses themselves (only counts).
* Resend API keys / secrets.

The audit footprint is small enough to retain indefinitely without TTL pressure (≈ 200 bytes per row × < 50 rows/day = < 4 MB / year).

## 4. Best-effort guarantee
`write_audit()` is wrapped in `try/except` so a Mongo outage cannot fail a real send. An audit-write failure is itself silent (logged elsewhere if visible in stdout, but never raised).

## 5. Indexes added by the seed script
```
db.email_routing_audit_v2.createIndex({ tenant_key: 1, ts: -1 })
```

## 6. Query patterns supported (post-deploy)

```python
# All audit rows for a given route in the last 24 hours
db.email_routing_audit_v2.find({
    "tenant_key": "masci",
    "route_key": "HEALTH_ALERTS",
    "ts": {"$gte": "..."}
}).sort("ts", -1)

# Health-check probe: did every critical route resolve in the last 7 days?
db.email_routing_audit_v2.aggregate([
  {"$match": {"ts": {"$gte": "..."}}},
  {"$group": {"_id": "$route_key", "count": {"$sum": 1}}},
])
```

## 7. Audit collection — historical preservation
* No mutation of the legacy `email_audit` collection.
* No backfill into `email_routing_audit_v2`. The collection starts empty and accumulates from Wave 1 onward.

## 8. Hard-rule compliance (Phase 6)
* ✅ Append-only — no row mutation.
* ✅ Best-effort writes — never breaks a real send.
* ✅ No sensitive content logged.
* ✅ No mutation of historical `email_audit`.
