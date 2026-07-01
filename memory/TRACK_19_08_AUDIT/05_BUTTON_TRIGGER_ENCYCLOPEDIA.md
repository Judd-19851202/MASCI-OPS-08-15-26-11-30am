# TRACK 19.08 · Button & Trigger Encyclopedia

Every user-triggered action on the top form pages. What happens · What API · What state changes · What emails · What audit events · Failure mode.

Full enumeration is 300+ buttons; this file captures the *categories* + the highest-value / highest-risk triggers with evidence. Cross-ref `05_BUTTON_TRIGGER_ENCYCLOPEDIA.appendix.md` (regeneratable via drift-lock test).

---

## 1 · Universal triggers (present on every New*.jsx form)

| Action | API | State change | Notifications | Audit | Failure mode |
| --- | --- | --- | --- | --- | --- |
| **Autosave** (every N ms after edit) | none (IndexedDB via `useFormDraft`) | Local draft row upserted | none | `draft.write.ok` telemetry event | fallback: in-memory retry |
| **Restore Draft** | none | React state ← draft | none | `draft.read.ok` | Discarded if `savedByActor` mismatch (Track 19.04 actor-scope) |
| **Discard Draft** | none | Draft cleared | none | `draft.clear.ok` | none |
| **Use GPS** | Browser geolocation | Sets `gps_lat`/`gps_lng`/`gps_accuracy`; reverse-geocode → `location` | none | none | Toast on denial |
| **Photo Upload** | `POST /photo-storage/upload` (chunked) | Appends R2 key + thumb URL to `photos[]` | none | none | Retry queue on 5xx |
| **Attachment Upload** | `POST /daily-reports/attachments/upload` (unified Track 19.04) | Appends envelope to `attachments[]` | none | none | 400 on disallowed type; retry on 5xx |
| **Signature Sign** | none (canvas) | Sets data-URL on signature field | none | none | Clear button erases |
| **Language toggle** | none | Local storage `masci_lang` = en/es | none | none | On submit, ES payload → OpenAI translate → EN payload |
| **Submit** | `POST /<form-root>` via `enqueueUpload` (offline queue) | Draft committed on 2xx | Fires `schedule_auto_email` server-side | `audit_events` insert + trust-spine correlation | Queued on network failure; retries × 5 |
| **Save & Exit** | Autosave-only (no server call) | Draft persisted | none | none | none |
| **Home** (nav) | none (Route link) | Navigate away; draft persists | none | none | none |
| **Print** (via `PrintPoster` etc.) | none | `window.print()` | none | none | none |

---

## 2 · Form-specific critical triggers

### 2.1 Daily Report

| Action | API | Downstream |
| --- | --- | --- |
| Apply Smart Prefill | none (client-side hydration from `/jobs/{pn}/recent-context`) | Populates crew + equipment + time pattern (post-Amendment). Sets `_prefilled` marker (stripped on submit). |
| Reset row hours (per-row) | none | Clears one row's `start_time`/`stop_time`/`lunch_minutes`/`hours` + un-marks. |
| Link Excavation | Fetches trench_excavations for project | Sets `linked_excavation_ids[]`. Excavation hard-gate: submit fails 422 if `excavation_activity_today=Yes` and no link. |
| Submit | `POST /api/daily-reports` | → PDF (WeasyPrint) → `schedule_auto_email("daily-report", doc)` → PM email routing → Job Photos mirror → audit event → optional Job update. Also flips excavation records to include this DR ID. |

### 2.2 Equipment Pre-Op

| Action | API | Downstream |
| --- | --- | --- |
| Item mark Fail | none (local) | Adds to `defects[]` snapshot. |
| Submit | `POST /api/equipment-inspections` | → PDF → `schedule_auto_email("equipment-inspection", doc)` → For each `defects[]` item: create `fleet_defects` doc **if unit is a fleet vehicle** (via `equipment_master.kind`) → optionally set `fleet_status.status=out_of_service` when critical → audit event. |
| Admin Sign-off | `PATCH /api/admin/equipment-inspections/{id}/signoff` | Sets `signoff_by` + `signoff_at`; audit event; optional email to inspector. |
| View | `GET /api/equipment-inspections/{id}` | Read-only render. |

### 2.3 DVIR

| Action | API | Downstream |
| --- | --- | --- |
| Defect Fail | none (local) | Snapshots to `defects[]`. |
| Submit | `POST /api/fleet/inspections` | → `fleet_audit` insert → for each defect: `fleet_defects` insert → if any defect severity ≥ threshold → `fleet_status` OOS transition → notifications (`shop`, `dispatch`, foreman) → PDF → email → audit event → optional Motive/Samsara sync if `integration_settings.motive.enabled` or `.samsara.enabled`. |
| Shop Acknowledge | `POST /api/shop/fleet/defects/{id}/acknowledge` | State → `acknowledged`; audit event. |
| Shop Assign | `POST /api/shop/fleet/defects/{id}/assign` | Assigns mechanic; audit event; notification. |
| Shop Start | `POST /api/shop/fleet/defects/{id}/start` | State → `in_progress`; audit event. |
| Shop Repair | `POST /api/shop/fleet/defects/{id}/repair` | State → `repaired`; audit event; optionally clears OOS if all defects repaired. |
| Shop Reassign | `POST /api/shop/fleet/defects/{id}/reassign` | Same as Assign; audit event. |
| Shop Manager Review | `POST /api/shop/fleet/defects/{id}/manager-review` | State → `manager_review`; audit event. |
| Dispatch Clear | `POST /api/dispatch/fleet/defects/{id}/clear` | State → `cleared`; sets `oos_cleared_at`; unit returns to service; notification. |
| Dispatch Mark OOS | `POST /api/dispatch/fleet/units/{unit_number}/oos` | Marks `fleet_status.status=out_of_service`; audit event. |

### 2.4 Safety Meeting

| Action | API | Downstream |
| --- | --- | --- |
| Pick topic from library | `GET /api/safety-portal/topics` | Populates `topic` + `topics_covered` template. |
| Add attendee | none | Appends `{name, employee_id, signature: ""}`. |
| Sign attendee | none | Canvas → data-URL on that attendee row. |
| Submit | `POST /api/meetings` | → PDF (WeasyPrint) → email routing → training-record mirror (attendance credits to `safety_training_records`) → audit event. |

### 2.5 Incident

| Action | API | Downstream |
| --- | --- | --- |
| Add person involved | none | Appends record; if severity ≥ medium and type=injury, expands `injuries[]` capture. |
| Submit | `POST /api/incidents` | → PDF → email (Safety + HR + Executive when severity ≥ high) → `corrective_actions` may be auto-seeded based on template → `lifecycle_state=reported` → audit event. |
| Transition | `POST /api/incidents/{id}/transition` | State machine: `reported → in_investigation → closed`. Emits `state-events` and audit events. |
| Add Recovery Action | Same transition endpoint (typed state event) | Appends to `recovery_actions[]`. |
| Add Corrective Action | `POST /api/corrective-actions` (linked via `source_id`) | Creates a CA record referencing this incident. |

### 2.6 JHA

| Action | API | Downstream |
| --- | --- | --- |
| Submit | `POST /api/jhas` (or `POST /api/inspections` legacy) | → PDF → email → audit event. |
| Acknowledge | `POST /api/jha-acknowledgements` | Records `{employee_id, jha_id, jha_revision, acknowledged_at}` — immutable. |
| Compliance | `GET /api/jha-acknowledgements/compliance` | Read-only cross-reference. |

### 2.7 QA-QC

Same shape as Equipment Pre-Op, but no fleet-defect side-effect. Downstream: PDF + email + `inspections` insert with subtype `qaqc`.

### 2.8 Safety Equipment Issuance / Training

* Submit → `POST /api/equipment-issuances` (or `-trainings`) → PDF → HR-accountability event → audit.
* Return (on issuance) → `PATCH /api/equipment-issuances/{id}/return` → PDF supplementary → audit.

---

## 3 · Admin-only triggers (out of primary form scope but form-adjacent)

* `POST /api/admin/equipment-inspections/{id}/signoff` — post-hoc admin sign-off.
* `POST /api/admin/qaqc-inspections/*` — QA-QC admin ops.
* `POST /api/admin/fleet/*` — fleet admin ops (severity audit, migrate kind field, PDF reference card).

---

## 4 · Idempotency

All submit paths use client-side `mintIdempotencyKey()` + server `with_idempotency` wrapper (Track iter440). A duplicate submit within the window returns the original doc rather than creating a new one.

---

## 5 · Failure & retry behaviour

Universal via `enqueueUpload` (`frontend/src/lib/resiliency`):
* `queued` → toast "Saved · will upload when reconnected"
* Retries × 5 with exponential backoff
* On give-up → `draft.write.fail` telemetry; draft preserved for later manual retry
* On success → `draft.write.ok` + draft committed

---

## 6 · Trust-Spine correlation

Every submit path passes a correlation id downstream through:
1. `audit_events` — includes `correlation_id`, `workflow`, `doc_id`, `actor`.
2. Email routing audit `email_routing_audit_v` — same correlation id.
3. PDF render — filename tag carries correlation id.

Auditors can trace any operational event by correlation id across all touched surfaces. This is the platform's Trust-Spine primitive.
