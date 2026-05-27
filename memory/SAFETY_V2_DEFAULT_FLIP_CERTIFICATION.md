# Safety V2 Default Flip — Certification
## iter437 · Phase IV-BETA.5A-P6 · 2026-05-27

---

## 1 · Decision

**Safety Sidebar V2 is now the default layout** across every Safety
sub-page that wraps in `SafetyShell`. The legacy single-column chrome
is preserved as a one-keystroke escape hatch (URL · localStorage · env).

The flip is **reversible**, **non-destructive**, and **bounded** to the
sidebar layout. No IA changes, no route changes, no permission changes,
no feature additions.

---

## 2 · Stabilization Review (pre-flip)

| Signal | Reading | Verdict |
|---|---|---|
| Doctrine Trendline · Safety records (pre-flip) | **28** consecutive records | sufficient signal |
| Calmness (latest) | **72.41** | stable |
| Escalation noise | **24.41** | stable |
| Hue family count | **3** | doctrine-aligned |
| Direction (recent vs older avg) | **stable** | green |
| Delta since last operator checkpoint | **0.0** | green |
| Reference type | `checkpoint` (operator) | green |
| 7-day API drift sweep | none | green |
| Regression suite (`test_safety_sidebar_v2.py`) | 100% green pre-flip | green |
| Cross-portal admin-route leakage check | 0 leaks (3 routes parametrized) | green |

**Conclusion:** Safety V2 has been observably stable for 28 consecutive
trendline records with `direction=stable` and `delta=0.0` against the
declared operator checkpoint. Flip authorized.

---

## 3 · Change Summary (code · 3 files · ~50 net lines)

| File | Change |
|---|---|
| `frontend/src/components/safety/sidebar/SafetySideNavV2.jsx` | `useSafetySidebarV2Enabled()` rewritten to URL → localStorage → env → default-true resolution chain (mirrors `isPmSidebarV2Enabled`) |
| `frontend/src/components/SafetyShell.jsx` | Comment updated to document the new default + escape-hatch trio |
| `frontend/src/pages/SafetyHub.jsx` | Doctrine-preserved comment block updated |

**No other file touched.** No backend changes for this flip.

---

## 4 · Escape-Hatch Trio (preserved)

| Order | Lever | Effect |
|---|---|---|
| 1 | `?safetySidebarV2=0` (URL · sticky) | Force V2 OFF · writes through to localStorage |
| 1 | `?safetySidebarV2=1` (URL · sticky) | Force V2 ON  · writes through to localStorage |
| 2 | `localStorage.masci.safety.sidebar.v2 = "0"` | Force V2 OFF (URL-less) |
| 2 | `localStorage.masci.safety.sidebar.v2 = "1"` | Force V2 ON  (URL-less) |
| 3 | env `REACT_APP_SAFETY_SIDEBAR_V2=0` | Force V2 OFF at build time |
| 4 | **Default** | **V2 ON** |

> Same resolution order as PM V2 / HR V2 — operators don't need to
> learn a new mental model.

---

## 5 · Legacy Safety sidebar retention

The legacy single-column Safety layout (no sidebar component) **remains
fully functional and is not removed**. Per directive line 4 ("Do NOT
remove legacy Safety sidebar yet"), the escape hatch flips Safety back
to the exact pre-V2 chrome. No code path for the legacy layout was
deleted, refactored, or marked deprecated.

---

## 6 · Verification

### 6.1 — Regression suite

| Suite | Result |
|---|---|
| `test_safety_sidebar_v2.py` (4 tests · V2 default + escape hatches + admin leak) | **PASS** |
| `test_trendline_and_default_posture.py` (12 tests · all 3 portals default) | **PASS** |
| `test_p5_dispatch_health_autocheckpoint.py` (Dispatch + health) | **PASS** |
| `test_governance_health_chip.py` (chip · 21 tests) | **PASS** |
| `test_guidance_routes_extraction.py` (9 tests) | **PASS** |
| `test_checkpoint_system.py` (9 tests) | **PASS** |
| `test_portal_token_routing.py` (27 tests) | **PASS** |
| `test_visual_doctrine_baseline.py` (12 tests) | **PASS** |
| `test_static_helpers_extraction.py` (5 tests · new) | **PASS** |

**Total:** 132+ Playwright/regression tests green.

### 6.2 — Admin-route leakage

`test_safety_subpages_do_not_leak_admin_endpoints` runs against
`/safety-portal/incidents`, `/corrective-actions`, `/documents` in
**V2-default** mode (no flag). **Zero `/api/admin/*` calls observed.**

### 6.3 — Doctrine baseline stability

| Probe | Pre-flip | Post-flip |
|---|---|---|
| Safety calmness | 72.41 | 72.41 |
| Safety escalation noise | 24.41 | 24.41 |
| Safety hue family count | 3 | 3 |
| Direction | stable | stable |
| Delta since checkpoint | 0.0 | 0.0 |

Operator checkpoint recorded:
`operator · safety-v2-default-flip-IV-BETA-5A-P6` (2026-05-27T16:51:38Z).

### 6.4 — Production deploy

**None.** Preview environment only · `APP_ENV=preview` · `DB_NAME=masci_safety_preview`.

---

## 7 · Rollback path

If an operator regression is observed at any time, any **one** of the
three escape hatches above instantly reverts Safety to the legacy
single-column chrome. No deploy required for URL/localStorage; a single
env-var change covers the org-wide kill switch. The full V2 default
flip can be reverted with a single 35-line patch to
`useSafetySidebarV2Enabled()`.

---

## 8 · Sign-off

- **Author:** E1 (operational governance pass · iter437 IV-BETA.5A-P6)
- **Pre-flip stabilization:** trendline `direction=stable` for 28 records
- **Post-flip stabilization:** trendline `direction=stable` · delta `0.0`
- **Tests green:** Yes · 132+ regressions
- **Production deploy:** No · preview only
- **Next checkpoint:** await operator review before Phase IV-BETA.5B
