# MASCI Five-Pillar Scorecard

**Track 13.5B · Portal- and Module-level Five-Pillar Scoring**
**Mode:** Analysis only — no code change.
**Generated:** 2026-06-12 (UTC)

> No arbitrary scoring. Every cell cites evidence: a route, a file, a finding-ID from `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`, or an audit doc.
> The Five Pillars (Powerful · Simple · Beautiful · Trusted · Proven) are the standing platform standard.

---

## 1. Scoring rubric

| Score | Meaning |
| --- | --- |
| 10 | Industry-leading; nothing to add. |
| 8-9 | Excellent; remaining gaps are nice-to-have. |
| 6-7 | Operationally trusted; visible improvement areas exist. |
| 4-5 | Functional but flagged by audits. |
| 2-3 | Operational but with active trust/usability defects. |
| 0-1 | Missing or broken. |

A score is only allowed to reach 10 when an audit document explicitly says "exemplary" or equivalent.

---

## 2. Portal-level scorecard

### 2.1 Trench Safety module (highest-scoring surface in MASCI)

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 9 | Full lifecycle: tabulated data + repair-review + reports + public QR + excavation form. Real APIs (`/api/trench-safety/*`). |
| Simple | 8 | One coherent voice across operator + public surfaces; the "Stop-Work Authority" copy reads as one platform. |
| Beautiful | 9 | Cited in `MASCI_VISUAL_IDENTITY_AUDIT.md` as **exemplary**. |
| Trusted | 9 | Public surface bilingually labelled; no D-class concerns; data render verified. |
| Proven | 9 | Multiple QA passes + public usage. |
| **Avg** | **8.8** | — |

### 2.2 HR Portal

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 9 | Termination flow · daily-report read · incident read · onboarding · MFA support · digest config. |
| Simple | 8 | "Cleanest operator portal today" per `TRACK_13_4D_E_FINAL_DISCOVERY_EXECUTIVE_SUMMARY.md` §3.2. |
| Beautiful | 8 | Post-13.4A clean. |
| Trusted | 9 | No outstanding D-class findings. |
| Proven | 8 | Real production usage by HR team. |
| **Avg** | **8.4** | — |

### 2.3 Dispatch Portal

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 9 | Live fleet map + assignment board + driver profile + qualification. |
| Simple | 8 | Post-13.4A Dispatch was specifically rated "Excellent" in `MASCI_HUMAN_USABILITY_AUDIT.md`. |
| Beautiful | 8 | Map dominance + clean rail. |
| Trusted | 7 | **D-01 unresolved**: production webhook arrival rate NEVER verified. Preview env stale by 22.8h (D-02). |
| Proven | 7 | Track 13.4A canvas guardrail PASS (`box=1084×520 · mean=24.85 · variance=275.46 · unique=103`); production verification checklist NOT executed. |
| **Avg** | **7.8** | — |

### 2.4 PM Portal

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 9 | 30 routes, Phase 4A Command Center APIs (7 sub-endpoints) live. |
| Simple | 6 | R-02 (form duplication) · U-01 (no PM-scoped CAPA list) · V-02 (tile-CTA color drift). |
| Beautiful | 7 | Post-13.4A improvements noted in visual identity audit; ad-hoc card sprawl remains. |
| Trusted | 7 | `co_pm_emails` scoping tested (`test_iter437_pm_jobs_endpoint.py`). Holds aggregation absent — see PM matrix §2.3. |
| Proven | 7 | Phase B2 preview captured at 3 viewports; live PM verified zero leakage. |
| **Avg** | **7.2** | — |

### 2.5 Safety Forms Hub + section

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 8 | Equipment Issuance · Training · Return · JHA · Posters · Field Safety Cards. |
| Simple | 7 | R-02 sub-form overlap not yet collapsed. |
| Beautiful | 7 | Bilingual hub stable. |
| Trusted | 7 | T-01: 75.8% ES coverage on safety strings (100 strings still EN-only on a **safety-critical** audience). |
| Proven | 7 | Public surfaces in real use. |
| **Avg** | **7.2** | — |

### 2.6 Shop Portal

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 7 | Smaller portal; serves the mechanic role only. |
| Simple | 7 | Clear vertical scope. |
| Beautiful | 6 | V-01 amber-vs-orange header drift. |
| Trusted | 7 | No outstanding D-class issues. |
| Proven | 7 | Used. |
| **Avg** | **6.8** | — |

### 2.7 Admin Portal

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 9 | 85 routes — biggest surface in MASCI. |
| Simple | 5 | "Powerful but confusing" per usability audit. R-04 (4 health pages) + R-05 (compliance duplication) + AdminCommandCenter ↔ OperationsCenterCommand overlap. |
| Beautiful | 6 | Mixed component styles; AssetMapping page in particular. |
| Trusted | 7 | No data-trust defects, but role coverage uneven. |
| Proven | 7 | Production-used; no production verification gap. |
| **Avg** | **6.8** | — |

### 2.8 Field Leadership

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 7 | 10 record kinds; read-only field views. |
| Simple | 6 | Legacy shared-password coexists with per-user portal (R-01 family / iter314). |
| Beautiful | 6 | iter343 chrome rebuild stabilized; still pre-design-system. |
| Trusted | 6 | T-09 backend PDFs EN-only. |
| Proven | 6 | iter314 test coverage exists; field usability uncaptured at iPad/phone (V-13 deferred for FL). |
| **Avg** | **6.2** | — |

### 2.9 Driver Portal

| Pillar | Score | Cited evidence |
| --- | :-: | --- |
| Powerful | 6 | DriverShift + magic-link entry are real. |
| Simple | 4 | V-15 / R-13 — no static landing page identifiable in `pages/`. |
| Beautiful | 5 | Same gap. |
| Trusted | 6 | Magic-link auth works. |
| Proven | 5 | iPad/phone capture deferred (V-13). |
| **Avg** | **5.2** | — |

---

## 3. Module-level scorecard

| Module | Powerful | Simple | Beautiful | Trusted | Proven | Avg | Anchor evidence |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | --- |
| Operations Map | 9 | 8 | 8 | 7 | 8 | 8.0 | D-09 (positive: dispatch + ops-map share hook) · D-01 keeps Trusted < 9 |
| Dispatch Lifecycle (DLS) | 9 | 7 | 7 | 8 | 8 | 7.8 | `dispatch_lifecycle.py` 1064-line router; admin governance health endpoint exists |
| Daily Report engine | 9 | 7 | 7 | 8 | 8 | 7.8 | 7 sub-endpoints in `/api/daily-reports/*`; verification chain real |
| Incident engine | 9 | 7 | 7 | 8 | 8 | 7.8 | 5 sub-endpoints in `/api/incidents/*` |
| QA/QC | 8 | 7 | 7 | 8 | 7 | 7.4 | `/api/qaqc/*`; AdminQaqcList lives |
| ODR | 8 | 7 | 7 | 7 | 7 | 7.2 | `OdrCenter`, `OdrNew`, `OdrPmPanel`, `OdrPublicViewer` all real |
| Trench Safety engine | 9 | 8 | 9 | 9 | 9 | 8.8 | Visual identity audit cites as exemplary |
| Operations Actions (OA-1) | 7 | 5 | 6 | 7 | 6 | 6.2 | V-08 / R-06 — tile still on 6 of 7 portals |
| PO Requests / Approvals | 7 | 6 | 6 | 6 | 7 | 6.4 | R-07 (digest + per-action duplication) |
| Training | 7 | 7 | 7 | 7 | 7 | 7.0 | Catalog + videos shipped |
| Hub Banners | 7 | 7 | 7 | 7 | 7 | 7.0 | `/api/hub-banners` router; admin-curated |
| Authentication (8 flows) | 7 | 5 | 6 | 7 | 7 | 6.4 | R-01 (8 distinct flows); rebuild list R-03 |
| Notification layer | 6 | 5 | 6 | 6 | 6 | 5.8 | R-07 + rebuild list R-08 |
| Translation surface | 6 | 5 | 6 | 5 | 6 | 5.6 | T-01..T-12 — see registry §F |
| White-label readiness | 2 | 3 | 3 | 3 | 2 | 2.6 | W-01..W-20 — registry §D (existential gaps) |

---

## 4. Cross-cutting concern scorecard

| Concern | Powerful | Simple | Beautiful | Trusted | Proven | Avg | Anchor |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | --- |
| Design System V1 — tokens.css | 8 | 8 | 8 | 8 | 8 | 8.0 | Phase A wired & verified |
| Design System V1 — primitives | 8 | 8 | 8 | 7 | 7 | 7.6 | Phase B1 isolated; Phase B2 PM V2 preview verified |
| Five-pillar governance | 8 | 9 | 8 | 8 | 8 | 8.2 | This scorecard + reality matrix |
| Audit ledger discipline | 9 | 8 | 7 | 9 | 9 | 8.4 | 22 governance docs + 106 evidence screenshots (per 13.4D/E summary §1) |

---

## 5. Aggregate platform score (weighted by portal usage)

A weighted average using a rough usage weighting (Admin · Dispatch · PM · HR · Safety + Trench · Shop · FL · Driver = 1.0 · 1.0 · 1.0 · 0.6 · 1.0 · 0.4 · 0.4 · 0.3):

| Pillar | Weighted average |
| --- | :-: |
| Powerful | **8.2** |
| Simple | **6.5** |
| Beautiful | **7.0** |
| Trusted | **7.2** |
| Proven | **7.1** |

**Platform aggregate: ~7.2 / 10.**

This number is the **honest** starting point for the journey to 10/10 across all five pillars. The gap-to-10 is largest on **Simple** (3.5 pts) and **Beautiful / Proven** (3.0 pts each) — exactly what the design system + production verification + naming collapse are designed to address.

---

## 6. Score-to-action mapping

| Pillar lowest score | Strongest gap | First action (analysis-only here) |
| --- | --- | --- |
| **Simple = 6.5** | Naming, duplicated surfaces, ad-hoc components | Collapse AdminCommandCenter ↔ OperationsCenterCommand (R-05) + rename non-role "Centers" (R-03). Migrate one pilot portal to B1 primitives (Phase B3). |
| **Beautiful = 7.0** | 4 header strategies, 15 status chips, ad-hoc cards | Pilot Phase B3 migration of PM (or HR) using design-system primitives. |
| **Proven = 7.1** | Production verification gap (D-01) | Execute the 7-point production verification checklist (Track 13.4D §3). |
| **Trusted = 7.2** | D-01 + translation gap T-01..T-12 | Same checklist + ES audit on the 806 untranslated UI strings (R-08). |

---

## 7. Standing rules

No deploy. No GitHub save. No merge. No new audit branches. This scorecard is a consolidation; it stands or falls on the evidence it cites.
