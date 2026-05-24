# COACHING_AND_VERBIAGE_AUDIT.md
**Phase 17 · iter413 · 2026-05-24**

## Verdict
**PASS with one observation.** Coaching surfaces are platform-native, verbiage is operator-language across all Phase 12-17 work. Some pre-Phase-12 legacy modules retain older voice but are not regressions.

## Coaching presence by surface
| Surface | Coaching mechanism | Voice | Status |
|---|---|---|---|
| Dispatch Command Portal (iter411) | 6 coaching bullets + 5 GuideTiles | Operational, calm | ✅ |
| Operational Attention section (iter411) | Per-card hint text ("Shop sees these too. Decide reassign vs hold.") | Action-oriented | ✅ |
| Issue Work tiles (iter411) | Subtitle per tile ("Lowboy / equipment haul", "Asphalt oil · binder · fuel") | Operator vocabulary | ✅ |
| Assignment Create Drawer (iter408/410) | Inline orange coaching strip per haul-type (Material vs Equipment Move vs Tanker) | Calm, ≤2 lines | ✅ |
| Shift Start QR generator (iter406) | LifecycleGuide with 4 sections (Print · Place · Scan · Restraint) | Operator vocabulary | ✅ |
| PM Haul Activity tile (iter409) | Subtitle + "production awareness · read-only" pill + empty state | Production-language | ✅ |
| Driver Shift Start (iter401/402) | Searchable dropdown hints + bilingual labels | Driver-language | ✅ |
| Dispatch Lifecycle Tile (iter396) | Inline LifecycleGuide | Operational | ✅ |

## Vocabulary scanner findings
- 16 T1 flags · ALL are `iter###` source-comments (expected harmless tier · serves audit-trail purpose)
- **0 T2 / T3 hits** across the entire frontend (ERP-language tier)
- File coverage: 5 frontend files flagged · 0 backend files

## Doctrine-locked vocabulary swaps (iter411 verified)
| Was | Now |
|---|---|
| "Equipment Movement Command Center" | "Dispatch Command" |
| "Utilization" | "What's moving vs sitting" |
| "Idle Alerts" | "Trucks sitting too long" |
| "Integrations" | "Systems that validate operations" |
| "Transfers" | "Equipment moves" |
| "Dashboard" | "Board / Flow / Status" |
| "Metrics" | "Operational signals" |
| "KPI / Score" | (removed entirely — replaced by `quiet / flowing / attention`) |

## Coaching gaps surfaced (non-blocking)
- Pre-Phase-12 Safety detail pages do not yet use `LifecycleGuide` pattern. Their existing voice is functional but visually older.
- HR Qualification pages lack inline coaching for newer flow scenarios. Mitigated by `/guidance` hub link.
- Inspections + Daily Report forms (legacy) lack the "Why does it matter? What happens next?" coaching pattern that iter392+ surfaces consistently.

## Recommendation
**No fixes warranted before Day-1 deployment.** Legacy modules are operationally correct and visually intact. The Day-1 debrief (see `/app/memory/DLS_DAY1_LIVE_OPS_DEBRIEF.md`) will name which legacy coaching gaps actually cause hesitation in real ops, vs. theoretical concerns.

## Verdict
Coaching and verbiage discipline holds platform-wide for Phase 12-17 work. Operator vocabulary scanner remains as automated guardrail.
