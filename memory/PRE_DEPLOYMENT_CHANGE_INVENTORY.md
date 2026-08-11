# PRE-DEPLOYMENT CHANGE INVENTORY

Date: 2026-08-11
Classification: governed release surfaces only

## Release delta doctrine

- Current tracked workspace diff at audit time: clean.
- Ignored release garbage removed: caches, pyc folders, transient stderr/stdout logs, throwaway local run logs.
- No unexplained tracked or untracked artifacts remain.

## Canonical transportation release surfaces

These are the governed Track 18 release surfaces and remain the reference inventory for release-safety review:

- frontend/src/pages/transportation/_shared.jsx
- frontend/src/pages/transportation/_lists.jsx
- frontend/src/pages/transportation/_orientation.jsx
- frontend/src/pages/transportation/_intelligence.jsx
- frontend/src/pages/transportation/_command_queue.jsx
- frontend/src/pages/transportation/_views.jsx
- backend/routes/transportation.py
- backend/routes/transportation_experience.py
- backend/routes/transportation_orientation.py
- backend/routes/transportation_automation.py
- backend/routes/transportation_intelligence.py
- backend/server.py

## Current pre-save release repairs

- Frontend suite drift corrected to current scoped-auth, hub, trust, KPI, and bilingual contracts.
- Daily-report legacy draft migration restored and device-scoped draft continuity re-verified.
- Runtime diagnostics payload bounded for reliable admin forensics consumption.
- Portfolio intelligence cache reuse corrected so C8 earned-value parity refreshes into C9 when prior cached rows are incomplete.
- Project daily work plan writes made duplicate-safe under concurrent integrity scanning.

## Disposition of removed artifacts

- Temporary caches: removed.
- Transient rerun logs: removed.
- Debug stderr/out tails: removed.
- Testing-agent release garbage at repo root: removed (`backend_test.py`, `test_result.md`).
- Governed evidence artifacts in /app/test_reports and /app/memory: retained.