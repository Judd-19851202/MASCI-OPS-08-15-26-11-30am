# Mobile, Offline, and Synchronization Architecture Lock

Date: 2026-07-14
Track: DR-02

## Mobile / tablet / desktop principles verified from repo
- explicit progressive steps exist in V3 sections
- dense all-in-one workflow exists in V1
- accessibility and test-id discipline are materially stronger in V3 section components

## Canonical UX lock
- one responsive shell must serve phone, tablet, and desktop
- progressive disclosure is canonical
- no desktop-only hidden critical flow
- all critical interactions retain `data-testid`

## Offline lock
- foreground-only queue is canonical
- no service worker dependence
- queue must remain idempotent
- queue must not depend on shell-specific form keys

Evidence:
- `resiliencyQueue.js:14-20,117-180`

## Synchronization lock
- submit idempotency key belongs to one report instance
- queued retry uses same idempotency key
- draft commit happens only on confirmed delivery

## Cross-device honesty lock
- repo does not prove cross-device live draft sync
- canonical behavior must not promise it

## Accessibility / language
- English/Spanish support is present in field UI via `useT` / translation helpers
- Spanish submit translation exists in both shells

Evidence:
- `NewDailyReport.jsx:1145-1148`
- `NewDailyReportV3.jsx:540-560`
