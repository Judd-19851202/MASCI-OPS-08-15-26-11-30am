# Dispatch Terminology Alignment — Phase IV-BETA.5A-P5B

*iter437 · 2026-02-27*
*Status: 🟢 ALIGNED · Dispatch vocabulary now in the cross-portal glossary*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Normalize Dispatch terminology with the established
`CROSS_PORTAL_VOCABULARY_GLOSSARY.md` (iter437 P3C). Confirm every
Dispatch label / kicker / subline / domain name aligns with the
canonical platform vocabulary.

## II. Portal-name alignment (🟢)

| Canonical | Source location | Status |
|---|---|---|
| **Dispatch Portal** | `DispatchHub.jsx` kicker · login form | 🟢 aligned |
| **Dispatch Command** | `DispatchHub.jsx` title | 🟢 already canonical — operator-recognised name |
| **Haul Board** | `DispatchBoard.jsx` page title · sidebar nav | 🟢 aligned |
| **Driver Coordination** | Sidebar V2 domain | 🟢 NEW · added by this sub-pass |
| **Lifecycle & Records** | Sidebar V2 domain | 🟢 NEW |
| **Guidance & Support** | Sidebar V2 domain | 🟢 NEW |

## III. Severity / escalation vocabulary (🟢)

Dispatch already uses the cross-portal canonical severity lexicon:

| Canonical | Source | Status |
|---|---|---|
| Critical | `severityTone() === "critical"` | 🟢 rose-100 / rose-900 — data-bound |
| High | `severityTone() === "high"` | 🟢 amber band |
| Medium | `severityTone() === "medium"` | 🟢 amber-emerald |
| Low | `severityTone() === "low"` | 🟢 emerald band |

## IV. Coaching subline alignment (🟢)

All 4 Dispatch sidebar domain sublines satisfy the platform standard:

| Domain | Subline | Word count | Period | ✓ |
|---|---|---|---|---|
| Live Board | "Haul-board, escalations, breakdowns. Real-time scan." | 6 | yes | 🟢 |
| Driver Coordination | "Drivers, qualifications, magic-link sessions." | 4 | yes | 🟢 |
| Lifecycle & Records | "Truck lifecycle, history, transition trails." | 5 | yes | 🟢 |
| Guidance & Support | "Operator guides, password rotation, training center." | 6 | yes | 🟢 |

Per-link description sublines also satisfy the ≤14 word budget; the
governance gate (`verify_coaching_sublines.py`) was extended to
include `DispatchSideNavV2.jsx` in `COACHING_FILES` and **passes**.

## V. Reserved punctuation alignment (🟢)

| Glyph | Use in Dispatch | Status |
|---|---|---|
| `·` (U+00B7) | Operational separator (e.g. "Trucking · Fleet") | 🟢 used canonically |
| `→` (U+2192) | CTA suffix on assignment-card "Open →" | 🟢 used canonically |
| `🚛` | Future · proposed for Dispatch email subject prefix `🚛 DISPATCH · …` | 🟡 NOT YET implemented — flagged for sub-pass 3 |

## VI. Anti-pattern check (🟢 no violations)

- ❌ "Empower" / "Streamline" / "Unleash" — NONE found
- ❌ Compound `·` more than 3 times — NONE found
- ❌ ALL-CAPS source text — NONE found
- ❌ Emoji in UI copy — NONE found (the `🚛` is a proposal, not in code)

## VII. Doctrine reaffirmed

- ✅ Dispatch vocabulary aligned with `CROSS_PORTAL_VOCABULARY_GLOSSARY.md`
- ✅ Coaching gate now governs Dispatch sidebar source
- ✅ Severity lexicon canonical
- ✅ Punctuation discipline canonical
- ✅ Preview only · NO production deploy
