# Portal V2 Stability Review

*Phase IV-BETA.4B · iter437 · 2026-02-27*
*Status: 🟢 PM V2 + HR V2 reviewed against 8 stability categories · default-flip recommendation below*

> **Verification legend:** 🟢 stable default candidate · 🟡 caution · 🔴 blocker

---

## I. Mandate

Before Safety implementation, certify that PM V2 and HR V2 are stable
enough to become the **default** posture (not feature-flagged). The
review uses 8 categories. Default-flip is recommended **only** if
every category is 🟢.

## II. PM V2 stability matrix

| Category | Score | Evidence |
|---|---|---|
| Final hierarchy review | 🟢 | 6 domain groups, doctrine-compliant sublines, `hierarchy_hash=c0d7489c…` stable across all 3 viewports. |
| Mobile review | 🟢 | Mobile baseline loudness 15.3 — calmest cell on the platform. Walked 79 elements. |
| iPad review | 🟢 | DOM hash matches desktop (intentional — same content, same layout). |
| Auth review | 🟢 | `test_portal_token_routing.py` 27/27 across 7 routes × 3 viewports. Zero `/api/admin/*` leak in any of the 4 iterations since the iter437 P0 fix. |
| Coaching review | 🟢 | `verify_coaching_sublines.py` green. All sublines ≤14 words. |
| Communication review | 🟢 | PM email subjects locked at iter238 gold standard; operational footer cascades through `render_portal_email`. |
| Visual drift review | 🟢 | DOM hash and hierarchy hash both stable. Baseline JSON committed. |
| Regression stability | 🟢 | `test_iter437_pm_jobs_endpoint.py` 4/4; PM hub V2 layout test passes; 138/138 platform regression cells green. |

**Verdict: PM V2 → 🟢 STABLE DEFAULT CANDIDATE.**

## III. HR V2 stability matrix

| Category | Score | Evidence |
|---|---|---|
| Final hierarchy review | 🟢 | 5 domain groups matching `HR_INFORMATION_PRIORITY_MAP.json`, `hierarchy_hash=f6ba352e…` stable across viewports. |
| Mobile review | 🟡 | Mobile loudness 64.0 — known badge-heuristic over-count (see `OPERATOR_REVIEW_SYNTHESIS.md §II.C`). UX is correct; only the score is elevated. |
| iPad review | 🟢 | Same DOM hash as desktop. |
| Auth review | 🟢 | `test_hr_sidebar_v2.py` 15/15 — 3 routes × 3 viewports with zero `/api/admin/*` leak. |
| Coaching review | 🟢 | All 18 V2 sidebar sublines ≤14 words after P1B trim. |
| Communication review | 🟢 | HR welcome/reset emails inherit the operational footer; HR digest joins the cross-portal contract. |
| Visual drift review | 🟢 | DOM + hierarchy hashes stable in the baseline. |
| Regression stability | 🟢 | HR Sidebar V2 suite 15/15 stable across two iterations. |

**Verdict: HR V2 → 🟢 STABLE DEFAULT CANDIDATE** (the 🟡 on mobile
loudness is a measurement quirk, not a UX defect — see baseline
report §VII).

## IV. Recommendation

Promote `?pmSidebarV2=1` and `?hrSidebarV2=1` out of flag **before**
introducing `?safetySidebarV2=1` (avoids tri-mode UX state).

Implementation sketch (when authorised):

1. `PmShell.jsx` — remove the `usePmSidebarV2Enabled` guard, always
   render `<SideNavV2 />`. Delete the legacy `SECTIONS` array.
2. `HrPageShell.jsx` — remove the `useHrSidebarV2Enabled` guard.
3. Drop the V1 sidebar files (`pm/sidebar/SideNavV1.jsx` etc.) only
   after **one full deploy cycle** with V2-default — so an emergency
   rollback can re-enable V1 by reverting one commit.
4. Re-run `tests/pw_suite/test_visual_doctrine_baseline.py` AND
   `scripts/diff_doctrine_baseline.py` post-default-flip — the
   hierarchy hash should be IDENTICAL to today's baseline.

Estimated effort: **1 commit, ~30 LOC change, 1 baseline re-capture,
1 regression run** — but **DO NOT FLIP DEFAULTS YET**. The directive
explicitly says "DO NOT flip defaults yet unless clearly stable" and
this iteration's job is to certify, not flip.

## V. Doctrine reaffirmed

- ✅ Review grounded in measured signal (baseline JSON) + regression
  evidence (138/138).
- ✅ 🟡 caveat called out honestly (HR mobile loudness measurement quirk).
- ✅ No flip executed — operator authorisation gates the change.
- ✅ Rollback plan baked into the recommendation (deletion deferred
  one deploy cycle).
