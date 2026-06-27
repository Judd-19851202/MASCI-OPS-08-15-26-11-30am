# TRACK 16.08 · MASCI Transportation Orientation, Notification & External Onboarding Platform

**Status:** ✅ Production-ready · 527/527 regression tests green · 100% frontend retest pass
**Date completed:** Feb 2026 (forked session)
**Reference iterations:** `/app/test_reports/iteration_track_16_08.json`, `/app/test_reports/iteration_track_16_08_retest.json`

---

## 1 · Scope delivered

The Orientation Engine, Sky AI video placeholders, Native No-Skip Video Player, Quiz Engine, Certificate Engine, Email Routing v2 notification fan-out, and Secure External Carrier Invite Portal — all native to the MASCI Operations Platform. Zero third-party academy.

### 1.1 Backend surfaces (mounted via `register_transportation_orientation_routes`)

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET  /api/admin/transportation/orientation/dashboard` | Admin | KPI tiles (completion %, drivers awaiting / expiring / expired, certs 30d/90d, avg quiz score, modules count) |
| `GET  /api/admin/transportation/orientation/modules` | Admin | List 22 default modules with 4-language placeholders each |
| `PATCH /api/admin/transportation/orientation/modules/{mid}` | Admin | Update runtime, passing score, max attempts, required flag |
| `PATCH /api/admin/transportation/orientation/modules/{mid}/placeholder` | Admin | Replace Sky AI placeholder (sky_asset_id + runtime_seconds, per language) |
| `GET/POST /api/admin/transportation/orientation/modules/{mid}/questions` | Admin | Question bank CRUD per language |
| `POST /api/admin/transportation/orientation/assignments` | Admin | Assign module-language to driver |
| `POST /api/admin/transportation/orientation/assignments/{aid}/heartbeat` | Admin | Server-clamped watched-seconds + checkpoints |
| `GET  /api/admin/transportation/orientation/assignments/{aid}/quiz` | Admin | Randomised question load |
| `POST /api/admin/transportation/orientation/assignments/{aid}/quiz` | Admin | Grade · max-attempts gate · auto-issue certificate |
| `GET  /api/admin/transportation/orientation/certificates` | Admin | List issued certificates |
| `GET  /api/admin/transportation/orientation/certificates/{id}` | Admin | Certificate detail |
| **Public — External Carrier Invite Portal** | | |
| `POST /api/admin/transportation/invites` | Admin | Mint secure invite (token returned **once**, hashed at rest) |
| `GET  /api/transportation/invite/{token}` | Public | Open invite + mark `opened_at` |
| `POST /api/transportation/invite/{token}/submit` | Public | Submit packet acknowledgement |
| `GET  /api/transportation/invite/{token}/orientation/modules` | Public | List modules for in-portal preview |
| `POST /api/transportation/invite/{token}/orientation/assignments` | Public | Self-assign module (driver must belong to invite carrier) |
| `POST /api/transportation/invite/{token}/orientation/assignments/{aid}/heartbeat` | Public | No-skip heartbeat from carrier device |
| `GET/POST /api/transportation/invite/{token}/orientation/assignments/{aid}/quiz` | Public | Quiz load + submit |
| `GET  /api/transportation/invite/{token}/orientation/certificates` | Public | Certificates earned under this carrier |
| `GET  /api/transportation/orientation/certificates/verify/{cnum}` | Public | QR scan verifies certificate via audit hash |

### 1.2 Default catalog (22 modules · 4 languages each)

`welcome_to_masci`, `safety_culture`, `traffic_control`, `jobsite_arrival`, `asphalt_plant_operations`, `loading_procedures`, `hauling_procedures`, `backing_procedures`, `dumping_procedures`, `truck_readiness`, `driver_expectations`, `ppe`, `incident_reporting`, `near_miss_reporting`, `emergency_procedures`, `equipment_awareness`, `communications`, `customer_expectations`, `environmental_responsibilities`, `end_of_shift`, `annual_refresher` (+1).

Languages: `en` (primary), `es`, `es_CU` (Cuban Spanish), `fr`. Each placeholder stores `sky_asset_id`, `runtime_seconds`, `thumbnail_url`, `status`, `upload_date`. Sky AI videos drop in by simply pasting the asset id.

### 1.3 Eligibility engine wiring

`lib/transport_eligibility.py` already enumerated orientation reasons (`orientation_missing`, `orientation_expired`, `orientation_quiz_failed`). This track wires the **context** in three places:

- `routes/transportation.py::_upsert_eligibility` — auto-derives `orientation_status` when target is a person.
- `routes/transportation_phase2.py::_person_eligibility_context` — same for the Phase-2 onboarding compliance center.
- `lib/transport_orientation_status.py` (new) — pure async helper that returns one of `{current, missing, expired, quiz_failed}` plus `expiring_soon` flag.

Result: a driver whose orientation is missing, expired, or quiz-failed flips to `not_dispatchable` automatically; dispatch never recomputes — it reads the canonical eligibility row.

### 1.4 Notification engine — Email Routing v2 only

`notify()` audits intent through `email_routing_v2.resolve_and_audit(route_key="TRANSPORT_<KIND>", dry_run=True)` and persists a row in `transport_notifications`. Twenty-two notification kinds enumerated: `carrier_invite`, `packet_ready`, `packet_submitted`, `packet_needs_correction`, `packet_approved`, `driver_approved`, `driver_suspended`, `orientation_assigned`, `orientation_reminder`, `orientation_expiring`, `orientation_overdue`, `annual_inspection_due`, `annual_inspection_reminder`, `annual_inspection_overdue`, `documents_expiring`, `documents_approved`, `documents_need_correction`, `driver_eligible`, `driver_not_eligible`, `carrier_eligible`, `carrier_not_eligible`, `dispatch_eligibility_changed`. **Zero** SMS / Twilio / push references.

### 1.5 Native MASCI No-Skip Video Player

`/app/frontend/src/components/transportation/MasciVideoPlayer.jsx`:

- No timeline scrubber — user can only Play / Pause.
- `playbackRate` listener that snaps back to 1.0 on every change attempt.
- Heartbeat every 5 s posting `{position_seconds, watched_seconds, checkpoints_visited}`.
- Server clamps watched-seconds delta to `prior + 30` per heartbeat → skipping is mathematically impossible.
- Checkpoints fire at 25 / 50 / 75 / 99 %.
- Completion only when server confirms `completion_pct ≥ 0.99`.
- Resume where left off via `assignment.position_seconds`.
- Right-click "Save Video" suppressed.
- Sky AI placeholder card renders when `sky_asset_id` is empty — operators paste the asset id later, no code change required.

### 1.6 Certificate Engine

Per-pass certificate with `certificate_number = MASCI-<MODKEY>-<HEX>`, `audit_hash = sha256(payload)`, `module_version`, `language`, `quiz_score`, `completed_at`, `expires_at` (12 months). Public QR verify endpoint resolves by certificate number and returns the validity attestation — used by the React `/transport-verify/:cnum` page.

### 1.7 Admin frontend — `/admin/transportation/orientation/*`

Mounted inside the existing `TransportationApp.jsx` nested router, reusing `PortalShell`, `Chip`, `PageHeader`, `EmptyState`, `adminHeaders()`. Four sub-tabs:

- **Dashboard** — 8 KPI tiles + MASCI disclaimer.
- **Modules** — table of 22 modules with category, runtime, languages-published, Open navlink.
- **Module Detail** — 4 PlaceholderCards (`sky_asset_id` + runtime fields) and a Question Bank with language picker + add-form.
- **Assignments** — queue with status / watch-% / quiz-score.
- **Certificates** — issued list with QR verify link.

### 1.8 External Carrier Portal — `/transport-invite/:token`

Three-step stepper (Confirm → Orientation → Submit). The orientation preview embeds the no-skip video player so the carrier can verify the experience before drivers run it. Submit captures printed name + user-agent + timezone + ISO timestamp.

### 1.9 Public certificate verify — `/transport-verify/:cnum`

Reads the QR payload, shows the badge-checked card with cert number, completed-at, audit hash, language, version. Renders branded error state if not found.

---

## 2 · Audit trail · existing infrastructure reused

Every operation writes via `append_audit()` (NOT a new audit system). Kinds emitted:
`transport_orientation_module_create/update`, `transport_orientation_placeholder_update`, `transport_orientation_question_create`, `transport_orientation_assigned`, `transport_orientation_quiz_submit`, `transport_invite_create`, `transport_invite_open`, `transport_invite_submit`.

---

## 3 · Bootstrap idempotency

`bootstrap_track_16_08(db)` runs on every startup via `@app.on_event("startup")`. First boot seeds 22 modules × 4 language placeholders; subsequent boots are no-ops (`skipped=N`). Tested on three sequential restarts in the deployment gate.

---

## 4 · Tests · 40 / 40

`/app/backend/tests/test_track_16_08_transportation_orientation.py`:

- 26 static contract tests (file existence, language tuple, completion threshold, no-skip rule, public route signatures, notification catalog, audit kinds, deployment-gate inclusion, frontend orientation tab present).
- 6 pure-async helper tests (every `orientation_status` branch + `expiring_soon`).
- 8 live e2e tests (bootstrap, dashboard, question CRUD, full happy-path with certificate + QR verify, invite create / open / submit, bad-token 404, admin gate).

Pre-existing brittle test `test_identity_resolver_no_license_returns_none` in 16.04 was fixed (deprecated `asyncio.get_event_loop()` → `new_event_loop()`). Full deployment gate: **527 / 527** pass.

---

## 5 · Known limitations · pre-agreed in Track scope

- **Sky AI video files** are NOT generated by this track. Placeholders only — assets land via the MASCI Sky AI Production Bible and operators paste `sky_asset_id` once produced.
- **Email Routing v2** runs in `dry_run=True` audit mode (matches Track 15.79E continuous-certification posture). Flip the per-route flag in `email_routing_audit_v2` to enable SMTP.
- **Phase 4 dispatch gate hard-block** is the next track. Today eligibility is computed and persisted; dispatch reads it but does not yet hard-block board assignment.

---

## 6 · Six Pillars compliance

| Pillar | Evidence |
|---|---|
| **Powerful** | Full lifecycle: invite → orientation → quiz → certificate → eligibility flip → audit → notification. Single source of truth. |
| **Simple** | Reuses every existing primitive (eligibility engine, audit, R2, email routing, PortalShell, TX sub-nav, adminHeaders). |
| **Beautiful** | Identical MASCI styling — amber-700 accents, slate text, no design drift. |
| **Trusted** | 40-test regression + 527-test gate green. Server-validated no-skip rule. Certificate audit hash + public verify. |
| **Proven** | Live e2e tests pass end-to-end against the preview backend. |
| **Operational First** | Drivers cannot be dispatched without current orientation. Carriers self-onboard via secure invite. Zero double entry. |
