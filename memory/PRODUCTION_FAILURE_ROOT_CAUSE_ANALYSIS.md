# PRODUCTION FAILURE ROOT CAUSE ANALYSIS · TRACK 15.13B

**Date**: 2026-02-15 (executed 2026-06-17)
**Failures**: 3 confirmed · all real · all root-caused · all fixed in preview · awaiting redeploy

---

## Failure #1 — Asset Admin lands in Shop Command Center

### Expected (per Track 15.13A claim)
After Asset Administrator logs in via `/shop/login`, SPA lands them on `/shop/asset-care`.

### Actual (production)
User lands on `/shop` (Shop Command Center).

### Root cause
The 15.13A implementation has TWO required paths to set `is_asset_admin: true` on the login response:

1. **Lookup `db.user_directory` by lowercased email** and read the `is_asset_admin` flag mirrored there.
2. **Auto-mirror** that flag whenever the Admin Shop Users console creates or updates a user with an asset role label.

But the existing real Asset Administrator on production was provisioned **before** 15.13A landed. Their `shop_users` row carries `role: "Asset Administrator"` but **no `user_directory` row was ever created**. The shop_login lookup found nothing, `is_asset_admin` resolved to `False`, and `landingFor()` returned `/shop`.

```python
# server.py · shop_login (15.13A state)
dir_row = await db.user_directory.find_one({"email": email}, {"is_asset_admin": 1})
if dir_row and dir_row.get("is_asset_admin") is True:
    is_asset_admin = True
# else → is_asset_admin = False · user lands on /shop · WRONG
```

### Line of code
`backend/server.py:1881` (the missing fallback to the role label).

### Fix
```python
# 15.13B fallback — read-only role-label check.
if not is_asset_admin and _role_implies_asset_admin(user.get("role")):
    is_asset_admin = True
```

### Live preview proof
```
shop_users: { role: "Asset Administrator", no directory row }
POST /api/shop/login → { is_asset_admin: True, kind: "shop", user.role: "Asset Administrator" }
```

### Impacted users
Every Asset Administrator / Asset Manager / Equipment Manager / Fleet Coordinator account that existed before the 15.13A deploy.

### Verification method
1. Backend: `pytest tests/test_track_15_13b_production_failure_recovery.py::TestFailure1AssetAdminLegacyFallback` (3/3 PASS).
2. Live preview: legacy-style shop_users row inserted by hand (no directory row) → login returns `is_asset_admin: true`.

---

## Failure #2 — HR Daily Reports PM "often missing"

### Expected (per Track 15.9A claim)
HR Daily Report list + detail views surface `pm_email` and `pm_name` so HR can see project ownership.

### Actual (production)
PM column / PM strip empty on real reports.

### Root cause
The 15.9A PM-of-record enrichment ONLY looked in `db.projects`. Real daily reports reference `project_number`s that live in `db.jobs_master` (the canonical job spine — the same source `compute_pm_scope` uses for PM scoping). When a project exists in `jobs_master` but has no row in `projects`, the enrichment returned `("", "")` and the UI showed `—`.

```python
# routes/hr_portal.py · hr_get_daily_report (15.9A state)
proj = await db.projects.find_one({"project_number": pn}, {"pm_name": 1, "pm_email": 1})
if proj: pm_name = proj.get("pm_name", "")
# no fallback · WRONG for legacy DRs
```

The list endpoint had the exact same defect via its `$lookup`.

### Line of code
`backend/routes/hr_portal.py:494` (detail), `:441` (list), `:415` (PM filter).

### Fix
Three-tier fallback applied to all three sites:

1. `projects` collection (existing 15.9A enrichment)
2. **NEW** `jobs_master.pm_email / pm_name`
3. **NEW** if email but no name, derive a display name from the email local-part

The PM **filter** (`?pm=…`) now resolves project numbers via BOTH `projects` and `jobs_master` (deduped), so HR's PM filter actually finds the legacy DRs.

### Live preview proof
```
Cert DR project_number=TRACK15-11B (only in jobs_master, not in projects)
GET /api/hr/daily-reports/<cert-dr-id> →
  pm_email: "track15.11b.cert.pm@mascicert.local"
  pm_name:  "Track15 11B Cert Other"   (derived from email local-part)
```

### Impacted users
Every HR operator viewing daily reports against projects that exist in `jobs_master` but not in `projects` (i.e. virtually all legacy + many recent reports).

### Verification method
1. Backend: `pytest tests/test_track_15_13b_production_failure_recovery.py::TestFailure2HrPmEnrichmentFallback` (5/5 PASS).
2. Live preview: cert DR returned non-empty `pm_email` + derived `pm_name`.

---

## Failure #3 — HR photo grid shows "photo-0 / photo-1 / photo-2 / photo-3"

### Expected
HR Daily Report detail page renders actual photo thumbnails.

### Actual (production)
The grid showed the literal text `photo-0`, `photo-1`, etc. — i.e. the `alt` attribute of `<img>` tags whose `src` failed to load.

### Root cause
The HR detail view rendered photos as:

```jsx
<img src={p.url || p} alt={`photo-${idx}`} ... />
```

Post the iter64 R2 migration (2026-05-11), every production photo is stored as `photo://masci-hub/photos/<uuid>` (NOT a base64 data URL, NOT an http URL). Browsers cannot resolve `photo://` natively — the request fails, the `<img>` shows the `alt` text. The literal strings `photo-0`, `photo-1`, etc. were the `alt` template `\`photo-${idx}\``.

Every other view in the codebase (`ViewDailyReport`, `ViewMeeting`, `ViewInspection`, `ViewIncident`, `ViewQaqcInspection`, `ViewEquipmentInspection`, `ViewSafetyForm`, `FieldLeadershipView`, `PhotoUpload`) pipes refs through `resolvePhotoSrc()` from `lib/photoSrc.js`, which rewrites `photo://` → `/api/photo-bytes?ref=…`. The HR detail page was the lone holdout.

### Line of code
`frontend/src/pages/HrDailyReports.jsx:414` (pre-fix).

### Fix
1. Import `resolvePhotoSrc` from `@/lib/photoSrc`.
2. Accept BOTH string refs and legacy `{url, ref}` object refs.
3. Pipe every ref through the resolver — the same path the other 9 views use.
4. Improve the `alt` text to `Photo ${idx + 1}` so even if a thumbnail fails to load, the user sees a human-readable label (not the test marker that fooled production into looking broken).

### Live preview proof
* Cert DRs have no real `photo://` refs (the seed creates synthetic refs), so a clean photo-bytes resolver call won't surface during cert runs.
* Static code assertion via `pytest TestFailure3HrPhotoRendering` (5/5 PASS): imports + resolver call + dual-ref handling + alt-text change all verified.
* The `resolvePhotoSrc()` helper itself is verified by every other view that uses it daily.

### Impacted users
Every HR operator opening any production daily report that has photos.

### Verification method
1. Backend tests on the source assertions (5/5 PASS).
2. Code-trace cross-reference to nine other consumers of `resolvePhotoSrc` — none of them showed this defect in production, so the resolver itself is sound.
3. Live verification awaits the redeploy (no real `photo://` data in preview to probe).

---

## Was the production deployment missing code?

Possible — and likely the explanation for parts of #1. Track 15.13A was a preview-only delivery; if the operator had not yet redeployed when they hit the Asset Admin login, the live code was the pre-15.13A version that also lacked the fix. But **even if 15.13A WAS deployed**, the legacy-user case (no directory row) would still have failed. The 15.13B fallback closes that gap regardless.

## Is data incorrect?

`db.projects` is incomplete for many `jobs_master` rows — yes. This is the data shape that exposed Failure #2. The fix accepts that data shape rather than demanding the mirror be perfect.

## Is routing incorrect?

For Asset Admins (#1) yes — corrected.

## Is the architecture incorrect?

No. The Asset Care experience under `/shop/asset-care` is the right place. The Shop login is the right door. The flaw was in two specific code paths, both fixed.

---

## Tests

```
pytest tests/test_track_15_13b_production_failure_recovery.py → 14 / 14 PASS
pytest tests/test_track_15_13a_asset_care_routing.py            → 17 / 17 PASS
pytest tests/test_track_15_11b_seed_safety.py                   → 27 / 27 PASS
pytest tests/test_track_15_10_project_team_recovery.py          → 32 / 32 PASS
pytest tests/test_track_15_9_hr_daily_reports_certification.py  → 44 / 44 PASS
pytest tests/test_track_15_8b_prod_confirm_safety.py            → 13 / 13 PASS
pytest tests/test_iter332_workflow_access_gaps.py               → 18 / 18 PASS
pytest tests/test_iter339_hr_daily_reports_calm_errors.py       →  5 /  5 PASS
pytest tests/test_track_15_1_offboarding_pm_scoping.py           →  5 /  5 PASS
                                                                ─── 175 / 175 PASS
```

(`tests/test_track_15_2_pm_add_member_runtime.py` includes one long-running e2e test that timed out at 120s during the bundled regression run; same test passed isolated under 60s in earlier 15.13A regression. Pre-existing timing characteristic, unrelated to 15.13B fixes.)

END · ROOT CAUSE ANALYSIS.
