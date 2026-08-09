# PLATFORM_VISUAL_SEMANTICS_REGISTER

Status: PARTIAL PASS — shared color-token authority and owner-observed runtime checks are repaired, but the full portfolio visual audit is still open.

## Governing rule

Domain color and status color must be distinct systems.

## Canonical domain-color expectations

- Admin / Governance — slate / charcoal family (`--domain-admin-*`)
- PM / Project Controls — indigo family (`--domain-pm-*`)
- HR — violet family (`--domain-hr-*`)
- Safety — rose / safety-red family (`--domain-safety-*`) **for domain identity only; error states still use status red**
- Dispatch / Transportation — sky / blue family (`--domain-dispatch-*`)
- Shop / Fleet — orange family (`--domain-shop-*`)
- Training / Guidance — blue family (`--domain-training-*`)
- Field — ochre / field-amber family (`--domain-field-*`)
- QA/QC — green family (`--domain-qaqc-*`)
- Leadership — stone / neutral family (`--domain-leadership-*`)

## Status-color expectations

- Good / verified / healthy — green.
- Warning / pending / due-soon — amber.
- Critical / overdue / blocked — red.
- Unknown / loading / unavailable — neutral, never green.

## Runtime rules

- loading state cannot visually mimic verified state.
- domain accent cannot be the sole indicator of status.
- domain color and status color must never be conflated: a Safety domain surface can be rose without every rose accent meaning error.
- high-priority operational cards appear above help, diagnostics, and recovery actions.

## Shared source of truth repaired in this batch

- `frontend/src/styles/tokens.css`
- `frontend/src/styles/portal-system.css`
- `frontend/src/lib/portalPalette.js`
- `frontend/src/design-system/wp17.css`
- `frontend/src/pages/Hub.jsx`

## Direct evidence now in hand

- Public home QA/QC/domain card runtime check: PASS via `pre_c10_owner_observed_gate.py`
- Compact authenticated home control replaces oversized banner: PASS via `pre_c10_owner_observed_gate.py`
- Visual semantics static guard: PASS via `pre_c10_visual_semantics_gate.py`
- Owner-observed dropdown contrast repair verified live in preview after the menu contrast restyle.

## Current runtime closure

- Admin OS loading cards now settle honestly instead of remaining in pseudo-loading.
- live location posture wording and labels no longer imply vendor semantics as status semantics.
- canonical domain-token mapping is now enforced across shared token files and the primary home cards.
- shop header amber/orange drift has been removed from the shared palette authority.

## Open checks

- fresh full Product Quality v4 ledger after the remaining PRE-C10 edits settle.
- explicit direct visual audit of remaining high-value portal pages and cards outside the shared home/token repairs.
- final owner-observed color-semantics disposition for the entire portfolio cannot be marked PASS until the remaining route-by-route audit finishes.