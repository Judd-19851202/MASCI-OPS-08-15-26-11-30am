# WP18C7 EN/ES Responsive Accessibility

## Localization
- New routes reuse existing translation wrapper patterns and existing portal shells.
- Labels are written in English-first strings compatible with the current `t(...)` fallback path.

## Responsive implementation evidence
- Shared workspace uses mobile-first grids, tab wrapping, and `overflow-x-auto` table containment.
- Direct browser runtime certification completed across all three C7 routes at `390 / 430 / 768 / 1024 / 1440` with alternating EN/ES language storage.
- **Result: 15 / 15 route-width combinations PASS**.

## Route-width matrix
- PM Forecasting & Commitments: `5 / 5` PASS
- Executive Forecasting Governance: `5 / 5` PASS
- Field Leadership Forecasting: `5 / 5` PASS

## Runtime note
- `auto_frontend_testing_agent` remained timing-sensitive in the preview environment, so direct Playwright browser automation via the screenshot runtime was used instead.
- One real defect was found during certification: scenario comparison existed in the backend payload but was not surfaced in the shared UI. Smallest Safe Repair was applied by adding the `forecast-scenario-comparison-table`, then the affected routes/widths were rerun to PASS.

## Accessibility
- Critical interactive elements and key user-facing surfaces include `data-testid` coverage for QA.
- Buttons, tabs, selector controls, commitment actions, and governance drill-downs remained usable across the certified widths.
