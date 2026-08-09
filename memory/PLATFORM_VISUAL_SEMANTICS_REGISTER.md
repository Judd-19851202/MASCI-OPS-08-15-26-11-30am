# PLATFORM_VISUAL_SEMANTICS_REGISTER

Status: OPEN — PRE-C10 blocking register

## Governing rule

Domain color and status color must be distinct systems.

## Domain-color expectations

- Safety — red/rose family for incident severity and urgent safety risk.
- PM / Project Controls — slate/blue family for planning and control surfaces.
- HR — teal/emerald family.
- QA/QC — amber/gold family.
- Dispatch / Transportation — orange family.
- Shop / Fleet — indigo/steel family.
- Admin / Governance — neutral/slate family with restrained accent usage.

## Status-color expectations

- Good / verified / healthy — green.
- Warning / pending / due-soon — amber.
- Critical / overdue / blocked — red.
- Unknown / loading / unavailable — neutral, never green.

## Runtime rules

- loading state cannot visually mimic verified state.
- domain accent cannot be the sole indicator of status.
- high-priority operational cards appear above help, diagnostics, and recovery actions.

## Current runtime closure

- Admin OS loading cards now settle honestly instead of remaining in pseudo-loading.
- live location posture wording and labels no longer imply vendor semantics as status semantics.

## Open checks

- full screenshot-led product-quality pass across all required widths.
- explicit audit of card ordering and domain/status separation on remaining high-value surfaces.