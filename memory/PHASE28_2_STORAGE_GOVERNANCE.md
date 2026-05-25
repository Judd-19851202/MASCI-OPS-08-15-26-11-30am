# PHASE 28.2 · Storage Governance
## iter430 · 2026-05-25

## Endpoint
`GET /api/admin/operational-attachments/storage-summary`
- Admin-gated · JSON only · NO UI surface.
- Single Mongo round-trip via `$facet`.

## Response shape (Phase 28.2)
```jsonc
{
  "tenant_id": "masci",
  "total": 60,
  "r2_backed":      {"count": 60, "total_size_bytes": 12_345_678},
  "inline_b64":     {"count": 0,  "total_size_bytes": 0},
  "unknown":        {"count": 0,  "total_size_bytes": 0},
  "migrated_pct": 100.0,
  "avg_attachment_size_bytes": 205_761,
  "projected_90_day_growth": {
    "based_on_window_days": 30,
    "recent_window_count": 18,
    "recent_window_bytes": 3_703_222,
    "projected_count": 54,
    "projected_bytes": 11_109_666
  },
  "captured_at": "2026-05-25T18:00:00+00:00"
}
```

## Doctrine
- Calm prediction · NOT analytics. The 90-day projection is the
  rolling 30-day throughput × 3 — no smoothing, no decay. The
  operator owns the interpretation.
- Unknown bucket exists explicitly so the operator can spot
  data-shape anomalies (a row with neither `r2_key` nor `data_b64`
  is a bug to investigate, not a number to bury in a chart).

## Usage runbook
1. **Before a migration**
   ```bash
   curl -s "$API_URL/api/admin/operational-attachments/storage-summary" \
     -H "X-Admin-Token: $TOKEN" | jq
   ```
   Confirm `inline_b64.count > 0`.

2. **Run migration**: `scripts/migrate_attachments_to_r2.py --apply`

3. **After migration**
   - Re-fetch the endpoint.
   - `migrated_pct` should be `100.0`.
   - `inline_b64.count` should be `0`.
   - `unknown.count` should be `0` (any non-zero is an anomaly).

4. **Cost sanity-check**
   - Multiply `projected_90_day_growth.projected_bytes` by your R2
     `$/GB-month` rate. That's the worst-case storage growth bill
     for the next quarter, based on actual upload behaviour.
   - If the number doesn't match billing reality within ±20 %,
     someone is uploading off-platform — investigate.

## What this endpoint is NOT
- ❌ A dashboard
- ❌ A monitoring portal
- ❌ A "Storage Center"
- ❌ A live-graph
- ❌ A cost-projection tool with charts
