# PLATFORM_ACRONYM_REGISTER

Status: OPEN — PRE-C10 blocking register

## Allowed construction/operations acronyms

- QA/QC
- PM
- HR
- JHA
- DVIR
- DOT
- OSHA
- CDL
- EMR

## Allowed with expansion or context on first use in user-facing detail

- C6 / C7 / C8 / C9 only in governance, admin, or advanced diagnostics contexts.
- KPI only when paired with surrounding business wording.

## Avoid in primary operator UX

- CAPA as the only visible label; prefer Corrective Actions.
- internal work-package or implementation acronyms without context.
- vendor and infrastructure acronyms when domain wording is sufficient.

## Runtime rules

- primary tile/header/breadcrumb labels must favor plain operational wording.
- advanced diagnostics may retain technical acronyms when clearly scoped as diagnostics.
- Spanish surfaces must preserve legitimate acronyms (for example QA/QC, OSHA, DOT) and translate surrounding text naturally.

## Open checks

- finish operator-visible CAPA to Corrective Actions sweep where appropriate.
- verify all materially changed EN/ES surfaces preserve allowed acronyms and remove unjustified software acronyms.