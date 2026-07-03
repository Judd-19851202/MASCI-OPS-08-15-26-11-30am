# TRACK 19.33 · HR COMPLIANCE AT RISK WIDGET

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Six Pillars Aggregate: 58/60 · Production Strong**
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

## Charter
Turn HR from reactive to proactive by surfacing employees and documents that require review **before** compliance risk becomes an operational incident. Delivered as a top-of-fold widget on the HR portal home.

## Doctrine
- **Zero-drift.** Consumes an existing role-gated endpoint (`GET /api/operations/expirations/summary` in `backend/routes/sprint_a.py`) — no new backend routes, no schema changes, no permission changes.
- **Read-only.** No employee mutation. No incident mutation. No side effects.
- **Existing design language.** Uses `Card` + `StatusChip` + `EmptyState` design-system primitives — no new visual vocabulary.
- **Existing lane rules.** Endpoint auth is `require_actor` (HR + Admin per existing HR lane rules). PM / Shop / Dispatch / Field / Safety (unless HR-authorized) do not reach this UI because they don't reach the HR portal home.

## Risk categories surfaced (from live existing data)

| Category | Data source | Available today | Renders in widget |
|---|---|---|---|
| Expired documents (any category) | `db.document_expirations` | ✅ | ✅ Critical severity |
| Documents expiring ≤ 30 days | Same | ✅ | ✅ Warning severity |
| Documents expiring 31 – 60 days | Same | ✅ | ✅ Info severity |
| CDL license expired/expiring | `document_expirations.category='CDL license'` | ✅ | ✅ (surfaces via title/kind) |
| Medical card expired/expiring | `document_expirations.category='Medical card'` | ✅ | ✅ (surfaces via title/kind) |
| OSHA card expired/expiring | `document_expirations` where category matches | ✅ | ✅ (surfaces via title/kind) |
| TWIC card expired/expiring | `document_expirations` where category matches | ✅ | ✅ (surfaces via title/kind) |
| Safety training expired/expiring | `db.safety_training_records` | ✅ | ✅ |

### Future (documented but NOT in this track — no schema available today)
| Category | Status | Documented for future track |
|---|---|---|
| Driver qualification incomplete (multi-field composite) | Requires composite check across `drivers` collection · not exposed by summary endpoint. | ✅ Roadmapped |
| Required training incomplete | Requires per-employee expected-training matrix lookup (not yet a schema). | ✅ Roadmapped |
| Missing onboarding documents | Requires expected-onboarding-checklist schema. | ✅ Roadmapped |
| Missing emergency contact | Requires nullable-field probe on `employees`. | ✅ Roadmapped |
| Missing required employment docs | Same as above. | ✅ Roadmapped |
| Open CAPA linked to employee | Requires CAPA-to-employee join across `incident_cases`. | ✅ Roadmapped |
| Safety-case involvement requiring HR review | Same as above. | ✅ Roadmapped |
| Employee inactive but still assigned | Requires cross-collection assignment probe. | ✅ Roadmapped |
| Employee active but missing readiness fields | Requires readiness-field schema on `employees`. | ✅ Roadmapped |

## Component

`frontend/src/components/hr/HrComplianceAtRiskWidget.jsx`
- Fetches `GET /api/operations/expirations/summary` on mount with `authHeaders` prop (HR token + Admin token fallback).
- Renders empty state ("No compliance risk right now.") when zero at-risk items.
- Renders three category chips (Expired · Expiring ≤ 30 days · 31–60 days) with counts.
- Renders top 8 highest-risk rows (expired first, then expiring in 30) with:
  - Owner name + title/kind
  - Due date
  - Severity chip (`Critical / Warning / Info`) + days remaining/overdue
  - Per-row "Open" deep-link to Employee 360 (when owner is an employee) or Document Expirations queue
- Footer bulk link "Open Document Expirations →" to the full queue.

## Wiring

`frontend/src/pages/HrHubV2.jsx` — widget mounted at the very top of the HR portal home page body (above Employee Directory Search).

## Permissions

- Widget renders only inside `HrHubV2`, which is behind `RequireHr` (route guard on `/hr`).
- Endpoint auth is `require_actor` (existing HR-lane gate). Wrong roles cannot reach `/hr`, and if they somehow bypassed it, the endpoint would return 401/403 which the widget renders as a clean `StatusChip` "offline_feed" — never as raw JSON.
- **No PM / Shop / Dispatch / Field / public visibility.**

## Bilingual

- Every string wrapped in `useT()`:
  - "Compliance At Risk", "Loading live compliance signals…", "Unable to load live compliance signals.",
  - "Employees or documents that likely need HR review before risk becomes an incident.",
  - "Attention", "All clear", "No compliance risk right now.",
  - "No expired documents and none expiring in the next 30 days.",
  - "Expired", "Expiring ≤ 30 days", "31–60 days",
  - "overdue", "Due", "Document",
  - "Open", "Open Document Expirations →",
  - "Loading".
- Owner name and document title come from the backend (already stored in canonical form).

## Zero-drift proof

- **0 new backend routes.**
- **0 new backend files.**
- **0 schema mutations.**
- **0 collections touched.**
- **0 permission changes.**
- **0 payload changes.**
- **0 PDF/email/notification changes.**
- **Only new frontend files:** 1 (`HrComplianceAtRiskWidget.jsx`).
- **Only edited frontend files:** 1 (`HrHubV2.jsx` — 2 lines added).

## Rollback path

- **Full source rollback:** delete `HrComplianceAtRiskWidget.jsx` and remove 2 lines from `HrHubV2.jsx`.
- **Runtime toggle:** simply don't mount the widget component. No feature flag needed because the widget is additive and never mutates state — the "off" state is functionally equivalent to a pre-19.33 HR portal home.
- **Rollback confidence:** HIGH.

## Live smoke verification

- ✅ `[data-testid="hr-compliance-at-risk-widget"]` present on `/hr` after HR + admin token injection.
- ✅ `hr-compliance-at-risk-summary` chip row rendered.
- ✅ `hr-compliance-at-risk-rows` list rendered with 8 rows.
- ✅ Screenshot: `/tmp/hr_compliance_widget.png` — displays live count 79 (60 expired · 19 expiring 30d · 9 expiring 60d). Each row shows owner, title, days overdue (`Critical · 41d overdue`), and Open link.
