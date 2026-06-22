# TRACK 15.62 — Implementation Architecture & Deployment Plan
**Status:** PLAN ONLY · NO CODE YET · awaiting approval to proceed.

---

## 1 · Operating principle

The 10 recommendations from Track 15.61 (R-PMCC · R-UX-NARRATIVE · R-HAUL · R-DEAD-FIELDS · R-IDENTITY · R-EXEC · R-MOTIVE · R-MATERIAL-VOCAB · R-UX-PROMPT · R-PHOTO-CAPS) are **one operational system, not ten projects.**

They share:
- One source of truth (`db.daily_reports`)
- One aggregator surface (per-project per-day roll-up)
- One UX (the `NewDailyReport` form)
- One render surface (`pdf_render.render_record_pdf("daily-report", …)`)
- One consumer set (PM · Executive · Operations · CEI · Safety · Attorney · Owner)

Implementing them serially would mean five form rebuilds, three aggregator rewrites, and four PDF cycles. Implementing them together means **one backend module, one form component, one PDF section, one verification pass.** Track 15.62 therefore ships as **a single coordinated release behind a feature flag.**

---

## 2 · Dependency map

```
                ┌──────────────────────────────────────────────────┐
                │  Foundational (must land first inside the release)│
                │                                                    │
                │  ① additive schema · narrative_sections, optional   │
                │  ② db.material_vocabulary collection · seed 20 rows │
                │  ③ feature flag DR_RECOVERY_ENABLED = false (off)  │
                └──────────────────────────────────────────────────┘
                                       │
                                       ▼
                ┌──────────────────────────────────────────────────┐
                │  Shared aggregator · lib/daily_report_rollup.py   │
                │                                                    │
                │  consumed by:                                      │
                │   - GET /api/pm/command-center/{overview,hauls,    │
                │           materials}     (R-PMCC)                  │
                │   - GET /api/admin/daily-roll-up?from=&to=         │
                │           (R-EXEC + Health Metrics)                │
                │   - optional Motive cross-join (R-MOTIVE)          │
                └──────────────────────────────────────────────────┘
                                       │
                                       ▼
                ┌──────────────────────────────────────────────────┐
                │  Form-side recovery (NewDailyReport.jsx)          │
                │                                                    │
                │  - NarrativeWorkflow component (R-UX-NARRATIVE +   │
                │    R-UX-PROMPT)                                    │
                │  - OutboundHaulRow with canonical material drop-   │
                │    down + EquipmentCombo for hauler (R-HAUL +      │
                │    R-MATERIAL-VOCAB + R-MOTIVE picker side)        │
                │  - EmployeeCombo on prepared_by + superintendent   │
                │    (R-IDENTITY)                                    │
                │  - progressive-disclosure of dead fields (R-DEAD-  │
                │    FIELDS)                                         │
                │  - completeness pill in header (R-UX-PROMPT)       │
                │  - per-photo caption input (R-PHOTO-CAPS frontend) │
                └──────────────────────────────────────────────────┘
                                       │
                                       ▼
                ┌──────────────────────────────────────────────────┐
                │  Dashboard read-side                              │
                │                                                    │
                │  - PM Command Center overview / hauls / materials  │
                │    tabs consume aggregator                        │
                │  - Admin Command Center · new "Daily Roll-Up" tab │
                │  - Daily Report Health card                       │
                └──────────────────────────────────────────────────┘
                                       │
                                       ▼
                ┌──────────────────────────────────────────────────┐
                │  PDF render · pdf_render.py                        │
                │                                                    │
                │  - render narrative_sections when present          │
                │  - render per-photo captions when present          │
                │  - 100 % backward compatible with legacy reports   │
                └──────────────────────────────────────────────────┘
                                       │
                                       ▼
                ┌──────────────────────────────────────────────────┐
                │  Flip DR_RECOVERY_ENABLED = true                  │
                │  Production verification: curl + playwright + the │
                │  Track-15.61 forensics harness as regression      │
                │  sentinel.                                        │
                └──────────────────────────────────────────────────┘
```

**No item depends on an item below it in this diagram.** The release ships top-to-bottom in one commit window.

---

## 3 · What truly needs a separate window — and what does not

| Item | Same window? | Justification |
|---|---|---|
| Schema additive (`narrative_sections`, `material_vocabulary`) | **same** | additive · zero migration · no risk |
| Shared aggregator module | **same** | new module · no existing caller affected |
| `/api/admin/daily-roll-up` new endpoint | **same** | new endpoint · no overlap with existing routes |
| PM Command Center aggregator hook-up | **same** | reads new aggregator output, schema unchanged |
| `NewDailyReport` form redesign | **same** | feature-flagged · legacy form remains until flag flips |
| Dead-field progressive disclosure | **same** | UI-only · no schema change |
| `EmployeeCombo` for `prepared_by`/`superintendent` | **same** | UI-only · free-text fallback preserved |
| Per-photo captions (FE + PDF) | **same** | additive optional field |
| Motive cross-join in aggregator | **same** | read-only join · existing indexes |
| Material vocabulary seed | **same** | first-time seed via idempotent script |

**Verdict: every item ships in the same window.** Zero items need a separate deploy.

---

## 4 · Risk register

| Risk | Surface | Probability | Mitigation |
|---|---|---|---|
| Aggregator query slow on prod | backend | LOW | indexed (`project_number`, `report_date`); 154-row corpus is trivial; benchmark < 50 ms before ship |
| Narrative schema collides with legacy reports | DB | NEGLIGIBLE | `narrative_sections` is optional + nullable + `extra="allow"` already on `DailyReportCreate`; legacy reports render via `general_notes` fallback |
| Material vocab string mismatch with historical | DB | LOW | new form writes canonical strings ("Dirt" already matches); free-text fallback retained for non-canonical entries |
| Motive cross-join performance | backend | LOW | window-capped to 7 days; indexes on `event_at` and `motive_truck_id` verified pre-ship |
| PDF render breaks on legacy report | render | NEGLIGIBLE | render-side adds new section ONLY if non-empty; legacy path unchanged |
| Operators reject new narrative UX | UX | MEDIUM | feature flag flip reverts to legacy form; old reports unaffected |
| PM dashboard counts now non-zero, exposes data quality issues | reporting | LOW-positive | the whole point of the track — this risk is desired |
| Frontend hot-reload during deploy momentarily shows mixed UI | deploy | LOW | atomic deploy (single Vercel/CI run) avoids this |
| Rollback corrupts data | rollback | NEGLIGIBLE | additive-only schema; rollback drops new code, leaves data intact |

**Database risks:** zero schema migrations. Zero destructive changes. All new fields optional. Rollback strategy: revert code, data remains valid for both old and new render paths.

**Reporting risks:** the PM Command Center will go from showing `loads_today=0` (a lie) to showing real numbers. If management has built expectations on "0 means nothing happened", expect a one-week reset. This is desired, not a regression — but flag the change in the release notes.

**Migration requirements:** ZERO. Track 15.62 is additive-only.

---

## 5 · Verification strategy (single coordinated pass)

After deploy and flag flip:

**Tier 1 — read-side smoke (curl)**

```
GET /api/pm/command-center/overview            → loads_today > 0 if any active job hauled
GET /api/pm/command-center/hauls               → rows[] not empty
GET /api/admin/daily-roll-up?from=…&to=…       → materials_out_by_material includes "Dirt": 50 loads (matches 15.61 baseline)
GET /api/admin/daily-report-health             → activity_log_completion_pct, narrative_score, median_word_count
GET /api/daily-reports/{best_known_id}         → still returns 200, payload schema unchanged
```

**Tier 2 — write-side smoke (Playwright)**

Test record tagged `TRACK_15_62_DELETE`. Submit a Daily Report via the new narrative workflow on preview, verify:
- prompts render
- save assembles `narrative_sections` correctly
- PDF renders with the new sections
- delete the record · verify zero residue

**Tier 3 — regression sentinel**

Re-run `/app/tests/post_deploy/track_15_61_audit.py` against production immediately after deploy. The harness is the same evidence floor. Compare new forensics.json to the 15.61 baseline. Expectations:
- Activity Log completion % ≥ 26 % (no regression; expect lift over 2-week adoption window)
- PM Command Center hauls tab rows count > 0 (proven fix)
- New `narrative_sections` field showing non-empty for any new report

**Tier 4 — full production verification**

Single Python harness `/app/tests/post_deploy/track_15_62_verify.py` that runs Tiers 1–3 end-to-end, asserts each contract, leaves zero artefacts, and dumps `track_15_62_verification.json`.

---

## 6 · Single ranked roadmap (proposed)

| # | Recommendation | Tier | Effort | Risk | Six-Pillar | Ships in 15.62? |
|---|---|---|---|---|---|---|
| 1 | R-PMCC — PM Command Center haul aggregator | P0 | S | LOW | 56/60 | **yes** |
| 2 | R-EXEC — `/api/admin/daily-roll-up` endpoint | P0 | M | LOW | 55/60 | **yes** |
| 3 | R-MATERIAL-VOCAB — canonical material vocabulary | P0 (promoted from P2 — foundational) | S | LOW | 54/60 | **yes** |
| 4 | R-UX-NARRATIVE — guided prompts narrative workflow | P0 | M-L | MED | 53/60 | **yes** |
| 5 | R-HAUL — outbound row pickers | P0 | M | LOW | 55/60 | **yes** |
| 6 | R-DEAD-FIELDS — progressive disclosure of 3 dead fields | P1 | S | NEGLIGIBLE | 57/60 | **yes** |
| 7 | R-IDENTITY — EmployeeCombo on preparer + super | P1 | S | LOW | 56/60 | **yes** |
| 8 | Daily Report Health Metrics — admin card | P1 | S | LOW | 55/60 | **yes** (shares R-EXEC aggregator) |
| 9 | R-MOTIVE — `asset_mappings` cross-join in aggregator | P1 | M | MED | 51/60 | **yes** |
| 10 | R-UX-PROMPT — completeness coaching pill | P2 | S | LOW | 55/60 | **yes** (depends on R-UX-NARRATIVE) |
| 11 | R-PHOTO-CAPS — per-photo captions | P2 | S | LOW | 52/60 | **yes** |

**11 items, ONE deployment window. No item is deferred.** Total estimated effort: ~3–5 days of focused engineering for one engineer (≈ 600–1000 LOC across ~15 files).

---

## 7 · Single deployment plan

**Phase 1 — Backend (one PR, all backend changes):**
1. Add `db.material_vocabulary` collection with idempotent seed script (~20 canonical materials).
2. Extend `DailyReportCreate` schema with optional `narrative_sections{work_completed, delays, inspections, materials_received, follow_ups, tomorrow_plan}` and optional `photo_captions[]` (additive, `extra="allow"` already permits).
3. Create `/app/backend/lib/daily_report_rollup.py` — single source of truth for: loads_in/out per project per day, by_material aggregation, narrative completeness scores, Motive cross-join.
4. Extend `/api/pm/command-center/overview` + `/hauls` + `/materials` to consume the new aggregator.
5. Add `/api/admin/daily-roll-up?from=&to=` (HR/Admin gate).
6. Add `/api/admin/daily-report-health` (HR/Admin gate · returns the live forensic metrics).
7. Add feature flag env: `DR_RECOVERY_ENABLED=true|false`.

**Phase 2 — PDF render (same PR):**
1. Extend `pdf_render.render_record_pdf("daily-report", record)` to render `narrative_sections` when present (six headed paragraphs).
2. Extend the photo section to render per-photo captions when present.
3. Backward-compatible — legacy reports continue to render identically.

**Phase 3 — Frontend (one PR, all frontend changes):**
1. New `NarrativeWorkflow` component (six prompts, auto-assembles `narrative_sections`).
2. New `OutboundHaulRow` component (material dropdown · EquipmentCombo hauler · canonical units).
3. Replace `prepared_by` + `superintendent` `Input` with `EmployeeCombo`.
4. Move `schedule_delays_notes`, `weather_impact_notes`, `linked_excavation_ids` behind a "More details" collapsible.
5. Header completeness pill (consumes a small client-side scorer mirroring the backend `daily_report_rollup.score()`).
6. Per-photo caption input in `PhotoUpload`.
7. Admin Command Center: new "Daily Roll-Up" tab consuming `/api/admin/daily-roll-up` + Daily Report Health card consuming `/api/admin/daily-report-health`.

**Phase 4 — Production verification (single harness):**
- `/app/tests/post_deploy/track_15_62_verify.py` runs all four tiers, dumps JSON evidence, exits 0 on clean pass.
- Cleanup tag `TRACK_15_62_DELETE` on any synthetic record.
- Zero residue verified.

**Phase 5 — Flag flip:**
- `DR_RECOVERY_ENABLED=true` in production env.
- Run verification harness against production.
- If green: track is DONE.
- If red: flip flag back to `false` (FE reverts to legacy form; new backend endpoints continue to function harmlessly).

---

## 8 · Deliverables list (single shipment)

1. `TRACK_15_62_IMPLEMENTATION_ARCHITECTURE.md` (this document)
2. `TRACK_15_62_PMCC_HAUL_RECOVERY.md`
3. `TRACK_15_62_NARRATIVE_RECOVERY.md`
4. `TRACK_15_62_EXECUTIVE_PRODUCTION.md`
5. `TRACK_15_62_MOTIVE_LINKAGE.md`
6. `TRACK_15_62_DAILY_REPORT_HEALTH.md`
7. `TRACK_15_62_DEAD_FIELD_RECOVERY.md`
8. `TRACK_15_62_IMPLEMENTATION_REPORT.md`
9. `TRACK_15_62_PRODUCTION_VERIFICATION.md`
10. `TRACK_15_62_EXECUTIVE_SUMMARY.md`
11. `TRACK_15_62_SIX_PILLAR_CERTIFICATION.md`
- PRD.md updated
- CHANGELOG.md updated

---

## 9 · Estimated engineering envelope

| Layer | Files touched | New LOC | Edited LOC |
|---|---|---|---|
| Backend schema + aggregator + endpoints | 5–6 | ~400 | ~50 |
| PDF render | 1 | ~80 | ~20 |
| Frontend NewDailyReport + new components | 6–7 | ~500 | ~150 |
| Frontend Admin Command Center additions | 2 | ~150 | 0 |
| Verification harness | 1 | ~300 | 0 |
| Tests + deliverables | 11 markdown + 1 py | ~3000 (markdown) | 0 |
| **Total code** | **15–17 files** | **~1430** | **~220** |

Realistic engineering time: **3–5 working days of focused dev** with thorough verification.

Realistic LLM-agent time within a single session: **likely too large for one continuous run; needs two sessions** — one for backend + PDF + verification harness, one for frontend redesign + dashboard surfaces + final verification.

This is an honest scope. The work is one project. The delivery may need two consecutive sessions to land safely.

---

## 10 · Six Pillars on the plan itself

| Pillar | Score | Why |
|---|---|---|
| Powerful | 10 | Closes every Track-15.61 gap in one coordinated release. |
| Simple | 9 | One feature flag, one aggregator, one form component family — but the plan itself is non-trivial (-1). |
| Beautiful | 10 | The architecture is one diagram, not six. |
| Trusted | 10 | Additive-only schema, feature-flagged, full rollback path, zero data risk. |
| Proven | 9 | Verification harness reuses the 15.61 forensics floor — same evidence basis. |
| Deployable | 10 | One window, one flag, one revert. |

**Total: 58 / 60 (97 %)**.

---

## 11 · Justification for the "ship-in-one" posture

Splitting these 11 items into multiple tracks would:
- Force two-to-five rebuilds of the same `NewDailyReport` form (each disturbs operator muscle memory).
- Force two-to-three aggregator rewrites (engineering tax).
- Force two-to-three production-verification cycles (operational tax).
- Leave the Daily Report system in a half-fixed state between deploys — which is exactly the trust failure Track 15.61 surfaced.
- Burn calendar time without proportional risk reduction (the items genuinely do not have meaningful sequential dependencies once the shared aggregator exists).

**Recommendation: APPROVE this architecture and proceed with implementation in two consecutive sessions** (Session A: backend + PDF + verification harness; Session B: frontend redesign + dashboard surfaces + final verification + deliverables). Both sessions ship to the same deploy window behind the same feature flag.

If a single session is mandated, **I can land Session A's backend block end-to-end this session** (additive schema · aggregator · new endpoints · PDF render · verification harness Tier 1+3) — Session B's frontend redesign would follow on operator request without exposing a half-finished form to the field.
