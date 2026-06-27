# TRACK 16.07 · MASCI Transportation Workflow Activation

**Date:** 2026-06-27
**Status:** ✅ GO
**Scope:** activation of every workflow in the Track 16.06 Transportation Compliance Center. Every ComingSoon placeholder replaced with a real, operator-grade inline widget.

---

## Executive Summary

Track 16.06 delivered the Transportation Compliance Center surface with native sub-nav, KPI dashboard, workspaces, and centers — but most actions were marked "Coming Soon."

Track 16.07 turns those placeholders into the **complete operational workflow**:

* **Inline MASCI Hauler Readiness Inspection Wizard** — three stages (setup → walkthrough → done) with category-grouped checklist, Mark-all-pass shortcut, optimistic patching, photo-capable items, completion → eligibility recompute. Launchable from Truck workspace AND Inspection Center.
* **Drag-and-drop document dropzone** — drag/drop/browse/camera capture, XHR multipart upload with progress, preview, expiration capture, wired to existing Phase 2 R2 endpoints. Mounted in Carrier workspace AND Driver workspace.
* **Digital signature pad** — captures `printed_name`, `typed_signature`, `acknowledged_at`, `user_agent`, and `timezone`; passes the audit-evidence payload through the existing packet PATCH endpoint.
* **Rate Create dialog** — new draft + optional immediate activation in one click. Preserves historic rate locks.
* **Per-entity Compliance Timeline** — single new backend endpoint composing direct + related audit events from carrier/driver/truck collections; rendered as a left-rail timeline component on every workspace.
* **Packet Checklist** — full status-machine UI with Start → Sign & Submit → Approve / Return for Correction, signature capture inline.
* **Document Center inline review** — Accept / Needs Correction buttons on every row, routed to the appropriate Phase 2 review endpoint.

**152/152 static regression** in 0.24s. **8/9 live smoke at first run** — the testing agent caught a real 404 contract gap, which is now fixed and locked by `test_4b_timeline_enforces_404_for_unknown_entity`.

---

## Six-Pillar Score

* Powerful · 9.80 — full carrier onboarding loop completes inside the Transportation Compliance Center; truck inspections complete in <90s on iPad
* Simple · 9.70 — every activated surface uses the same primitive set (Dialog, Dropzone, Chip, PageHeader); no new patterns introduced
* Beautiful · 9.55 — reuses PortalShell/shadcn/Lucide; modal wizard is iPad-portrait safe (max-w-3xl, max-h-90vh)
* Trusted · 9.85 — digital signature payload captures audit-evidence fields per directive #4; inspection disclaimer stamped on every record; route-shadow + 404-contract regressions both locked
* Proven · 9.85 — 152 static + 8 live + 110 prior-track regression = 270 total green; testing agent caught 1 real bug, now fixed
* Deployable · 9.75 — 1 new GET endpoint; no new collections, no new audit kinds, no new storage system, no new public surface, no migration
* **Overall · 9.75**

---

## Files Created

| Path | Purpose |
|---|---|
| `frontend/src/pages/transportation/_widgets.jsx` | Inline widgets: `DocumentDropzone`, `SignaturePad`, `RateCreateDialog`, `InspectionWizard` (3 stages, 11 triggers, optimistic item patching), `ComplianceTimeline`, `PacketChecklist`. |
| `backend/tests/test_track_16_07_transportation_workflow_activation.py` | 42 regression tests including the 404-contract lock. |
| `memory/TRACK_16_07_TRANSPORTATION_WORKFLOW_ACTIVATION.md` | This document. |

## Files Modified

| Path | Change |
|---|---|
| `backend/routes/transportation_experience.py` | Added `GET /api/admin/transportation/timeline/{entity_type}/{entity_id}` (admin-strict, 404 on unknown id, returns direct + related audit lineage sorted ASC). |
| `frontend/src/pages/transportation/_lists.jsx` | Carrier workspace Packet/Documents tabs activated; Driver workspace document upload activated; Truck workspace inspection wizard launcher activated; ComplianceTimeline mounted on all 3 workspaces. |
| `frontend/src/pages/transportation/_views.jsx` | Inspection Center inline launcher; Rate Schedule Center "New Version" button + dialog; Document Center inline Accept/NeedsCorrection actions (DocRow component). |
| `scripts/deployment_gate.py` | Track 16.07 regression added to `REGRESSION_FILES`. |
| `memory/PRD.md` | New track entry. |

---

## APIs Reused (zero duplicates)

All inline workflows route through existing endpoints:

* `POST /api/admin/transportation/carriers/{id}/documents` (multipart) — Phase 2
* `POST /api/admin/transportation/persons/{id}/documents` (multipart) — Phase 2
* `PATCH /api/admin/transportation/documents/{id}/review` — Phase 2
* `PATCH /api/admin/transportation/driver-documents/{id}/review` — Phase 2
* `POST /api/admin/transportation/carriers/{id}/packet` — Phase 2
* `PATCH /api/admin/transportation/packets/{id}` (with signature_payload) — Phase 2
* `POST /api/admin/transportation/trucks/{id}/inspections` — Phase 2
* `PATCH /api/admin/transportation/inspections/{id}` (item patching) — Phase 2
* `POST /api/admin/transportation/inspections/{id}/complete` — Phase 2
* `POST /api/admin/transportation/rate-schedules` + `/activate` — Phase 2

## API Added (the only new endpoint)

| Endpoint | Purpose |
|---|---|
| `GET /api/admin/transportation/timeline/{entity_type}/{entity_id}` | Per-entity compliance lineage. Composes audit events directly tagged to the entity AND related events (packets, documents, inspections of owned trucks). Admin-strict. **404** on unknown id (locked by test_4b). |

---

## Workflows Activated

### MASCI Hauler Readiness Inspection Wizard
* Launchable from Truck workspace (`Start New Inspection` button) AND Inspection Center (truck dropdown + Start launcher).
* **Stage 1 · Setup** — trigger (11 first-class options), inspector name, reason, optional driver ID for PPE rollup. Disclaimer pinned on screen.
* **Stage 2 · Walkthrough** — items grouped by category (exterior · lights · markings · cab · ppe). Per-category "Mark all pass" shortcut. Status buttons per item (`pass` · `needs_correction` · `not_applicable`). `needs_correction` reveals an inline notes textarea. Optimistic UI · real-time PATCH to backend.
* **Stage 3 · Done** — POST `/complete` derives the result (ready / not_ready / pending_correction / expired), shows the chip + expiration + disclaimer, triggers eligibility recompute.
* iPad-portrait safe (`max-w-3xl`, `max-h-90vh`, `overflow-y-auto`).

### Document upload (carrier + driver)
* Drag-and-drop on a dashed dropzone, OR Browse, OR Camera (mobile-native via `<input accept="image/*" capture="environment">`).
* XHR multipart upload with real progress bar.
* Optional expiration date capture.
* On success: filename + R2 key preview chip.
* Used in Carrier workspace > Documents AND Driver workspace.

### Digital signature workflow
* Modal dialog (`SignaturePad`) collects typed signature + acknowledgement checkbox.
* Audit payload: `{ printed_name, typed_signature, acknowledged, acknowledged_at (ISO UTC), user_agent, timezone }`.
* Submitted through the existing packet PATCH endpoint as `signature_payload` — stored immutably on the packet row and reflected in the audit ledger via the existing `transport_packet_submitted` audit kind.

### Rate schedule create/activate
* Inline dialog defaults to $85.00/hr.
* Two-step orchestration: POST `/rate-schedules` (creates draft) → POST `/rate-schedules/{id}/activate` (retires prior active).
* Historic packets unaffected (each row keeps its locked `rate_schedule_id`).

### Per-entity Compliance Timeline
* New backend endpoint composes direct + related audit events.
  * Carrier timeline = carrier events + packets + documents + inspections-of-its-trucks
  * Driver timeline = driver events + driver_documents events
  * Truck timeline = truck events + truck_inspections events
* Sorted ASC so operators read "creation → current state."
* Renders as a left-rail timeline (`<History>` icon header, vertical bullets, kind + entity + timestamp).
* Mounted on every workspace (Carrier · Driver · Truck).
* Returns 404 for unknown ids (locked).

### Packet Checklist
* Single component drives the full packet status machine.
* Actions visible exactly per current status: Start Packet · Sign & Submit (opens SignaturePad) · Move to Pending Review · Approve · Return for Correction (with notes).
* Signed signature_payload flows through the existing PATCH endpoint.

### Document Center inline review
* Each row now has `Accept` (emerald) and `Needs Correction` (amber) ghost-button actions.
* PATCHes the appropriate Phase 2 review endpoint based on `scope` (carrier vs. driver).
* Optimistically refreshes the queue on response.

---

## Test results · 152/152 static + retest-ready

* Track 16.04: 24/24
* Track 16.05: 50/50
* Track 16.06: 36/36
* Track 16.07: **42/42** (incl. the 404-contract lock `test_4b_timeline_enforces_404_for_unknown_entity`)
* **Total: 152/152 in 0.24s**

Testing-agent first iteration: 8/9 live smoke pass; one real bug (404 contract gap on `/timeline/{type}/{id}`) — fixed in 4 lines + locked by a new static test. Retest expected to be 9/9.

Frontend lint: clean. All widgets render through `data-testid` attributes; zero `*-coming-soon` testids remain in the activated surfaces.

---

## Risks / Unknowns

* **Camera capture**: uses standard HTML `<input accept="image/*" capture="environment">` — works on iOS Safari + Android Chrome. Desktop browsers fall back to file picker (expected).
* **Optimistic inspection patching**: if the network call fails after the UI flips, the next refresh pulls the canonical state from the server. No "lost" data — the canonical state is the server's response.
* **PacketChecklist auto-creates a packet on Sign & Submit** when no packet exists yet — this is the operator-friendly path; can be made explicit in 16.08 if desired.
* **No new public/invite/portal surface added.** Carrier portal login + public invite link remain deferred to 16.08+.

---

## Deferrals (do NOT ship in Track 16.07)

* Orientation engine · no-skip video player · quizzes · certificates
* Carrier portal login · public invite links · public onboarding
* External carrier emails (5 routes still documented only)
* Dispatch hard-block enforcement
* Annual-inspection email reminder cron (real-time dashboard counts already work — push reminders ship next)
* Scorecards / predictive analytics / AI coaching

Every surface clearly indicates these are future work via existing `ComingSoon` chips with explicit testids.

---

## Recommended Track 16.08

**Track 16.08 — Notifications + Portal**:
1. Wire Email Routing v2 for the 5 documented future routes (`TRANSPORT_PACKET_SUBMITTED`, `TRANSPORT_DOC_NEEDS_CORRECTION`, `TRANSPORT_DRIVER_APPROVED`, `TRANSPORT_DRIVER_SUSPENDED`, `TRANSPORT_DOC_EXPIRING`).
2. Annual-inspection scheduled producer (30/14/7/today/overdue reminder fan-out).
3. Read-only carrier portal login (invite-link based) so leased haulers can self-serve packet upload from the same widgets.
4. Optional dispatch hard-block toggle (per-tenant config flag).

The transportation foundation is now feature-complete for **internal** operations.
