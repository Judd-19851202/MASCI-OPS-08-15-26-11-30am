# TRACK 23.4 — DAILY REPORT V3 DEFAULT CUTOVER

**Status:** 🟢 SHIPPED (2026-02-06 17:46 UTC)
**Mandate:** V3 is the production default. Not a pilot. Not experimental. V1 remains only as emergency rollback.

---

## Cutover event

Single API call. No Mongo hand-edit. Zero source-code deploy required for the cutover itself.

```
POST /api/admin/dr-v3-flag/tenant-default
Headers: X-Admin-Token: <admin-token>
Body:    {"enabled": true}
```

Response captured:
```
{"ok":true,"tenant_default":true}
```

Anonymous flag check confirms V3 is now the default for every unauthenticated visitor:
```
GET /api/feature-flags/dr-v3
→ {"enabled":true, "source":"tenant_default", "scope":"tenant", ...}
```

Also removed the "V3 Pilot" label from the shell header per operator directive ("no pilot language"). Header now reads plain **"MASCI · Daily Job Report"**.

## Certification (live evidence)

| Check | Result |
|---|---|
| `/daily/new` no-query → V3 renders | ✅ `[data-testid=dr-v3-form]` present · h1 = "Today's report" |
| Autosave pill visible on load | ✅ `[data-testid=dr-v3-draft-pill]` = "Autosave on" |
| Mobile 390 no horizontal scroll | ✅ verified via screenshot |
| Rollback flip (`tenant_default=false`) → V1 renders | ✅ `has_v3=0` · h1 = "Daily Job Report" · draft restore prompt visible |
| Restore production state (`tenant_default=true`) | ✅ V3 renders again with no query string |
| Submit endpoint unchanged | ✅ `POST /api/daily-reports` — same route V1 used |
| Notifications / ODS / Trust Spine / PDF / auto-email | ✅ unchanged (same insert path, same emitters) |
| Cost-code selector hidden when absent | ✅ Track 23.1 lock re-verified |
| Photo intelligence pipeline | ✅ Track 22.9B lock re-verified |
| AI summary single card | ✅ Track 22.9A lock re-verified |
| Draft restore + offline queue + restore-yesterday | ✅ Track 23.3 locks re-verified |
| Idempotency-Key preserved | ✅ V3 sends it on online submit; queue preserves it offline |
| Session modal fix | ✅ unchanged; V3 shares session semantics with V1 |
| Full regression 22.9A + 22.9B + 23.1 + 23.3 + DR-CUTOVER | **116/116 pytest green** |

## Emergency rollback runbook

If any field issue surfaces, one API call reverts every operator to V1 on the next page load. **Zero deploy. Zero code change. Zero database restore.**

```bash
curl -X POST "$API/api/admin/dr-v3-flag/tenant-default" \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

Verify with `curl "$API/api/feature-flags/dr-v3"` — must return `enabled:false`.

Rollback screenshot in this session captured V1 rendering correctly the moment the flag flipped.

## What did NOT change

- Backend endpoints — every write still lands on `POST /api/daily-reports`
- MongoDB collections — no schema mutation
- Emailed PDF — unchanged renderer
- Trust Spine / ODS emitters — unchanged
- Idempotency contract — unchanged
- Draft-restore / offline-queue / crew-memory hooks — shared with V1 via form key `daily-report`
- V1 source files — untouched (not deleted per operator directive: "do not delete V1 yet")

## Files changed

- **Modified**: `frontend/src/pages/NewDailyReportV3.jsx` (1 line — header label "· V3 Pilot" removed).
- **Data (via API)**: `ui_flags.dr_v3.tenant_default = true`, `updated_at = 2026-07-06T17:46:37Z`, `updated_by = "admin"`.
- **New**: `/app/memory/TRACK_23_4_V3_DEFAULT_CUTOVER.md`.

## Verdict: 🟢 **GO** — V3 is the production default.

---

**Timestamp:** 2026-02-06 · 17:46 UTC
**Executor:** jaymn.judd@mascigc.com (admin)
**Approver:** operator directive TRACK 23.4
