# OMEGA · Push Notification Feasibility Report

**Date:** 2026-06-01
**Mode:** Research and design only. No code. No fixes.
**Scope:** Can MASCI Docs support required push-notification registration for public-gate mobile workflows?

---

## 1 · Current state (forensic)

| Area | Evidence | Verdict |
|---|---|---|
| `device_id` capture | `/app/frontend/src/lib/crewMemory.js` — localStorage-only, never synced to server. No `device_id` field on `daily_reports`, `qaqc_inspections`, or any other workflow row. | 🔴 Not captured server-side |
| Browser push subscriptions | Collections `push_subscriptions`, `web_push_subs`, `devices`, `device_registrations` all return **0 rows** on the live preview database | 🔴 No infrastructure |
| VAPID key configuration | `backend/.env` has no `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `WEBPUSH_*` variables | 🔴 Not configured |
| Push library | No `pywebpush`, `pyfcm`, or equivalent in the import graph (verified by grep) | 🔴 Not installed |
| Service worker | `/app/frontend/public/sw-thumbs.js` — scope-limited to `/api/job-photos/*/thumb` (read SW header comment lines 4-25). No push event listener. No subscription registration. | 🟡 Single SW exists but is photo-only |
| Web app manifest | `/app/frontend/public/site.webmanifest` — `display: "standalone"`, full icon set including maskable + apple-touch-icon-167, theme_color `#0f172a`. Manifest IS properly configured. | 🟢 Manifest-ready |
| HTTPS | Production (`mascidocs.com`) and preview (`*.preview.emergentagent.com`) both serve over TLS | 🟢 |
| `apple-mobile-web-app-capable` | `index.html:22-24` — `<meta name="apple-mobile-web-app-capable" content="yes">` + status bar style + title | 🟢 iOS PWA-ready |
| Notification permission UX | No `Notification.requestPermission()` call in any frontend file (grep confirmed) | 🔴 Not implemented |
| Notifications schema | `notifications` collection schema already carries a `delivery = {internal, email, push, sms}` envelope — push and sms keys exist but are always `false` today | 🟢 Forward-compatible schema |

**Summary of current state:** The platform is *infrastructure-prepared* (manifest, HTTPS, schema fields) but *delivery-unimplemented* (no VAPID, no service-worker push listener, no permission prompt, no subscription endpoint, no dispatcher).

---

## 2 · Per-question answers

### Q1 — Current `device_id` capture

`device_id` is a **client-local concept only**. `crewMemory.js` may generate a device-scoped storage key, but nothing is written to the server. The submitter row carries no `device_id` field.

### Q2 — Are browser push subscriptions currently collected?

**No.** Zero rows in any of the candidate collections. No backend route accepts a subscription. No frontend code calls `pushManager.subscribe()`.

### Q3 — Does iOS / iPad Safari support the needed push workflow in this deployment model?

**Conditional yes.** Per Apple's web push documentation and current public reporting:

| Condition | Status for MASCI Docs |
|---|---|
| iOS / iPadOS 16.4+ | Must be enforced — older iPads in the field are common |
| Served over HTTPS | ✅ |
| Valid web app manifest with `display: standalone` | ✅ |
| User **adds the app to the home screen** | ❌ Not enforced — most field users open via shared Safari link |
| User launches from the home screen icon (standalone context) | ❌ Same as above |
| User explicitly grants notification permission **from inside the installed PWA** | Not implemented |
| EU users (DMA / iOS 17.4+) | Web push from PWA may degrade to Safari-tab mode in EU regions and not work — MASCI is currently US-only, so not a near-term issue |

**Critical iOS-specific limitation:** Web push on iOS **does not work in a regular Safari tab** — only inside a home-screen-installed PWA. This means any "push-required" public-gate UX must include a mandatory home-screen-install step before submit. That is a significant UX shift.

**Android Chrome:** No standalone-install requirement. Web push works in regular browser tabs as long as the user grants permission.

### Q4 — Can public-gate forms safely bind `device_id + supervisor_name + employee_directory_email + push_subscription`?

**Technically yes — with caveats.**

| Binding | Feasible? | Constraint |
|---|---|---|
| `device_id` (client-generated UUID, stored in localStorage) | ✅ | Cleared if user clears site data; not authoritative |
| `supervisor_name` from employee directory dropdown | ✅ | Requires directory enrichment (~260 of 261 currently have no email) |
| `employee_directory_email` | ✅ | Requires `employees.email` to be populated and validated |
| `push_subscription` (the `PushSubscription.toJSON()` envelope) | ✅ | iOS PWA-install requirement + Notification permission grant required |

A safe binding row could look like:

```
{
  "submission_id": "<dr_uuid>",
  "device_id": "<localStorage uuid>",
  "employee_id": "<dropdown selection>",
  "employee_email": "<from directory>",
  "push_subscription": { "endpoint": "...", "keys": { "p256dh": "...", "auth": "..." } },
  "created_at": "..."
}
```

This is feasible to design. It is NOT implemented today.

### Q5 — Can notification permission be required *before* submission?

**Technically yes, with significant UX cost.**

* `Notification.requestPermission()` only resolves with `"granted"` if the user explicitly clicks Allow on the browser prompt.
* On iOS, the prompt does not appear at all unless the user is in a standalone PWA context.
* Making submission *block* on permission grant means a field user who declined cannot submit a Daily Report — this is a hard accountability trade-off the operator must weigh: do you refuse to accept a submission from a denying user, or accept it and accept the gap?

**Operator-level decision required:** This is not a technical question; it's a policy question.

### Q6 — Fallback path if user denies permission

The platform must define a graceful degradation tier:

| Tier | If user denies push | Fallback delivery |
|---|---|---|
| Tier 1 | Push declined | SMS (requires phone capture + Twilio integration) |
| Tier 2 | SMS declined / unavailable | Email (requires email capture + employee directory enrichment) |
| Tier 3 | Email declined / unavailable | In-app bell on next authenticated portal visit |
| Tier 4 | None of the above | PM is notified; office contacts field via off-platform channel |

Today only Tier 4 is implemented.

### Q7 — Can secure revision links be sent by push / email / SMS?

**Push** — Yes. A signed, single-use, scoped URL (e.g. `/revise/<jwt>?dr=<id>`) can be embedded in the push payload. The PushSubscription's `endpoint` is opaque from the browser side; payload signing is handled server-side with VAPID.

**Email** — Yes. Trivially. Same signed URL via SMTP / SES / SendGrid.

**SMS** — Yes. Shortened link via a bit.ly-style shortener (Twilio bundles one). Payload size ≤ 160 chars is the SMS constraint.

All three can carry the same signed revision token. The **signing infrastructure does not exist today** — there is no JWT-issuer for revision links, no signed-URL middleware, and no `/revise` endpoint.

### Q8 — Privacy / security concerns

| Concern | Severity | Notes |
|---|---|---|
| Push subscription endpoints are PII-adjacent | Medium | Endpoint reveals which push service (FCM/Apple) → device platform. Should be encrypted at rest, never logged. |
| Forcing permission before submit creates coercion concerns | Medium | Some jurisdictions require revocable consent for push. |
| Linking `device_id + employee_email + ip + user_agent` creates a fingerprint | Medium | If captured, retention policy must be defined; user_agent + ip already in `audit_events` so this is incremental. |
| iOS PWA install instruction can be socially engineered (phishing) | Low | Mitigated if install is initiated from a known QR code at the trailer. |
| Field user's device may be a shared / supervisor tablet | High | Push delivered to a shared tablet does not reach the specific person — accountability assumption may fail. |
| Revoked employees can still receive push if subscription not invalidated | Medium | Must add an offboarding hook to delete `push_subscriptions` on employee deactivation. |
| GDPR / CCPA — push subscription is personal data | Medium | Operator's compliance posture must include push-subscription deletion on right-to-be-forgotten request. |

### Q9 — Which workflows should this apply to?

**Recommended priority order based on the forensic findings:**

| Workflow | Push-priority | Why |
|---|---|---|
| Daily Reports (OC-002) | 🟢 P1 | Highest kickback volume; primary submitter accountability gap |
| QA/QC Follow-Up (OC-003) | 🟢 P1 | CAPA delivery requires reaching sub-rep or assigned dept |
| JHA Acknowledgement (OC-005) | 🟡 P2 | Acknowledgement is captured at sign-time; revision is rare. Push adds value for daily-meeting reminders, not for OC-005 closure. |
| Safety Meetings | 🟡 P2 | Same logic as JHA |
| Equipment Pre-Op Inspections | 🟢 P1 | Defect-found path needs Shop Manager + foreman both. |
| Site Inspection Follow-Up (OC-004) | 🟢 P1 | Same pattern as QA/QC |
| Incident Reports | 🟡 P2 | OC-001 lifecycle already reaches Safety/Admin/Super-Admin via in-app bell; field-side reach is less critical here than office-side reach. |

---

## 3 · Feasibility verdict

🟡 **TECHNICALLY FEASIBLE · OPERATIONALLY EXPENSIVE.**

* **Android Chrome / desktop Chrome / desktop Edge:** Feasible with low friction. VAPID + service worker + permission prompt + subscription endpoint. ~1 sprint of work.

* **iOS Safari (iPad / iPhone):** Feasible BUT requires:
  1. Mandatory home-screen install before push works
  2. iOS 16.4+ enforcement
  3. Standalone-launch context detection
  4. EU-region carve-out (if/when MASCI expands)
  5. User onboarding to install + grant permission — meaningful UX redesign for the first-visit field user

* **Backend:** Feasible. VAPID keys generated, `pywebpush` added, subscription endpoint added (`POST /api/push/subscribe`), dispatcher integrated into existing `emit_notification` to flip `delivery.push = true` and actually deliver.

* **Fallback ladder (SMS/email):** Feasible BUT each tier is its own integration project (Twilio, SES). Each tier requires its own contact-information capture and consent flow.

**Sprint estimate (high-level, NOT a commitment):**

| Phase | Scope | Estimate |
|---|---|---|
| P-A | VAPID + service-worker push handler + subscription endpoint + Android-only delivery | ~1.5 weeks |
| P-B | iOS standalone-install onboarding UI + iOS-conditional delivery | ~1 week |
| P-C | Subscription binding to submission rows + revocation hooks + retention policy | ~1 week |
| P-D | Fallback SMS via Twilio | ~1 week |
| P-E | Fallback email tier integration into the signed revision-link mechanism | ~3 days |
| P-F | Privacy/GDPR · offboarding hook · right-to-be-forgotten | ~3 days |

**Total realistic sprint cost: ~5 weeks of focused engineering.**

This is roughly equivalent to one full iter453+iter454 build. Operator must decide whether push delivery is in-Phase-1A scope or a follow-on phase.

---

## 4 · Recommendation (operator decision)

This work is **out of the current Phase 1A scope** as currently authorized. The operator's iter451-455 directive does not include push infrastructure.

**Three viable paths:**

* **Path X — Defer push to a Phase 1A.5 sprint.** Complete iter453-455 first to ship the lifecycle infrastructure. Then bolt push delivery on top of the already-shipped `delivery.{internal,email,push,sms}` envelope.

* **Path Y — Insert a pre-iter453 sprint for push + revision-link infrastructure.** Adds ~5 weeks before OC-003/004/005 build resumes.

* **Path Z — Accept email-only fallback for now.** Skip push entirely. Use the email channel (which already partially exists via `schedule_auto_email` + PM routing) and add a signed-revision-link mechanism scoped narrowly to email-bound submissions. Lower cost, smaller coverage.

No code. Research only. Awaiting operator authorization for one of X / Y / Z.
