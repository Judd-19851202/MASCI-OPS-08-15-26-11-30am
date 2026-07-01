# TRACK 19.11 MAIN · Equipment Pre-Op · HelpDrawer Consolidation

**Status:** ✅ GREEN · CLOSED

## Before

Equipment Pre-Op previously stacked 3 separate visible coaching components on top of the form by default:

1. `<HelpTipBlock formKey="preop" showCounter />` — before Section 01 (5 collapsible tips)
2. `<HelpTipBlock formKey="preop.defects" />` — between Section 02 and the dynamic checklist iteration
3. `<HelpTipBlock formKey="preop.signoff" />` — inside Section 99 (Operator Sign-Off)

Combined with the `HelpDrawer` trigger below the subtitle (Track 19.10 POC), that was **4 competing coaching surfaces** on a single form page. Operators reported visual noise at 5:30 AM: "Which one do I read?"

## After

**One coaching surface. One drawer. One "? Open help" button.**

Every coaching band that used to stack on top of the form is now a section inside the `HelpDrawer` panel. Main screen = action. Drawer = explanation.

The `HelpDrawer.sections` array now carries **5 bands**:

1. **Why this Pre-Op matters** — original band 1.
2. **Who sees this** — Track 19.11 MAIN NEW.
3. **What happens after you submit** — expanded to include the OOS + shop-notification + historical-record context that used to live in stacked strips.
4. **When to stop and call** — includes camera obstruction + critical fluid + major safety guidance.
5. **Common pre-op mistakes** — Track 19.11 MAIN NEW.

## What was preserved

- The `HelpDrawer` trigger, its `testIdPrefix="equipment-help-drawer"`, its `role="dialog"` + `aria-modal="true"` accessibility hooks, and its bilingual `useT()` string routing.
- Every operator-facing message about stopping work / getting a supervisor / camera visibility — moved into the drawer verbatim.

## What was removed

- Three `<HelpTipBlock>` visible defaults on Equipment Pre-Op.
- The `import { HelpTipBlock } from "@/components/HelpTip"` import on Equipment Pre-Op.
- No dead code left behind.

## What was NOT touched

- The `HelpTipBlock` component itself remains untouched — other forms (Daily Report, DVIR, Safety Meeting) may still consume it. Only Equipment Pre-Op's default-visible defaults were retired for Track 19.11 MAIN.
- The `WhyItMattersPanel` component (previously imported but unused on Equipment Pre-Op) was also removed from imports. Zero visual regression because it wasn't rendered.

## Bilingual parity

Every new drawer section title + body has an ES translation in `frontend/src/lib/i18n.js`. Zero EN-only additions. Locked in the Track 19.11 MAIN pytest suite.

## Regression

- 67/67 Track 19.11 MAIN pytest lock assertions GREEN.
- Track 19.10 lock test updated to reflect the new doctrine (HelpTipBlock retired on Equipment Pre-Op; 5 bands migrated into the drawer).
- Live smoke: `equipment-help-drawer-trigger` visible; opens the drawer; drawer contains exactly 5 sections; close button dismisses cleanly.
- ES live smoke: Spanish drawer titles render correctly.

## Doctrine for future forms

DVIR (19.12) and Safety Meeting (19.13) should follow the same doctrine on their own modernization tracks:

1. Every coaching band that was previously a visible stacked strip becomes a `HelpDrawer` section.
2. The form retains **one** "? Open help" trigger on the header.
3. The `HelpTipBlock` component may remain in the codebase but must not render as a visible default on modernized forms.
