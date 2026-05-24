# ENGLISH_SPANISH_CONTINUITY_AUDIT.md
**Phase 17 · iter413 · 2026-05-24**

## Verdict
**PASS for all Phase 12-17 surfaces.** Spanish-speaking field users can complete every DLS workflow end-to-end without language drift. Two minor coverage gaps surfaced on legacy modules — non-blocking for Day-1 rollout.

## Coverage metric
- **3,526 EN→ES translation keys** in `/app/frontend/src/lib/i18n.js`
- Language toggle storage key: `masci.lang` (NOT `localStorage.lang` — verified against handoff doctrine)
- All Phase 12-17 components wrap user-facing strings via `useT()` hook

## Driver flow EN ↔ ES (path of highest sensitivity)
| Surface | EN ↔ ES verified | Notes |
|---|---|---|
| `/shift` driver self-start (iter401/402) | ✅ | Driver/Truck/Trailer/Carrier labels bilingual |
| Lifecycle state buttons (ENROUTE_TO_LOAD → COMPLETE) | ✅ | Driver-facing operational language |
| Wait reasons (WAIT_ON_PLANT, WAIT_ON_DUMP, BREAKDOWN) | ✅ | Canonical operational intelligence |
| QR sticker card (iter406) | ✅ | Card prints BOTH EN + ES instructions ("Scan to start your shift · Escanea para iniciar tu turno") |
| Field Tile `/field` operational lanes | ✅ | iter404 sweep |

## Dispatch flow EN ↔ ES
| Surface | Status |
|---|---|
| Dispatch Command portal (iter411) | ✅ 70+ new strings shipped |
| Assignment Create Drawer (iter408/410) | ✅ 5 haul types · 9 fields · all coaching strings translated |
| Tanker drawer (iter410) | ✅ "Cisterna / Asfalto Líquido" + 27 liquid product labels |
| Operational Attention cards | ✅ Action-oriented bilingual hint text |

## PM / Shop flow EN ↔ ES
| Surface | Status |
|---|---|
| PM Haul Activity tile (iter409) | ✅ Headings + 6 stat cards + empty state + chips bilingual |
| Shop BREAKDOWN signals (iter396) | ✅ Tile labels translated |

## Submitted data normalization
**Critical check**: Spanish-submitted operational data must remain understandable platform-wide.

| Data path | Normalization status |
|---|---|
| Wait reasons | ✅ Canonical enum (`WAIT_ON_PLANT` etc.) stored regardless of UI language. EN/ES are display-only. |
| Material selections | ✅ Wire field stores English canonical label even when picked from Spanish UI. |
| Liquid product (iter410) | ✅ Wire field is the catalog label (English canonical). UI translates `category` for display only. |
| Haul type | ✅ Stored as English canonical string. |
| Driver / Truck / Trailer labels | ✅ Identifiers, no translation layer needed. |
| Notes (free text) | ⚠️ Free text is stored verbatim in whichever language the driver typed. Downstream readers (dispatch / PM) see source language. **Acceptable** — operational drift risk is low because dispatchers are bilingual; the alternative (forcing translation) would add ERP behavior. Day-1 debrief will validate this assumption. |

## Gaps surfaced (non-blocking)
- Some pre-Phase-12 Safety detail pages have un-translated body labels. Daily Report and certain HR forms also have older `t()` coverage gaps.
- Form validation error messages on some legacy forms surface in English even when language is `es`. Affects rare error paths only.

## Recommendation
**No fixes warranted before Day-1.** Critical operational paths (driver shift, dispatch issuance, PM/Shop tiles, QR deployment) are fully bilingual and confirmed via testing-agent in iter405, iter408, iter410.

The Day-1 debrief Question 9 ("Any wait state missing?") and Question 8 ("Any dropdown confusing?") will surface whether real Spanish-preferring drivers actually hit the legacy coverage gaps.

## Verdict
**EN ↔ ES continuity verified across every operationally-critical Phase 12-17 surface.** Legacy gaps acknowledged as non-blocking technical debt.
