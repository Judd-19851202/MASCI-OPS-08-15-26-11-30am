# Trench Safety — Surface Correction Plan
**Date:** 2026-02-07
**Status:** PROPOSED — no code changes made during this audit per directive.

This is the corrective sprint that closes the four drift items and stands up the missing Safety Portal Command Center surfaces. Designed as a single OMEGA-style phase ("Phase 7.5 · Safety Portal Command Center Hardening") to run **before** Phase 7 frontend resumes.

---

## 1. Sprint scope (proposed Phase 7.5)

### Block A — Surface Re-ownership (drift correction)
A1. **Tabulated Data CRUD → Safety Portal.**
- Re-gate `POST/PUT/DELETE /api/trench-boxes` from `require_admin` → `require_safety_or_admin`.
- Add Upload / Replace / Delete UI inside `/safety/trench-safety/tabulated-data`.
- Convert `/admin/trench-boxes` into a redirect to `/safety/trench-safety/tabulated-data` for Safety roles; keep Admin Console entry only for bulk import / advanced ops if needed (deprecated by default).

A2. **Photo Upload backend gate → Safety.**
- Change `POST /trench-safety/assets/{id}/photos` from `require_shop_or_admin` → `require_safety_or_admin`.
- Keep Shop able to attach photos to a *repair* record via a different endpoint or shared helper — the canonical asset-level photo library is Safety-owned.
- Update existing Phase 7 test suite to match new auth.

A3. **Repair Review + Field Report Review → Safety Portal.**
- New route `/safety/trench-safety/repairs` rendering the unified Repair Queue (all states, severity badge, hold badge, reinspection badge).
- Filter "Awaiting Safety Verification" → repairs in status `Completed` with `requires_reinspection=true`.
- Verify dialog → `POST /…/repairs/{id}/verify` with `reinspection_passed` + notes.
- New route `/safety/trench-safety/field-reports` rendering all `trench_safety_repairs` rows with `source="Public QR Damage Report"`, sorted by `received_at`. Resolve / assign actions piped through the existing PATCH endpoint.

A4. **Legacy `/trench-boxes` → redirect.**
- Replace with `<Navigate to="/trench-safety/tabulated-data" replace />` in `App.js`. Preserves printed QR posters.

### Block B — Missing Safety Portal UI (no drift, but P0 to stand up the Command Center)
B1. **Asset CRUD UI on `/safety/trench-safety/assets`**
- `+ New Asset` dialog (Asset Type · Asset ID · Serial · Manufacturer · Model · Size · Color · Condition · Requires Cert).
- Edit pencil on Asset Detail.
- Change Status menu (validated against `validate_status_transition`).
- Audit Timeline panel on Asset Detail (renders `GET /trench-safety/assets/{id}/audit`).

B2. **Inspections** — Create-inspection dialog (pass/fail + severity) on Asset Detail, plus an Inspection History list.

B3. **Holds** — Open Hold dialog + Clear Hold dialog on Asset Detail, respecting Hold Hierarchy priority.

B4. **Certifications** — Upload Certification form, status row, Revoke action on Asset Detail.

B5. **QR Management UI (Phase 7 deliverable)** — Generate QR PNG + Download button + Reprint audit trigger on Asset Detail.

B6. **Photo Management UI (Phase 7 deliverable)** — Drop-zone upload, Internal vs Field-Safe toggle, library grid on Asset Detail.

### Block C — Acceptance Tests
- Backend: pytest extensions for the re-gated endpoints (A1, A2). New endpoints under `/safety/trench-safety/repairs` + `/field-reports` (same backend, new frontend).
- Frontend: testing_agent_v3_fork run against the Safety Portal Command Center asserting each section exists and writes succeed for Safety role.
- Regression: full pytest suite still green (Phase 2 → Phase 7).

### Block D — Markdown Certifications
- `TRENCH_SAFETY_PHASE_7_5_SURFACE_RE_OWNERSHIP_REPORT.md`
- `TRENCH_SAFETY_PHASE_7_5_COMMAND_CENTER_IMPLEMENTATION_REPORT.md`
- `TRENCH_SAFETY_PHASE_7_5_GO_NO_GO.md`

---

## 2. Sequencing

Each block is a sub-phase and is independently testable:

1. **A1 + A4** — Tabulated Data move + legacy redirect (one PR, isolated).
2. **A2** — Photo Upload re-gating (one PR, retest Phase 7 backend).
3. **A3** — Safety-side Repair Review + Field Reports inbox (new pages; reuses Phase 6 backend).
4. **B1** — Asset CRUD UI (one PR; depends on no other block).
5. **B2 / B3 / B4** — Inspections / Holds / Certifications UI (can ship in parallel after B1).
6. **B5 / B6** — Phase 7 frontend deliverables, now landing on a complete Safety Portal Asset Detail.

After (6) we resume the Phase 7 certification path that this sprint paused.

---

## 3. Out-of-scope (deferred)

- Verify Matching Assets workflow (proposed in Phase 9 / Reports).
- OCR Configuration (Phase 10).
- QR Configuration (Phase 10 Admin).
- Asset Type Definitions admin UI (Phase 11).

---

## 4. Risks + Mitigations

| Risk | Mitigation |
|---|---|
| Re-gating `POST /api/trench-boxes` from admin → safety may break existing admin-only tests | Run full backend pytest immediately after the auth change; update any test that asserts `require_admin`. |
| Two routes (`/admin/trench-boxes` redirect, `/safety/trench-safety/tabulated-data` new owner) might confuse cached operators | Add a one-time toast on the redirected path: *"Tabulated Data management has moved to Safety Portal."* |
| Photo Upload gate change may affect Shop's ability to attach repair photos | Either: (a) keep a Shop-allowed path for attaching to a repair record specifically, or (b) Shop uploads through Safety with audit. Decide in Block A2 design. |
| The "Field Reports inbox" overlaps with the Shop Repair queue conceptually | Field Reports = upstream of a repair; once Safety triages / accepts, it becomes a Repair. Make the data model surface that lifecycle (`pending_shop_review` already exists on the repair doc). |

---

## 5. Estimated effort
~ 5–7 working sessions if executed in the order above. Each block is independently certifiable.
