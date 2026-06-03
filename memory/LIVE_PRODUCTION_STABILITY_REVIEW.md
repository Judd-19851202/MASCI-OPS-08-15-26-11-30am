# LIVE PRODUCTION · STABILITY REVIEW
## OMEGA Directive · Phase 10 of 10

**Date**: 2026-06-03
**Target**: https://mascidocs.com (production)
**Probe vector**: External anonymous probes + cross-reference against pre-deploy certification artifacts

---

## 🟡 PHASE 10 VERDICT — PRODUCTION STABLE WITH 1 HIGH-SEVERITY OBSERVATION (PRE-EXISTING, NOT FROM DELTA)

The OKCP scope-gating deploy itself is clean and stable. However, external probing surfaced **one pre-existing condition** that did not originate from the current deploy but requires operator review: anonymous `/api/employees` returns the full employee roster.

---

## 1 · Stability signals (probed externally)

| Signal | Result | Verdict |
|---|---|:-:|
| Backend uptime + stable health | uptime 149 s at probe; `/api/health` 200 | 🟢 |
| Sentry capture | `sentry.enabled=true` per `/api/version` | 🟢 |
| Frontend bundle integrity | 5.00 MB JS served in 413 ms, Cloudflare-edged | 🟢 |
| Edge layer | Cloudflare in front; HSTS preload header active | 🟢 |
| Auth gating | `/api/projects`, `/api/users` return 401 to anon | 🟢 |
| Public guidance API | 27/27 form_keys returned expected gated/served behaviour | 🟢 |
| Session-timeout discipline | tiered (ADMIN_HR 15m/4h, OPS 30m/8h, FIELD 60m/12h) | 🟢 |
| 404 / 5xx noise on public surface | no 5xx observed during probe window | 🟢 |

---

## 2 · Findings (classified)

### 2.1 · 🔴 BLOCKER · — none from this deploy.

The OKCP scope-gating delta introduced **zero** blockers. The 20 sensitive form_keys are correctly gated; the 7 public form_keys serve correctly; Spanish parity holds. This is the intended outcome of the deploy and it is achieved live.

### 2.2 · 🟠 HIGH · Pre-existing — `/api/employees` returns full roster to anonymous callers (NOT FROM THIS DEPLOY)

**Finding**: `GET https://mascidocs.com/api/employees` (no `Authorization` header) returns 200 with a payload containing **247 employee records** including:
- Names (e.g., "Alan Danford", "Alec Perkins", "Alejandro Escobedo")
- Internal IDs and `employee_id` fields
- CDL fields (holder, expiration, state, endorsements, restrictions)
- Medical card expiration dates
- Driver status
- `status_history` entries with actor emails (e.g., `jaymn.judd@mascigc.com`) and timestamps

Email and phone are populated on only 2 / 3 records respectively, but names + CDL + medical-card data on 247 employees is sensitive PII exposure.

**Pre-existing or new?** This is **pre-existing**. The OKCP scope-gating deploy did not touch `routes/employees.py` or any employee-listing route. The exposure predates the current deploy. The directive's own §1 acknowledged this earlier ("No public employee creation | `routes/employees.py` returns 410 on `/api/employees/add` | test failures here are env-related, not code-related") — meaning the create endpoint is gated, but the **list endpoint was not enumerated**.

**Possible intent**: There may be a legitimate operational use case (e.g., an unauthenticated dispatcher-portal driver lookup, a shift-start QR pre-fill, or a non-PII subset endpoint). The agent cannot determine intent without operator review.

**Severity**: HIGH if unintended; INFO if intended-by-design.

**Recommended action (NOT executed per directive STOP rule)**:
1. Operator confirms intent (intended-by-design vs. regression).
2. If unintended: gate the route to authenticated callers OR restrict fields to a public-safe projection (omit `status_history`, `medical_card_expiration_date`, `cdl_*`, `email`, `phone`, `employee_id`).
3. If intended: document the decision in a public-route inventory so future audits don't re-flag.

**Rollback decision**: Rollback of the current OKCP deploy would NOT resolve this finding (it pre-dates). A separate operator-authorized remediation is the correct path.

### 2.3 · 🟡 MEDIUM · Pre-existing — `/api/version` `commit` and `built_at` are `unknown`

**Finding**: `/api/version` returns `commit=unknown`, `built_at=unknown`. `release` field carries a hash but is not tied to a git commit.

**Impact**: Reduced post-deploy forensic confidence. Hard to correlate Sentry traces with a specific deployed commit.

**Action**: Wire `GIT_COMMIT` and `BUILT_AT` env vars in the Emergent Production Deploy panel. Pre-existing; not a deploy blocker.

### 2.4 · 🟡 MEDIUM · Pre-existing — `passkeys` TTL index conflict on startup

Documented in `FINAL_PRE_DEPLOY_GO_NO_GO.md` §9. MongoDB index already exists with a different TTL value (86400 s vs 300 s). Logged as a WARNING at boot; non-blocking. Pre-existing.

**Action**: Drop and recreate the WebAuthn challenges TTL index during a maintenance window. Not a deploy blocker.

### 2.5 · 🟢 LOW · Pre-existing — frontend ESLint `react-hooks/exhaustive-deps` warnings

Four pre-existing warnings on AdminIntegrationCenter, AdminOperationsEvents, AssetProfile, ShiftStart. Compile succeeds; runtime unaffected. Cosmetic.

### 2.6 · 🟢 LOW · Pre-existing — `CSP` and `X-Frame-Options` headers absent

Modern security-defence-in-depth misses. Cloudflare + HSTS preload provide partial mitigation. Add CSP + frame-ancestors in a future hardening cycle.

### 2.7 · 🟢 LOW · Pre-existing — `RESEND_API_KEY missing` log on preview pod

Preview-only by design; production has its own configuration via Emergent Production Deploy panel.

### 2.8 · 🟢 LOW · Pre-existing — 4 unrelated pre-existing pytest failures (out of scope per delta directive)

`test_iter209_helptip_engine`, `test_iter286/iter287_driver_qualification_*`, `test_iter317a_fl_portal_coaching_parity`. None affect production runtime; all pre-date the OKCP delta.

---

## 3 · Severity rollup

| Class | Count | Attributable to this deploy? |
|---|---:|:-:|
| 🔴 BLOCKER | 0 | n/a |
| 🟠 HIGH | 1 (`/api/employees` roster exposure) | **NO** — pre-existing, unrelated to OKCP delta |
| 🟡 MEDIUM | 2 (version stamping, passkeys TTL) | **NO** — pre-existing |
| 🟢 LOW | 4+ (ESLint warnings, CSP, RESEND on preview, 4 pre-existing pytests) | **NO** — all pre-existing |

**Deploy-attributable risk: ZERO.** All findings predate this deploy and are tracked for separate remediation cycles.

---

## 4 · 30-day observation recommendations

1. **Days 1–2**: Operator completes Phase 3, 4, 5, 6 (UI), 7, 8, 9 walkthrough checklists. Promote PHASE statuses from 🟡 to 🟢 as each is validated.
2. **Day 1**: Operator reviews and decides on §2.2 (`/api/employees` exposure) — confirm intent or schedule remediation.
3. **Week 1**: Monitor Sentry for error spikes attributable to the OKCP scope change. None expected (the change tightens permissions; the only failure mode is "an authenticated user expects to see a tip but it's filtered" — handled by route-level auth).
4. **Week 1**: Wire `GIT_COMMIT` and `BUILT_AT` env vars in Emergent Production Deploy panel for future post-deploy forensics.
5. **Week 2**: Drop + recreate the WebAuthn challenges TTL index during a maintenance window.
6. **Week 4**: Add CSP + X-Frame-Options headers (defence-in-depth hardening).
7. **Week 4**: Close the 4 pre-existing pytest failures (iter209, iter286, iter287, iter317a) in a dedicated maintenance sprint.

---

## 5 · Phase 10 outcome

🟡 **PRODUCTION STABLE WITH 1 HIGH-SEVERITY PRE-EXISTING OBSERVATION** (`/api/employees` anonymous exposure).
The OKCP scope-gating deploy itself is 🟢 CLEAN.
Operator decision required on §2.2.
