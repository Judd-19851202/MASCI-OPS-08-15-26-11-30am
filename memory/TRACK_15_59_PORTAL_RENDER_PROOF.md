# TRACK 15.59 — Portal Render Proof (Phase 8)

After the multi-login above, the directory + per-portal tokens were injected
into the browser's `localStorage` and the browser visited the canonical
landing surface for each of four portals.

**Source data:** `/app/test_reports/track_15_59_live_prod_verify.json` → `phases.8_portal_render`

| # | Portal URL | Final URL | Title | Still on login? | DOM bytes | Screenshot |
|---|------------|-----------|-------|-----------------|-----------|------------|
| 1 | `/admin` | `https://mascidocs.com/admin` | `Admin Console · MASCI` | no | 172,061 | `phase8_admin.png` |
| 2 | `/pm` | `https://mascidocs.com/pm/command-center` | `PM Command Center · MASCI` | no | 86,255 | `phase8_pm.png` |
| 3 | `/safety-portal` | `https://mascidocs.com/safety-portal` | `MASCI Operations Platform` | no | 80,863 | `phase8_safety-portal.png` |
| 4 | `/hr` | `https://mascidocs.com/hr` | `MASCI Operations Platform` | no | 81,286 | `phase8_hr.png` |

## What "still on login" means

For every visit, the script checks:
1. The final `page.url` after the React router resolves — it must NOT contain `/login` or `/sign-in`.
2. The hydrated DOM body length — a healthy authenticated portal renders 80 KB+ of mark-up (tile grids, nav, data widgets); the bare login form is sub-30 KB.

Both signals are green on all four portals.

## Notes on `/pm`

`/pm` correctly resolves to `/pm/command-center` because the PM portal home
is now the Command Center (introduced in iter343 / iter450). The token used
is the directory-minted `pm` token, NOT the legacy `PM_PASSWORD=Happy123!`
shared bypass. The landing is real per-user PM data, scoped through
`compute_pm_scope` against the super-admin's all-projects visibility.

## Notes on title fallbacks

`/safety-portal` and `/hr` still render with the generic SPA title
"MASCI Operations Platform" — both surfaces have not yet bumped their
per-route `<title>` tags. This is a cosmetic backlog item, not a
functional gate. Body content was correct in both cases (verified via
screenshot inspection — visible Safety Hub tiles / HR Hub tiles).

**Result:** 4 / 4 portals rendered authenticated content. Phase 8 PASS.
