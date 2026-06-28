# Track 18.00 · Phase C · RBAC-aware Universal Search

**Date:** 2026-02-10
**Status:** ✅ GO — FULL BACKEND PASS · 23/23 regression · `retest_needed=false`
**Type:** Single composer endpoint · cross-portal RBAC · zero new business logic

---

## Mission

One search bar across the entire Transportation Operations
parent shell that finds drivers · carriers · trucks · dispatch
assignments · projects · documents · orientation modules /
certificates · action items — while strictly respecting the
calling user's portal-token capabilities.

---

## Verdict

✅ **GO**

* **23/23** Phase C regression tests pass.
* **55/55** cross-track regression tests (Phase A · Phase B ·
  16.15A · 16.16) remain green.
* `testing_agent_v3_fork` returned **FULL BACKEND PASS · 15/15
  live RBAC matrix tests** against the deployed preview.
* `retest_needed=false`.

---

## Endpoint

```
GET /api/admin/transportation/search
  q       required · 1..80 chars
  limit   optional · default 20 · max 50
  types   optional · comma-separated subset of allowed groups

→ 200 { ok, query, results[], counts{}, schema_version: "18.00C" }
→ 401 if no portal token presented
→ 403 if portal token has no search permission
```

Mounted via `register_track_18_00_phase_c_routes` after Track
16.16 in `server.py`. Reuses the existing
`make_require_any_portal_token` helper.

---

## RBAC matrix (locked)

| `_actor` | Allowed groups |
|---|---|
| `admin` / `leadership` | drivers · carriers · trucks · dispatch · projects · documents · orientation · actions · intelligence · timeline |
| `dispatch` | trucks · drivers · carriers · dispatch · projects |
| `hr` | drivers · documents · orientation |
| `pm` | projects · dispatch · trucks |
| `safety` | drivers · trucks |
| `shop` | trucks |
| `fl` | drivers · projects |
| unknown / anon | ∅ → 403 |

**Verified live** with the seven portal tokens issued by
`/api/auth/multi-login`. HR token explicitly cannot leak the
`trucks` group.

---

## Source collections (reuse only)

| Group | Collection | Safe fields |
|---|---|---|
| drivers | `transport_persons` | name · employee_id |
| carriers | `carriers` | name · dot_number · mc_number · contact_name |
| trucks | `transport_trucks` | unit_number · vin · plate · truck_number |
| dispatch | `dispatch_assignments` | assignment_id · project_number · driver_name · unit_number · carrier_name |
| projects | `projects` | project_number · name · customer · location |
| documents | `carrier_documents` + `driver_documents` | document_type · status · file_name |
| orientation | `transport_orientation_modules` + `transport_orientation_certificates` | key · title · certificate_number · person_name |
| actions | `transport_action_items` | title · status · event_key |

No new collection. No new index. No new search store.

---

## Result schema

Every result row:

```
{
  type:     "driver" | "carrier" | "truck" | "assignment" | "project" |
            "document" | "orientation_module" | "orientation_certificate" |
            "action_item"
  group:    one of the 8 group keys above
  title:    primary display string
  subtitle: secondary display string
  status:   row's existing status (eligible/active/pending_review/…)
  source:   collection name (transparency)
  route:    DEEP-LINK into an existing workspace (never empty)
  reason:   "Matched name or employee id" / similar
  metadata: { id, ... }
}
```

Every result carries a deep link. No dead results. No "coming soon".

---

## Frontend

`/app/frontend/src/pages/transportation/TransportationSearch.jsx`
mounted at the top of the Transportation Operations shell via
the `txops-search-rail` wrapper on every workspace.

* `data-testid="txops-search"` root
* `data-testid="txops-search-input"` input
* `data-testid="txops-search-shortcut-hint"` keyboard chip
* `data-testid="txops-search-drawer"` results drawer
* `data-testid="txops-search-group-{group}"` group sections
* `data-testid="txops-search-result-action-{group}-{i}"` clickable result rows
* `data-testid="txops-search-empty"` empty state
* `data-testid="txops-search-error"` error state
* `data-testid="txops-search-loading"` spinner
* `data-testid="txops-search-clear"` clear button

Behaviour: `/` keyboard shortcut focuses the input · 300 ms
debounce · Escape closes drawer · outside click closes drawer ·
result click navigates to deep-link route.

---

## Audit

Single `audit_events` row per search with:

* `kind: "transportation_search_performed"`
* `at: ISO timestamp`
* `actor`, `portal`, `role`
* `query_length` (int)
* `query_prefix` (first 3 chars only — PII-safe)
* `result_count`, `counts` (per-group counts)

**The full query text is intentionally NOT stored.** Verified
end-to-end against live MongoDB by the testing agent.

---

## Performance

* 300 ms frontend debounce.
* Server-side `asyncio.gather` across permitted groups, 4 s
  hard timeout (returns partial results on timeout).
* Default limit 20 · max 50.
* Safe `re.escape()` on every user query; query bounded to 80
  chars; `$regex` always paired with `$options: "i"`.

---

## Files changed / added

| File | Change |
|---|---|
| `/app/backend/routes/transportation_search.py` | NEW · ~270 LOC composer |
| `/app/backend/server.py` | +14 lines (router registration after Track 16.16) |
| `/app/frontend/src/pages/transportation/TransportationSearch.jsx` | NEW · ~220 LOC |
| `/app/frontend/src/pages/transportation/TransportationApp.jsx` | +6 lines (mount in shell header rail) |
| `/app/backend/tests/test_track_18_00_phase_c_universal_search.py` | NEW · 23 regression tests |
| `/app/scripts/deployment_gate.py` | +1 line |

No collection touched. No business logic added.

---

## Hard guarantees (locked in regression)

1. No new collection · no new index · no new business logic.
2. No source-record mutation (verified by static check).
3. Exactly ONE insert per search (the audit row).
4. Safe regex escaping (`truck.*214` → literal match).
5. Default limit 20 · max 50 (caller cannot exceed).
6. Stable schema `18.00C`.
7. Every result carries a deep link.
8. Per-portal RBAC matrix enforced and tested with 7 tokens live.
9. Phase A shell + Phase B Mission Control preserved (zero regressions).

---

## Deferrals (not built in Phase C)

* External full-text search engine.
* Fuzzy ranking.
* Saved searches.
* Search analytics dashboard.
* Cross-portal global search outside Transportation Operations.
* Public search.
* File-content / OCR search.
* AI semantic search.

---

## Next phase

**Phase D · Universal relationships + standardized right rail**
— add a single thin `GET /api/admin/transportation/related/{entity_type}/{id}`
composer endpoint that returns dispatch / truck / carrier / HR /
orientation / certificates / documents / safety / intelligence /
cleanup / audit cross-links for any entity. Then wire the existing
right-rail scaffolds (already built in Phase A) to real data.
