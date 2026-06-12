# MASCI Platform Reality Matrix

**Track 13.5B · Five-Pillar Operational Reality Validation**
**Mode:** Analysis only — no code change, no design, no rebuild.
**Generated:** 2026-06-12 (UTC) · Discovery is closed; this consolidates only.

> Source of truth: master findings registry (`MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md`, 77 catalogued findings), reality discovery audit, visual identity audit, human usability audit, production reality audit, rebuild list. No new finding registries are created here.

---

## 1. Mission

Answer: **does every visible thing inside MASCI OPS deserve to exist?**

Every object below was inspected against the Five Pillars and given a binary keeper/flag verdict plus a 0-10 score per pillar. Verdicts must cite existing evidence (a file path, a route, a finding-ID, or a screenshot index). No new scoring frameworks are introduced.

---

## 2. Portal inventory (object level)

Nine authenticated portals + one internal Dev portal + 22 public surfaces inventoried per `MASCI_PLATFORM_MASTER_FINDINGS_REGISTRY.md` S-01 / S-02.

### 2.1 Admin (85 routes — the largest portal)

| Object | Location | Roles | Purpose | Data source | Status | Why it earned its place / what flags it |
| --- | --- | --- | --- | --- | --- | --- |
| AdminHub | `/admin` (`AdminHub.jsx`) | Super-admin · Admin | Portal landing | `/api/admin/*` summary | Operational | Real; the only admin entry point. |
| AdminCommandCenter | `/admin/command-center` | Super-admin | "Center" landing | `/api/operations-center/*` | Operational | Real but **duplicated** with `OperationsCenterCommand` (V-09). |
| OperationsCenterCommand | `/operations-center` | Super-admin | Cross-portal ops glance | `/api/operations-center/*` | Operational | Real. Overlaps AdminCommandCenter; see Command Center matrix. |
| AdminCompliance + AdminComplianceFindings | `/admin/compliance*` | Admin | Compliance overview | `/api/compliance/*` | Operational | **Duplicated** (R-05). Two pages doing one job. |
| AdminPersistence · AdminProduction · AdminStability · AdminClusterCapacity | `/admin/health/*` | Super-admin | Platform health | `/api/admin/*` health | Operational | **4 pages for one concept** (R-04). |
| AdminIntegrationCenter | `/admin/integrations` | Super-admin | 3rd-party wire-up | `/api/admin/integrations` | Operational but Incomplete | "Center" naming conflicts with real Command Centers (V-09). |
| AdminLegacyImports | `/admin/legacy-imports` | Super-admin | Bulk import | `/api/admin/legacy-imports` | Operational | Real one-shot tool. Powerful=8 / Simple=6 / Beautiful=5. |
| AdminDeployReadiness | `/admin/deploy-readiness` | Super-admin | Pre-deploy gate | `/api/admin/deploy-readiness` | Operational | Real safety net. |
| AdminTrainingVideos | `/admin/training-videos` | Admin | Catalog editor | `/api/training-videos` | Operational | Real. |
| AdminQaqcList | `/admin/qaqc` | Admin | QA/QC inventory | `/api/qaqc/*` | Operational | Real. |
| AdminAssetMapping | `/admin/asset-mapping` | Super-admin | Motive ↔ equipment | `/api/admin/asset-mapping` | Operational | Real. Confusing UI; Simple=5. |
| AdminTerminations | `/admin/terminations` | HR/Admin | Off-board flow | `/api/hr/*` | Operational | Real and used. |
| AdminSchedulerRuns | `/admin/scheduler-runs` | Super-admin | Cron audit | `/api/admin/scheduler` | Operational | Real but for one operator. |
| AdminMfa | `/admin/mfa` | Super-admin | TOTP enroll | `/api/admin/mfa/*` | Operational | Real (iter375). |
| AdminRecovery | `/admin/recovery` | Super-admin | DR drill | `/api/admin/recovery` | Operational | Real. |
| AdminGuide / CheatSheet | `/admin/guide`, `/admin/cheat-sheet` | Admin | Internal docs | static | Operational | Real but living. |

### 2.2 Dispatch (10 routes)

| Object | Location | Status | Verdict |
| --- | --- | --- | --- |
| DispatchHub (`/dispatch-portal`) | `DispatchHub.jsx` | Operational | Real. Powerful=9 / Simple=8 / Beautiful=8 / Trusted=7 (D-01 unresolved) / Proven=7. |
| DispatchBoard (`/dispatch-portal/board`) | `DispatchBoard.jsx` | Operational | Real and field-critical. |
| DispatchCommandCenter (`/dispatch-portal/command`) | `DispatchCommandCenter.jsx` | Operational | Real. **Naming overlap** with PmCommandCenter / AdminCommandCenter (V-09). |
| Operations Map embed | `/api/operations-map/snapshot` | Operational | Real after 13.4A fix (canvas guardrail PASSES `box=1084×520 · mean=24.85 · variance=275.46 · unique=103`). |
| Driver Profile (`DispatchDriverProfile.jsx`) | `/dispatch-portal/drivers/:id` | Operational | Real. |
| Driver Qualification (`DispatchDriverQualification.jsx`) | `/dispatch-portal/drivers/:id/qual` | Operational | Real. |
| Login + reset + change-password | `/dispatch-portal/login` etc. | Operational | Real but shares pattern with 7 other auth flows (R-01). |

### 2.3 PM (30 routes — second largest)

Detailed in `MASCI_PM_REALITY_MATRIX.md`. Top-level verdict:

| Object | Location | Status | Verdict |
| --- | --- | --- | --- |
| PmHub | `/pm/hub` | Operational | Real. Five-pillar avg ~7.4. |
| PmCommandCenter | `/pm/command-center` | Operational | Real, backed by `/api/pm/command-center/*` (7 sub-endpoints exist). |
| PmJobs | `/pm/jobs` | Operational | Real with `co_pm_emails` scoping. |
| PmCrewCompliance | `/pm/crew-compliance` | Operational | Real. |
| PmFieldLeadership | `/pm/field-leadership` | Operational | Real read-only. |
| PmFleet | `/pm/fleet` | Operational | Real. |
| PmPeople / PmSuppliers / PmPosters | various | Operational | Real but **low-traffic**; flag for the Simple test. |
| PmQaqcList | `/pm/qaqc` | Operational | Real. |
| JobPhotosLibrary (mounted at `/pm/photos`) | shared component | Operational | Real but currently empty in preview (image above). |
| Daily Reports / Incidents dashboards (PM-scoped) | `/pm/daily`, `/pm/incidents` | Operational | Real, share component with safety. |
| PM V2 preview | `/_internal/pm-v2-preview` | Mock | **Mock by design** (Phase B2). |

### 2.4 Safety + Safety Portal (20 + 22 routes)

| Object | Location | Status | Verdict |
| --- | --- | --- | --- |
| SafetySection landing | `/safety` | Operational | Real. |
| Safety Forms Login + Hub | `/safety/forms*` | Operational | Real. Bilingual ES/EN; T-01 75.8% ES coverage on safety strings — flag. |
| Equipment Issuance + Training | `/safety/forms/equipment-*` | Operational | Real. R-02: overlap with Daily Report fields. |
| Trench Safety (public + ops) | `/trench-safety/*`, `TrenchSafetyHub`, `TrenchSafetyAssetsList`, `TrenchSafetyAssetDetail`, `TrenchSafetyOpsCenter`, `TrenchSafetyTabulatedData`, `TrenchSafetyReports`, public QR + Excavation Form | Operational | **Exemplary module** (cited in `MASCI_VISUAL_IDENTITY_AUDIT.md`). Trusted=9, Proven=9. |
| JHA Plans Hub + Admin + Posters | `/jha-plans*`, `/safety/posters*` | Operational | Real. |
| Trench-box admin + poster | `/trench-boxes*` | Operational | Real. |
| FieldSafetyCards | `/safety/cards` | Operational | Real. |
| Site Inspections / QA/QC / Meetings | `/inspect*`, `/qa-qc/*`, `/meetings/*` | Operational | Real; share photo-block with Daily/Incident (R-02). |

### 2.5 HR (23 routes)

Cited in `TRACK_13_4D_E_FINAL_DISCOVERY_EXECUTIVE_SUMMARY.md` §3.2 as **"Excellent post-13.4A; cleanest operator portal today."**

| Object | Status | Verdict |
| --- | --- | --- |
| HrHub `/hr` | Operational | Real. Five-pillar avg ~8.5. |
| HrLogin + reset + change-password | Operational | Real; pattern duplicated 8× (R-01). |
| HR Daily Reports / Incidents read | Operational | Real. |
| Termination + onboarding flows | Operational | Real. |

### 2.6 Shop (8 routes)

| Object | Status | Verdict |
| --- | --- | --- |
| ShopHub | Operational | Real; header amber drift (V-01) flagged on Beautiful. |
| ShopLogin | Operational | Real, shares R-01 pattern. |

### 2.7 Field Leadership (6 routes legacy + 6 portal routes)

Two parallel surfaces:
- Legacy shared-password `/field-leadership/*` — Operational but Incomplete (transitional).
- Per-user FL portal `/field-leadership/portal/*` — Operational (iter314).

Status: Real but **the legacy + portal coexistence is itself a Simple/Trusted flag.**

### 2.8 Driver (1 active surface + magic-link entry)

- DriverMagicLanding · DriverShift · ShiftStart. **Driver Hub static landing is missing** (V-15 / R-13).
- Verdict: Operational but Incomplete. Cited in `MASCI_HUMAN_USABILITY_AUDIT.md`: "Driver: Needs Rebuild".

### 2.9 ODR (5 routes)

OdrCenter · OdrNew · OdrPmPanel · OdrDetail · OdrPublicViewer. Operational. **"Center" naming** flagged in V-09.

### 2.10 Public surfaces

22 first-class. Most polished: Trench Safety public landing + QR + Excavation Form (`PublicExcavationForm.jsx`). Lowest polish: public form chrome drift (V-14) — each public surface carries its own header.

---

## 3. Cross-cutting object inventory

### 3.1 Status / chip components

| Concern | Evidence | Verdict |
| --- | --- | --- |
| 15 distinct status-chip components (some sharing filenames) | V-07 | **Duplicated**. Phase B1 introduced `StatusChip` + `statusRegistry` to retire these, but no portal has migrated. |
| Mixed case `Open` / `open` | V-10 | **Inconsistent**. Cosmetic but compounds Simple/Trusted score. |
| Status verbs ambiguous (`offline` = 3 different things across Dispatch/Driver/Asset) | V-11 | **HIGH trust risk**. |
| No shared closure verb | V-12 | **Inconsistent**. |
| Engine literals not wrapped in `t()` | R-11 / T-12 | **Translation 0%**. |
| Forbidden labels still possible | StatusChip absent in production | Phase B1 only — vocabulary defined, not enforced. |

### 3.2 Card / tile / dashboard components

- 8 named "Center" surfaces (see Command Center matrix).
- 4 admin health dashboards (R-04).
- ≥ 7 ad-hoc card renderers across PM alone (HubCard, MasterListPanel, raw divs in /pm/daily, etc., per `MASCI_VISUAL_IDENTITY_AUDIT.md`).
- One canonical `Card` primitive exists (Phase B1) but unused outside `/_internal/*`.

### 3.3 Header / navigation chrome

- ≥ 4 portal-header strategies (V-06).
- Hub file size variance 145 → 668 lines (V-05).
- `PortalShell` primitive exists (Phase B1) but unused in operator portals.

### 3.4 Forms

- Daily Report · Site Inspection · Incident share photos + crew + narrative fields with no shared sub-form (R-02).
- Equipment Issuance + Equipment Training share skeleton — same pattern.
- 8 auth flows sharing skeleton (R-01).

### 3.5 Notifications

- PO digest + per-action PO email can deliver the same event twice (R-07).
- Bell, digest, per-action share no single ownership model.

### 3.6 Map / telematics

- One canonical map: `/api/operations-map/snapshot`. Dispatch and `/operations-map` consume the same hook (D-09 — positive finding).
- 100 / 190 motive-mapped assets have NO GPS coords (D-03).
- 67 circle geofences render as 0 (D-06).
- Production webhook arrival rate **NOT verified** (D-01).

---

## 4. Five-Pillar verdict per portal

Scores are evidence-grounded, NOT aspirational. Citations name a finding ID, an audit file, or a route. See `MASCI_FIVE_PILLAR_SCORECARD.md` for the per-portal scoring narrative.

| Portal | Powerful | Simple | Beautiful | Trusted | Proven | Avg |
| --- | :-: | :-: | :-: | :-: | :-: | :-: |
| Dispatch | 9 | 8 | 8 | 7 | 7 | 7.8 |
| HR | 9 | 8 | 8 | 9 | 8 | 8.4 |
| Trench Safety (Safety module) | 9 | 8 | 9 | 9 | 9 | 8.8 |
| PM | 9 | 6 | 7 | 7 | 7 | 7.2 |
| Admin | 9 | 5 | 6 | 7 | 7 | 6.8 |
| Safety (forms hub) | 8 | 7 | 7 | 7 | 7 | 7.2 |
| Shop | 7 | 7 | 6 | 7 | 7 | 6.8 |
| Field Leadership | 7 | 6 | 6 | 6 | 6 | 6.2 |
| Driver | 6 | 4 | 5 | 6 | 5 | 5.2 |

Justifications are itemised in `MASCI_FIVE_PILLAR_SCORECARD.md`.

---

## 5. Final classification (per directive §"Final Executive Verdict")

| Question | Answer |
| --- | --- |
| **1. Deserves to stay exactly as-is** | Trench Safety module · HR portal · Dispatch (post-13.4A fix) · Operations Map · Master sign-in. |
| **2. Operationally valuable but incomplete** | PM Command Center (real APIs, calmer chrome pending) · Field Leadership (legacy + portal coexist) · Driver (no static hub) · Admin AssetMapping (functional, hostile UI) · Equipment Issuance / Return (R-02 sharing not yet done). |
| **3. Visual-only / preview** | PM V2 Preview (`/_internal/pm-v2-preview` — explicit mock by design) · Design System Demo (`/_internal/design-system` — explicit mock by design). |
| **4. Duplicated** | AdminCommandCenter vs OperationsCenterCommand (V-09 / R-03) · AdminCompliance vs AdminComplianceFindings (R-05) · 4 admin health pages (R-04) · 8 *Center pages (V-09) · 15 status chip components (V-07) · 8 auth flow variations (R-01). |
| **5. Confusing** | The word "Center" means 8 different things (V-09) · `offline` means 3 different things (V-11) · status case drift `Open`/`open` (V-10) · closure verbs vary 7 ways (V-12) · public form chrome drift across 22 surfaces (V-14). |
| **6. Trusted** | Trench Safety data · Operations Map canvas render · HR daily-report verification chain · Dispatch Map (post-13.4A). |
| **7. Untrusted** | Production Motive feed (D-01 — never verified) · 100 / 190 GPS-missing assets (D-03) · 67 circle geofences not rendered (D-06) · 806 untranslated UI strings (R-08, T-01..T-07) · backend EN-only PDFs/emails (R-10, T-08/T-09). |
| **8. Proven** | Phase A tokens.css wiring · Phase B1 primitives (lint clean, zero-diff verified) · Phase B2 PM V2 preview isolation (zero leakage across 6 PM routes) · Track 13.4A Dispatch fix (canvas guardrail PASS). |
| **9. Unproven** | Production webhook arrival rate · production GPS coverage · production feed_status=live · independent operational_summary rederivation (all 7 items on the 13.4D production verification checklist). |
| **10. First implementation priority** | See `MASCI_REALITY_GAP_PRIORITY_LIST.md` §1 — **execute the 7-point production verification checklist** (Track 13.4D), then **collapse the 8 Command Centers** to a coherent naming taxonomy (R-03). |

---

## 6. What this matrix is NOT

- ❌ Not a new discovery program.
- ❌ Not a new findings registry.
- ❌ Not a recovery plan.
- ❌ Not a design system.
- ❌ Not a risk register.

It is a single consolidated view of what already exists, scored against the Five Pillars, with the next action item explicitly named.

Standing rules still in force: **No deploy. No GitHub save. No merge.**
