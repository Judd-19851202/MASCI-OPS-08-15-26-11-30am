# TRACK 20.9 · Zero-Drift Matrix

**Verdict:** 🟢 **Zero drift on production runtime behavior.**

## What Track 20.9 changed

| Category | Files | Nature of change |
|---|---|---|
| Frontend runtime code | 2 files | **Additive bug fixes only.** `MasterListPanel.jsx` gains a `restoreRow` function that was called but never defined (TD-20.9-A01). `TrenchBoxPosterCard.jsx` gains a `const branding = useBranding();` line that was implicitly assumed (TD-20.9-A02). Both fixes turn crashing code paths into working code paths per their obvious original intent. |
| Frontend build config | 1 new file (`eslint.config.js`) + 1 script edit (`package.json`) | Real ESLint 9 gate replaces stub. Does NOT touch runtime code. |
| Backend runtime code | **0 files** | No route added or removed · no permission gate modified · no email path added or removed. |
| Backend tests | 0 files touched (Track 20.9 lock test is new) | Test-only additions. |
| Repo hygiene | `/app/.gitignore` (862 → 140 lines) · `/app/README.md` (1 line → real runbook) · `/app/DEPLOYMENT_CHECKLIST.md` (iter142 → Track 20.9) | Doc-only edits. |

## Structural invariants (all preserved)

| Invariant | Before Track 20.9 | After Track 20.9 |
|---|---|---|
| Backend route count | 300+ | Same |
| Frontend route count | 300+ | Same |
| Number of `PhotoUpload.jsx` files | 1 | Same |
| Number of `_dispatch_auto_email` functions | 1 | Same |
| Track 20.6B synthetic-test-record short-circuit | Present | **Same — untouched** |
| Track 20.7 photo-capture fallback | Present | Same |
| CORS `allow_credentials=True` | Yes | Same |
| CORS regex `_DEFAULT_CORS_REGEX` | Present | Same |
| Env-var interface (`REACT_APP_BACKEND_URL`, `MONGO_URL`, `DB_NAME`, `RESEND_API_KEY`, etc.) | Unchanged | Unchanged |
| Universal Thread count (6) | Same | Same |
| Portal count (7) | Same | Same |
| Test envelope pass count | 385+ · 0 skipped · 0 failed | Same |

## Behavior deltas (surface-level only)

Both belong under the "make shipped UI actually work as designed" banner, not "change platform behavior":

1. **`MasterListPanel.jsx` archive-tab restore button** — was throwing `ReferenceError: restoreRow is not defined` on click; is now functional per the surrounding scaffolding (`restoreEndpoint` prop, `restoringId` state, restore icon UI). Users who clicked this button before Track 20.9 experienced a hard failure; users who click it after will see the intended toast + refresh flow.
2. **`TrenchBoxPosterCard.jsx` rendering** — every render was throwing `ReferenceError: branding is not defined` at the first `branding.safety_email` access; is now functional per the imported `useBranding` hook. The poster now renders per its obvious original intent.

Both fixes are **bug fixes, not behavior changes**. The code as authored assumed these identifiers existed. Track 20.9 completes the intent that was already in the file.

## What Track 20.9 explicitly did NOT do

- ❌ Did NOT refactor `server.py` (15,986 lines).
- ❌ Did NOT refactor `App.js` (1,283 lines).
- ❌ Did NOT tighten CORS `allow_methods` / `allow_headers`.
- ❌ Did NOT batch-fix the 909 remaining cosmetic lint errors.
- ❌ Did NOT dedupe the 708 duplicate keys in `frontend/src/lib/i18n.js`.
- ❌ Did NOT change any env-var default.
- ❌ Did NOT alter any dependency version in `backend/requirements.txt` or `frontend/package.json` (beyond the two `scripts` edits).
- ❌ Did NOT add any feature.
- ❌ Did NOT touch any workflow, permission, schema, or email path.

All deferred items are documented under `TRACK_20_9_SERVER_APP_SPLIT_PLAN.md` (server + app) and the Class-C tech-debt entries in `TECHNICAL_DEBT_REGISTER.md`.

## No parallel systems introduced

- Still exactly ONE `PhotoUpload.jsx`.
- Still exactly ONE `_dispatch_auto_email`.
- Still exactly ONE canonical multi-login endpoint.
- Still exactly ONE trust-spine event schema.
- Still exactly ONE ownership-lane vocabulary.

## Email safety

- The Track 20.6B synthetic-test-record short-circuit is byte-identical.
- Zero live emails triggered by Track 20.9 execution.
- No email transport touched.

## Deployment call

🟢 Zero-Drift-compliant. Ship.
