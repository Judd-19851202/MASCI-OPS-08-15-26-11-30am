# Safety Escalation Visual Reduction

*Phase IV-BETA.5A · iter437 · 2026-02-27*
*Status: 🟢 IMPLEMENTED · doctrine baseline updated*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Remove **false** urgency from the Safety portal so **true** urgency
becomes unmistakable. Specifically: collapse the 9-hue Hub palette to
the 4-domain doctrine palette, retire decorative red, and neutralise
per-tile CTA explosion.

## II. Before / after (🟢 VERIFIED · doctrine baseline)

Source: `/app/memory/HUB_VISUAL_BASELINE.json` post iter437 IV-BETA.5A.

| Metric | Audit (iter437 IV-BETA.4) | Post-pass (iter437 IV-BETA.5A) |
|---|---|---|
| Distinct hue families (Hub) | **9** | **2** (per baseline desktop) |
| `bg-*` per-page hits (Hub) | 5.8 avg | (not yet re-measured per-page — pending) |
| Red occurrences (Hub) | **42** | **3** (incidents-domain tiles only) |
| Per-tile CTA colours | 8 distinct | **1** neutral `slate-800` |
| Loudness composite | not yet baselined | desktop=66.78 · ipad=66.78 · mobile=68.04 |
| Sublines over 14-word budget | 5+ | **0** (passes `verify_coaching_sublines.py`) |

## III. Reserved-red discipline (🟢 contract preserved)

Red is now reserved for these surfaces ONLY:

| Surface | Element | Red usage | Verdict |
|---|---|---|---|
| Severity pill (`SEV_PILL`) | data-bound | red-700 / red-100 | 🟢 preserved · TRUE signal |
| Incidents tile stripe (Hub) | static | red-700 left border | 🟢 ONE red domain |
| Incidents page header stripe | static | red-700 left border | 🟢 page-level anchor |
| OSHA Recordable pill | data-bound | red-900 | 🟢 preserved · TRUE signal |
| Severe-tier banner (`ViewIncident`) | data-bound | rose tone | 🟢 preserved · per-record only |
| Severe-incident email prefix | static | `🚨 SEVERE INCIDENT` | 🟢 preserved · TRUE signal |

## IV. Demoted (🟢 false urgency removed)

| Element | Before | After |
|---|---|---|
| `STATUS_PILL` Open | red-100 | slate-100 |
| `STATUS_PILL` Investigating | amber-100 | slate-100 |
| `STATUS_PILL` Closed | emerald-100 | slate-100 (faded) |
| Incidents page header icon block | amber-600 | slate-800 |
| Incidents page header kicker | amber-700 | red-700 (matches incidents-domain stripe) |
| Hub CTA buttons (8 colours) | red/redDeep/amber/emerald/cyan/indigo/slate/purple | single slate-800 |
| Hub tile stripes (8 colours) | 8 distinct | 4 (red · cyan · violet · slate) |
| `Fire Extinguishers` accent | redDeep (red-900) | violet-600 (compliance domain) |
| `Weekly Digest` accent | emerald | violet-600 (compliance domain) |
| `Topic Library` accent | amber | slate-500 (audits & guidance) |
| `Trucking · Fleet` accent | amber | slate-500 (audits & guidance) |

## V. CTA neutralisation (🟢)

All 16 Hub tile CTA spans now share `bg-slate-800 hover:bg-slate-900`.
The accent prop is intentionally **decoupled** from the CTA — the
left-edge stripe carries the domain identity. This matches the HR P1B
trim pattern and removes 8 distinct on-tile button colours from the
Hub at one stroke.

## VI. Sidebar V2 stripe palette (🟢)

`SafetySideNavV2.jsx` uses 4 stripe colours, mirroring the Hub palette:

| Domain | Stripe |
|---|---|
| Incidents & Escalation | red-700 (`#b91c1c`) |
| Documents & Training | cyan-700 (`#0e7490`) |
| Compliance & Records | violet-600 (`#7c3aed`) |
| Audits & Guidance | slate-600 (`#475569`) |

No fifth stripe, no per-route accent — the domain stripe is the
single visual identifier.

## VII. Doctrine reaffirmed (🟢)

- ✅ Severity pill (data-bound) untouched · TRUE urgency loud
- ✅ Severe-tier banner per-record discipline preserved
- ✅ Severe-incident email subject preserved
- ✅ Red reserved for incidents-domain tile/sidebar stripes + severity pills
- ✅ Single neutral CTA across Hub
- ✅ No decorative red on non-incidents surfaces
- ✅ Sublines ≤14 words across the governed Sidebar V2
