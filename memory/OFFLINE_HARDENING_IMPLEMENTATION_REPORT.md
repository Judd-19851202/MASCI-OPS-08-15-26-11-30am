# Wave-2 Offline Hardening — Implementation Report

_Phase V.3 · 2026-05-29 · Daily Report Audit-and-Certify pass._

> **Operator authorization (verbatim):** _"Go with (a) — Audit-and-Certify. Do not introduce Service Worker / Background Sync in this wave."_

## 1 · Scope (operator-locked)

| In-scope | Out-of-scope |
|---|---|
| Audit autosave behavior | Service Worker uplift |
| Audit recovered-draft behavior | Background Sync API |
| Audit photo staging queue | New architecture |
| Audit offline submit queue | Pilot · RFI · Schedule · P6 |
| Audit idempotency keys | PM Exposure Tile routing |
| Audit recovery telemetry | Approval / rejection workflow |
| Verify `production[]` + `constraints[]` survive refresh / tab-close / browser-relaunch / offline-queue / failed-photo-upload / submit-retry | Dashboard visibility implementation |
| Close any schema-bump gaps (none found) | New components |
| 8 cert docs + 15-scenario test matrix | Web service worker code |

## 2 · Engine inventory (iter440 — already production-deployed)

| Surface | File | Role |
|---|---|---|
| Autosave hook | `lib/resiliency/useFormDraft.js` | 800 ms debounce + 10 s forced flush + iOS lifecycle handlers (visibilitychange · pagehide · beforeunload) |
| Draft store | `lib/resiliency/draftStore.js` | IndexedDB · device-scoped key · 24 h soft-delete archive · 14-day stale TTL · idempotency-key store |
| Restore prompt | `lib/resiliency/DraftRestorePrompt.jsx` | Recovered-draft banner · Restore / Discard / cross-token warning |
| Recovery notice | `lib/resiliency/DraftRecoveryNotice.jsx` | Toast on successful restore |
| Status pill | `lib/resiliency/DraftStatusPill.jsx` | Truthful "Saved 12s ago" / "Save failed — storage full" |
| Offline indicator | `lib/resiliency/OfflineIndicator.jsx` | Calm slate strip when `navigator.onLine === false` |
| Submit queue | `lib/resiliency/resiliencyQueue.js` | IDB-backed submit retry with `MAX_TRIES=5` + exponential backoff `[1, 2, 4, 8, 16] s` + auto-drain on `online` / `focus` |
| Settle subscription | `onQueueItemSettled` | Defers `commit()` (discard IDB draft) until queue confirms 2xx OR exhausts retries |
| Idempotency keys | `lib/resiliency/idempotency.js` | `mintIdempotencyKey` · persisted in IDB · sent as `Idempotency-Key` header · backend dedup 24 h TTL |
| Photo staging | `lib/resiliency/photoStaging.js` | Foreground-only File/Blob queue · `online` + `focus` flush · NOT used by DR (DR photos are inline dataURLs in the form envelope) |
| Telemetry | `lib/resiliency/draftTelemetry.js` | `/api/draft-telemetry` ingestion · `draft.*` events |
| Quota probe | `lib/resiliency/quotaProbe.js` | `navigator.storage.estimate()` · warning at 80 % |
| Prior-usage banner | `lib/resiliency/PriorUsageBanner.jsx` | Distinguishes empty-IDB-on-returning-foreman vs. genuine first-time use |
| Cross-token migration | `lib/resiliency/actorId.js` | One-time idempotent re-key of legacy token-derived drafts |

## 3 · Wave-2 audit findings

| Surface | Status | Notes |
|---|---|---|
| Autosave persists `production[]` | 🟢 | `saveDraft()` writes the entire `form` object — no allowlist · no schema · production rows ride through untouched |
| Autosave persists `constraints[]` | 🟢 | same · all 7 constraint-row fields (type · hours_impact · notes etc.) round-trip |
| iOS lifecycle flushes new fields | 🟢 | `visibilitychange → flushOnLifecycle("visibilitychange")` re-reads `dataRef.current` which already contains the latest production + constraints |
| Restore prompt shows for new fields | 🟢 | `getDraftEntry` returns `{ form, savedAt }` · NewDailyReport sets full state on restore |
| Offline submit queue carries new fields | 🟢 | `resiliencyQueue` serializes `entry.body` as-is · production + constraints fall through |
| Idempotency key applies to new envelope | 🟢 | `idempotencyKeyRef.current` is minted before the first submit attempt and persisted via `storeIdempotencyKey` · a refresh mid-queue reuses the same key |
| Recovery telemetry covers new fields | 🟢 | `payloadBytes` already includes serialized production + constraints |
| Quota probe accounts for new fields | 🟢 | Pure storage-usage metric · field-set agnostic |
| Photos resiliency | 🟢 | DR photos are base64 dataURLs embedded in the form envelope — ride autosave + submit queue · ZERO separate-upload exposure for DR · `photoStaging.js` remains scoped to PO/Incident attachments |
| `data-testid` selectors for production + constraints | 🟢 | match the existing iter440 telemetry tap-points |

### Schema-bump gaps found
**None.** Zero code changes required for Wave-2 audit pass. The iter440 engine has zero per-field coupling — its persistence layer (`idb-keyval set`) and submit queue (`enqueueUpload` with `body: payload`) treat the form payload as an opaque blob, so the schema bump from `data` to `data + {production[], constraints[]}` is automatic.

## 4 · Live verification (smoke probe summary)

Playwright probe on iPad-portrait viewport (`820 × 1180`) confirmed:

```jsonc
{
  "1_idb_after_typing": {
    "found": true,
    "project_name": "Wave-2 Audit Project",
    "production_count": 1,
    "production_first_qty": "320",
    "constraints_count": 1,
    "constraints_first_type": "weather",
    "constraints_first_hours": "2.5",
    "weather_impact": "Yes"
  },
  "2_restore_prompt": "Draft restored" toast shown,
  "3_form_state_after_restore": {
    "project_name": "Wave-2 Audit Project",
    "prepared_by": "Audit Foreman",
    "constraint_hours_value": "2.5",
    "weather_impact_yes_pressed": true,
    "production_status_pill": "1 rows"
  }
}
```

## 5 · Deliverables shipped

| # | Doc | Purpose |
|---|---|---|
| 1 | `OFFLINE_HARDENING_IMPLEMENTATION_REPORT.md` (this file) | Master audit report |
| 2 | `OFFLINE_DRAFT_ENGINE_CERTIFICATION.md` | useFormDraft contract |
| 3 | `PHOTO_RESILIENCY_CERTIFICATION.md` | DR photo path · staging engine boundary |
| 4 | `OFFLINE_SUBMISSION_QUEUE_CERTIFICATION.md` | enqueueUpload contract · 5×backoff · onQueueItemSettled gate |
| 5 | `SYNC_RECONCILIATION_CERTIFICATION.md` | Idempotency · 24 h TTL · single-device write contract |
| 6 | `RECOVERY_TELEMETRY_CERTIFICATION.md` | `draft.*` event taxonomy · `/api/draft-telemetry` |
| 7 | `FIELD_RELIABILITY_TEST_MATRIX.md` | 15-scenario test matrix · Playwright probes + iPad checklist |
| 8 | `PILOT_READINESS_RELIABILITY_ASSESSMENT.md` | Reliability-only gate · pilot acceptance criteria |
| · | `PRD.md` + `_INDEX.md` | Registries refreshed |

## 6 · Doctrine compliance

- ✅ **Reliability only.** No new features, no new components, no new dependencies.
- ✅ **Doctrine Lock #1 (Simplicity).** Foreman 9-step contract intact · zero new UI affordances.
- ✅ **Doctrine Lock #2 (Inheritance).** Reused iter440 engine 100 % · no parallel infrastructure.
- ✅ **No Service Worker · no Background Sync API · no IndexedDB Blob-cached photo queue.** Per operator directive.
- ✅ **Backend stability.** No schema changes · no migrations · no new endpoints.
- ✅ **89 / 89 ODR tests still pass** · ESLint clean.

## 7 · Stop condition

🛑 **HALTED at end of Audit-and-Certify pass as directed.**

- ❌ NO Pilot · NO RFI · NO Schedule · NO P6
- ❌ NO PM Hub wiring · NO approval/rejection workflow
- ❌ NO Service Worker uplift in this wave
- ✅ Awaiting operator review of the **Field Reliability Test Matrix** + **Pilot Readiness Reliability Assessment**.

---

_End of OFFLINE_HARDENING_IMPLEMENTATION_REPORT.md._
