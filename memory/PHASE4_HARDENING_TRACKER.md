# PHASE 4 — ENTERPRISE HARDENING TRACKER
**Generated:** 2026-05-23 · iter369
**Status:** Kickoff iteration — auth regression lock established, no auth code changed.

The master tracker for Phase 4 enterprise hardening work. Updated each iteration. Phase 4 explicitly avoids architecture sprawl; everything below must materially improve trust, maintainability, security, or stability.

---

## Phase 4 sub-tracks

| Track | Status | Iterations | Owner |
|---|---|---|---|
| P4A · Auth Gate Consolidation | 🟡 PLANNED · regression lock laid iter369 | iter370+ | E1 incremental |
| P4B · MFA + Portal Governance | 🔴 NOT STARTED · needs integration choice | TBD | operator decision |
| P4C · Production Parity Finalization | 🟡 PLAYBOOK READY · pending operator deploy | one-shot after deploy | operator |
| P4D · Architectural Hardening | 🔴 NOT STARTED · `server.py` 12k+ LOC | TBD | careful refactor |
| P4E · Operational Trust & Adoption | 🟢 ONGOING · iter354-368 already lowered friction | continuous | E1 |
| P4F · Governance Engine Maturity | 🟢 ONGOING · 16 detectors, low false-positive | continuous | E1 |
| P4G · Operational Language Lock | 🟢 LOCKED · 11 canonical terms, glossary owns truth | locked | E1 |
| P4H · Coaching System Maturity | 🟢 LOCKED · 7 LifecycleGuides, ES parity | locked | E1 |

---

## What iter369 shipped (Phase 4 kickoff deliverable)

- **NO auth code changed.** Per the "incremental + regression locked" rule, the first step is to lock current behavior, not to refactor.
- **Auth inventory completed.** 23 distinct RBAC dependency functions catalogued. See `AUTH_CONSOLIDATION_PROGRESS.md` for the categorization.
- **Auth regression lock established.** `/app/backend/tests/test_iter369_auth_regression_lock.py` — 16/16 PASS. Tests 6 representative top-of-funnel gates (admin-strict, admin-namespace, safety, hr, dispatch, fl) + 2 public routes (negative control). Bypasses the conftest auto-injection patcher using raw urllib + browser-UA workaround so future refactors cannot accidentally pass a broken test.
- **5 Phase 4 tracker documents created** in `/app/memory/`.

---

## What iter370+ should ship (P4A roadmap)

Per "small changes, regression locked" rule, here's the proposed sequencing:

**iter370** — Migrate `require_dispatch_or_admin` family (lowest risk: dispatch is the smallest portal, fewest routes)
- Replace 3-5 routes' inline gates with `require_any_of([require_dispatch_token, require_admin])`
- Run iter369 regression lock + cumulative pytest
- If green: commit. If red: revert.

**iter371** — Migrate `require_shop_or_admin` family (similar size/risk)

**iter372** — Migrate `require_safety_or_admin` family (highest-traffic, save for last)

**iter373** — Consolidate inline `require_hr_or_admin` instances if multiple exist with subtle differences

**iter374** — Decision point: keep the 3 admin variants (`require_admin`, `require_admin_strict`, `require_admin_async`) or consolidate via parameters? Their differences are intentional (PM token policy varies). Recommend KEEP unless operator wants a single function with `mode=` parameter.

**STOP CRITERIA**: Any iteration where the iter369 regression lock fires → revert immediately, file as a bug, do not proceed.

---

## What is NOT in Phase 4 scope

These are deliberately deferred:
- Auth code rewrite without behavior change verification (too risky).
- MFA without integration choice (operator must decide TOTP vs SMS vs magic-link first).
- server.py extraction without first locking the public route inventory (would silently break clients).
- New dashboards, new endpoints, new collections (Phase 4 is hardening, not extension).

---

## Cumulative regression health

iter354 → iter369: **81/81 pytest items PASS** in 29s.

- iter354 governance phase2 — 5 tests
- iter355 employee linkage — 5 tests
- iter356 capa lifecycle — 11 tests
- iter357 notifications digest — 5 tests
- iter358 digest expansion — 6 tests
- iter359 employee roster field — 5 tests
- iter363 employee linkage persistence — 11 tests
- iter364 p1 linkage persistence — 6 tests
- iter368 incident-capa reverse link — 4 tests
- iter369 auth regression lock — 16 tests

This suite must remain green throughout all iter370+ work.
