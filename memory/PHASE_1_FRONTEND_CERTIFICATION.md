# Phase 1 · Frontend Certification

**Date:** 2026-02-05
**Status:** 🟢 GO

## Build
- Command: `yarn build` (`craco build`)
- Result: **Compiled with warnings** (zero errors)
- Main bundle: **1.14 MB gzipped** (`build/static/js/main.19f3be9e.js`)
- Second-largest chunk: 278 kB (`2872.05051741.chunk.js`)
- Sentry chunk: 157 kB (isolated)
- Chunk count: **193 JS chunks** (180 route-level lazy imports + shared runtime chunks)
- Total build output: 48 MB
- Compilation warnings: **110 ESLint** (`react-hooks/exhaustive-deps` · all Class C) + **1 Tailwind** (`duration-[400ms]` ambiguity · Class C) + browserslist-data-old notice (Class C)

## Runtime smoke (Playwright · preview URL)

| Route | HTTP | Title | Console errors | Network failures (excl. navigation-cancel) | Verdict |
|---|---|---|---|---|---|
| `/` (public Hub) | 200 | MASCI Operations Platform | 0 | 0 | 🟢 |
| `/sign-in` (master sign-in) | 200 | MASCI Operations Platform | 0 | 0† | 🟢 |
| `/signin` (deep-link fallback) | 200 (404 UI) | MASCI Operations Platform | 0 | 0 | 🟢 (renders 404 page correctly) |

† 3 `net::ERR_ABORTED` observed on `/sign-in` (Cloudflare RUM + `/api/usage/track` fire-and-forget + Sentry envelope) — all confirmed as navigation-cancel behavior, Class D False Positive.

## Route inventory (machine-extracted)
- Total `<Route>` declarations: **385**
- Unique paths: **385** (zero duplicates)
- Guards: **11** (`A · TX · AP · APS · P · S · H · FL · SF · DP · D`)
- Provider mounts: 1 (`BrandingProvider`)
- Chrome components: 15
- Load kinds: 204 lazy · 170 eager · 11 inline/local

Full inventory: `/app/memory/track_22_2/APP_JS_INVENTORY.json`

## Guard distribution
| Guard | Route count | Role |
|---|---:|---|
| PUBLIC | 143 | Anonymous / cross-portal |
| A | 65 | Admin |
| AP | 45 | Admin OR PM |
| SF | 33 | Safety |
| H | 28 | HR |
| S | 25 | Shop |
| P | 22 | PM |
| DP | 10 | Dispatch |
| D | 6 | Dev |
| FL | 4 | Field Leadership |
| APS | 3 | Admin OR PM OR Safety |
| TX | 1 | Transportation Ops |

## Playwright coverage — Phase 1 scope (smoke)
- Public landing: ✅ (rendered)
- Sign-in (master): ✅ (form + 7 workspace links + zero console errors)
- Deep-link 404: ✅ (custom 404 with Sign-In + Public-Home CTAs)

Full per-portal auth-gated coverage is a **Phase B (Track 22.2)** deliverable, not a Phase 1 blocker. Public + sign-in smoke sufficient to certify deployment.

## Rollback profile
- Backend rollback: `git revert <passkeys.py-3-line-diff>` (Track 22.4A)
- Frontend rollback: **none needed** — App.js untouched this session
- No schema migrations · no auth changes · no CORS changes · no permission changes

## Certification
🟢 **Frontend GO for Phase 1 deployment.**
