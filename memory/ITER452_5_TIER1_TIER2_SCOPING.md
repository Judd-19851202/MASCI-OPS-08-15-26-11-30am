# OMEGA · iter452.5 · Scoping Addendum · Tier 1 / Tier 2 Separation

**Date:** 2026-06-01
**Mode:** Design / scoping addendum to `PUBLIC_GATE_ACCOUNTABILITY_REMEDIATION_PLAN.md`. No code.
**Authorization:** Operator iter452.5 direction received. Tier 1 / Tier 2 split confirmed.
**Goal:** Deliver the minimum platform capability required to guarantee corrective actions reach the responsible party. Do not expand scope beyond what is necessary to unblock iter453 and iter454.

---

## 1 · Tier 1 — Required for Phase 1A continuation

The operator's six bullets, mapped to concrete deliverables:

| # | Operator requirement | Concrete deliverable | Module |
|---|---|---|---|
| 1.1 | Submitter identity resolution | `resolve_identity(payload, project_number, workflow_kind)` returning a denormalized identity snapshot | NEW · `backend/lib/field_submitter_identity.py` |
| 1.2 | Employee directory mapping | Project-scoped employee list endpoint + frontend dropdown picker | EXTENDED · `GET /api/projects/{num}/team` (verify or add) + NEW shared React component |
| 1.3 | Project ownership resolution | Already exists — reuse `pm_routing.recipients_for_record_async()`; just denormalize the result onto the submission row at submit time | EXISTING · no new code path |
| 1.4 | Email-based revision delivery | Signed JWT (`/revise/<jwt>`) + email driver using existing `schedule_auto_email` infra + `/revise/<jwt>` render page | NEW · `lib/signed_revision_links.py` + `routes/revise.py` + `pages/Revise.jsx` |
| 1.5 | Audit trail integration | Three new event kinds in `workflow_state_events`: `revision_link_issued`, `revision_link_consumed`, `revision_saved` | EXISTING · just write rows |
| 1.6 | Reusable workflow hooks | One FastAPI dep `Depends(field_submitter_identity_gate)` + one React component `<FieldSubmitterIdentityForm/>` + one lifecycle hook `notify_field_submitter()` | NEW · packaged as the platform service |

**Tier 1 explicitly excludes** (deferred to Tier 2 per operator direction):
* SMS delivery
* Push notifications (VAPID, service-worker push, web push)
* Device binding beyond the existing localStorage `device_id` (which is captured as a string only)
* PWA install flow / iOS standalone-install onboarding UI
* Advanced preference management (channel preference UI, opt-in/out granularity, per-workflow channel mute)

---

## 2 · Tier 1 minimum field set (revised down from the 12-field plan)

The earlier plan listed 10 captured + 2 resolved fields. For Tier-1 strict minimum, drop the SMS/push-only fields. Final 8 fields:

| Field | Source | Purpose |
|---|---|---|
| `submitter_employee_id` | Required dropdown | Identity anchor (operator req 1.1, 1.2) |
| `submitter_name` | Denormalized from directory | Audit readability (1.5) |
| `submitter_email_at_submit` | Required text input · pre-filled from directory if available | Email revision delivery (1.4) |
| `submitter_consent_at` | Auto-captured | Privacy compliance |
| `submitter_consent_text_version` | Auto-captured constant | Audit |
| `project_number` | Required (already today) | Project scope (1.3) |
| `resolved_pm_email` | Auto-resolved · jobs_master | Office routing (1.3) |
| `resolved_co_pm_emails[]` | Auto-resolved · jobs_master | Office routing (1.3) |

**Dropped from Tier 1 (deferred to Tier 2):**
* `submitter_phone_at_submit` — SMS-only utility
* `submitter_device_id` — only used by push subscription binding
* `resolved_superintendent_email` — already optional; can stay opt-in but is not Tier-1-blocking

**Single hard rule:** `submitter_email_at_submit` is required (no longer "soft-required at least one of email or phone"). Field crews without email fall back to the PM-relay path (Option E in `REVISION_DELIVERY_OPTIONS.md`) — operator accepts this for Tier 1.

This single-channel posture is the key cost reduction.

---

## 3 · Tier 1 — revised effort estimate

| Phase | Original scope | Tier 1 scope | Best | Realistic | Buffered |
|---|---|---|---:|---:|---:|
| R1 — Foundations | Collection + lib + JWT + env | Same (collection + lib + JWT + env) | 3 d | 4 d | 5 d |
| R2 — Email Tier-1 dispatcher | Email driver + `/revise/<jwt>` + first wire-up | Same | 3 d | 4 d | 5 d |
| R3 — Shared UI form | Dropdown + email + phone + consent | **Reduced** to dropdown + email + consent only (no phone field, no install messaging) | **1.5 d** | **2 d** | **3 d** |
| R4 — Workflow rollout | 6 workflows × ~2 hrs each | **Reduced** to 2 workflows (OC-001 incident + OC-002 DR) since OC-003/-004 will be net-new in iter453 and inherit natively · OC-005 lands in iter454 · safety meetings + equipment pre-op deferred | **0.5 d** | **0.75 d** | **1 d** |
| R5 — Backfill policy + legacy shim | Shim + "legacy submitter" UI badge | Same | 1 d | 1.5 d | 2 d |
| R-CERT — Tier-1 certification (mirrors iter451 pattern) | NEW · pre-deploy operational cert | NEW | 1 d | 1.5 d | 2 d |
| **Tier 1 TOTAL** | | | **10 d** | **13.75 d** | **18 d** |

**Tier 1 realistic: ~2.75 weeks. Buffered: ~3.5 weeks.**

(Slight reduction vs. the earlier "14.5 days realistic" because R3 + R4 narrowed: no phone field; no SMS install UX copy; only 2 workflow wires instead of 6.)

---

## 4 · Tier 2 — Future enhancement scope

Operator's explicit Tier 2 list, mapped:

| Item | Concrete deliverable |
|---|---|
| SMS delivery | Twilio driver · phone capture field (resurrect from Tier-1 drop) · TCPA consent text · short-link service |
| Push notifications | VAPID keypair · service-worker push listener · `POST /api/push/subscribe` endpoint · pushManager subscribe wiring in frontend |
| Device binding enhancements | Server-persisted `submitter_device_id` · device-revocation endpoints · multi-device per-employee linkage |
| PWA install flows | iOS standalone-install detection · install-prompt UI · "Add to Home Screen" coaching modal · post-install push-permission flow |
| Advanced preference management | Per-employee channel preferences (email vs SMS vs push vs all) · per-workflow channel mutes · self-service preference UI · opt-out audit |

### Tier 2 effort estimate

| Phase | Scope | Best | Realistic | Buffered |
|---|---|---:|---:|---:|
| T2-R6a | SMS Tier-2: Twilio driver + phone-capture field + TCPA flow | 3 d | 4 d | 5 d |
| T2-R6b | Push Tier-3: VAPID + SW + Android delivery | 4 d | 5 d | 7 d |
| T2-R6c | iOS PWA install flow + push permission UX | 3 d | 4 d | 5 d |
| T2-R6d | Device binding enhancements | 2 d | 3 d | 4 d |
| T2-R6e | Preference management UI + opt-out audit | 3 d | 4 d | 5 d |
| **Tier 2 TOTAL (additive on top of Tier 1)** | | **15 d** | **20 d** | **26 d** |
| **Tier 1 + Tier 2 CUMULATIVE** | | **25 d** | **33.75 d** | **44 d** |

**Tier 1 + Tier 2 realistic: ~6.75 weeks. Buffered: ~9 weeks.**

---

## 5 · Side-by-side scope comparison

| | Tier 1 only | Tier 1 + Tier 2 |
|---|---|---|
| Delivery channels | Email only | Email + SMS + Web Push |
| Coverage estimate | ~70% of field submitters (email-reachable) | ~98% (email + SMS + push tiers) |
| iOS Safari behavior | Email arrives in Mail app · open `/revise/<jwt>` in Safari | Push arrives directly in PWA · deep-link to revision UI |
| Captured fields per submission | 8 (no phone, no device-id) | 10+ (phone, device-id, push subscription if granted) |
| Field-side accountability gap | Closed for the email-reachable 70% — PM-relay fallback for the rest | Closed for ~98% — PM-relay for ~2% |
| Engineering days (realistic) | ~13.75 d (~2.75 wk) | ~33.75 d (~6.75 wk) |
| Engineering days (buffered) | ~18 d (~3.5 wk) | ~44 d (~9 wk) |
| Phase 1A unblocking | ✅ Yes — sufficient | ✅ Yes — superset |
| Phase 1A required scope | This | Not required for Phase 1A |

**Operator recommendation: ship Tier 1 in iter452.5. Tier 2 fits naturally into Phase 1A.5 or Phase 2.**

---

## 6 · Earliest safe iter453 start point

The critical question: **when can iter453 BUILD safely begin without creating retrofit debt?**

The retrofit-debt risk applies if iter453 ships OC-003/OC-004 with the *old* submission model (free-text submitter), because those rows would then need to be retrofitted later when Tier 1 lands.

### Decomposition of Tier 1 dependencies for iter453

iter453 (OC-003 + OC-004) needs:

| Tier 1 deliverable | iter453 needs it because | Can iter453 start without it? |
|---|---|---|
| R1 — `field_submitter_identity.py` lib | OC-003/OC-004 forms must call `resolve_identity()` on POST | 🔴 **NO — hard blocker** |
| R1 — `field_submitter_bindings` collection | Submission rows must reference the binding row | 🔴 **NO — hard blocker** |
| R1 — `Depends(field_submitter_identity_gate)` dep | Drop-in for OC-003/OC-004 public POST routes | 🔴 **NO — hard blocker** |
| R2 — Email dispatcher + JWT + `/revise/<jwt>` page | OC-003/OC-004 kickback / CAPA-assignment must send revision emails | 🔴 **NO — hard blocker** |
| R3 — Shared `<FieldSubmitterIdentityForm/>` React component | OC-003/OC-004 New* forms embed this | 🔴 **NO — hard blocker** |
| R4 — Retrofit OC-001 incident submission | Independent of iter453 | 🟢 **YES — non-blocking** |
| R4 — Retrofit OC-002 DR submission | Independent of iter453 | 🟢 **YES — non-blocking** |
| R5 — Legacy backfill shim | Only affects pre-Tier-1 rows; iter453 rows are net-new | 🟢 **YES — non-blocking** |
| R-CERT — Tier-1 ops cert | Quality gate; iter453 should not ship before this passes | 🟡 **YES for BUILD · NO for DEPLOY** |

### The safe-start matrix

| iter453 activity | Safe to begin after | Why |
|---|---|---|
| iter453 design / scoping documents | iter452 deploy authorization (now) | Pure design — no implementation |
| iter453 BUILD of OC-003 server routes | After R1 ships (Tier 1 foundations) | Routes use the new dep |
| iter453 BUILD of OC-003 frontend forms | After R3 ships (shared React component) | Embed the component |
| iter453 BUILD of OC-003 lifecycle transitions | After R2 ships (email dispatcher) | Transition handlers call `notify_field_submitter()` |
| iter453 BUILD of OC-004 server + frontend | Same as OC-003 | Same dependencies |
| iter453 preview certification | After R-CERT (Tier-1 ops cert passes on preview) | Quality gate · ensures the shared service is stable before iter453 inherits it |
| iter453 production deploy | After Tier 1 production deploy | iter453 cannot deploy code that depends on a not-yet-deployed shared service |

### Earliest safe iter453 BUILD start

**🟢 Day 9 of iter452.5** (after R1 + R2 + R3 land in preview — roughly the end of Week 2):

```
iter452.5 Week 1  ── R1 (5 d) ──────────────┐
iter452.5 Week 2  ── R2 (5 d) ────── R3 (3 d) ─┐
                                                │
                                                ▼  ◄── earliest iter453 BUILD start
iter452.5 Week 3  ── R4 (1 d) ─── R5 (2 d) ─── R-CERT (2 d) ──┐
                                                                │
                                                                ▼  ◄── earliest iter453 preview certification
iter452.5 deploy authorization (operator decision)
                                                                │
                                                                ▼  ◄── earliest iter453 production deploy
```

(R3 can run **partially in parallel** with R2 — the React component does not need the dispatcher to be done to be built; the team can start it on Day 6 once R1 has produced the API surface for the identity gate.)

### Net effect

* **iter453 design** can begin **immediately** (today, in parallel with iter452.5 R1).
* **iter453 BUILD** can begin on **Day 9 of iter452.5** (start of Week 3 of the platform sprint).
* **iter453 preview certification** can begin on **Day 16 of iter452.5** (after Tier-1 ops cert).
* **iter453 production deploy** requires Tier 1 to be in production first.

Net: **iter453 BUILD is delayed by ~2 weeks vs. an unsafe parallel start, NOT by the full 3-week sprint length.** This is the critical-path payoff of the shared-service approach.

---

## 7 · Sequencing recommendation

```
NOW
 │
 ▼
─── iter452 production deploy authorization (operator · independent)
 │
 ▼
─── iter452.5 PLATFORM SPRINT (Tier 1 ONLY) ──────── (13.75 realistic / 18 buffered days)
       Week 1   : R1 Foundations — lib + collection + JWT + env
       Week 2   : R2 email dispatcher + `/revise/<jwt>`  ║  R3 shared form (parallel)
                                                          ║
                                                          ▼  ◄── iter453 BUILD authorized to begin
       Week 3   : R4 retrofit OC-001 + OC-002 (1 d)
                  R5 legacy shim + UI badge (2 d)
                  R-CERT Tier-1 pre-deploy ops cert (2 d)
 │
 ▼
─── iter452.5 production deploy (operator authorization)
 │
 ▼
─── iter453 BUILD continues / completes (uses Tier-1 service natively from day 1)
 │
 ▼
─── iter453 pre-deploy operational certification
 │
 ▼
─── iter453 production deploy
 │
 ▼
─── iter454 BUILD (OC-005 JHA Ledger — uses Tier-1 service natively)
 │
 ▼
─── iter454 certification + deploy
 │
 ▼
─── iter455 Phase 1A Integration Certification
       + operator authorization decision for Tier 2 platform sprint
       + Phase 1B authorization
```

---

## 8 · Risk register (delta from earlier plan)

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| R-T1.1 — Email-only delivery misses ~30% of field submitters | High | Medium | PM-relay (Option E) covers the gap; operator accepts as Tier 1 trade-off |
| R-T1.2 — Field crews mistype their email at submit time | Medium | Medium | Pre-fill from directory when available; require confirmation re-entry for new addresses; bounce-monitoring sends alert to PM |
| R-T1.3 — iter453 BUILD starts before R3 is stable | Low | High | Operator gate: iter453 BUILD authorization is conditional on R1+R2+R3 preview-ready, not just R1 |
| R-T1.4 — Legacy submissions (pre-iter452.5) show up in OC-003/004 reports without identity | Medium | Low | R5 legacy shim renders "legacy submitter — identity not enforced" badge; report tooling filters by `submitter_employee_id IS NOT NULL` |
| R-T1.5 — Tier 2 deferral creates user expectation that push/SMS will arrive | Medium | Low | Tier-1 launch copy explicitly says "email channel only for now"; preference UI says "more channels coming" |

No HIGH-severity unmitigated items.

---

## 9 · Final answer to operator's questions

| Operator question | Answer |
|---|---|
| Tier 1 only — revised estimate | **13.75 realistic days · 18 buffered days · ~2.75-3.5 weeks** |
| Tier 1 + Tier 2 — revised estimate | **33.75 realistic days · 44 buffered days · ~6.75-9 weeks** |
| Earliest point iter453 may safely begin without retrofit debt | **End of iter452.5 Week 2 (≈ Day 9 of the platform sprint)** — after R1 foundations + R2 email dispatcher + R3 shared React form are preview-ready. iter453 *design* can begin immediately, in parallel with iter452.5 Week 1. |

---

## 10 · Awaiting operator confirmation

The Tier 1 / Tier 2 split is captured. The estimates are revised. The iter453 safe-start point is identified.

Confirmable in one operator message:

> "PROCEED WITH ITER452.5 TIER 1 ONLY. ITER453 DESIGN AUTHORIZED IN PARALLEL. ITER453 BUILD AUTHORIZED FROM DAY 9 OF ITER452.5."

Or any explicit variation. No code until that authorization message lands.

🛑 **Stopped.** Design decision delivered. Awaiting authorization.
