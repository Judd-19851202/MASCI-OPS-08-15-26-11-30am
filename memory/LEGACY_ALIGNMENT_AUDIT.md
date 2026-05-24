# LEGACY_ALIGNMENT_AUDIT.md
**Phase 17 · iter413 · 2026-05-24**

## Verdict
**PASS for live deployment.** All pre-Phase-12 modules remain operationally correct. Aesthetic drift exists but does not impair workflows. No fix required pre-rollout; queued as P2/P3 backlog.

## What "legacy" means in this audit
Pre-iter392 modules built before the DLS / Phase-12+ doctrine emerged. These predate:
- `LifecycleGuide` coaching pattern
- Section-card platform rhythm (white card + colored left stripe)
- Operator vocabulary scanner enforcement
- 3,526-entry i18n coverage push

## Modules audited
| Module | Doctrine alignment | Visual rhythm | Translation | Coaching | Verdict |
|---|---|---|---|---|---|
| **Daily Report Builder** | ✅ correct flow | ⚠️ older form-density | ⚠️ partial | ⚠️ minimal | Non-blocking |
| **Safety detail pages** | ✅ doctrine-quiet on DLS | ⚠️ pre-Phase-12 | ⚠️ partial | ⚠️ pre-LifecycleGuide | Non-blocking |
| **HR Qualification screens** | ✅ scope discipline | ⚠️ older table-style | ⚠️ partial | ⚠️ minimal | Non-blocking |
| **Inspections / Pre-Ops** | ✅ correct | ⚠️ older form chrome | ⚠️ partial | ⚠️ form-instructional only | Non-blocking |
| **Asset Transfers list** | ✅ reused by iter411 hub | ✅ aligned | ✅ | ✅ | Aligned (was modernized through iter319) |
| **Field Leadership pages** | ✅ aligned via iter319 | ✅ aligned | ✅ | ✅ via iter319+iter396 | Aligned |
| **Public Field Tile `/field`** | ✅ aligned via iter403/404 | ✅ aligned | ✅ | ✅ via iter404 | Aligned |
| **Public Forms `/forms/*`** | ✅ correct routing | ⚠️ older form chrome | ⚠️ partial | ⚠️ minimal | Non-blocking |

## Drift patterns NOT present (verified)
- ❌ Old role-creep (Safety leaking DLS, PM operating dispatch) — clean (see `ROLE_VISIBILITY_AUDIT.md`)
- ❌ Old write surfaces masquerading as read-only — clean
- ❌ Old hardcoded English-only labels in critical paths — clean for Phase 12-17 surfaces
- ❌ Old dashboard sprawl reintroduced — restraint scanner clean

## Drift patterns PRESENT (non-blocking, queued)
1. **Form-density legacy** — older forms use compact label-input pairs vs the iter408-era spaced `min-h-[48px]` searchable comboboxes
2. **Pre-LifecycleGuide coaching** — older pages explain via paragraph headers, not the `LifecycleGuide` 4-section pattern
3. **Translation coverage gaps** — older validation messages + tooltips still English-only in edge paths
4. **Pre-card-rhythm chrome** — older pages use `bg-white p-4 border` without the colored-left-stripe convention of Phase 12+

## Why we are NOT fixing this in iter413
The Phase 17 directive is explicit: **"DO NOT fix everything immediately. FIRST find ALL gaps. THEN prioritize surgically."**

Legacy aesthetic drift is:
- ✅ Not a blocker for Day-1 operations (workflows still complete correctly)
- ✅ Not a doctrine violation (no role-creep, no analytics drift, no ERP behavior)
- ✅ Captured for future surgical pickup once Day-1 debrief names the modules operations actually struggle with

## Backlog priorities derived
- 🟠 P2 — Inspections + Daily Report form chrome modernization (if Day-1 debrief names them as friction)
- 🟠 P2 — Safety detail page card-rhythm alignment (if Safety leadership requests)
- 🟠 P2 — HR Qualification screen modernization (low usage frequency → defer)
- 🔵 P3 — Translation coverage sweep across legacy forms (Day-1 debrief Question 8 will scope this)

## Verdict
Legacy alignment debt acknowledged, scoped, and held until Day-1 names which gaps actually cost operations time. **Restraint maintained.**
