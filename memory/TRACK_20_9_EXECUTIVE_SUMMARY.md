# TRACK 20.9 · Executive Summary

**Verdict:** 🟢 **DEPLOYMENT-READY.** Codebase is cleaner. Two Class-A runtime bugs fixed. Zero platform behavior changed.

## What Track 20.9 did (nine surgical cleanups)

| # | Item | Result |
|---|---|---|
| 1 | Frontend lint — replace fake stub with real ESLint 9 | ✅ Real `eslint.config.js` in place · `yarn lint` runs authoritative rules · `yarn lint:strict` gates CI. |
| 2 | Two Class-A runtime bugs caught by the new lint | ✅ **FIXED** — TD-20.9-A01 (`restoreRow` undefined in `MasterListPanel.jsx`) · TD-20.9-A02 (`branding` undefined in `TrenchBoxPosterCard.jsx`). |
| 3 | Deployment checklist — refresh from iter142 stale to Track 20.8 standard | ✅ Rewritten to include synthetic `TEST_` email gate · photo fallback smoke · Operational Threads smoke · post-deploy monitoring. |
| 4 | README / RUNBOOK — replace "Here are your Instructions" boilerplate | ✅ Real MASCI runbook: boot / test / deploy / rollback / env vars / health checks / email-safety rule / track discipline / common runbooks. |
| 5 | Requirements cleanup | ✅ **NO CHANGE NEEDED.** Verified `backend/requirements.txt` is already 169 lines · one dependency per line · all versions pinned · no whitespace-separated multi-deps. |
| 6 | `.gitignore` cleanup | ✅ Rewritten from 862 lines of leaked webpack cache filenames + duplicated `credentials.json` blocks to 140 concise lines. Every secret protection preserved. Track 15.80 lock preserved. |
| 7 | `server.py` audit / safe split plan | ✅ Audited. **No refactor pre-deploy** — the file is 15,986 lines, imported from 100+ places. Phase-2 split plan documented in `TRACK_20_9_SERVER_APP_SPLIT_PLAN.md`. |
| 8 | `App.js` audit / safe split plan | ✅ Audited. **No refactor pre-deploy** — the file is 1,283 lines and defines the entire 300+ route registry. Phase-2 route-group extraction plan documented. |
| 9 | CORS hardening review | ✅ Reviewed. `allow_credentials=True` + regex domain lock + explicit prod list. `allow_methods=["*"]` and `allow_headers=["*"]` are intentional (Universal Threads use many methods). Phase-2 tightening plan documented. |
| 10 | Public repo security review | ✅ `git ls-files` grep for `.env` / `credentials.json` / `.pem` / SEALED* / SECRETS_* returns zero real secret matches. Only match is the secret-scanner test file itself. |

## Class-A bugs fixed inline (per Track 20.6A doctrine)

- **TD-20.9-A01** — `MasterListPanel.jsx::restoreRow` was called from the archive-tab restore button but never defined. Every restore click would throw `ReferenceError`. Fixed by adding the missing function using the same pattern as other row mutations in the file.
- **TD-20.9-A02** — `TrenchBoxPosterCard.jsx` imported `useBranding` but never called it, then referenced `branding.safety_email` in JSX. Every render would throw `ReferenceError`. Fixed by calling `const branding = useBranding();`.

Both fixes are TEST-ONLY-DISCOVERY / RUNTIME-BUG-FIX — the lint gate that caught them is genuinely new value.

## Class-C tech debt classified (fix post-deploy)

- **TD-20.9-C01** — 708 duplicate keys in `frontend/src/lib/i18n.js` bilingual dictionary. Real silent bug (last-write-wins on translations), but 700+ manual dedupes carries real risk to actual translations. Dedicated bilingual cleanup track.
- **TD-20.9-C02** — 188 `react/no-unescaped-entities` errors (quote-escape cosmetics). Auto-fixable via `eslint --fix`, but touching 188 files pre-deploy is unnecessary risk. Batch-fix track.
- **TD-20.9-C03** — 78 unused `eslint-disable` directive warnings. Batch-fix track.
- **TD-20.9-C04** — 6 `react/no-unstable-nested-components` errors. Real render-perf bugs but not runtime crashes. Careful-refactor track.
- **TD-20.9-C05** — 5 `no-empty` in `GlobalSearch.jsx` — intentional `catch {}` around `localStorage` for private-browsing safety. Change to `catch { /* storage unavailable */ }` in a small polish track.

All logged in `TECHNICAL_DEBT_REGISTER.md`.

## Zero-drift proof (production behavior)

- Backend: **zero routes added/removed** · **zero payload shape changed** · **zero permission gate modified** · **zero email path added or removed** · **zero collection touched**.
- Frontend: **zero routes added/removed** · two undefined-identifier fixes (surface bug → no bug — behavior improves, existing surface unaffected).
- Emails: **zero live emails triggered** by Track 20.9 execution.
- Test envelope: same 385+ passed · 0 skipped · 0 failed as Track 20.8.

## Deliverables

10 markdown docs under `memory/TRACK_20_9_*.md` (executive summary · cleanup report · deployment-checklist update · README/runbook report · dependency-format report · gitignore-security report · server/app split plan · zero-drift matrix · test report · TD-20.9-A01/A02 fix reports rolled into cleanup report) + lock test `backend/tests/test_track_20_9_cleanup.py`.

## Deployment call

🟢 **GO.**
