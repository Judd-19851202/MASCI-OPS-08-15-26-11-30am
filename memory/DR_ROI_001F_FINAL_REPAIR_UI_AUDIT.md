# DR-ROI-001F-FINAL-REPAIR · UI Audit

## Header — Restored MASCI Identity
| Attribute        | Before (Session A drift)                     | After (FINAL-REPAIR)                                   |
|------------------|----------------------------------------------|--------------------------------------------------------|
| Logo             | none / smaller inline                        | `<MasciLogo className="h-12 w-auto" />` (red M)        |
| Eyebrow          | "OPERATIONAL INTELLIGENCE REPORT · V2"       | "MASCI Field Operations" (red-700 mono uppercase)      |
| H1               | "New Daily Report"                            | **"Daily Job Report"** (platform terminology)          |
| Container        | Naked header text                            | Bordered white card `border-2 border-slate-200`        |
| Right cluster    | Draft chip + PDF buttons                     | Draft chip + save status only · no PDF                 |

## Field Form — Removed Non-Field Concerns
| Element                          | Session A drift              | FINAL-REPAIR |
|----------------------------------|------------------------------|--------------|
| Preview PDF button               | Present (disabled)           | **Removed**  |
| Download PDF button              | Present (disabled)           | **Removed**  |
| ConfidencePanel (readiness bar)  | Rendered on shell            | **Deleted**  |
| SupervisorApprovalPanel (audit)  | Rendered on shell            | **Deleted**  |
| PhotoIntelligencePanel (dashboard) | Full observation ledger    | Quiet · items-to-verify only |
| PM Intelligence Panel            | Already removed              | Still absent · CI-locked |

## Daily Operational Summary — The One New Field Concept
| Attribute                | Value                                                                     |
|--------------------------|---------------------------------------------------------------------------|
| Position                 | After Photos + Photo Evidence · before Signature                          |
| Section number           | 09                                                                        |
| Title                    | "Daily Operational Summary"                                               |
| Body                     | Read-only card OR editable textarea (toggled by "Edit Summary")           |
| Buttons                  | **Accept Summary** (red-700 primary) · Edit Summary · Regenerate Summary  |
| Empty state              | "Add Day Setup, at least one Activity Card, and Photos…" · no AI branding |
| Loading state            | "Drafting your daily summary from what you entered…"                      |
| Testids                  | `dr-v2-section-ai-summary`, `dr-v2-ai-accept`, `dr-v2-ai-edit`, `dr-v2-ai-regenerate`, `dr-v2-ai-editor`, `dr-v2-ai-summary-body`, `dr-v2-ai-empty`, `dr-v2-ai-summary-error` |

## Photo Evidence — Quiet & Supportive
- Renders **only when** at least one photo has an unresolved item to verify.
- Never lists detected observations, confidences, or accept/dismiss for
  suggested links (those live server-side).
- Just: "A couple of photos look like they may need a quick check." with
  Confirm / Not applicable buttons.
- Falls back to `null` when there is nothing to ask.

## Section Grammar — V1-Native Throughout
Every section renders via `<Section number="…" title="…" testId="…" />`
imported from `@/components/Section`. Same numbered pattern V1 uses:
- 01 · Day Setup
- 02 · MASCI Crews on Site
- 03 · Equipment on Site
- 04 · Activity Cards
- 05 · Delays · Constraints · Extra Work
- 06 · Tomorrow / Follow-Up
- 07 · Safety · Quality
- 08 · Field Photos
- 08b · Items To Verify From Photos (conditional)
- 09 · Daily Operational Summary
- 10 · Signature + Submit

## Language Audit
| Term (case-insensitive)           | Present anywhere in field form? |
|-----------------------------------|--------------------------------|
| claude / anthropic                | No                             |
| gpt / openai / gemini             | No                             |
| llm / model / provider            | No                             |
| token cost / tokens used          | No                             |
| ai agent / raw model              | No                             |
| Preview PDF / Download PDF        | No                             |
| Confidence dashboard              | No                             |
| Supervisor approval audit log     | No                             |
| "New Daily Report"                | No                             |
| "Daily Job Report"                | Yes (H1 + preview-off state)   |
| "MASCI Field Operations"          | Yes (eyebrow)                  |
