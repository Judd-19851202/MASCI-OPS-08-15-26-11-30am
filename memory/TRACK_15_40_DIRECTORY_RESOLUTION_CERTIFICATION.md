# TRACK 15.40 · Directory Resolution Certification

**Date:** 2026-06-19
**Track:** 15.40 · Objective 1
**Status:** 🟢 CERTIFIED — 0 false Unknown Person rows

---

## 1 · Certification evidence

### 1.1 · Backend pytest
`/app/backend/tests/test_track_15_40_directory_resolution.py` — **5/5 PASS**

```
test_employee_fallback_by_user_id PASSED          [ 20%]
test_employee_fallback_by_email PASSED            [ 40%]
test_unknown_user_falls_back_to_sentinel PASSED   [ 60%]
test_alec_perkins_resolves PASSED                 [ 80%]
test_resolve_display_name_sources_order PASSED    [100%]

5 passed, 1 warning in 2.70s
```

### 1.2 · Live API verification

```
curl /api/admin/jobs/20-07/team (post-fix)
  total active rows: 3
  unknown rows:      0
  co_pm        display_name=PM Demo (Preview Fixture)
  foreman      display_name=Alec Perkins
  safety_rep   display_name=Alec Perkins
```

```
curl /api/admin/jobs/20-07/team/audit?limit=20 (post-fix)
  items=20
  alec_target_display_name=10
  unknown_for_alec_user_id=0
```

### 1.3 · Iter527 frontend cert (testing agent)
* DIR-1 — `page.locator('text=Unknown person').count() === 0` · `page.locator('text=Alec Perkins').count() === 2` → **PASS**
* DIR-2 — initial run flagged 9 historical `(unknown)` tokens in the audit drawer body text. **Resolved post-iter527**: frontend `AssignmentHistoryDrawer.who` chain updated to prefer `target_display_name`; re-verified in `/tmp/audit_drawer.png` → drawer body text contains 10 `Alec Perkins`, 0 `(unknown)`.
* DIR-3 — server-side audit enrichment returns 10 Alec items, 0 unknown for Alec's user_id → **PASS**

### 1.4 · Viewport matrix (iter527)

| Viewport | Unknown rows | Alec rows | Horizontal scroll | Verdict |
|---|---|---|---|---|
| Desktop 1920×1080 | 0 | 2 | 0 | 🟢 PASS |
| iPad portrait 768×1024 | 0 | 2 | 0 | 🟢 PASS |
| iPad landscape 1024×768 | 0 | 2 | 0 | 🟢 PASS |

### 1.5 · Regression matrix

| Surface | Behavior | Verdict |
|---|---|---|
| Team Assignment add row | unchanged | PASS |
| Team Assignment inline role change | unchanged | PASS |
| Team Assignment structured remove | unchanged | PASS |
| Audit history newest-first ordering | unchanged | PASS |
| Auth surface | untouched | PASS |
| Notification recipient computation | untouched | PASS |
| Mongo schema | unchanged | PASS |

---

## 2 · Coverage map (where the fix runs)

* `GET /api/admin/jobs/{pn}/team` — admin roster fetch
* `GET /api/pm/job/{pn}/team` — PM roster fetch (same enricher)
* `POST /api/admin/jobs/{pn}/team` — fresh adds get correctly enriched on the response payload
* `PATCH /api/admin/jobs/{pn}/team/{id}` — role change responses
* `DELETE /api/admin/jobs/{pn}/team/{id}` — remove responses
* `GET /api/admin/jobs/{pn}/team/audit` — audit drawer source

---

## 3 · Risks / residuals

* If the `employees` collection grows beyond ~10k entries AND an
  unindexed query path is used by the resolver, latency could rise.
  Current preview DB has < 200 employees; index on `employees.id`
  already exists. No action needed.
* `_recently_read_at` (notifications) and `_resolve_audit_name` cache
  are per-request — no memory pressure.

---

## 4 · Verdict

🟢 **Directory Resolution CERTIFIED.**

Alec Perkins (and every other employee carried only by the `employees`
collection) now resolves to his real name on:
- Active roster rows (admin + PM scopes)
- Assignment-mutation API responses
- Audit history (both `target_display_name` and snapshot `display_name`)

Zero false "Unknown person" rows remain on project 20-07.
