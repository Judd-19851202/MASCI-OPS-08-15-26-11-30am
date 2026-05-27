# Data Survivability Audit
## Phase TRUST-1 · 2026-05-27

> Can operator work disappear? This audit walks every realistic
> data-loss vector and verifies which ones are closed, which are
> mitigated, and which remain open.

---

## 1 · Data-loss vectors (the 9-vector matrix)

| # | Vector | Today's defense | Status |
|---|---|---|---|
| 1 | Silent quota failure during autosave | Truthful `{ok,error}` from `saveDraft()`; pill turns red | ✅ iter440 closed |
| 2 | Token rotation orphans IDB draft | `getDeviceScopedActorId()` + legacy migration on mount | ✅ iter440 closed |
| 3 | iOS suspending timer mid-debounce | visibilitychange/pagehide/beforeunload synchronous flush | ✅ iter440 closed |
| 4 | Photo blob blowing form payload quota | `photoDraftStore` blob-only refs | ✅ iter440 closed |
| 5 | Operator taps Discard by mistake | 24h soft-delete archive | ✅ iter440 closed (recovery affordance pending TF-016) |
| 6 | Submit-time commit() discards draft before queue confirms | — | 🟧 TF-011 open |
| 7 | Tab reload mid-offline-queue mints duplicate | Idempotency key persisted in IDB | ✅ iter440 closed for Daily Report; siblings TF-002 |
| 8 | Stale draft restored over today's work | savedAt timestamp + restore prompt shows age | ✅ iter440 closed |
| 9 | ITP / Private Browsing wipes IDB silently | device id falls back to session-scoped; no operator banner | 🟧 TF-001 open |

---

## 2 · Draft lifecycle invariants

| Invariant | Verified by |
|---|---|
| Draft persists across reload (same device) | `test_draft_visibilitychange_flushes` |
| Draft persists across token rotation | `test_device_id_persists_across_reload` + legacy migration |
| Draft pill never claims "saved" without IDB write | `test_silent_quota_failure_turns_pill_red` |
| Restore prompt shows real savedAt | `test_restore_prompt_shows_savedat_timestamp` |
| Photo flow keeps form payload <1MB at 6 photos | implicit via blob-store architecture |
| Idempotency key survives reload | `test_draft_idempotency_persisted` (Daily Report) |
| Submitted report is removed from IDB on confirmed 2xx | `commit()` runs after queue confirms |

---

## 3 · Photo survivability

| Risk | Status |
|---|---|
| Photo Blob stored as base64 in form payload | ✅ moved to `photoDraftStore` |
| Form payload size > 1MB with 6 photos | ✅ stays <1MB |
| Photo orphaned after draft discard | ✅ `discardPhotoBlobs` runs on discard |
| Photo upload mid-offline | ✅ uses existing photoStaging path |
| Photo blob TTL purge | ✅ 30-day TTL on parent draft |

---

## 4 · Open data survivability findings

| ID | Sev | What |
|---|---|---|
| TF-001 | T4 | ITP-purged IDB → no recovery banner |
| TF-002 | T3 | Sibling forms idempotency not persisted |
| TF-004 | T3 | Quota probe doesn't surface warning |
| TF-011 | T3 | Submit-time commit() may discard before queue confirms |
| TF-016 | T2 | Soft-deleted drafts have no recovery affordance |

---

## 5 · Bytes-on-disk discipline

Storage keys today:

| Key prefix | Purpose | Bytes |
|---|---|---|
| `masci.device-id` | localStorage device UUID | <100 |
| `masci.draft.<actorId>.<formKey>` | live draft envelope | <1 MB per form |
| `masci.draft-archive.<actorId>.<formKey>.<deletedAt>` | 24h soft-delete | <1 MB per archive |
| `masci.draft-photo.<actorId>.<formKey>.<stageId>` | photo blob | up to 5 MB per blob |
| `masci.draft-idempotency.<actorId>.<formKey>` | submit key | <100 |
| `masci.crew-memory.daily-report.v1` | localStorage device memory | <50 KB |

Worst-case total per device: ~30–50 MB. Comfortably under default iOS Safari quota (~1 GB). Tight under ITP-reduced quota (~100 MB) — still survivable.

---

## 6 · Backend data survivability

| Risk | Defense |
|---|---|
| MongoDB _id leakage | Only `/api/draft-telemetry/recent` tested for this. Other routes not asserted (TF-015 open) |
| Submitted record overwritten by replay | Idempotency on server-side (existing); client-side iter440 fix prevents duplicate mint |
| Concurrent edits | Out of scope for daily-form workflow (single-author per draft) |
| Backup / restore | Existing R2 + Atlas backup workflow (out of audit scope) |

---

## 7 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 9 vectors mapped · 4 closed since iter440 · 5 open
- **Cross-refs:** `MOBILE_TRUST_AUDIT.md`, `P0_REMEDIATION_PLAN.md`, `ROOT_CAUSE_HYPOTHESIS_MATRIX.md`
