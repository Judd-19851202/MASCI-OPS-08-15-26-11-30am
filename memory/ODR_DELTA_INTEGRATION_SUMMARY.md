# ODR DELTA INTEGRATION SUMMARY

_Phase V.1 · Operational Daily Record · Architecture Revision Master · 2026-05-29_

This document is the authoritative map of how the eight approved
gap-audit deltas (**D1–D8**) and the ten newly-locked operator
doctrine statements (**O1–O10**) land across the five ODR
architecture artifacts. It is the read-first reference for any
agent or operator reading the revised spec.

**No implementation. No code. No routes. No collections. No UI.**
This is a spec revision pass only.

---

## 1 · Newly-locked operator doctrine (O1–O10)

Locked verbatim into the architecture · embedded in every artifact's
"Doctrine inherited" preamble.

| # | Doctrine statement |
|---|---|
| O1 | The ODR must support real construction complexity without making the foreman carry that complexity. |
| O2 | One ODR may contain many: production segments · work areas · crew operation types · material events · equipment events · delays · extra work events · safety events · constraints · photos. |
| O3 | The ODR must remain simple enough for normal field completion in under 5 minutes. |
| O4 | Complex days may take longer, but the system must use repeat/add-row patterns, smart defaults, voice-first input, dropdowns, and auto-fill to reduce burden. |
| O5 | The platform must work harder than the foreman. |
| O6 | ODR is single-entry / multi-consumer: PM · Safety · Dispatch · Shop · HR · Executive · Operational Memory · Search · RFI · Schedule · Claims · future AI must consume ODR data without duplicate field entry. |
| O7 | ODR must be bilingual by architecture, not retrofit: field users may complete the form in Spanish while the company record normalizes to English and preserves the original Spanish. |
| O8 | ODR must inherit platform-wide Tier-1 Reliability Layer: autosave · offline drafts · offline photo queue · draft recovery · GPS capture · device verification · sync status · edit history. |
| O9 | Safety/compliance requirements may hard-stop submission. Production/detail deficiencies should coach, not punish. |
| O10 | The ODR PDF must be redesigned as an executive/claims/owner-ready operational record, not a raw form dump. |

---

## 2 · The eight approved deltas (D1–D8)

| # | Delta | Source requirement | Severity | Status |
|---|---|---|---|---|
| D1 | `production_segments: List[ProductionSegment]` | REQ #1 · Multi-Event Reality | HIGH | ✅ approved |
| D2 | Top-level `work_areas` + `work_area_id` FK on every event | REQ #1 · Multi-Event Reality | HIGH | ✅ approved |
| D3 | Top-level `materials: List[MaterialEvent]` | REQ #1 · Multi-Event Reality | MEDIUM | ✅ approved |
| D4 | `ReliabilityBlock` + `DeviceFingerprint` + `SyncConflict` | REQ #3 · Tier-1 Reliability | HIGH | ✅ approved |
| D5 | `CompletionTelemetry` envelope | REQ #2 · Simplicity Doctrine | LOW | ✅ approved |
| D6 | `LocalizedString` envelope on 10 free-text fields + `odr_translation_events` collection | REQ #4 · Bilingual | HIGH | ✅ approved · **MANDATORY · NOT DEFERRABLE** |
| D7 | `SafetyBlock.events: List[SafetyEvent]` per-event lineage | REQ #6 · Safety Hard-Stop | LOW | ✅ approved |
| D8 | `odr_bilingual_probe.py` governance probe | REQ #4 · Bilingual governance | LOW | ✅ approved |

---

## 3 · Delta × Artifact incidence matrix

| Delta | DATA_MODEL | UI_WIREFRAMES | ECOSYSTEM | PDF_LAYOUT | MIGRATION_PLAN |
|---|---|---|---|---|---|
| D1 · ProductionSegment | ▲ structural | ▲ § 6 reshape | ▲ projectors per-segment | ▲ Page 3 per-segment | ▲ legacy activities → segments |
| D2 · work_areas | ▲ new top-level block | ▲ new § 2.5 | ▲ work_area-aware reads | ▲ Page 4 work_area column | ▲ legacy single-area default |
| D3 · materials | ▲ new top-level block | ▲ new § 5.5 | ▲ Memory / PM / Shop consume | ▲ Page 2/3 materials sub-table | ▲ legacy `materials[]` → new block |
| D4 · ReliabilityBlock | ▲ envelope addition | ▲ global shell sync pill | ▲ admin · governance probe | ▽ informational only | ▲ legacy default values |
| D5 · CompletionTelemetry | ▲ envelope addition | ▽ no visible change | ▲ admin health view | ▽ no PDF surface | ▲ legacy nulls |
| D6 · LocalizedString | ▲ 10 field rewrites | ▲ global EN/ES toggle | ▲ projectors read `.text` only | ▲ English-only render rule | ▲ legacy ES canonicalization |
| D7 · SafetyEvent[] | ▲ § 3.10 refactor | ▲ § 10 multi-event branch | ▲ Safety projector iterates events | ▲ Page 5 per-event blocks | ▲ legacy single-event default |
| D8 · bilingual probe | ▽ N/A | ▽ N/A | ▲ pre_deploy_check.sh stage | ▽ N/A | ▽ N/A |

Legend: ▲ = revision required · ▽ = no change · all revisions land
as "Delta Integration Addendum (D1–D8)" appended to each artifact.

---

## 4 · The 10 bilingual-wrapped free-text fields (D6 inventory)

These fields are converted from `str` → `LocalizedString` in the
revised data model. The list is **closed** — any future free-text
field added to the ODR must explicitly opt in or out of localization
with operator approval.

| # | Field path | Section | Voice-first? |
|---|---|---|---|
| 1 | `DelayEntry.description` | § 7 Delays | yes |
| 2 | `ExtraWorkEntry.description` | § 8 Extra Work | yes |
| 3 | `ConstraintEntry.description` | § 9 Constraints | yes |
| 4 | `SubRow.work_performed` | § 5 Subs | yes |
| 5 | `PhotoRef.text_caption` | § 12 Photos | yes |
| 6 | `PhotoRef.voice_caption` | § 12 Photos | yes (audio source) |
| 7 | `TomorrowPlanBlock.planned_work` | § 13 Tomorrow | yes |
| 8 | `WeatherImpactBlock.description` | § 11 Weather | yes |
| 9 | `PlanVsActualBlock.variance_reason` | § 14 Plan vs Actual | yes |
| 10 | `MaterialEvent.description` + `WorkArea.label` + `WorkArea.notes` | § 5.5 · § 2.5 (new) | yes |

The audit-only `ReviewEvent.note` and admin-strict fields stay
English-only; they are not foreman-authored.

---

## 5 · Doctrine cross-reference map

| Doctrine | Where enforced in artifacts |
|---|---|
| O1 (complexity ≠ burden) | DATA_MODEL § 2 envelope · UI § 0 shell · ECOSYSTEM § 3 projector pattern |
| O2 (many of everything) | All five artifacts via D1–D3 + D7 |
| O3 (< 5 min normal day) | DATA_MODEL § 2 (CompletionTelemetry · D5) · UI § 17 + per-section receipts (audit Track 2) |
| O4 (smart defaults · voice · dropdowns) | UI § 17 cross-cutting rules · DATA_MODEL closed-set enums (§ 4) |
| O5 (platform > foreman) | ECOSYSTEM § 3 (auto-fill contracts) · UI auto-fill density |
| O6 (single-entry · multi-consumer) | ECOSYSTEM § 1, § 2 (12 consumers) · gap-audit REQ #5 |
| O7 (bilingual by architecture · D6) | DATA_MODEL LocalizedString · UI EN/ES toggle · ECOSYSTEM English-canonical reads · PDF English-only · governance via D8 |
| O8 (Tier-1 Reliability · D4) | DATA_MODEL ReliabilityBlock + DeviceFingerprint + SyncConflict |
| O9 (safety hard-stop · production coach) | DATA_MODEL § 3.10 + ReadinessSnapshot · ECOSYSTEM § 4 dispatch order · gap-audit REQ #6 |
| O10 (executive-grade PDF) | PDF_LAYOUT all sections · 5 variants · forensic envelope |

---

## 6 · New collections introduced by D1–D8

In addition to the four collections already specified
(`odr`, `odr_photos`, `odr_section_events`, `odr_consumer_index`),
the deltas introduce:

| Collection | Purpose | Append-only? |
|---|---|---|
| `odr_translation_events` | D6 audit trail — every ES → EN transition (or human override) is logged | yes — protected by `trendline_integrity_probe.py` extension |

No other collections are introduced. `work_areas`, `materials`,
`production_segments`, `reliability`, `device_fingerprint`,
`completion_telemetry`, `safety_events` all live **inside** the
`odr` document.

---

## 7 · New probes / governance instruments

| Probe | Source delta | Mode |
|---|---|---|
| `odr_bilingual_probe.py` | D8 | gate (HARD on missing LocalizedString fields · WARN on translation lineage gaps) |
| `odr_doctrine_probe.py` *(planned · already in MIGRATION_PLAN § 1.2)* | pre-existing | gate |
| `trendline_integrity_probe.py` extension (covers `odr_section_events` + `odr_translation_events`) | extension of Wave 1.1B probe | gate |

The bilingual probe is **wired into `pre_deploy_check.sh` from day
one of M0** — bilingual doctrine cannot drift without breaking the
gate.

---

## 8 · Survivability of the 25 open architecture questions

All 25 questions previously logged in the artifact `§ Open
questions` blocks remain **valid and unblocked** by D1–D8. The two
clarifications noted in the gap audit (§ Effect of remediation)
hold:

- **DATA_MODEL § 8 Q2** (timezone) — now also governs per-work-area
  TZ. Default remains site-TZ.
- **UI_WIREFRAMES § 18 Q4** ("multiple secondary_operations") — now
  subsumed by `production_segments`. Default cap: 6 segments / ODR.

No question is invalidated. No new blocking question is introduced.

---

## 9 · What this revision pass does NOT do

- ❌ Does not change any production code
- ❌ Does not change any frontend file
- ❌ Does not create any Mongo collection
- ❌ Does not modify environment variables, .env files, or supervisor config
- ❌ Does not begin Wave M0 (dual-write pilot)
- ❌ Does not touch the V-Prelude Observation Freeze (still intact)
- ❌ Does not modify the live production deployment

The only filesystem mutations in this pass are:

1. This document (new)
2. `ODR_DATA_MODEL.md` — appended addendum
3. `ODR_UI_WIREFRAMES.md` — appended addendum
4. `ODR_ECOSYSTEM_INTEGRATION_MAP.md` — appended addendum
5. `ODR_PDF_LAYOUT_DESIGN.md` — appended addendum
6. `ODR_MIGRATION_PLAN.md` — appended addendum
7. `_INDEX.md` — ODR § added under § 4 of the master index
8. `ODR_SPEC_LOCK_READINESS_REVIEW.md` (new)
9. `PRD.md` — append-only stanza

---

## 10 · Next operator actions

1. Read the appended addendum in each of the 5 artifacts.
2. Read `ODR_SPEC_LOCK_READINESS_REVIEW.md` for the consolidated
   "ready-to-lock" certification.
3. Answer the 25 open architecture questions (or accept defaults).
4. Issue the spec lock command → implementation Wave M0 begins.

_Architecture revision pass authorized. Stop after artifact updates._
