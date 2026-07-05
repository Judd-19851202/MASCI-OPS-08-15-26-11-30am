# Phase 1 · Open Item Matrix

**Date:** 2026-02-05
**Standard:** Defect Constitution — every item Fixed OR Blocked-with-owner. No un-classified items.

## Class A · Fix Now (this session)
_Empty._ No open Class A defects.

## Class B · Blocks Deployment
_Empty._ No open Class B defects.

## Class C · Engineering Debt (owned, blocked-with-owner, non-blocking to deploy)

| # | Item | Owner | Target | Exit criteria | Blocking condition | Operational risk |
|---:|---|---|---|---|---|---|
| C-1 | App.js is a 1,283-line monolith with 385 routes / 180 lazy imports / 11 guards / 1 provider — needs modularization into `frontend/src/app/*` | Next-session executor (Track 22.2 Phase B) | Track 22.2 Phase B — single fresh execution window | Parity harness JSON-diff empty + Playwright per-portal green + bundle report `after ≤ before` + 385 routes preserved | Cannot safely fit 385-route AST extraction + 12-portal Playwright + before/after bundle report in remaining context budget of this session | None — App.js is stable, production-safe, and untouched (md5 `d84cea05c1f64bd2ae82823d7f6aadcc`). All artifacts ready under `/app/memory/TRACK_22_2_*` |
| C-2 | 110 `react-hooks/exhaustive-deps` ESLint warnings across the frontend | Frontend hygiene track lead | Track 22.6 (proposed) — dedicated frontend hygiene sweep | 0 ESLint warnings on `yarn build` | Same-session fix requires per-warning intent review (each `useEffect` deps array is a semantic decision); mechanical auto-fix can introduce infinite re-render loops | Low — React warns but does not break. No runtime failures observed |
| C-3 | 1 Tailwind arbitrary-class warning: `duration-[400ms]` ambiguous match | Frontend hygiene track lead | Track 22.6 | Replace with numeric duration or explicit CSS var | Cosmetic; requires locating usage across the codebase and picking replacement semantics | None |
| C-4 | Upstream `python_multipart` PendingDeprecation warning from Starlette | Backend track lead | Track 22.4B (proposed) — Starlette v0.35+ multipart migration | 0 PendingDeprecationWarning on backend boot | External dependency (Starlette); requires SDK version bump + regression envelope | None (upstream library warning only; no functional impact) |
| C-5 | App.js line 5 (`// AuthProvider removed 2026-04-28`) + lines 87–93 (documented `NewIncident` retirement comment block) are historical narrative comments | Track 22.2 Phase B executor | Track 22.2 Phase B — will be consolidated into feature-file docstrings during route extraction | Comments moved to per-feature module headers | Immediate deletion would drop context needed by lock tests (iter333/335/336 scan `NewIncident.jsx`); safe removal must happen with route ownership refactor | None — comments have zero runtime impact |
| C-6 | `browserslist` data 7 months old (build warning) | DevOps | Any future frontend build | `npx update-browserslist-db@latest` | Requires container rebuild; noisy but non-functional | None |

## Class D · False Positive (investigated and confirmed non-defect)

| # | Item | Investigation |
|---:|---|---|
| D-1 | Playwright reported 3 `net::ERR_ABORTED` on `/sign-in` navigation | Confirmed navigation-cancel behavior: `cdn-cgi/rum` (Cloudflare telemetry preview), `/api/usage/track` (fire-and-forget analytics), Sentry envelope — all cancelled by browser during page transition. Not defects. |
| D-2 | Historic `410 Gone` "retired admin-login" tests failing in legacy monolith suite | Intentional design — these tests assert that certain retired admin-login endpoints return `410 Gone`. They pass under their own envelope; they only fail if aggregated with the wrong test env vars. Not tracked in Track 22.* lock envelope. |

## Class E · Intentional Design (documented decisions)

| # | Item | Rationale |
|---:|---|---|
| E-1 | Starlette CORS `allow_origin_regex=cors_origin_regex` at `server.py:15831` | Preserved intentionally per Track 22.3. Not Pydantic; Starlette's regex-based CORS is idiomatic. Documented in `TRACK_22_3_ZERO_DRIFT_MATRIX.md`. |
| E-2 | `frontend/src/pages/NewIncident.jsx` retained on disk without a route | Retained because lock tests iter333/335/336 scan it as a cross-form pattern reference. Removal requires those lock tests to be updated first. Documented in `App.js:87-93`. |
| E-3 | `EMAIL_SAFETY_MODE=strict` in preview (never dispatch live emails during dev/test) | Deliberate + permanent. Enforced by monkey-patched Resend SDK. Runtime attests `live_emails_possible=false`. |

## Class F · Future Enhancement (not defects; opportunities)

| # | Item | Value proposition |
|---:|---|---|
| F-1 | Main bundle 1.14 MB gzipped could be further split via manual chunk boundaries | Reduce initial paint on cold-load; requires webpack magic-comment audit |
| F-2 | Sentry chunk (157 kB) could be conditionally loaded on error | Reduce always-on JS budget; requires Sentry SDK lazy-init pattern |
| F-3 | Full Playwright coverage per portal (currently smoke only for public/hub + sign-in) | Comprehensive regression harness; requires seed data + role tokens |

## Summary
- **Class A · Fix Now:** 0
- **Class B · Blocks Deployment:** 0
- **Class C · Engineering Debt (owned):** 6
- **Class D · False Positive:** 2
- **Class E · Intentional Design:** 3
- **Class F · Future Enhancement:** 3

**Deployability:** 🟢 GO. Zero Class A/B open.
