# Safety Hub V2 Certification

*Phase IV-BETA.5A · iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · REGRESSION-LOCKED · awaiting operator review*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Apply Operational Calmness Doctrine to the Safety Portal **Hub surface
only** (Phase IV-BETA.5A scope). Eliminate false urgency so true
urgency stays unmistakable. Sidebar V2 ships behind
`?safetySidebarV2=1` to maintain zero-risk additive rollout.

## II. Scope honoured (🟢 VERIFIED · operator directive)

In-scope and now implemented:

- Safety Hub (`SafetyHub.jsx`) tile palette + CTA collapse
- Safety Sidebar V2 (`SafetySideNavV2.jsx`) — 4-domain group structure
- `SafetyShell.jsx` conditional sidebar mount behind flag
- Incident surfaces (see `SAFETY_INCIDENT_GOVERNANCE_ALIGNMENT.md`)
- Hub mobile + iPad layouts (see `SAFETY_MOBILE_CALMNESS_REPORT.md`)
- Visual loudness reduction (see `SAFETY_ESCALATION_VISUAL_REDUCTION.md`)
- Sidebar hierarchy (4-domain group)
- Regression harness (see `SAFETY_PLAYWRIGHT_REGRESSION_REPORT.md`)

**OUT of scope (deliberately NOT touched · per directive):**

- Inspections, Reports, JHA, Trench, Compliance Engine, OSHA Export
- Notification engine, backend escalation logic
- Database schemas, auth/permissions
- Live compliance workflows

## III. Sidebar V2 contract (🟢 VERIFIED)

`SafetySideNavV2.jsx` ships behind `?safetySidebarV2=1`. When flag
is OFF, the legacy single-column Safety layout renders unchanged.

| Domain | Stripe | Purpose |
|---|---|---|
| Incidents & Escalation | `#b91c1c` (red-700) | The ONE red domain — owns true urgency signalling. |
| Documents & Training | `#0e7490` (cyan-700) | Safety brand chrome — operational reference. |
| Compliance & Records | `#7c3aed` (violet-600) | Read-mostly compliance, expirations, reports. |
| Audits & Guidance | `#475569` (slate-600) | Lowest-frequency surfaces. Visually demoted. |

Coaching sublines: all ≤14 words, sentence case, period termination.
Passes `verify_coaching_sublines.py` (now includes the new
`SafetySideNavV2.jsx` in `COACHING_FILES`).

## IV. Hub V2 changes (🟢 VERIFIED)

| Before (iter318 baseline) | After (iter437 IV-BETA.5A) |
|---|---|
| 9 distinct hue families on Hub tiles | **2** hue families (per doctrine baseline) |
| 8 distinct CTA button colours | **1** neutral `slate-800` CTA across all 16 tiles |
| Decorative red on non-incidents tiles | Red **reserved** for incidents domain only |
| Tile sublines: 5 over 14-word budget | **0** sublines over 14-word budget |
| Loud amber-600 icon block on Incidents page header | Neutral `slate-800` icon block + red-700 stripe |
| `STATUS_PILL` open=red, investigating=amber, closed=emerald | All **slate-100** (status ≠ severity; severity pill remains the danger signal) |

## V. Test results (🟢 VERIFIED · `python3 -m pytest tests/pw_suite/`)

| Suite | Outcome |
|---|---|
| `test_safety_sidebar_v2.py` | 21 pass · 0 fail |
| `test_visual_doctrine_baseline.py` | 12 pass (Safety + HR + PM + Admin × desktop / iPad / mobile) |
| `test_hr_sidebar_v2.py` | 21 pass (HR regression stays green) |
| `test_portal_token_routing.py` | 21 pass (zero `/api/admin/*` leakage) |

Visual baseline snapshot (Safety):

| Viewport | Hue families | Loudness | Elements |
|---|---|---|---|
| desktop | 2 | 66.78 | 133 |
| ipad | 2 | 66.78 | 133 |
| mobile | 2 | 68.04 | 106 |

Hue family count collapsed from **9 → 2** vs the iter437 IV-BETA.4
audit baseline. (The remaining loudness score is dominated by the
existing badge density inherent to the Hub KPI strip + severity
pills — both of which are *preserved by doctrine* as true-signal
elements.)

## VI. Doctrine preserved (🟢)

- ✅ Severity pills (`SEV_PILL`) untouched — true urgency still loud
- ✅ Severe-tier banner pattern untouched (record-level only)
- ✅ Severe-incident email subject `🚨 SEVERE INCIDENT · …` untouched
- ✅ Operational seriousness preserved · NOT "minimalised"
- ✅ Operator accountability surfaces (aging badge, OSHA recordable
  pill) preserved as data-bound signal
- ✅ Sidebar V2 ships behind flag · legacy users unaffected
- ✅ Preview only · NO production deploy this phase

## VII. Hand-off

This document closes the Hub V2 + Sidebar V2 + Incident-surface phase
(Phase IV-BETA.5A). The **Inspections / Reports / JHA / Trench**
governance phase is **NOT YET AUTHORISED** — operator review of these
deliverables is required before any further Safety surface is touched.
