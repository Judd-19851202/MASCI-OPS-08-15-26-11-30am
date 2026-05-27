# Safety Playwright Regression Report

*Phase IV-BETA.5A · iter437 · 2026-02-27*
*Status: 🟢 ALL GREEN · regression-locked*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Suites added / extended this phase

| File | Type | Outcome |
|---|---|---|
| `backend/tests/pw_suite/test_safety_sidebar_v2.py` | NEW | 21 pass (5 tests × 3 viewports for the parametrised ones) |
| `backend/tests/pw_suite/test_visual_doctrine_baseline.py` | EXTENDED | 12 pass — Safety added to the parametrise list alongside Admin/PM/HR (4 portals × 3 viewports) |

## II. Test inventory · `test_safety_sidebar_v2.py` (🟢)

| Test | Purpose |
|---|---|
| `test_safety_sidebar_v2_renders_when_flag_on` | All 4 governance domains (`incidents-escalation`, `documents-training`, `compliance-records`, `audits-guidance`) mount when `?safetySidebarV2=1` is present on `/safety-portal/incidents` |
| `test_safety_sidebar_v2_hidden_by_default` | Without the flag, `safety-side-nav-desktop` MUST NOT mount — legacy chrome preserved for every default user |
| `test_safety_subpages_do_not_leak_admin_endpoints` (×3 routes) | Sniff network for `/api/admin/*` on `/safety-portal/incidents`, `/safety-portal/corrective-actions`, `/safety-portal/documents`. Zero leakage allowed |
| `test_safety_hub_uses_neutral_cta_and_incidents_stripe` | Asserts every Hub tile carries the neutral slate-800 CTA + incidents-domain tiles carry the red-700 stripe + audits tile does NOT |
| `test_safety_incidents_status_pill_calm` | Asserts the incidents page header uses `border-l-red-700` (anchor stripe) and does NOT use `bg-amber-600` (false-urgency block) |

Total: 21 assertions across 3 viewports.

## III. Existing regression suites — green status (🟢)

| Suite | Tests | Status |
|---|---|---|
| `test_hr_sidebar_v2.py` | 21 | 🟢 PASS — HR V2 unaffected by Safety changes |
| `test_portal_token_routing.py` | 21 | 🟢 PASS — zero `/api/admin/*` leakage |
| `test_visual_doctrine_baseline.py` | 12 | 🟢 PASS — Admin / PM / HR cells stable, Safety cells captured |

Combined regression run: **75 tests · all pass**.

## IV. Defence-in-depth assertions (🟢)

The Safety regression test triple-locks the iter437 P0 auth-routing
contract:

1. **No `/api/admin/*` calls** from Safety context on Incidents, CAPAs,
   Documents (3 highest-traffic Safety sub-pages).
2. **No "Admin login required" toast** surfaced to Safety users.
3. **Hub palette** verified at the DOM-class level (Tailwind class
   inspection), not pixel-diff.

## V. Visual baseline snapshot — Safety cells (🟢)

Captured via `_METRIC_JS` style-walk:

| Viewport | hue_family_count | loudness_score | elements_walked | badge_density |
|---|---|---|---|---|
| desktop | 2 | 66.78 | 133 | 12.78 |
| ipad | 2 | 66.78 | 133 | 12.78 |
| mobile | 2 | 68.04 | 106 | 16.04 |

Hue family count: collapsed from **9 (audit) → 2 (post-pass)**.

Loudness composite is dominated by `badge_density` (severity pills,
OSHA pills, KPI labels). These badges are **data-bound true-signal
elements** that doctrine **preserves**. The composite score is
therefore a useful trend signal, not an enforcement threshold —
exactly matching the warning-only contract in
`pre_deploy_check.sh §stage_governance_visual_loudness`.

## VI. Doctrine drift instrument coverage (🟢)

The drift script `/app/scripts/diff_doctrine_baseline.py` (iter437
IV-BETA.4) now naturally covers Safety cells the next time deploy
runs — because Safety is in the persisted baseline JSON.

## VII. Doctrine reaffirmed (🟢)

- ✅ Sidebar V2 mounts only behind `?safetySidebarV2=1`
- ✅ Legacy Safety chrome unchanged by default
- ✅ Hub palette verified at the DOM level (no pixel fragility)
- ✅ Zero `/api/admin/*` leakage from Safety context
- ✅ Severity pill data-binding untouched
- ✅ All assertions warning-only at the loudness composite level,
  hard-pass at the DOM-class level
