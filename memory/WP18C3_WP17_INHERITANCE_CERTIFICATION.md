# WP18C3 WP-17 Inheritance Certification

Date: 2026-08-03

## Shared-shell inheritance

WP-18C3 uses existing governed shells and primitives rather than introducing a drifted UI family:
- PM page uses `PmShell`
- admin page uses `LegacyAdminModernShell`
- shared primitives use existing `Button`, `Input`, `Textarea`, `Alert`, `Badge`, and `Tabs`

## Operator-language and accessibility posture

- pages are written in operator-facing business language
- strings are wired through `useT()` for EN/ES compatibility with the established localization layer
- forms use labeled controls and explicit status badges
- guarded alerts explain trust-line rules instead of hiding them

## Test-id coverage

All interactive and critical user-facing elements on the new PM/admin budget surfaces were given unique `data-testid` values.

Verified examples from `/app/test_reports/iteration_112.json`:
- `pm-project-budget-authority-page`
- `pm-project-budget-upload-button`
- `pm-project-budget-file-input`
- `admin-project-budget-authority-page`
- `admin-project-budget-backfill-button`
- `admin-project-budget-tabs`

## Responsive / state posture

The new surfaces include explicit states for:
- loading
- empty imports / versions / review queues
- approved / rejected / review-required rows
- queued backfill response
- export availability

Testing agent verification passed on the rendered PM and admin pages. No blank-page or broken-layout issue was reported.

## Zero-drift result

WP-18C3 extended the accepted WP-17/C1/C2 language and shell system instead of creating a replacement visual system.
