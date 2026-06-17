# TRUST GAP REPORT · TRACK 15.13B

**Date**: 2026-02-15 (executed 2026-06-17)
**Purpose**: For every item in Tracks 15.9A · 15.10 · 15.11C · 15.12 · 15.12A · 15.13A, state honestly what evidence backs the closure claim and what does not.
**Author rule**: no PASS unless evidence is named.

---

## Tier definitions

| Tier | Definition |
| ---- | ---------- |
| **🟢 PRODUCTION VERIFIED** | A real production user / operator confirmed the workflow worked end-to-end after the relevant deploy. |
| **🟡 PREVIEW VERIFIED** | Workflow exercised in the preview environment via the live API + the live SPA. Includes my own Playwright cert runs and curl-driven proofs. Does **not** prove production. |
| **🔵 CODE-REVIEW ONLY** | Tests pass, lint passes, code reads correctly — but no live UI or curl run was performed. Easiest tier to be wrong about. |
| **🔴 FAILED IN PRODUCTION** | Even if a lower tier said PASS, production usage proved otherwise. |

---

## Track-by-track honest accounting

### Track 15.9A — HR Daily Reports Operational Certification

| Item | Tier at close | Production reality | Honest note |
| ---- | ------------- | ------------------ | ----------- |
| `/api/hr/daily-reports` returns rows | 🟡 PREVIEW VERIFIED | ✅ works | curl + 44 tests |
| `?pm` / `?superintendent` / `?foreman` / `?project` / `?date_from` filters | 🟡 PREVIEW VERIFIED | partial | filters resolve, but `?pm=` only resolved via `db.projects` — legacy DRs invisible (fixed 15.13B) |
| Sample row carries `pm_email` / `pm_name` / `superintendent` | 🟡 PREVIEW VERIFIED | **🔴 FAILED** — production showed empty PM column because cert seed populated `jobs_master` while real DRs ride that source too, and the 15.9A enrichment only read `db.projects` |
| HR DETAIL view renders narrative · crews · subs · photos · sign-off | 🔵 CODE-REVIEW ONLY | **🔴 FAILED** — photos rendered as literal alt strings (`photo-0..photo-3`). The detail page was added in 15.9 but I never opened a real DR in the live SPA with `photo://` refs |
| HR detail PM strip (Track 15.9A) | 🔵 CODE-REVIEW ONLY | **🔴 FAILED** — same root cause as the list endpoint |
| Read-only contract (no DELETE/PATCH) | 🟡 PREVIEW VERIFIED | ✅ works | curl returns 401/405 |

**Recovery**: PM enrichment now has a 3-tier fallback (`projects` → `jobs_master` → derived from email local-part); photos pipe through `resolvePhotoSrc()` exactly like every other view.

---

### Track 15.10 — Project Team Management Recovery

| Item | Tier at close | Production reality | Honest note |
| ---- | ------------- | ------------------ | ----------- |
| `(unnamed)` elimination via fallback hierarchy | 🟡 PREVIEW VERIFIED | not reported broken | I screenshotted a single cert project; no real production confirmation collected |
| Back navigation + breadcrumb | 🟡 PREVIEW VERIFIED | not reported broken | same caveat |
| Login status visibility / PM / Co-PM / Exec / Sup rows | 🟡 PREVIEW VERIFIED | not reported broken | same caveat |
| Directory picker · candidate pool · add member | 🔵 CODE-REVIEW ONLY (tests cover this) | not reported broken | the actual modal click flow was not exercised in my live cert run |

---

### Track 15.11C — PM Runtime Browser Certification

| Item | Tier at close | Production reality | Honest note |
| ---- | ------------- | ------------------ | ----------- |
| Multi-project dashboard | 🟡 PREVIEW VERIFIED | not reported broken | cert run + screenshots |
| Scope leak prevention | 🟡 PREVIEW VERIFIED | not reported broken | curl proof |
| `_authHeaders` fix in `PmProjectFirstHome.jsx` | 🟡 PREVIEW VERIFIED | not reported broken | live cert PM saw dailies + photos |
| Zero-residue rollback | 🟡 PREVIEW VERIFIED | n/a (preview-only seed) | rollback ledger archived |

**Note**: Track 15.11C closed by me as "Five-Pillar 9.96/10" — that score was based on preview cert only. It said *"Proven 10"* in the report. **Honest tier was 🟡 PREVIEW VERIFIED, not 🟢 PROVEN.** Adjusted retroactively.

---

### Track 15.12 — Final Release Gate

| Item | Tier at close | Production reality | Honest note |
| ---- | ------------- | ------------------ | ----------- |
| Phase 1 build verification | 🟡 PREVIEW VERIFIED | ✅ | curl `/api/health` + supervisor status |
| Phase 2 167/167 tests | 🟢 PROVEN | ✅ | green is green |
| Phase 4 PM dashboard runtime | 🟡 PREVIEW VERIFIED | not reported broken | cert PM screenshots only |
| Phase 7 HR Daily Reports verification | 🟡 PREVIEW VERIFIED → **🔴 FAILED in production** | **the gate report said `pm_name` / `pm_email` / `superintendent` were present on the sample row** — but the cert seed I ran had explicit `jobs_master` rows that DID have a `projects` mirror, masking the real-world case where they don't |
| Phase 8 security audit (scope leak) | 🟡 PREVIEW VERIFIED | not reported broken | curl proof |
| Phase 9 iPad certification | 🟡 PREVIEW VERIFIED | not reported broken | screenshots |
| Phase 11 regression audit | 🔵 CODE-REVIEW ONLY | partial | "Track 15.9A landed cleanly with zero regression elsewhere" — this conclusion was code-only |

**The 15.12 gate's biggest failure**: it asserted "🟢 DEPLOY" without ever opening a real HR Daily Report detail page in a real browser. Every other phase had a screenshot. Phase 7 had API curls only. **That's the trust gap.**

---

### Track 15.12A — HR Diagnostic + PM Photo Workflow Recovery

| Item | Tier at close | Production reality | Honest note |
| ---- | ------------- | ------------------ | ----------- |
| HR red banner diagnostic | 🔵 CODE-REVIEW ONLY (couldn't reproduce in preview) | banner self-cleared in production per user amendment | best-effort, no false claim |
| PM photo lightbox on `/pm/command-center` | 🟡 PREVIEW VERIFIED | not reported broken in production | live cert run |
| Context-aware back button on `ViewDailyReport.jsx` | 🟡 PREVIEW VERIFIED | not reported broken | live cert run |
| `RedirectWithId` state forwarding | 🟡 PREVIEW VERIFIED | not reported broken | live cert run |

---

### Track 15.13A — Asset Care Routing Recovery

| Item | Tier at close | Production reality | Honest note |
| ---- | ------------- | ------------------ | ----------- |
| `_mirror_asset_admin_flag()` helper on shop user create/update | 🟡 PREVIEW VERIFIED | works for NEW asset admins | cert run confirmed |
| `shop_login` echoes `is_asset_admin` from directory | 🟡 PREVIEW VERIFIED | **🔴 FAILED for LEGACY users** — existing real Asset Admin had a `shop_users` row but NO `user_directory` row (created before 15.13A landed), so the lookup returned None and `is_asset_admin: false` was emitted — landing them on /shop |
| Welcome email branches by role | 🔵 CODE-REVIEW ONLY | unknown — operator never re-issued the welcome email for a real Asset Admin yet | safe code change, but the live re-issuance never happened |
| ShopHubV2 Asset Care tile | 🟡 PREVIEW VERIFIED | unknown — production has not re-deployed since 15.13A landed (or the user didn't refresh) | preview screenshot |
| ShopLogin.jsx routes Asset Admin to `/shop/asset-care` | 🟡 PREVIEW VERIFIED | **🔴 FAILED in production** — same root cause as the backend mirror: legacy user has no directory row |

**Recovery in 15.13B**: shop_login falls back to `_role_implies_asset_admin(user.role)` so existing Asset Administrators are routed correctly without a backfill script.

---

## The pattern of the trust gap

Every failure in this list shares ONE root cause:

> **I asserted "PROVEN" when the workflow had been demonstrated only against
> a clean cert dataset I seeded myself, not against the dirty real-world
> data that production carries.**

Specifically:
* My cert seed writes `jobs_master` rows that production may not have.
* My cert seed writes `user_directory` rows alongside `shop_users`, masking the legacy case where only `shop_users` exists.
* My cert seed creates `job_photos` with synthetic `key: cert/...` refs, not the production `photo://masci-hub/...` URIs that trigger the resolver bug.

A cert seed designed by the same person writing the fix will never expose
the case it didn't think to seed.

---

## Going-forward rule (proposed)

* **No closure claims "PROVEN" without one production-data-shape probe.**
* The probe doesn't have to be in production — but it MUST exercise a
  document type the cert seed did NOT create (e.g. open a randomly-picked
  real daily report ID from preview's real data, not a `cert-dr-…` ID).
* If preview has no data of the right shape, that fact itself is the
  closure note, and the tier drops to 🟡 PREVIEW VERIFIED LIMITED.

---

## Action items already taken in 15.13B

1. **Failure #1 (Asset Admin routing)** — shop_login falls back to the role-label check. Live proven: legacy shop_user with role `Asset Administrator` and no directory row → `is_asset_admin: true` returned on login.
2. **Failure #2 (HR PM missing)** — 3-tier fallback `projects` → `jobs_master` → derived. Live proven against the cert seed and against `jobs_master`-only rows.
3. **Failure #3 (HR photos)** — `resolvePhotoSrc()` wraps every photo ref in the HR detail page. The literal alt text `photo-0..photo-3` cannot render anymore because the resolver now turns `photo://` refs into `/api/photo-bytes?ref=…`.

END · TRUST GAP REPORT.
