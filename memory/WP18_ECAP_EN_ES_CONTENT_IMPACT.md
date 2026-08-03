# WP18 ECAP EN / ES Content Impact

Date: 2026-08-03

## Final language rule

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

- English remains the canonical backend and architecture language.
- Operator-facing experiences must remain complete in English and Spanish where they are operator-visible.

## WP-18C content impact

All new operator-facing surfaces introduced by Budget Hierarchy, Project Controls, reporting, and EV must ship with:

1. English canonical labels
2. Spanish operator-facing translations
3. equivalent validation / alert meaning in both languages
4. PDF/email/report output parity where those surfaces are user-visible

## No language regression rule

Existing EN/ES operator experience may not regress because of controls implementation.

## Required coverage areas

- PM / controls views visible to operators
- field / Daily Report / production interactions
- safety, HR, training, dispatch, and shop alerts if impacted
- finance/admin operator surfaces that are user-facing
- reports, PDFs, and outbound email templates impacted by WP-18C