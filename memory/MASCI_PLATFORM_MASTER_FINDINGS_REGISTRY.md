# MASCI Platform — Master Findings Registry (Track 13.4B · Phase 3)

**Mode:** Inventory only. NO prioritisation in this document (see Priority Matrix sibling doc).  
**Generated:** 2026-02 (Track 13.4B Phase 3)  
**Sources merged:** Surface Inventory · Identity Variance · Reality Discovery · White-Label Readiness · Track 13.4A Dispatch · Translation · Motive.

Finding-ID convention:
- `V-##` = Visual / Identity Variance (Phase 2A)
- `R-##` = Reality Discovery (Phase 2B)
- `W-##` = White-Label Readiness (Phase 2C)
- `D-##` = Dispatch / Motive Data Integrity (Track 13.4A §7)
- `T-##` = Translation (Phase 3 reclassification)
- `S-##` = Surface Inventory observation (Phase 1)

---

## A. Surface Inventory Observations (`S-##`)

| ID | Description | Evidence | Affected scope |
|---|---|---|---|
| S-01 | 9 authenticated portals + 1 internal Dev portal | Phase 1 §B | platform-wide |
| S-02 | 22 first-class public surfaces · 86 unauthenticated routes total | Phase 1 §C | platform-wide |
| S-03 | 23 named functional modules | Phase 1 §D | platform-wide |
| S-04 | 174 backend route files · 942 endpoint registrations · 750 distinct API paths | Phase 1 §A | backend |
| S-05 | 167 MongoDB collections | Phase 1 §A | backend |
| S-06 | 3,312 distinct frontend `data-testid` attributes | Phase 1 §A | frontend |

---

## B. Identity Variance (`V-##`)

| ID | Category | Description | Evidence | Portals affected | Modules affected | White-label impact | Trust impact | Field impact |
|---|---|---|---|---|---|---|---|---|
| V-01 | Theme drift | ShopHub header uses amber-500/700/300 vs Shop tile palette orange-600/700 | `portalPalette.js` source comment | Shop | UI shell | low (still single-tenant brand) | low | low |
| V-02 | Theme drift | PmHub tile-CTA uses amber but canonical PM palette is indigo | `portalPalette.js` source comment | PM | UI shell | low | low | low |
| V-03 | Theme overlap | Field Leadership red-700 overlaps with Admin/Leadership brand-red | `portalPalette.js` source comment | FL · Admin · Leadership | UI shell | low | medium (operator role confusion) | medium |
| V-04 | Token unwired | `tokens.css` declared "PROPOSAL — NOT YET WIRED" | file header | platform | UI shell | **HIGH** (no retheming layer) | n/a | n/a |
| V-05 | Hub size variance | Hub files 145 → 668 lines (4.6×) | `wc -l` per hub | all portals | UI shell | medium (hard to clone for tenant) | medium | low |
| V-06 | Header pattern variance | ≥4 different portal-header strategies | grep per hub | all portals | UI shell | medium | medium | low |
| V-07 | Status-chip sprawl | 15 distinct status/badge components, 2 share filename | `find` | platform | UI shell | medium | medium | low |
| V-08 | Cross-portal tile leakage | OA-1 tile still mounted on 6 of 7 portals after 13.4A | grep `<OperationsActionsTile` | Dispatch · PM · Shop · Safety · FL · Admin | OA-1 | medium | low | low |
| V-09 | Command-center sprawl | 8 distinct `*Center` pages with overlapping signals | Phase 1 §D | Admin · PM · Dispatch · Trench · ODR · Guidance · Ops Training · Operations | UI shell | medium | medium | low |
| V-10 | Status case drift | Mixed `Open/open`, `Active/active` | grep | all portals | status engines | low | medium (visual inconsistency) | low |
| V-11 | Status verb overload | `offline`, `active`, `open` each mean ≥3 different things across engines | source review | all portals | status engines | medium | **HIGH** (operator interpretation risk) | medium |
| V-12 | Closure verb drift | `closed`, `done`, `signed_off`, `final`, `success`, `approved`, `receipted` — no shared closure verb | per-engine | all portals | workflow engines | medium | medium | medium |
| V-13 | Mobile evidence gap | 22 Phase-1 portal landings captured at desktop only | screenshot index | all portals | UI shell | n/a | n/a | **HIGH** (mobile is field) |
| V-14 | Public surface chrome drift | Each public surface has its own header chrome | source review | public | UI shell | **HIGH** (each must be rebrandable) | low | low |
| V-15 | Driver portal landing missing | No static driver landing page identifiable in `pages/` | Phase 1 §B | Driver | UI shell | medium | medium | medium |

---

## C. Reality Discovery (`R-##`)

| ID | Category | Description | Evidence | Workflows affected | Trust impact | Field impact |
|---|---|---|---|---|---|---|
| R-01 | Auth flow sprawl | 8 distinct auth-flow variations doing the same job (7 per-portal + master `/sign-in`) | App.js route grep | all logins | medium | medium |
| R-02 | Form data duplication | Daily Report / Site Inspection / Incident overlap substantially (photos · crew · narrative) | source review | 3 form workflows | low | **HIGH** (field re-entry) |
| R-03 | Command-center sprawl | 8 `*CommandCenter` pages with overlapping signals | Phase 1 §D | command-center workflow | medium | low |
| R-04 | Admin health sprawl | 4 admin health pages (Persistence · Production · Stability · Cluster Capacity) | Admin nav | admin oversight | low | n/a |
| R-05 | Compliance duplicate | `AdminCompliance` + `AdminComplianceFindings` — 2 pages | Admin nav | compliance | low | n/a |
| R-06 | OA-1 still cross-portal | Operations Actions tile still on 6 of 7 portals after 13.4A | grep | OA-1 | medium | medium |
| R-07 | Notification duplication | PO digest + per-action PO email surface the same event | source review | PO Request | low | medium |
| R-08 | Translation gap measured | 806 frontend strings wrapped in `t()` have NO Spanish entry (20.5% UI gap) | `/tmp/orphans.txt` | all UI | **HIGH** | **HIGH** |
| R-09 | Dead translation weight | 1,146 ES entries unused | comm | all UI | low | low |
| R-10 | Email/PDF/Excel English-only | Backend emails, PDFs, Excel exports all English-only | source review | all outbound docs | medium | **HIGH** (Spanish crew gets EN PDF) |
| R-11 | Status verbs not in `t()` | Engine-level status strings rendered without translation wrap | source review | all status surfaces | medium | medium |
| R-12 | Closure verb drift | (see V-12) | per-engine | all workflows | medium | medium |
| R-13 | Driver portal landing gap | (see V-15) | Phase 1 §B | Driver | medium | medium |
| R-14 | Public form chrome drift | (see V-14) | source review | public forms | low | low |
| R-15 | `guidance_search_misses` invisible | Collection accumulates user search misses but no operator-visible audit view | Mongo + Admin nav | guidance / coaching loop | low | medium |

---

## D. White-Label Readiness (`W-##`)

| ID | Description | Evidence | White-label impact | Customer #2 impact |
|---|---|---|---|---|
| W-01 | No tenant model in DB | 0 of 6 tenant collections present | **EXISTENTIAL** | **BLOCKS ONBOARDING** |
| W-02 | No tenant scoping in production routes | grep returns matches only in test fixtures | **EXISTENTIAL** | **BLOCKS ONBOARDING** |
| W-03 | 497 source files reference "MASCI" | grep | **EXISTENTIAL** | brand leak everywhere |
| W-04 | 52 source files reference `mascigc.com` | grep | **HIGH** | email-routing leak |
| W-05 | 73 source files reference "ForgedOps" | grep | low (parent brand) | n/a |
| W-06 | `tokens.css` PROPOSAL — not wired | file header | **HIGH** | no retheming layer ready |
| W-07 | `portalPalette.js` static | source | **HIGH** | colors hardcoded |
| W-08 | Hardcoded recipient emails with platform-level env override only | `safety_forms.py` ll. 14–31, 72; FL routes ll. 75–76 | **HIGH** | Customer #2 emails go to MASCI staff |
| W-09 | Hardcoded legal phrases identify MASCI as owning entity (EN + ES) | `safety_forms.py` ll. 189/195/493/498 | **EXISTENTIAL** (legal) | legal exposure |
| W-10 | PDFs / outage alerts inline-branded MASCI | server.py ll. 251/257/2183/2402, outage_alerts.py l. 159 | **HIGH** | every PDF/email leaks brand |
| W-11 | Excel export filenames prefix `MASCI_` | server.py exports | medium | export leak |
| W-12 | No tenant onboarding surface exists | Admin nav | **EXISTENTIAL** | no admin path to create Customer #2 |
| W-13 | Per-workflow status engines hardcoded | 12 engines | **HIGH** | no per-tenant workflow customisation |
| W-14 | 8 auth flows × 0 tenant scope | per-portal `/login` | **HIGH** | Customer #2 logins mingle |
| W-15 | Public surfaces share single brand chrome family | Phase 1 §C | **HIGH** | no public-page tenant isolation |
| W-16 | `forgedops-logo.png` exists but unused as primary mark | assets dir | low | n/a |
| W-17 | Training catalog partially tenant-ready (`training_guides`, `training_videos`) | Phase 1 §G | partial-positive | partial-positive |
| W-18 | Digest cadence partially tenant-ready (`digest_settings`) | `admin_digest_config.py` | partial-positive | partial-positive |
| W-19 | 1 token + 1 palette + 1 i18n file — no overlay model | core layout | **HIGH** | no per-tenant overlay |
| W-20 | Email templates Python-coded — customer cannot customise without code | `branded_portal_emails.py`, `email_routing.py` | **HIGH** | customer-controlled templates impossible |

---

## E. Dispatch / Motive Data Integrity (`D-##`) — from Track 13.4A §7

| ID | Description | Evidence | Trust impact | Operational impact |
|---|---|---|---|---|
| D-01 | Production Motive webhook activity NOT verified | preview env only | **HIGH** (live trust) | **HIGH** |
| D-02 | Preview env receives no live webhooks → 22.8h-stale data | `/api/operations-map/snapshot` | medium (preview-only) | medium |
| D-03 | 100 of 190 motive-mapped assets have NO GPS coords | snapshot count | medium | **HIGH** (can't locate 53% of fleet) |
| D-04 | 157 assets are "no recent position" / stale | snapshot count | medium | **HIGH** |
| D-05 | 33 assets attention-required (stale_position band) | snapshot count | medium | medium |
| D-06 | 67 circle geofences in DB render as 0 (`_polygon_from_motive` skips circles) | source + DB count | medium | medium |
| D-07 | Marker `marker_kind` heuristically derived from equipment label | `operations_map_v1.py` | low | low |
| D-08 | `operational_summary` counts not independently rederived in this track | source review | low | low |
| D-09 | Dispatch and `/operations-map` consume same hook → cross-portal consistent | source review | (positive) | (positive) |

---

## F. Translation (`T-##`) — reclassification of R-08/R-09/R-10/R-11

Bucketed via keyword heuristics applied to the 3,932 distinct `t()` keys vs the 4,272 ES entries (numbers exact, classification approximate):

| ID | Category | Total t() keys | With ES | Orphan | Readiness % |
|---|---|---|---|---|---|
| T-01 | **Safety-Critical UI** | 413 | 313 | **100** | **75.8 %** |
| T-02 | Field-Critical UI | 719 | 593 | 126 | 82.5 % |
| T-03 | Workflow-Critical UI | 439 | 362 | 77 | 82.5 % |
| T-04 | Public-Facing UI | 91 | 67 | 24 | 73.6 % |
| T-05 | Admin / Office UI | 73 | 54 | 19 | 74.0 % |
| T-06 | Technical / Internal UI | 48 | 33 | 15 | 68.8 % |
| T-07 | Unclassified UI (mixed) | 2,149 | 1,704 | 445 | 79.3 % |
| T-08 | Outbound email body translation | 0 of N | 0 | all | **0 %** |
| T-09 | Server-rendered PDF translation | 0 of N | 0 | all | **0 %** |
| T-10 | Excel / CSV export translation | 0 of N | 0 | all | **0 %** |
| T-11 | Backend `HTTPException` detail string translation | 0 of N | 0 | all | **0 %** |
| T-12 | Status verb translation (engine level) | engine literals not wrapped | 0 | all | **0 %** |

---

## G. Field finding metadata template

Every row above conforms to the metadata schema requested:

```
Finding ID         → V-/R-/W-/D-/T-/S- prefix
Category           → column "Category"
Source Audit       → Phase 1 / Phase 2A / Phase 2B / Phase 2C / Track 13.4A
Description        → column "Description"
Evidence Source    → column "Evidence" (file:line or DB collection or grep result)
Affected Portals   → column "Portals affected" (where applicable)
Affected Modules   → column "Modules affected"
Affected Users     → implied by portal column
Affected Workflows → column "Workflows affected"
White-Label Impact → column "White-label impact"
Operational Impact → column "Operational impact" / "Field impact"
Trust Impact       → column "Trust impact"
Field Impact       → column "Field impact"
Status             → all rows currently `observed · not yet remediated`
```

---

## H. Total findings count

| Source | Count |
|---|---|
| Surface Inventory (`S-`) | 6 |
| Identity Variance (`V-`) | 15 |
| Reality Discovery (`R-`) | 15 |
| White-Label Readiness (`W-`) | 20 |
| Dispatch / Motive (`D-`) | 9 |
| Translation (`T-`) | 12 |
| **Total findings catalogued** | **77** |

Prioritisation is **out of scope** for this document; see  
`/app/memory/MASCI_PLATFORM_PRIORITY_MATRIX.md`.
