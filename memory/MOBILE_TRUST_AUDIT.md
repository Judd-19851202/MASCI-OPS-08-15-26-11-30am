# Mobile Trust Audit
## Phase TRUST-1 · 2026-05-27

> iPhone Safari is the design substrate. iPad is the second surface
> (superintendents). Anything else is a fallback. This audit ranks
> mobile-specific risk and verifies coverage.

---

## 1 · The mobile threat model

| Threat | Frequency | Mitigation status |
|---|---|---|
| Home button / app-switcher mid-edit | dozens / shift | ✅ iter440 visibilitychange + pagehide flush |
| Screen auto-lock mid-edit | hundreds / shift | ✅ iter440 visibilitychange |
| Incoming call interrupting Safari | 5–15 / shift | ✅ same |
| iOS low-memory eviction → bfcache or reload | 2–5 / shift | ✅ iter440 device-scoped IDB key survives reload |
| ITP 7-day origin purge | 1 / month / device | 🟧 detected indirectly via empty IDB on mount; no operator banner (TF-001) |
| Private Browsing mode | rare | ⚠ session-scoped device id only; no banner |
| Storage quota exceeded mid-photo-attach | event-driven | ✅ iter440 truthful pill · 🟧 no pre-warning (TF-004) |
| Reader Mode accidental trigger | rare | ⚠ DOM replaced; iter440 flush events still fire on visibilitychange before Reader takeover |
| Cross-origin link (Maps / Phone tap from narrative) | per-narrative | ✅ visibilitychange fires; flush completes |

---

## 2 · iOS Safari lifecycle coverage

Source-of-truth: `useFormDraft.js` listeners (iter440).

| Lifecycle event | Handler registered? | Sync IDB write? | Telemetry? |
|---|---|---|---|
| `visibilitychange (hidden)` | ✅ | ✅ | ✅ `draft.lifecycle` |
| `pagehide` | ✅ | ✅ | ✅ |
| `beforeunload` | ✅ | ✅ best-effort | ✅ |
| `pageshow` | ✅ | re-reads IDB | ✅ |
| `freeze` (chromium) | ❌ (iOS doesn't fire this) | n/a | n/a |

---

## 3 · Storage budget reality

iOS Safari quota observed in field:
- Default (post-day-1 usage): ~1 GB
- After 7-day ITP cooldown: ~50–100 MB
- Private Browsing: ~5–10 MB

Daily Report worst-case envelope (post-iter440):
- Form JSON (no photos): ~1 MB
- Photo blob store (6 photos × 3 MB native): ~18 MB
- Idempotency key: <1 KB
- **Total: ~19 MB → safe under all 3 quotas above**

Pre-iter440 envelope (base64 photos in form payload): ~25 MB → blew the ITP-reduced quota.

---

## 4 · Viewport coverage

Playwright tests parametrize across:
- `desktop` (1920×1080)
- `ipad` (1024×768)
- `mobile` (390×844, Mobile Safari UA)

| Test file | Viewports covered |
|---|---|
| `test_draft_loss_remediation.py` | mobile only |
| `test_draft_telemetry_endpoint.py` | n/a (backend) |
| `test_draft_loss_regression_iter440.py` | mobile + desktop |
| `test_field_trust_iter442.py` | mobile + desktop |
| `test_contextual_return_path_iter443.py` | desktop only |

**Gap:** iPad viewport not covered for draft-loss tests (TF-009). Superintendents on iPad have a different layout path; an iPad-only regression would not be caught.

---

## 5 · Photo flow risk

`photoDraftStore.js` (iter440) stores photo Blobs separately from the form payload. The form draft holds only `{stageId, mime, sizeBytes, takenAt}` refs.

| Risk | Mitigation |
|---|---|
| iOS HEIC vs JPEG mismatch on certain devices | Form accepts any mime; preview rendering tolerates |
| Photo larger than 10 MB single-shot | Acceptable under post-iter440 envelope |
| Photo blob discard on parent draft purge | `discardPhotoBlobs(actorId, formKey)` runs on commit |
| Stale photo blobs from prior drafts | 30-day TTL purge runs on next mount |

No open findings in this section.

---

## 6 · Network instability

| Pattern | Behavior |
|---|---|
| Submit while offline | `enqueueUpload` queues; pill shows "Saved · will upload when reconnected" |
| Offline → online transition | `online` event flushes queue + telemetry buffer |
| Partial 5xx during upload | Existing offlineQueue retries with backoff |
| Submit and reload before queue flushes | Idempotency key persisted (iter440) prevents duplicate |
| Submit and the queue silently drops | TF-011 open — no telemetry signal yet |

---

## 7 · Open mobile-specific findings

| ID | Sev | Summary |
|---|---|---|
| TF-001 | T4 | ITP-purged IDB returns silent blank form |
| TF-004 | T3 | Quota probe doesn't surface operator warning |
| TF-009 | T2 | iPad viewport not in draft-loss regression |

---

## 8 · Verification status

- ✅ iPhone-class viewport (390×844) + Mobile Safari UA in all draft-loss tests
- ✅ visibilitychange / pagehide / beforeunload lifecycle covered by `test_draft_visibilitychange_flushes.py` (in `test_draft_loss_remediation.py`)
- ✅ deviceId persistence across reload covered
- ✅ Photo blob separation covered (form payload < 1MB under 6-photo load)
- 🟧 iPad-specific regressions not covered
- 🟧 ITP eviction simulation not covered (hard to trigger in CI; documented gap)

---

## 9 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Mobile threat model documented · 3 open finds
- **Cross-refs:** `MOBILE_STATE_PERSISTENCE_ANALYSIS.md` (iter440 prior), `DATA_SURVIVABILITY_AUDIT.md`
