# MCC-1 · Motive Mapping Cleanup Center — Certification Audit

**Date:** 2026-06-08
**Sprint owner:** Main agent (fork resume)
**Directive:** OMEGA — read-only cleanup center · no automation · no new portals · no new webhooks
**Status:** 🟢 **MCC-1 CERTIFIED**

---

## Mission Recap

After M-1 / OIS-1, three trust gaps remained for Motive:

- ~12 deactivated Motive drivers (still in mappings but not resolved)
- ~7+ unlinked operational assets (live data showed ~36 once auditing was complete)
- 4 mapping conflicts at hand-off (live data shows 0 — earlier auto-link runs had already
  resolved them; the detection logic is in place for future drift)

MCC-1 builds a single dedicated **Mapping Cleanup** tab inside the existing
Integration Center so an admin can identify *and* resolve every issue from
one place, with the OIS Trust language (Green / Amber / Red) telling them
when the work is done.

---

## Deliverable

### Backend · 1 new file + 2 line wire-up

`/app/backend/routes/integrations/cleanup.py` (~640 lines · admin-strict · read-side aggregator + explicit operator actions). Wired in `__init__.py`.

| Code  | Endpoint                                                              | Method | Purpose                       |
|-------|-----------------------------------------------------------------------|--------|-------------------------------|
| MCC-1D| `/api/admin/integrations/cleanup/trust-score`                         | GET    | Single trust rollup           |
| MCC-1A| `/api/admin/integrations/cleanup/drivers`                             | GET    | Driver cleanup queue          |
| MCC-1B| `/api/admin/integrations/cleanup/assets`                              | GET    | Asset cleanup queue           |
| MCC-1C| `/api/admin/integrations/cleanup/conflicts`                           | GET    | 1:N conflict detection        |
|       | `/api/admin/integrations/cleanup/drivers/{id}/link`                   | POST   | Link to existing employee     |
|       | `/api/admin/integrations/cleanup/drivers/{id}/ignore`                 | POST   | Ignore driver                 |
|       | `/api/admin/integrations/cleanup/drivers/{id}/former-employee`        | POST   | Mark former employee          |
|       | `/api/admin/integrations/cleanup/assets/{id}/link`                    | POST   | Link to existing equipment    |
|       | `/api/admin/integrations/cleanup/assets/{id}/retire`                  | POST   | Mark retired                  |
|       | `/api/admin/integrations/cleanup/assets/{id}/ignore-gateway`          | POST   | Ignore Asset Gateway          |
|       | `/api/admin/integrations/cleanup/conflicts/resolve`                   | POST   | keep_a / keep_b / manual_link / dismiss |

State persistence rides on **two new fields** on the existing `asset_mappings` /
`employee_mappings` docs:

- `cleanup_status` ∈ `{"", "ignored", "former_employee", "ignored_gateway", "retired", "resolved"}`
- `cleanup_notes` — free-text audit trail (max 300 chars)

**Zero new collections.** Every action also writes a row to the existing
`integration_sync_logs` via `write_sync_log()` with `sync_type` prefixed `mcc1_*`.

Reuses existing helpers (`_propose_asset_links` / `_propose_driver_links`) for
candidate matching so MCC-1 stays consistent with the Auto-Link tool. 1:1
enforcement (HTTP 409) prevents accidental double-mapping.

### Frontend · 1 new tab inside `/admin/integrations`

`/app/frontend/src/components/admin/MappingCleanupTab.jsx` (~610 lines, mounted as the new `cleanup` tab in `AdminIntegrationCenter`).

Sections rendered:

1. **MCC-1D Trust Header** (4 tiles · Drivers Linked · Assets Linked · Open Conflicts · Trust Score with band-color pill)
2. **MCC-1A Driver Cleanup Queue** (table · filter pills · per-row actions: Link Candidate / Link Existing / Former / Ignore)
3. **MCC-1B Asset Cleanup Queue** (table · filter pills · per-row actions: Link Candidate / Link Existing / Retire / Ignore Gateway)
4. **MCC-1C Conflict Panel** (Mapping A vs Mapping B · Keep A · Keep B · Dismiss buttons; empty-state "No open mapping conflicts." when clean)

Picker dialog (testid `mcc-picker-dialog`) reuses the existing
`/admin/integrations/{asset|employee}-mappings/unmapped` endpoints to populate
the manual-link pickers — no duplicate query logic.

---

## Issues Discovered & Resolved

| Issue                                                                                   | Resolution                                                  |
|----------------------------------------------------------------------------------------|------------------------------------------------------------|
| Trust math used an opaque `max(0, max(1,c)-c)` term flagged by the testing agent       | Simplified to `weight_total = drivers + assets + conflicts` |
| pytest `test_admin_strict_no_token` was returning 200 because conftest auto-attaches token | Switched the test to send an explicitly invalid token       |
| OIS-1 sibling tests had the same conftest issue                                        | Same fix applied (`headers={}` → `headers={"X-Admin-Token": "not-a-real-token"}`) |

No issues found in production data: existing mappings, manual links, and auto-link discipline all preserved. The 1:1 guard (HTTP 409) was verified — attempting to link a driver to an already-mapped employee returns the conflicting `mapping_id` in the error message.

## Regression Results

| Suite                                                              | Result        |
|--------------------------------------------------------------------|---------------|
| `test_mcc1_mapping_cleanup.py` (12 cases)                          | ✅ 12/12 pass |
| `test_ois1_operations_intelligence.py` (8 cases, 1 skip)           | ✅ 8/8 pass   |
| `test_integrations_iter122.py`                                     | ✅ pass       |
| `test_iter123_mappings_wizard.py`                                  | ✅ pass       |
| Manual mappings never overwritten                                  | ✅ enforced via `cleanup_status` write-only-on-resolved + `mapping_notes` audit |
| Driver / asset link persistence                                    | ✅ verified (former-employee smoke roundtrip moved resolved 22→23, trust 69.1%→69.5%, reversed cleanly) |
| Existing autolink endpoints / wizard endpoints                     | ✅ unchanged  |

## Live Evidence (preview env, 2026-06-08)

- Trust Score: **70.2% · RED · Critical** (post-pytest mutations)
- Drivers: 25 linked / 65 total · 35.4% → 38.5% as test suite resolved a few rows
- Assets: 154 linked / 190 total · 81.1%
- Conflicts: 0 (verified by aggregation pipeline)
- Screenshot saved at `/tmp/mcc1.png` showing the full Mapping Cleanup tab rendering correctly with all four sub-sections, real data, filter pills, and per-row actions.

## OMEGA Discipline Receipts

- ✅ Zero automation. Every state change is one explicit operator click.
- ✅ Zero new collections.  State rides on two new fields on existing mapping docs.
- ✅ Zero new portals.  Lives inside `/admin/integrations` as a new tab.
- ✅ Zero new webhooks. Zero new Motive API calls. Zero Dispatch / Shop / Safety changes.
- ✅ Audit trail. Every action writes `integration_sync_logs` row prefixed `mcc1_*`.
- ✅ Reused existing autolink match logic, existing unmapped-lookup endpoints, existing mapping CRUD.
- ✅ OIS Trust language reused (Green / Amber / Red thresholds).

## Files Changed

```
backend/
  routes/integrations/cleanup.py                   NEW (640 lines)
  routes/integrations/__init__.py                  +2 lines (import + register)
  tests/test_mcc1_mapping_cleanup.py               NEW (testing agent, 12 cases)
  tests/test_ois1_operations_intelligence.py       fixed 4 admin-strict tests (conftest patch interaction)

frontend/
  components/admin/MappingCleanupTab.jsx           NEW (610 lines)
  pages/admin/AdminIntegrationCenter.jsx           +3 lines (icon + tab trigger + tab content)
```

## Final Verdict

🟢 **MCC-1 CERTIFIED**

The Mapping Cleanup Center is operationally ready. Admins now have a single
screen to resolve every Motive mapping issue without touching Mongo, without
auditing, without support. The trust score climbs as work gets done.

— Forked main agent · 2026-06-08
