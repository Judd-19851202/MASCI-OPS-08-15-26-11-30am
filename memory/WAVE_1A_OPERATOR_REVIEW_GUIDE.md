# Wave-1A · Operator Review Guide

_Phase V.2 · Daily Report Elite Upgrade · 2026-05-29._

> Read top-to-bottom in ~4 minutes. By the end of §8 you have
> everything needed to authorize Wave-1B (UI surface) or hold.

---

## 1 · State of the substrate

| Wave | Scope | Status |
|---|---|---|
| M0.0 → M1 | ODR substrate · doctrines · archive · unified projector | ✅ Live |
| Pivot planning | 7 docs · build authorization checklist | ✅ Closed |
| **Wave-1A** | **POST restore · production · constraints · audit footer · advisory flags** | ✅ **This wave** |

## 2 · Wave-1A in 60 seconds

Six moves shipped. **No frontend code shipped — the data plumbing
is ready; the UI surface waits for Wave-1B authorization.**

1. **POST `/api/daily-reports` restored** (M1 freeze partial revert)
2. **DELETE `/api/daily-reports/{id}` stays frozen** (historical immutability)
3. **`production: List[ProductionRow]`** added — 7-unit closed enum
4. **`constraints: List[ConstraintRow]`** added — 11-type closed enum
5. **`audit_envelope_sha256`** stamped at insert + `GET /api/daily-reports/{id}/audit-footer` returns canonical footer
6. **Advisory flags** derived server-side (utility → RFI · weather → schedule · informational only)

15 / 15 Wave-1A tests passing. 82 / 82 cumulative ODR tests passing.
Both governance probes green.

## 3 · What did NOT change (per directive)

| Prohibited | Status |
|---|---|
| Build new ODR form | ❌ NOT BUILT |
| Start pilot | ❌ NOT STARTED |
| Start RFI module | ❌ NOT TOUCHED |
| Start Schedule module | ❌ NOT TOUCHED |
| Start P6 integration | ❌ NOT TOUCHED |
| Add dashboard bloat | ❌ NONE ADDED |
| Add new navigation | ❌ NONE ADDED |
| Change Daily Report name | ❌ STILL "DAILY REPORT" |
| Increase foreman workload | ❌ NEW FIELDS OPTIONAL · WORKFLOW UNCHANGED |

## 4 · Doctrine compliance

| Doctrine | Status |
|---|---|
| Doctrine Lock #1 (Simplicity Test) | ✅ Foreman workflow unchanged · new fields optional |
| Doctrine Lock #2 (Platform Inheritance) | ✅ No new module · no new collection · no new dep |
| Audience Projection (M0.4) | ✅ Forward-compatible projection mapping documented |
| Operational Linking Rules | ✅ legacy_daily_report stays target-only |
| Operational Calmness | ✅ Advisory copy is "Potential" · no urgency |
| Cross-Portal Coaching Standard | ✅ Non-punitive |

## 5 · 6 mandated artifacts produced

| # | Artifact |
|---|---|
| 1 | `WAVE_1A_IMPLEMENTATION_REPORT.md` |
| 2 | `PRODUCTION_TRACKING_CERTIFICATION.md` |
| 3 | `CONSTRAINT_TRACKING_CERTIFICATION.md` |
| 4 | `OFFLINE_HARDENING_CERTIFICATION.md` |
| 5 | `DAILY_REPORT_AUDIT_FOOTER_CERTIFICATION.md` |
| 6 | `ADVISORY_FLAG_CERTIFICATION.md` |
| 7 | `WAVE_1A_OPERATOR_REVIEW_GUIDE.md` (this) |

## 6 · Spot-check checklist (~3 minutes)

- [ ] `POST /api/daily-reports` returns 200 with the new fields persisted
- [ ] `DELETE /api/daily-reports/{id}` returns 410
- [ ] `GET /api/daily-reports/{id}` returns the row with `production[]`, `constraints[]`, `audit_envelope_sha256`
- [ ] `GET /api/daily-reports/{id}/audit-footer` returns sha + footer line
- [ ] Try `unit: "FATHOMS"` on a production row → 422
- [ ] Try `constraint_type: "wormhole"` → 422
- [ ] Try a constraint with `type: utility` → response shows `may_require_rfi: true` AND `may_affect_schedule: true`
- [ ] Try a constraint with `type: weather` → `may_affect_schedule: true` only
- [ ] `GET /api/operational-records?limit=200` includes any newly-created DR
- [ ] 82 / 82 ODR pytest still passing

## 7 · Approval items · what to sign off on before Wave-1B

- [ ] **Wave-1A backend acceptance** — read `WAVE_1A_IMPLEMENTATION_REPORT.md` + the 5 sibling certifications
- [ ] **Production unit closed enum acceptance** — `{LF, SY, CY, TON, EA, ACRE, OTHER}` — confirm this matches MASCI field language
- [ ] **Constraint type closed enum acceptance** — `{weather, utility, survey, material, equipment, trucking, mot, cei_inspection, owner_engineer, safety, other}` — confirm this matches MASCI field language
- [ ] **Advisory flag derivation table acceptance** — read `ADVISORY_FLAG_CERTIFICATION.md §2` — confirm the heuristic matches MASCI's operational reality
- [ ] **Wave-1B authorization decision** — pick UI scope: full (all new fields visible on the form) · partial (production only, constraints hidden until Wave-1C) · hold (no UI yet · use Wave-1A backend through admin/API only)
- [ ] **Wave-1C scope decision** — offline hardening + DR PDF audit footer rendering (~2.5–3 dev-days estimated)

## 8 · What's next (operator picks)

| Option | Description | Effort |
|---|---|---|
| **Wave-1B** | Frontend UI for production rows + constraint chips on the existing Daily Report form (no new pages) | ~2.5–3 dev-days |
| **Wave-1C** | Offline strengthening + DR PDF audit footer rendering · field-readiness test surface | ~2.5–3 dev-days |
| **B then C** | Recommended sequence — UI lands first so the field can use the new fields before the offline hardening lands | total ~5–6 dev-days, parallelizable to ~4 calendar days |
| **C then B** | Conservative — offline + audit footer first, then UI · safer for pilot readiness | total ~5–6 dev-days |
| **Hold** | Pause Wave-1B/1C until operator review of Wave-1A in the field | 0 |

Pilot rollout authorization is gated behind Wave-1C completion (the
7 acceptance criteria in `OFFLINE_HARDENING_CERTIFICATION.md §5`).

## 9 · Stop condition

🛑 **HALTED at end of Wave-1A as directed.**

- ❌ NO pilot
- ❌ NO RFI / Schedule / P6 work
- ❌ NO production deploy
- ❌ NO frontend UI for the new fields yet
- ✅ Awaiting operator review and Wave-1B/1C authorization

---

_End of WAVE_1A_OPERATOR_REVIEW_GUIDE.md · supersedes the Daily Report Elite Upgrade review for the next wave decision._
