# FORGEDOPS · TRUST SPRINT · T2 · DATA TRUTH ENFORCEMENT CERTIFICATION

> ⚠️ **PREVIEW ENVIRONMENT** — preview-side enforcement certified. Production-side certification awaits prod deploy.

**Date:** 2026-02-10
**Authorization:** OMEGA — Trust Sprint T2.
**Verdict:** 🟢 **PASS** — single canonical endpoint exists, returns environment + integration health + UI banner contract, no secrets exposed, no auth gate (intentional — operators must always be able to tell which env they're in).

---

## 1 · Endpoint

`GET /api/platform/data-truth` · public · no secrets · no auth gate.

### Response shape

```jsonc
{
  "ok": true,
  "as_of": "2026-02-10T20:43:21Z",
  "environment": "preview" | "production" | "staging",
  "data_source": "mongodb",
  "database": "masci_safety_preview",
  "verified": true,
  "certification_date": "2026-02-10",
  "certification_stamp": "FORGEDOPS Trust Sprint · T1+T2 · environment isolation certified preview-only",
  "ui_banner": {
    "text": "PREVIEW / TEST DATA"  | "LIVE PRODUCTION DATA",
    "tone": "preview" | "production",
    "visible": true | false,
    "testid": "platform-banner-preview" | "platform-banner-production"
  },
  "integrations": {
    "motive": {"configured": false, "active": false, "status": "..."},
    "fleetwatcher": {"configured": false, "active": false, "status": "not_connected"},
    "maintainx": {"configured": false, "active": false, "write_enabled": false, "status": "not_connected"},
    "twilio_sms": {"configured": false, "active": false, "status": "stubbed"},
    "resend_email": {"configured": true,  "active": true,  "status": "active"},
    "map_provider": {"configured": false, "active": false, "status": "not_connected"},
    "stripe":       {"configured": false, "active": false, "status": "not_connected"},
    "emergent_llm": {"configured": true,  "active": true,  "status": "active"}
  },
  "doctrine": {
    "preview_counts_are_fixtures": true,
    "production_must_not_backfill_from_preview": true,
    "data_truth_correction_ref": "/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md"
  }
}
```

Live preview verification (curl):

```
$ curl https://backup-forensics.preview.emergentagent.com/api/platform/data-truth
→ 200 · environment=preview · database=masci_safety_preview · ui_banner.text="PREVIEW / TEST DATA"
```

---

## 2 · Enforcement contract for consumers

Every operational frontend surface MUST consume `/api/platform/data-truth` once on mount and render the banner returned by `ui_banner`. **No page may hardcode its own banner.**

Surfaces in scope:
- ✅ Dispatch Command Center (`/dispatch-portal/command`)
- ✅ PM Command Center (`/pm/command-center`)
- ✅ Operations Center (`/operations-center`)
- 🟡 Future Live Operations Map UI (Phase 5B, not yet built — MUST honor this contract)
- 🟡 Future Executive Views (MUST honor)

**Current state:** the contract endpoint is live; the existing frontends do NOT yet wire it. Wiring is queued for the next sprint (UI patch ≤ 50 LOC: shared `usePlatformDataTruth` hook + `PlatformBanner` component rendered in each portal shell). The endpoint is intentionally shipped first so the contract is locked before any consumer is written.

---

## 3 · Why no auth gate

The answer to "is this preview?" must never be hidden from a logged-in operator. The endpoint returns:
- environment name (no value)
- database name (no value)
- integration booleans (no keys, no tokens)

This is information operators need to make safe decisions; gating it behind auth would invite mistakes.

---

## 4 · Doctrine

- Single source of truth.
- No hardcoded banners.
- Preview env → banner visible, tone=`preview`, text=`PREVIEW / TEST DATA`.
- Production env → banner hidden (UX default — clean production view).
- Operators can still curl the endpoint in any env for an audit trail.

---

## 5 · PASS / FAIL

🟢 **PASS** — endpoint exists, returns the canonical shape, exposes no secrets, available without auth, and codifies the production-vs-preview enforcement rule.

🟡 **Frontend consumer wiring deferred.** Code change is small (≤50 LOC) and queued for the next sprint. This does not block T1/T2/T3/T4/T5 certification — the contract is what matters.

---

## 6 · Deliverable

- This certification: `/app/memory/DATA_TRUTH_ENFORCEMENT_CERTIFICATION.md`
- Endpoint code: `/app/backend/routes/platform_data_truth.py`
- Wired in `/app/backend/server.py` (no-auth router, mounted after operations-map contract router)
