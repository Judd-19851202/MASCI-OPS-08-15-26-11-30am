# Remaining High-Value Fixes · Phase 8 · Document 3 of 5

**Date:** 2026-05-24
**Constraint:** Restraint-compliant. Each entry below MUST satisfy ALL FIVE filters: operationally meaningful · commercially meaningful · adoption-positive · low-noise · simple to implement. Anything failing one filter is excluded.

**Total entries: 7.** Every item is small, surgical, and reuses existing infrastructure.

---

## 🟢 P1 · Tenant-driven branding env vars

**What:** Replace 15+ MASCI literal references in `backend/server.py` (FastAPI title, PDF download filenames, source-bundle ZIP name, XLSX export filenames) with reads from a new env var family: `TENANT_NAME`, `TENANT_LEGAL_NAME`, `TENANT_EMAIL_FROM`. Default values keep MASCI behavior unchanged.

**Why high-value:**
- Operational: zero impact (defaults preserve current behavior)
- Commercial: removes the single most visible productization blocker on the backend side
- Adoption: invisible to users; only visible to the operator at first config
- Low-noise: env-var-driven, no UI changes
- Simple: ~4-6 hours of grep + replace + 4 new env defaults

**Why now:** Cheap to do; expensive to defer. Every new feature that hardcodes "MASCI" in a string compounds the eventual sweep cost.

**Effort:** 4-6 hours.

---

## 🟢 P1 · Extract Phase 6 completion-banner derivations into custom hooks

**What:** Move `incidentCompletionTone`/`incidentCompletionLabel`/`incidentMissingSections` from `NewIncident.jsx` into `hooks/useIncidentCompletion.js`. Move `drCompletionTone`/`drCompletionLabel`/`drAttentionItems` from `NewDailyReport.jsx` into `hooks/useDailyReportCompletion.js`.

**Why high-value:**
- Operational: no behavior change
- Commercial: signals professional code organization for any future external technical review
- Adoption: zero user-facing impact
- Low-noise: refactor only
- Simple: each hook is ~40 lines; the file imports them; ~2 hours of work

**Why now:** Both files are above the 700-line soft limit (NewIncident 1306, NewDailyReport 1591). The completion-banner logic is the most extractable piece without touching JSX. This is the cheap maintainability win.

**Effort:** 2-3 hours.

---

## 🟢 P2 · Frontend page `<title>` tag → env-driven

**What:** `frontend/public/index.html` `<title>` and meta tags currently say "MASCI Operations Platform." Wire them to `REACT_APP_TENANT_NAME` (env default = "MASCI") in `index.html` via a small inline script, or via build-time substitution.

**Why high-value:**
- Operational: zero
- Commercial: browser tab + bookmark name reflect the tenant
- Adoption: zero
- Low-noise: build-config only
- Simple: 30 minutes

**Why now:** Pairs naturally with the backend env-var sweep (P1 above). Doing both at once is one mental context.

**Effort:** 30 minutes.

---

## 🟢 P2 · Per-portal bell unread-count cap notice

**What:** When `unread_count` returned by `/api/notifications/unread-count` exceeds 50, surface a small slate hint on the bell: `50+ · review and acknowledge`. Currently the badge shows raw numbers (60, 87, 130…) which produces signal fatigue.

**Why high-value:**
- Operational: protects against the documented Phase 7 risk of notification volume creep
- Commercial: customers will not notice during normal volume, only during high-incident periods
- Adoption: makes the bell feel professional rather than alarming
- Low-noise: cosmetic + one threshold constant
- Simple: ~1 hour of frontend work

**Why now:** Cheap to do; pre-empts a real risk documented in `OPERATIONAL_SIGNAL_DISCIPLINE_REVIEW.md` (60-day post-deploy watch item #1).

**Effort:** 1 hour.

---

## 🟢 P2 · "What this means" links on Phase 6 completion banners

**What:** The Phase 5D ViewIncident banner has a "What this means" link to the operational glossary. The Phase 6 incident + daily report completion banners do NOT yet have an equivalent. Adding a single `What this means →` link on each banner pointing to the corresponding glossary anchor closes the consistency gap.

**Why high-value:**
- Operational: improves Phase 6 banner trust + glossary discoverability
- Commercial: reinforces the platform's "always explain itself" voice
- Adoption: positive for new users; invisible for experienced ones
- Low-noise: one link element per banner
- Simple: ~30 minutes per file, EN+ES

**Why now:** Closes a small but real inconsistency. Pre-deploy is the right window because it touches user-facing banners.

**Effort:** 1 hour.

---

## 🟢 P3 · iter383 `/api/legacy-imports/*` extraction

**What:** Resume the route extraction work from iter383. Pre-flight is complete in `PHASE4D_EXTRACTION_TRACKER.md`. Estimated removal: ~400-500 LOC from `server.py`.

**Why high-value:**
- Operational: zero behavior change (parity-lock guaranteed)
- Commercial: improves long-term maintainability
- Adoption: zero
- Low-noise: routes move; surface unchanged
- Simple: pre-flight is done; the extraction itself is mechanical

**Why now:** After the first 14 days of production deploy, when no urgent operational issues are stealing focus.

**Effort:** 2-3 days (matches prior extraction iterations).

---

## 🟢 P3 · 233 inherited pytest isolation failure cleanup

**What:** `conftest.py` teardown refactor to fix state leakage across the 4,700-test suite. Goal: full CI green.

**Why high-value:**
- Operational: zero behavior change
- Commercial: confidence signal for any external technical review
- Adoption: zero
- Low-noise: tests only
- Simple: not simple — but the path is known (fixture state leakage at the conftest level)

**Why now:** Should pair with iter383 work since both touch backend testing scaffolding.

**Effort:** 3-5 days.

---

## ❌ Explicitly NOT in this list

The following were considered and rejected against the five filters. Each is in `DO_NOT_BUILD_YET.md` for the long-form rationale.

| Considered | Rejected on filter |
|---|---|
| Leadership Readiness Tile (admin home) | Adoption-positive but signal-noisy when other tiles exist; restraint-compliant says wait |
| Field Shadow Run admin entry | Not commercially-meaningful until commercial customers exist |
| Per-user notification preferences | Adoption-negative (settings paralysis) |
| Dark mode | Adoption-zero; UI redesign in disguise |
| Audit-log exports | Already covered by CSV exports + audit trails |
| AI corrective-action suggestions | Operationally negative (perfunctory CAPAs) |
| Activity feed | Operationally negative (volume overwhelm) |
| Multi-tenant scaffolding | Too large for Phase 8; tracked in PRODUCTIZATION_READINESS_SCORECARD.md |

---

## Recommended execution order

1. **iter384** — P1 branding env vars + P2 `<title>` tag + P2 bell cap (these share context).
2. **iter385** — P1 completion-banner hook extraction + P2 "What this means" links.
3. **iter386** — Production deploy. Watch first 14 days.
4. **iter387** — Resume iter383 extraction.
5. **iter388** — Pytest isolation cleanup.

Each iteration is small (≤ 2 days). Each ships independently. None expand the platform.

---

## Phase 8 conclusion on fixes

Seven entries. All small. All restraint-compliant. Zero feature expansion. Five of seven hours are env-var / tenant-name plumbing — the cheapest possible productization step.

**The platform does not need more features. It needs these seven small finishes and then commercial validation.**
