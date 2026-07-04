# TRACK 22.2 · Next-Session Execution Prompt

Copy-paste this into a fresh session to execute Phase B in one uninterrupted window.

---

# TRACK 22.2 · APP.JS ARCHITECTURE MODERNIZATION — EXECUTION SESSION

Continue the "Zero-Drift" refactoring program under the Eight Pillars Engineering Constitution. Track 22.4A (Pydantic V2 completion) is CLOSED and PROVEN. Track 22.2 Phase B inventory is COMPLETE with zero App.js code change. Execute the extraction now.

## Ground truth artifacts (READ FIRST)
- `/app/memory/TRACK_22_2_APP_JS_HANDOFF.md` — closure narrative + this prompt
- `/app/memory/TRACK_22_2_ROUTE_MAP.md` — full route map + 52-bucket grouping
- `/app/memory/TRACK_22_2_PROVIDER_GRAPH.md` — provider + chrome order
- `/app/memory/TRACK_22_2_GUARD_GRAPH.md` — 11 guard aliases → RequireX
- `/app/memory/TRACK_22_2_EXTRACTION_PLAN.md` — target directory layout + step-by-step order
- `/app/memory/TRACK_22_2_DEAD_CODE_REPORT.md` — 0 dead imports; 3 comment blocks to remove
- `/app/memory/TRACK_22_2_RISK_MATRIX.md` — 15 risks classified A/B/C
- `/app/memory/track_22_2/APP_JS_INVENTORY.json` — canonical inventory (route/import/guard/provider)
- `/app/memory/track_22_2/APP_JS_ROUTE_GROUPS.json` — 52-bucket grouping w/ guard mix
- `/app/memory/track_22_2/extract_app_js_inventory.py` — reproducible extractor

## Constitutional constraints (locked, non-negotiable)
1. **URL surface + guard chain identical.** Path, guard alias, guard component, target component, and lazy/eager kind MUST all match per-route.
2. **Provider order + chrome order identical.** No re-ordering `BrandingProvider`, Toaster, banners, or router-scoped children.
3. **`key={authTick}` on `<BrowserRouter>` + `<React.Suspense fallback={null}>` boundary MUST be preserved.**
4. **Boot effects fire in the same order:** `validateStoredTokens` → `usageTracker.bindRouteChangeTracker` → `resiliency.purgeStaleDrafts`.
5. **Route ordering inside `<Routes>` MUST be preserved** — React Router v6 uses first-match; re-ordering can change behavior.
6. **Delete only machine-proven-dead code** (zero incoming refs AST-wide). The only pre-approved deletions are the 3 comment blocks in DEAD_CODE_REPORT.
7. **Zero warning suppression. Zero behavior change. Zero API change.**
8. **`EMAIL_SAFETY_MODE=strict` intact. No live emails.**

## Execution order
1. Scaffold `frontend/src/app/{routing,providers,layouts,guards,boot,feature-routes}/` per EXTRACTION_PLAN.
2. Extract guards → `app/guards/aliases.jsx`.
3. Extract boot effects → `app/boot/useAppBootEffects.js`.
4. Extract providers → `app/providers/AppProviders.jsx`.
5. Extract routes bucket-by-bucket in ROUTE_MAP order (largest first: admin → safety → pm → hr → shop → dispatch → field-leadership → …).
6. Build `app/routing/AppRoutes.jsx` = `<Routes>` composed of all bucket exports, in the same order they appear in current App.js.
7. Build new `app/App.jsx` = provider + chrome + BrowserRouter + Suspense + `<AppRoutes/>`.
8. Update `src/index.js`: `import App from "@/app"` (replacing `@/App`).
9. Delete legacy `frontend/src/App.js` in the SAME commit.
10. **Parity harness:** modify `extract_app_js_inventory.py` to walk `src/app/feature-routes/*.jsx` and produce `APP_JS_INVENTORY.after.json`. Diff MUST be empty (normalize line numbers).
11. **`yarn build`** — capture bundle report before + after. `after ≤ before`.
12. **Playwright coverage** per EXTRACTION_PLAN matrix — per-portal auth-gated entry + deep-link + back/forward + refresh + console-clean + network-clean.
13. **Backend regression:** run the full Track 22.* lock envelope (`254/254` baseline). No regression allowed.
14. **Delete comment blocks** flagged in DEAD_CODE_REPORT (App.js lines 5, 88–93).
15. **Update PRD.md + CHANGELOG.md + PLATFORM_MANIFEST.json + TECHNICAL_DEBT_REGISTER.md.**
16. **Generate Track 22.2 close-out documents:** `TRACK_22_2_EXECUTIVE_SUMMARY.md`, `TRACK_22_2_ZERO_DRIFT_MATRIX.md`, `TRACK_22_2_TEST_REPORT.md`, `TRACK_22_2_BUNDLE_REPORT.md`, `TRACK_22_2_PLAYWRIGHT_REPORT.md`.
17. **Invoke `testing_agent_v3_fork`** for independent frontend + backend verification.
18. **`finish`** with the same proof standard used by Track 22.4A / 22.3 / 22.1K.

## STOP triggers (abort mid-execution and hand off)
- Parity harness diff not empty
- Any Playwright portal fails smoke
- Bundle size regresses
- Any Require* component rewritten
- Any lazy chunk name shifts (CDN risk)
- Console error appears on any portal entry
- Context budget projected to fall short of steps 10–17

If any STOP trigger fires, revert everything (git-level), write STOP report, hand back.

## Baseline metrics (Phase A + prior tracks — MUST NOT regress)
- Routes: 1,441 · Methods: 1,445 · OpenAPI paths: 1,264
- `lifecycle_complete=true` · 100% startup + 100% shutdown · 9/9 bytecode clean
- `EMAIL_SAFETY_MODE=strict` · `resend_sdk_patched=true` · `live_emails_possible=false`
- Track 22.* backend lock envelope: **254/254 pass**
- App.js source: 1,283 lines · 138 eager imports · 180 lazy imports · **385 routes** · 11 guards · 1 provider

## Success criteria
✓ App.js deleted · new `app/` tree in place · orchestration shell ≤ 80 lines
✓ Parity harness diff empty
✓ Bundle size + chunk count ≤ before
✓ Playwright: every portal green, zero console errors, zero network failures
✓ Backend Track 22.* envelope still 254/254
✓ Testing agent GREEN
✓ Zero Drift matrix signed off
✓ Eight Pillars ≥ 9.70 (target 9.95+)

---

END OF NEXT-SESSION PROMPT
