# Wave-1B + 1C · Operator Review Guide

_Phase V.2 · 2026-05-29 · supersedes Wave-1A review guide for the pilot decision._

> Read top-to-bottom in ~5 minutes. By the end of §8 you have
> everything needed to authorize the pilot-prep wave (Wave-1D) —
> or to hold for further review.

---

## 1 · State of the substrate

| Wave | Scope | Status |
|---|---|---|
| M0.0 → M1 | ODR substrate · doctrines · archive · unified projector | ✅ Live |
| Pivot planning | 7 docs · build authorization checklist | ✅ Closed |
| Wave-1A | Backend: POST restore · structured fields · audit footer · advisory flags | ✅ Closed |
| **Wave-1B** | **Frontend UI for production + constraints + PM exposure tile** | ✅ **This review** |
| **Wave-1C** | **DR PDF audit footer render + offline baseline + pilot readiness** | ✅ **This review** |

## 2 · Wave-1B + 1C in 60 seconds

**Wave-1B (UI):**
- Production card added inside existing Daily Report form (step 4 · `CollapseCard`)
- Constraint chip-selector card added (step 6 · 11 chips · one-tap)
- PM exposure tile component + aggregator endpoint
- **No new form. No new page. No new wizard. 9-step contract preserved.**

**Wave-1C (audit + offline):**
- DR PDF now renders `Official Record · DR-... · sha256=<16> · rendered <UTC>` in `@bottom-center` of every page (WeasyPrint slot)
- Existing offline / recovery posture re-baselined
- Pilot readiness assessment produced — gating: ~2.25 dev-days + 1 field session

## 3 · Field-facing impact (Doctrine Lock #1 verdict)

| Step | Pre-Wave | Post-Wave | Foreman impact |
|---|---|---|---|
| 1 Project | unchanged | unchanged | 0 |
| 2 Crew | unchanged | unchanged | 0 |
| 3 Equipment | unchanged | unchanged | 0 |
| 4 Production | Activity log only | + optional production card | +15–30 s if foreman fills 1–3 rows |
| 5 Photos | unchanged | unchanged | 0 |
| 6 Issues/Delays | Y/N + notes | + optional constraint chip selector | +10–15 s if any constraint |
| 7 Safety | unchanged | unchanged | 0 |
| 8 Sign | unchanged | unchanged | 0 |
| 9 Submit | unchanged | unchanged + audit footer renders later | 0 |

**< 5 min target preserved.** Empty production + constraints = same
< 3 min stretch as Wave-1A.

## 4 · Doctrine compliance

| Doctrine | Status |
|---|---|
| Doctrine Lock #1 (Simplicity Test) | ✅ 9-step locked · new cards optional · foreman load unchanged when skipped |
| Doctrine Lock #2 (Platform Inheritance) | ✅ Reuses CollapseCard + RepeatBlock + WeasyPrint · no new component family |
| Audience Projection | ✅ DR audit footer is universal · no audience-specific stripping needed |
| Operational Calmness | ✅ All UI is slate · all copy is non-punitive · "Signal only" framing throughout |
| Cross-Portal Coaching Standard | ✅ No punitive prompts |
| Operational Linking Rules | ✅ `legacy_daily_report` target-only preserved |

## 5 · Forbidden actions (per directive · all NOT done)

- ❌ NO new ODR form · NO Daily Report rename
- ❌ NO pilot · NO RFI module · NO Schedule module · NO P6 integration
- ❌ NO new navigation · NO dashboard clutter
- ❌ NO foreman burden increase
- ❌ NO production deploy

## 6 · 9 mandated artifacts produced

| # | Artifact |
|---|---|
| 1 | `WAVE_1B_IMPLEMENTATION_REPORT.md` |
| 2 | `PRODUCTION_UI_CERTIFICATION.md` |
| 3 | `CONSTRAINT_UI_CERTIFICATION.md` |
| 4 | `PM_EXPOSURE_TILE_CERTIFICATION.md` |
| 5 | `WAVE_1C_IMPLEMENTATION_REPORT.md` |
| 6 | `OFFLINE_RECOVERY_CERTIFICATION.md` |
| 7 | `PDF_AUDIT_FOOTER_RENDER_CERTIFICATION.md` |
| 8 | `PILOT_READINESS_ASSESSMENT.md` |
| 9 | `WAVE_1B_1C_OPERATOR_REVIEW_GUIDE.md` (this) |

## 7 · Test surface · 89 / 89 passing

| Suite | Result |
|---|---|
| M0.1 substrate | 🟢 12 / 12 |
| M0.2 + M0.2A engines | 🟢 24 / 24 |
| M0.3 surfaces | 🟢 7 / 7 |
| M0.4 photo embedding | 🟢 9 / 9 |
| M1 Option C | 🟢 15 / 15 |
| Wave-1A | 🟢 15 / 15 |
| **Wave-1B + 1C (this wave)** | 🟢 **7 / 7** |
| Public link continuity probe `--gate` | 🟢 0 fail · 0 warn |
| Bilingual probe `--gate` | 🟢 0 fail |

## 8 · Approval items · what to sign off on before pilot

- [ ] **Wave-1B UI acceptance** — read `WAVE_1B_IMPLEMENTATION_REPORT.md` + `PRODUCTION_UI_CERTIFICATION.md` + `CONSTRAINT_UI_CERTIFICATION.md`
- [ ] **PM exposure tile acceptance** — read `PM_EXPOSURE_TILE_CERTIFICATION.md` · decide preferred placement (PM Hub vs. project detail)
- [ ] **Wave-1C audit footer acceptance** — read `PDF_AUDIT_FOOTER_RENDER_CERTIFICATION.md` · verify the footer line copy reads correctly for FAA / FDOT / CEI / Owner audiences
- [ ] **Pilot readiness assessment acceptance** — read `PILOT_READINESS_ASSESSMENT.md` · acknowledge that 1 / 7 acceptance criteria are met and 6 require Wave-1D
- [ ] **Wave-1D authorization decision** — pilot-prep scope (~2.25 dev-days: service-worker queue formalization + queued banner + recovery telemetry + 3 automated test harnesses)
- [ ] **Field test coordination** — decide which foreman + which job site for the first weak-signal preview submit (criterion #7)

## 9 · Spot-check checklist (~3 minutes)

- [ ] Open the existing Daily Report form (no new route)
- [ ] Scroll to "Production Quantities" — confirm the optional card is present
- [ ] Add a production row · pick `unit: LF` · type `qty: 240` · save · refresh · verify it persists
- [ ] Scroll to "Issues / Delays · Structured" — confirm the 11 chip buttons
- [ ] Tap the "Utility" chip · confirm a row appears with `constraint_type: utility` · type a hours value + notes · save · refresh · verify it persists
- [ ] In the response, verify `may_require_rfi: true` AND `may_affect_schedule: true` on that row
- [ ] `curl GET /api/daily-reports/exposure-signals?days=14` returns a JSON body with `"kind": "signal_only"`
- [ ] Generate a DR PDF (via the existing export flow) — confirm the footer line `Official Record · DR-... · sha256=... · rendered ...` appears at the bottom-center of every page

## 10 · Stop condition

🛑 **HALTED at end of Wave-1B + Wave-1C as directed.**

- ❌ NO pilot until pilot readiness assessment is reviewed and approved
- ❌ NO RFI / Schedule / P6 work
- ❌ NO production deploy
- ✅ Awaiting operator review of the 9 artifacts produced and the 6 approval items in §8

---

_End of WAVE_1B_1C_OPERATOR_REVIEW_GUIDE.md · supersedes the Wave-1A operator review guide for the pilot-prep wave decision._
