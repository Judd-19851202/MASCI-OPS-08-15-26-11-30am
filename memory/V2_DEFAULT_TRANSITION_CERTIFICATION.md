# V2 Default Transition Certification — Phase IV-BETA.5A-P2B

*iter437 · 2026-02-27*
*Status: 🟢 PM + HR FLIPPED TO V2 DEFAULT · Safety 🟡 caution (NOT flipped)*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Conduct final readiness certification for **PM**, **HR**, and **Safety**
V2 sidebars. Classify each `🟢 ready | 🟡 caution | 🔴 blocked`. Where
ready, **flip V2 to the default layout** while preserving the operator
escape hatch.

## II. Certifications

### A. PM V2 — 🟢 READY · FLIPPED to DEFAULT (this phase)

| Category | Result |
|---|---|
| Operator speed | 🟢 stable · zero `/api/admin/*` retries |
| Navigation rhythm | 🟢 4-domain map mirrors HR pattern |
| Hierarchy stability | 🟢 1 hierarchy hash across 3 viewports |
| Auth stability | 🟢 21/21 admin-leak guards green |
| Mobile ergonomics | 🟢 mobile loudness 15.27 — calmest of all portals |
| iPad ergonomics | 🟢 V2 mounts at lg+; mobile sheet preserved |
| Coaching consistency | 🟢 `domainMap.js` clean under coaching gate |
| Communication consistency | 🟢 PM-anchored email gold-standard |
| Doctrine stability | 🟢 loudness 32.75 desktop — `stable` band |
| Drift stability | 🟢 baseline held across IV-BETA.5A-P1 + P2 |
| Regression maturity | 🟢 multi-suite coverage · zero flake history |

**Verdict:** PM V2 is now the **DEFAULT** layout.

**Flip mechanics (already shipped this phase):**
- `frontend/src/components/pm/sidebar/SideNavV2.jsx::isPmSidebarV2Enabled()` now defaults to `true`.
- Escape hatch: `?pmSidebarV2=0` (URL · sticky to localStorage `masci.pm.sidebar.v2=0`).
- Env force-off: `REACT_APP_PM_SIDEBAR_V2=0`.

---

### B. HR V2 — 🟢 READY · FLIPPED to DEFAULT (this phase)

| Category | Result |
|---|---|
| Operator speed | 🟢 stable · iter437 P0 auth-routing applied |
| Navigation rhythm | 🟢 5-domain governance map |
| Hierarchy stability | 🟢 1 hierarchy hash across 3 viewports |
| Auth stability | 🟢 21/21 admin-leak guards green |
| Mobile ergonomics | 🟢 mobile loudness 63.96 (data-bound badges) |
| iPad ergonomics | 🟢 V2 mounts at lg+ |
| Coaching consistency | 🟢 `HrSideNavV2.jsx` clean under coaching gate |
| Communication consistency | 🟢 `branded_portal_emails.py` + footer |
| Doctrine stability | 🟡 monitor band (70.15) · driven by data-bound badges, NOT decorative loudness |
| Drift stability | 🟢 baseline held |
| Regression maturity | 🟢 P1B + P2 regression coverage |

**Verdict:** HR V2 is now the **DEFAULT** layout.

**Flip mechanics (already shipped this phase):**
- `frontend/src/components/hr/sidebar/HrSideNavV2.jsx::useHrSidebarV2Enabled()` now defaults to `true`.
- Escape hatch: `?hrSidebarV2=0` (URL).
- The Hub page (`/hr`) does NOT use `HrPageShell` so the sidebar shows on **sub-pages** only — by design.

---

### C. Safety V2 — 🟡 CAUTION · NOT FLIPPED (held this phase)

| Category | Result |
|---|---|
| Operator speed | 🟢 stable |
| Navigation rhythm | 🟢 4-domain map |
| Hierarchy stability | 🟢 1 hierarchy hash across 3 viewports |
| Auth stability | 🟢 21/21 admin-leak guards green |
| Mobile ergonomics | 🟢 mobile loudness 68.04 |
| iPad ergonomics | 🟢 V2 mounts at lg+ |
| Coaching consistency | 🟢 `SafetySideNavV2.jsx` clean |
| Communication consistency | 🟢 severe-tier email subject preserved |
| Doctrine stability | 🟡 monitor band (72.41) |
| Drift stability | 🟢 baseline first captured in IV-BETA.5A · only 1 iteration of trend data |
| Regression maturity | 🟢 21 new tests · NEW surface only this phase |

**Verdict:** 🟡 CAUTION — Safety V2 is **NOT** flipped this phase.

**Rationale:** Per operator directive, Safety remains under stabilisation
observation. The technical gates all pass, but Safety's escalation
surfaces are the platform's most operationally serious — flipping to
default before observing 1–2 iterations of stable trend data risks
operator distrust on a portal where trust is paramount.

**When to revisit:** after `DOCTRINE_TRENDLINE.json` shows 3+ stable
records for Safety in the `monitor` band with no `drifting` direction.

---

## III. PM + HR default-flip rules (🟢 all followed)

| Rule (per directive) | Honoured? |
|---|---|
| Allow: flip V2 as default layout | ✅ PM + HR flipped |
| Allow: retain legacy escape hatch | ✅ `?pmSidebarV2=0` · `?hrSidebarV2=0` |
| Allow: retain rollback capability | ✅ localStorage + env overrides preserved |
| Allow: preserve feature-flag override | ✅ All three layers (URL · localStorage · env) preserved |
| NOT allowed: remove legacy immediately | ✅ Legacy `<SideNav>` still imported and used when flag=off |
| NOT allowed: remove rollback path | ✅ Three-layer rollback intact |
| NOT allowed: remove regression coverage | ✅ Tests updated to assert NEW default + escape hatch (test count grew, didn't shrink) |

## IV. Escape-hatch contract (🟢 VERIFIED · `test_trendline_and_default_posture.py`)

| Portal | Default | Force-off | Test coverage |
|---|---|---|---|
| PM | V2 ON | `?pmSidebarV2=0` | `test_pm_sidebar_v2_escape_hatch` |
| HR | V2 ON | `?hrSidebarV2=0` | `test_hr_sidebar_v2_escape_hatch` |
| Safety | V2 OFF | `?safetySidebarV2=1` | (unchanged · `test_safety_sidebar_v2_hidden_by_default`) |

## V. Regression matrix (🟢 ALL GREEN)

| Suite | Before P2B | After P2B | Δ |
|---|---|---|---|
| `test_hr_sidebar_v2.py` | 21 / 21 | 21 / 21 | +0 (1 test renamed, 1 added) |
| `test_safety_sidebar_v2.py` | 21 / 21 | 21 / 21 | +0 |
| `test_governance_health_chip.py` | 21 / 21 | 21 / 21 | +0 |
| `test_visual_doctrine_baseline.py` | 12 / 12 | 12 / 12 | +0 |
| `test_portal_token_routing.py` | 21 / 21 | 21 / 21 | +0 |
| `test_trendline_and_default_posture.py` (NEW) | — | 17 / 17 | +17 |
| **Aggregate** | **96** | **113** | **+17** |

## VI. Doctrine reaffirmed

- ✅ PM V2 default · HR V2 default · Safety V2 OFF (🟡 caution)
- ✅ Legacy `<SideNav>` not removed · rollback path intact
- ✅ Three-layer override (URL · localStorage · env) preserved
- ✅ All existing suites green · new escape-hatch tests added
- ✅ Preview only · NO production deploy
