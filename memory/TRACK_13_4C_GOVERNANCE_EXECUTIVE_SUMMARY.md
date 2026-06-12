# Track 13.4C — Governance, Prioritisation & Recovery-Planning Executive Summary

**Mode:** decision framework only.  
**Status:** complete · NO implementation · NO design · NO standardisation · NO recovery work · NO white-label building.  
**Generated:** 2026-02.

---

## 1. Executive Summary

Track 13.4B's discovery surfaced 77 catalogued findings across 8
documents. Track 13.4C does not solve any of them. Instead it:

- Separates **MASCI operational recovery** from **ForgedOps productisation**
  so the two roadmaps cannot distort each other.
- Names what is good and **must be preserved** (12 items).
- Names what is duplicative or wrong-role and **could be removed**
  (10 categories).
- Names what needs **rebuild** (8 areas) and what needs
  **standardisation** (10 surfaces).
- Maps every Tier-1 finding against the **Five Pillars** —
  *Trust* and *Proven* are the dominantly-violated pillars today.
- Issues a **Master Risk Register** of 33 risks, each status-`observed`.

No decision binds engineering to act on any of this. Each list is a
gate the operator unlocks per-track.

---

## 2. Top 10 MASCI Operational Priorities

From `/app/memory/MASCI_OPERATIONAL_RECOVERY_PRIORITY_STACK.md`:

1. **D-01 Production Motive webhook unverified** — Dispatch trust depends on this.
2. **D-03 100 / 190 assets without GPS** — dispatcher cannot locate 53 % of fleet from the map.
3. **D-04 157 stale assets** — dispatcher fog of war.
4. **T-01 Safety-Critical UI Spanish 75.8 %** — Spanish crew reads safety strings in English.
5. **T-08 / T-09 Outbound emails & PDFs 0 % Spanish** — Spanish recipients get English-only documents.
6. **V-11 Status verb overload** — `offline` / `active` / `open` each mean ≥ 3 different things.
7. **V-12 Closure verb drift** — 7 different closure verbs.
8. **R-06 `OperationsActionsTile` still on 6 portals** — cross-portal language inside role portals.
9. **R-02 Daily / Inspect / Incident form overlap** — foremen re-enter the same data.
10. **V-15 Driver portal landing missing** — drivers have no static "today" surface.

---

## 3. Top 10 ForgedOps Productisation Priorities

From `/app/memory/FORGEDOPS_PRODUCTIZATION_PRIORITY_STACK.md`:

1. **W-01 No tenant model** — existential.
2. **W-02 No tenant scoping in routes** — pair with W-01.
3. **W-09 Hardcoded MASCI legal text (EN + ES)** — legal exposure.
4. **V-04 / W-06 `tokens.css` PROPOSAL — not wired** — retheming infrastructure exists in name only.
5. **W-07 `portalPalette.js` static** — colors hardcoded.
6. **W-08 Hardcoded recipient emails** — Customer #2 emails default to MASCI staff.
7. **W-12 No tenant onboarding surface** — no admin path exists to create Customer #2.
8. **W-13 Per-workflow status engines hardcoded** — blocks workflow tenant config.
9. **W-15 Public surfaces single brand chrome** — Public Safety Tile, QR, asset lookup all MASCI-styled.
10. **W-20 Email templates Python-coded** — customer cannot edit emails without engineering.

(Two roadmaps. Intentional that they do not share items.)

---

## 4. Preserve List Summary

12 items recorded in `/app/memory/MASCI_PLATFORM_PRESERVE_LIST.md`:

Trench Safety architecture · PM portal rebuild improvements ·
Dispatch Map recovery (Track 13.4A) · cross-portal Operations Map
consistency · per-portal authentication isolation · append-only RC
Certification Ledger discipline · Operational Guidance Center
coaching loop · operator-native tile-label language · Safety Forms
bilingual EN+ES legal text · Track 13.4A Visual Render Guardrail ·
working integration baseline (Resend · R2 · Motive) · existing
positive tenant-config plumbing (`training_guides`,
`training_videos`, `digest_settings`).

**Rule:** every future change must declare which Preserve item it
touches and must not weaken it.

---

## 5. Remove List Summary

Catalogued in `/app/memory/MASCI_PLATFORM_REMOVE_LIST.md` — not yet
removed:

- Duplications: `OperationsActionsTile` on 6 portals · two
  `StatusBadge.jsx` files · 4 admin health pages · 2 compliance pages
  · 8 `*CommandCenter` pages · 8 auth flows · 15 status-chip components
  · PO digest + per-action PO email overlap · 1,146 unused ES dictionary keys.
- Dead surfaces: `guidance_search_misses` collection
  with no audit view · `forgedops-logo.png` unused.
- Wrong-role features: `OperationsActionsTile` cross-portal · HR
  `MotiveDrivers` borderline.

---

## 6. Rebuild List Summary

8 architectural rebuild blocks recorded in
`/app/memory/MASCI_PLATFORM_REBUILD_LIST.md`:

R-01 Status & Verbiage Engine ·  
R-02 Portal Identity & Header ·  
R-03 Navigation Architecture ·  
R-04 Theme Layer (token wiring) ·  
R-05 Command Center Architecture ·  
R-06 Forms Layer (overlap reduction) ·  
R-07 Driver Portal ·  
R-08 Notification Layer.

Each rebuild is conditional on operator authorisation per track.

---

## 7. Standardisation Summary

10 surfaces to standardise eventually, per
`/app/memory/MASCI_PLATFORM_STANDARDIZATION_LIST.md`:

S-1 Status Chips · S-2 Colors · S-3 Terminology · S-4 Notifications ·
S-5 Coaching Patterns · S-6 Table Patterns · S-7 Form Patterns ·
S-8 Empty States · S-9 Headers · S-10 Navigation Structures.

---

## 8. Five-Pillar Summary

From `/app/memory/MASCI_PLATFORM_FIVE_PILLAR_MATRIX.md`:

| Pillar | Tier-1 violations | Top violator |
|---|---|---|
| Powerful | 6 | Dispatch data integrity (D-01 / D-03 / D-04) |
| Simple | 5 | `tokens.css` not wired (V-04) |
| Beautiful | 4 | `tokens.css` not wired (V-04) |
| **Trusted** | **11 of 12** | D-01 / D-03 / D-04 / T-01 / W-01 / W-09 |
| **Proven** | **10 of 12** | T-01 / T-08 / T-09 / V-04 / D-01 |

**Headline:** *Trust* and *Proven* are the dominantly-violated
pillars. Most Tier-1 findings are "the thing exists in name but
isn't verified to work" (`tokens.css` proposal-only · production
webhook unverified · Spanish path falls through on safety-critical
strings · no tenant model).

---

## 9. Risk Register Summary

33 risk rows recorded in
`/app/memory/MASCI_PLATFORM_MASTER_RISK_REGISTER.md`. All status
`observed`. None remediated. Highest-impact rows (impact 4):

- RISK-001 No tenant model
- RISK-002 Hardcoded MASCI legal text in EN + ES
- RISK-003 Production Motive webhook unverified
- RISK-004 100 / 190 assets no-GPS
- RISK-005 157 stale assets

Plus dedicated **Dispatch Reality Status** and **Translation Reality
Status** sections (mandated).

---

## 10. Recommendation — what Track 13.4D should focus on

Track 13.4D should be:

> **Production-Reality Validation & Dispatch Data Integrity Audit.**

Rationale (no implementation proposed — focus only):

- The single dominant-pillar violation across Tier 1 is **Proven**:
  most blockers are "this exists in name only, not in verified
  operation". Track 13.4D must close those proof gaps.
- Specifically: validate the **production** Motive webhook arrival
  rate · the production GPS coverage rate · the per-unit staleness
  root causes · independent rederivation of the operational summary
  counts (D-01 … D-08).
- Add: production Spanish-coverage spot-check on safety-critical
  surfaces (does the user with `lang=es` actually see Spanish at
  `/inspect/new` · `/incidents/new` · `/jha/new` · trench surfaces?).
- Add: 22 portal-landing screenshots at iPad and phone viewports to
  close the Phase-1 mobile evidence gap (V-13).
- Defer Design System V1 to a separate track after Track 13.4D so
  the design system is anchored in *proven* reality, not assumption.

---

## Phase-completion checklist

- ✅ MASCI Operational Recovery Priority Stack.
- ✅ ForgedOps Productisation Priority Stack.
- ✅ Preserve List.
- ✅ Remove List.
- ✅ Rebuild List.
- ✅ Standardisation List.
- ✅ Five-Pillar Matrix.
- ✅ Master Risk Register (incl. Dispatch Reality and Translation Reality dedicated sections).
- ✅ Executive Summary with the 10 required sections (this document).
- 🚫 No deploy.
- 🚫 No GitHub save.
- 🚫 No merge.
- 🚫 No implementation.
- 🚫 No design.
- 🚫 No standardisation.
- 🚫 No white-label building.

Operator decision required before Track 13.4D begins.
