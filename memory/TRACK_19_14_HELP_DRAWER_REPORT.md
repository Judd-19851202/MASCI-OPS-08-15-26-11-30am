# TRACK 19.14 · HelpDrawer Coverage Report (Cross-Form)

**Status:** ✅ CERTIFIED

## Summary

The `HelpDrawer` primitive is now the single coaching surface across all four modernized operational forms. Every form imports the same primitive file. Every form retired its previous stacked `<HelpTipBlock>` defaults. Every form configures a form-specific set of coaching bands.

| Form | Bands | testIdPrefix | Retired stacked defaults |
|---|---|---|---|
| Equipment Pre-Op | 5 | `equipment-help-drawer` | `preop`, `preop.defects`, `preop.signoff` |
| DVIR | 5 | `dvir-help-drawer` | `{formCopy.helpFormKey}` (variant-driven) |
| Safety Meeting / Toolbox Talk | 8 | `meeting-help-drawer` | `meeting`, `meeting.context`, `meeting.topic`, `meeting.attendees`, `meeting.photos`, `meeting.signoff` |

**Total stacked defaults retired: 10** across the three form-modernization tracks.

## Doctrine

1. Main screen = action.
2. Drawer = explanation.
3. `<HelpTip>` inline nudges next to specific fields may remain (contextual). Stacked `<HelpTipBlock>` visible defaults are RETIRED on all modernized forms.
4. Every band title + body has an ES translation locked in `frontend/src/lib/i18n.js`.

## Band content per form

### Equipment Pre-Op (5 bands · Track 19.11 MAIN)
1. Why this Pre-Op matters
2. Who sees this
3. What happens after you submit
4. When to stop and call
5. Common pre-op mistakes

### DVIR (5 bands · Track 19.12)
1. Why this DVIR matters
2. Who sees this
3. What happens after you submit
4. When to stop and call
5. Common DVIR mistakes

### Safety Meeting / Toolbox Talk (8 bands · Tracks 19.13 + 19.14)
1. Why this meeting matters
2. Who receives this
3. How attendance is documented
4. How knowledge is retained
5. Legal documentation
6. Common meeting mistakes
7. Supervisor best practices
8. Crew engagement tips

The Safety Meeting drawer carries three additional bands (Legal · Supervisor best practices · Crew engagement) reflecting the training-heavy nature of the form.

## Accessibility (locked per primitive · Track 19.10)

* `role="dialog"` on the drawer panel
* `aria-modal="true"` on the drawer panel
* Every drawer trigger has a stable `data-testid="{prefix}-trigger"`
* Every drawer close button has a stable `data-testid="{prefix}-close"`
* Every band section has a stable `data-testid="{prefix}-section-{i}"`

## Regression

Playwright live smoke opened and closed each of the three form drawers, counted the expected band count per form, and confirmed all sections render bilingual. 0 console errors across all runs.

**Certified GREEN.**
