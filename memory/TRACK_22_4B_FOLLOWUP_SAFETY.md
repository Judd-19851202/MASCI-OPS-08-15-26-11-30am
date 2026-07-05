# TRACK 22.4b-followup-Safety — Closure Memo

**Status:** ✅ CLOSED · 2026-07-05
**Owner:** e1 · continuation from fork
**Predecessors:** TRACK 22.4 (deep audit) · TRACK 22.4b-followup Preview Validation Identities

---

## 1 · Mandate (user's exact words)

> A — Yes. Start with the P0 seam bug reproduction and fix.
> Do not skip B-02 or B-04. Complete the full Safety follow-up track.
> Required order:
> 1. Reproduce and fix the PVI Safety seam 401 bug.
> 2. Regression-lock the shared seam.
> 3. Close B-02 Safety Meeting subject/company nulls.
> 4. Close B-04 Trench repair lifecycle invariants.
> 5. Prove Shop cannot clear Safety Hold.
> 6. Prove Repair Complete does not equal Safe To Use.
> 7. Prove Safety verification is required for return-to-service.
> Motive remains untouched. No dashboards. No V2 workflows. No fake green.

---

## 2 · P0 · The seam 401 root cause (reproduced + fixed)

**Reproduction:** with a freshly-minted safety PVI token, `GET /api/safety/overview` returned `401 · Safety auth required`, and `GET /api/shop/me` returned `401 · Shop, PM, or admin login required`.

**Root cause:** the initial PVI wire had two gaps:

1. The shared `role_guard_validation_seam.py` wrapper existed but was **never actually invoked** — it wrapped `_wrapped(*args, **kwargs)` with an internal-args signature that FastAPI cannot introspect. All fallback logic was pasted inline into two guards only: `make_require_safety_or_admin` and `make_require_shop_or_admin_fleet`.
2. The **single-role** `make_require_safety_token` (used by `/api/safety/overview`) and the **module-level** `require_shop_or_admin` in `server.py` (used by `/api/shop/me` and every trench-safety Shop write) had **no fallback at all**. Every PVI token 401'd there.

**Fix:** rebuilt `role_guard_validation_seam.py` as a pure async helper `try_validation_fallback(db, token, expected_role=...)` — the one place role-scoped PVI verification lives. Wired the helper into:

| Guard | File | Change |
|---|---|---|
| `_require_safety_token` (single-role) | `routes/safety_portal/_deps.py` | Added PVI fallback via helper |
| `_require_safety_or_admin` (safety writes) | `routes/safety_portal/_deps.py` | Replaced inline block with helper call (DRY) |
| `_require_shop_or_admin_fleet` (fleet-ops) | `routes/shop_portal_deps.py` | Replaced inline block with helper call (DRY) |
| `require_shop_or_admin` (server-level) | `server.py` | Added PVI fallback (was missing) |

All four guards now share **exactly one** PVI verification code path. Real production auth still runs first; PVI fallback only fires on real-auth failure AND in preview-class envs AND with role match at the token layer.

**Regression lock:** `backend/tests/test_track_22_4b_followup_safety_seam.py` — 11 tests. Covers: real safety token still passes, valid PVI accepted, cross-role PVI rejected, garbage tokens rejected, admin token still bypasses, revoked PVI 401s immediately.

---

## 3 · B-02 · Safety Meeting subject / company nulls — CLOSED

**Root cause:** three separate write-side gaps + one legacy corpus.

1. `topic` (subject) and `project_name` had no Pydantic validator — empty strings passed through.
2. `normalize_meeting_attendees` looked up MASCI employees by `employee_id` only. If a safety rep typed a MASCI employee's name manually (no id), the row was silently stored with `company=""` and `attendee_type="manual"`.
3. Legacy corpus: 43 meetings inserted before the Slice-2 normalization guard had 160 attendee rows with no `company`, no `attendee_type`, no `is_masci_employee` flag.

**Fix stack:**

| Layer | File | Change |
|---|---|---|
| Write validation | `routes/safety.py :: MeetingCreate` | Added `_topic_required` and `_project_name_required` field validators — empty strings now 422 |
| Attendee normalization | `lib/meeting_identity.py :: normalize_meeting_attendees` | Added name-based lookup fallback — a manual attendee whose name uniquely matches an active MASCI employee is auto-promoted to `attendee_type="employee"` with `company="MASCI"` locked |
| Legacy corpus | `backend/scripts/backfill_b02_meeting_nulls.py` | Idempotent, dry-run capable, refuses APP_ENV=production without explicit override. Applied to preview: repaired 46 meetings (3 via employee_id + 43 via name), flagged 123 as `attendee_type="manual" · review_status="needs_review"` for admin follow-up. Zero fabrications. Re-run is zero-diff. |

**Post-fix DB invariants (queried directly):**

- `attendees.is_masci_employee=True AND company IN ("", null)` → **0** (was 160)
- `attendees.attendee_type IN ("", null)` → **0**
- `meetings.topic IN ("", null)` → **0**

**Regression lock:** `tests/test_track_22_4b_followup_safety_b02.py` — 6 tests. Empty topic rejected · empty project_name rejected · empty-company attendee rejected · MASCI-employee-by-name auto-locks to `company="MASCI"` · legacy corpus invariants held.

---

## 4 · B-04 · Trench repair lifecycle role invariants — CLOSED

Exercised end-to-end with **live PVI tokens** against **live backend routes** (no mocks, no stubs).

| Invariant | Status | Evidence |
|---|---|---|
| Shop CAN open a repair | ✅ | `POST /api/trench-safety/assets/TB-B04-VALIDATION/repairs` with `X-Shop-Token: PVI.*` → 200 · asset flips to `Maintenance Hold` |
| Shop CAN mark repair Completed | ✅ | `POST /api/trench-safety/repairs/{id}/complete` with `X-Shop-Token: PVI.*` → 200 |
| **Repair Complete ≠ Safe To Use** | ✅ | After Shop marks Completed with `requires_reinspection=True`, `asset.operational_status == "Inspection Hold"` — NOT "Available" |
| **Shop CANNOT verify repair** | ✅ | `POST /api/trench-safety/repairs/{id}/verify` with `X-Shop-Token: PVI.*` → **401** |
| **Shop CANNOT clear a Safety Hold** | ✅ | `POST /api/trench-safety/holds/{id}/clear` with `X-Shop-Token: PVI.*` → **401** |
| Safety verification returns asset to Available | ✅ | `POST /api/trench-safety/repairs/{id}/verify` with `X-Safety-Token: PVI.*` and `reinspection_passed=true` → 200 · `asset.operational_status == "Available"` |
| Safety CAN clear Safety Hold | ✅ | `POST /api/trench-safety/holds/{id}/clear` with `X-Safety-Token: PVI.*` → 200 |

**No code changes were needed to the trench-safety routes themselves** — the doctrine was already architecturally correct. What was missing was the ability to actually *exercise* the Shop vs Safety split without minting real user accounts, which the seam now enables.

**Regression lock:** `tests/test_track_22_4b_followup_safety_b04.py` — 6 tests, per-test-hermetic asset (`TB-B04-VALIDATION`), asserts every invariant above.

---

## 5 · Full test suite result

```
tests/test_track_22_4b_followup_safety_seam.py .............................. 11 passed
tests/test_track_22_4b_followup_safety_b02.py ................................ 6 passed
tests/test_track_22_4b_followup_safety_b04.py ................................ 6 passed
tests/test_track_22_4b_followup_validation_identities.py .................... 13 passed
                                                                       36 passed in 25.91s
```

---

## 6 · Doctrine boundaries held

- ✅ **Motive routes / credentials / logic** — untouched.
- ✅ **Production RBAC** — never weakened. PVI fallback is env + feature-flag + role-match gated; production reads it as 404 by construction.
- ✅ **No new dashboards / no V2 workflows** — every fix is inline in existing files.
- ✅ **No fake green** — every invariant is proven by direct HTTP call + DB query, not by mocked components.
- ✅ **No fabrication** — the B-02 backfill never invents a company; unresolvable rows are flagged for admin review.

---

## 7 · Deferred to follow-up tracks

- **B-01 · HR request identity nulls** — needs HR PVI exercise (`Track 22.4b-followup-HR`).
- **B-06 · Driver Portal / DVIR** — needs Driver PVI exercise (`Track 22.4b-followup-Driver`).
- **B-03 · DR report_number lazy-assign race** — separate track (was originally closed in TRACK 22.4b-followup Verification Closure Pack but the read-model race case is still open).
- **B-05 · Roll-off location docs** · **B-07 · QA/QC visibility route discovery** · **B-08 · Equipment inspection route discovery** — documentation-tier.

---

## 8 · Files touched

**Backend (fixes):**
- `backend/routes/role_guard_validation_seam.py` — rewritten as pure async helper
- `backend/routes/safety_portal/_deps.py` — wired PVI fallback into 2 guards
- `backend/routes/shop_portal_deps.py` — refactored to helper
- `backend/server.py` — wired PVI fallback into `require_shop_or_admin`
- `backend/routes/safety.py` — added `_topic_required` + `_project_name_required` validators
- `backend/lib/meeting_identity.py` — added name-based MASCI employee promotion

**Backend (new):**
- `backend/scripts/backfill_b02_meeting_nulls.py` — idempotent legacy corpus repair
- `backend/tests/test_track_22_4b_followup_safety_seam.py` — 11 regression tests
- `backend/tests/test_track_22_4b_followup_safety_b02.py` — 6 regression tests
- `backend/tests/test_track_22_4b_followup_safety_b04.py` — 6 regression tests

**Memory:**
- `memory/TRACK_22_4B_DEFECT_REGISTER.csv` — B-02 + B-04 rows updated to `CLOSED` with evidence
- `memory/TRACK_22_4B_FOLLOWUP_SAFETY.md` — this file (new)
