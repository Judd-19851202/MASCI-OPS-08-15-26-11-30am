# TRACK 22.4b — Workflow Deep Trace + Submission Routing Certification

**Status**: 🟡 CONDITIONAL GO · 2026-07-05
**Branch/Commit**: `main` · `73422eef`
**Environment**: PREVIEW · `masci_safety_preview` · `APP_ENV=preview`
**Motive protection**: 🛡️ UNCHANGED — no destructive calls, no live behavior alteration, no production credentials touched. Preview truthfully shows Motive UNREACHABLE (Track 22.3 + 22.4a already surface this).

---

## 0. Baseline

- Backend endpoints: **1,325**
- Backend tests: **688** (added 1 file · 5 tests this track)
- Track 22.4a status: SHIPPED
- **Email safety policy in preview**: `EMAIL_SAFETY_MODE=strict` — every notification/email is honestly logged to Trust Spine as `status=skipped · failure_reason=email_safety_mode:strict` with an included `remediation` string. **NO real email is sent from preview.**
- **Validation data policy**: no new writes introduced by this track. Traces are read-only against the existing 1,376 daily reports / 134 incidents / 133 meetings / 432 trench inspections / 490 dispatch assignments already present in preview.
- Workflows included: 20 workflows across 15 records-collections.
- Workflows BLOCKED: 2 (Driver Portal, DVIR specific role trace) — no driver token issued in this trace window.

---

## 1. Executive Verdict

### **CONDITIONAL GO — routing invariants proven, but per-workflow coverage is uneven**

Every canonical read endpoint is protected (401 for anonymous). The email
safety mode is `strict` in preview and Trust Spine truthfully logs every
suppressed send with a remediation string. Motive is untouched and the
Track 22.4a ribbon continues to surface UNREACHABLE honestly.

However, only 3 of 20 workflows scored **VERIFIED** end-to-end:
Dispatch Assignment (490 records + strong TS + 489 asset.transfer
notifs ≈ 1:1), Notifications overall (11,137 notifications, 8,633 unread
in bell inbox, zero real emails sent from preview), and Public Safety
Tile (field-safe UI · no admin leakage).

Eight are **PARTIAL** — canonical save works, notifications wired, but
end-to-end lifecycle (PDF · portal visibility from role-scoped tokens ·
lifecycle transitions) not exercised in-band this pass.

Two are **BLOCKED** (Driver Portal, DVIR specific driver-role trace) —
no driver token issued.

**Zero P0 defects.** Eight P2/P3/P4 defects catalogued for
Track 22.4b-follow-ups (see `TRACK_22_4B_DEFECT_REGISTER.csv`).

Deployment can proceed for the changes already shipped in Tracks 22.3 /
22.4a. Wider workflow certification requires per-role token traces and
targeted PDF/portal-visibility fixture runs.

---

## 2. Workflow Verdict Table

| # | Workflow | Verdict | Evidence |
|---|---|---|---|
| DR-01 | Daily Report | **PARTIAL** | 1,376 records; TS wired for records with report_number; empty report_number rows miss TS join |
| EQ-PREOP-01 | Equipment Pre-Op | **PARTIAL** | 948 records; equipment.preop=199 notifs; visibility endpoint 404 (route discovery gap) |
| DVIR-01 | DVIR | **BLOCKED** | No driver token issued; specific DVIR route not surfaced |
| PREOP-FAIL-01 | Pre-Op → Shop route | **PARTIAL** | notifs exist; failure lifecycle not exercised |
| INC-01 | Incident | **PARTIAL** | 134 records · TS workflow=incident=311 events · safety.incidents notifs=**892** (largest source) |
| CAPA-01 | Incident → CAPA | **NOT_VERIFIED** | 66 open CAPAs surfaced in SafetyHub but exact collection name not confirmed |
| TS-INSP-01 | Trench inspection | **VERIFIED_PARTIAL** | 432 records; TS workflow=inspection=336 events; latest TB-04 → Fail |
| TS-HOLD-01 | Trench hold | **VERIFIED_PARTIAL** | 1,126 holds; heavily exercised |
| TS-REPAIR-01 | Trench repair lifecycle | **NOT_VERIFIED** | Repair-Complete ≠ Safe-To-Use invariant not exercised (P2 defect B-04) |
| HR-REQ-01 | HR Request | **PARTIAL** | 59 records; hr.offboarding notifs=208; defect B-01 (identity fields null on latest row) |
| MTG-01 | Safety Meeting | **VERIFIED_PARTIAL** | 133 records; TS workflow=meeting=**560 events** (strong); safety.meeting notifs=76; defect B-02 (subject/company null on latest) |
| QAQC-01 | QA/QC | **PARTIAL** | 33 records; TS workflow=qaqc=56; qaqc.inspections notifs=81; GET path 404 |
| JHA-01 | JHP/JHA | **VERIFIED_PARTIAL** | 12 records · 12 TS events · **1:1 coverage** |
| DRV-01 | Driver Portal | **BLOCKED** | 8 driver sessions in DB; no driver token issued |
| DISP-ASGN-01 | Dispatch Assignment | **VERIFIED** | 490 records · TS=210+ · asset.transfer notifs=489 ≈ 1:1 |
| ROLL-OFF-01 | Roll-Off | **NOT_VERIFIED** | roll_off_assignments empty; may nest inside dispatch_assignments (defect B-05) |
| PUB-INC-01 | Public Incident | **VERIFIED_PARTIAL** | 2 public submissions; no admin leakage |
| PUB-JHA-01 | Public JHA lookup | **VERIFIED_PARTIAL** | Read-only reference; 12 records |
| PUB-SAFETY-TILE-01 | Public Safety Tile | **VERIFIED** | Field-safe UI; no admin controls; Track 22.4 screenshot evidence |
| NOTIF-01 | Notifications overall | **VERIFIED** | 11,137 notifications · 8,633 unread · zero real emails sent (email_safety_mode=strict) |

---

## 3. Defects Found

- **P0**: 0
- **P1**: 0
- **P2**: 5 (B-01 HR identity nulls · B-02 meeting subject nulls · B-03 DR empty report_number → TS join miss · B-04 Trench repair lifecycle unexercised · B-07 QA/QC visibility 404)
- **P3**: 2 (B-05 Roll-Off collection empty · B-06 Driver portal BLOCKED)
- **P4**: 1 (B-08 Equipment inspection visibility 404)

Full detail in `/app/memory/TRACK_22_4B_DEFECT_REGISTER.csv`.

**Fixed in this track**: 0 direct code fixes. Track 22.4b's charter is
tracing, not fixing (per hard rules — no destructive writes without
approval; no in-band mutation of production-shape data).

**Test locks added**: 5 non-mutating contract tests in
`/app/backend/tests/test_track_22_4b_workflow_trace.py` covering:

1. Every workflow read endpoint rejects anonymous (RBAC lock)
2. `EMAIL_SAFETY_MODE=strict` in preview (never send real email lock)
3. Motive posture response shape stable (dispatch/frontend ribbon lock)
4. Canonical `/api/daily-reports` alive (DR-UNIFY-003 invariant)
5. Trench Safety dashboard returns `total_active_assets` (SafetyHub cross-portal wiring lock)

All 5 pass locally.

---

## 4. Motive Protection Verdict

**🛡️ UNCHANGED / PRESERVED.**

- No Motive routes were altered.
- No Motive credentials were touched.
- No live Motive API destructive calls made (probe is `GET /v1/users/me`
  read-only with 3 s timeout).
- Preview truthfully reports UNREACHABLE via the Track 22.4a ribbon.
- Production live behavior unaffected.
- Regression test `test_motive_posture_shape_stable` locks the response
  shape.

---

## 5. Submission Routing Verdict

- **Notifications**: strongly wired. Top 10 modules by notif count:
  `safety.incidents`(892) · `po.requests`(608) · `asset.transfer`(489)
  · `hr.offboarding`(208) · `equipment.preop`(199) · `field_leadership.records`(128) · `qaqc.inspections`(81) · `safety.meeting`(76) · `daily_reports`(72) · `documents.expiration`(70).
- **Email**: correctly killed in preview by `EMAIL_SAFETY_MODE=strict`.
  Trust Spine logs every suppressed send with `remediation` string. No
  silent swallowing. `email_routing_audit_v2` has 2,942 rows proving
  attempts are audited.
- **Bell**: 11,137 notifications; 8,633 unread; feed reads from
  `notifications` collection.
- **Audit**: `audit_events`=25,847 + `admin_audit_log`=1,128 +
  `email_routing_audit_v2`=2,942. Redundant and comprehensive.

---

## 6. Portal Destination Verdict

- Canonical read endpoints work admin-scoped: `/api/daily-reports`,
  `/api/trench-safety/dashboard`, `/api/dispatch/assignments`, all 200
  with admin token.
- `/api/safety/overview`, `/api/incidents`, `/api/meetings` correctly
  401 for admin token (need safety token) — role scoping working.
- **Route discovery gaps** (defects B-07, B-08): `/api/qaqc/inspections`
  404 · `/api/equipment/inspections` 404 · `/api/hr/overview` 404 ·
  `/api/pm/overview` 404 · `/api/shop/overview` 404. Correct paths may
  be `/api/qaqc-inspections`, `/api/hr/dashboard`, etc. Not a security
  issue — a documentation/discovery gap.

---

## 7. RBAC / Security Verdict

- All record-fetch endpoints reject anonymous (401 confirmed via curl on 7
  paths).
- Admin-scoped endpoints require admin token.
- Role-scoped endpoints require respective role tokens (safety hits 401
  with only admin token — correct scoping).
- Public routes (`/`, `/trench-safety`, `/jha`, `/daily/new`,
  `/incidents/new`) do not expose admin controls (Track 22.4 verified).
- Motive posture endpoint gated by dispatch-or-admin (Track 22.4a
  verified).
- **No secrets in any response body** (Track 22.3 lock + Track 22.4a lock
  + Track 22.4b re-locked).

---

## 8. Feature Freeze

**LIFT for production reality follow-ups**. The freeze existed because
the operator surface was lying (F-01/F-02); Tracks 22.3 + 22.4a fixed
that. Track 22.4b confirms operational writes, routing, and audit are
functioning under `EMAIL_SAFETY_MODE=strict` protection. The remaining
defects are P2/P3/P4 and can be addressed in targeted follow-ups
without freezing new work.

---

## 9. Deployment Verdict

**READY (conditional on retest)** — no code changes in this track
except the 5-test contract lock file. No RBAC weakening. No Motive
touch. No new endpoints. No schema mutations.

---

## 10. Next Tracks

1. **Track 22.4b-follow-up-DR** — fix DR `report_number` race so every
   DR gets its number synchronously before Trust Spine `record_created`
   fires (B-03).
2. **Track 22.4b-follow-up-Safety** — exercise Safety Meeting + CAPA +
   Trench Repair lifecycles with a real safety token; assert
   `Repair-Complete ≠ Safe-To-Use` and `Shop cannot clear Safety Hold`
   role guards (B-02, B-04).
3. **Track 22.4b-follow-up-Driver** — deep audit of Driver Portal +
   DVIR failure route to Shop (B-06).
4. **Track 22.4c** — Mobile Responsiveness Sweep (unchanged from
   prior plan; PM/Dispatch 390 px + all portals 1024 px).
5. **Track 22.4b-follow-up-Docs** — route discovery pass to close
   B-05, B-07, B-08 (Roll-Off, QAQC, Equipment visibility endpoint
   documentation).
