# OMEGA · Revision Delivery Options

**Date:** 2026-06-01
**Mode:** Research / design only. No code.
**Scope:** How can a public-gate submitter be given a secure, time-bound path back to their own submission for correction?

---

## 1 · The problem

A field user submits a Daily Report through `/daily/submit`. Office reviews, finds an issue, kicks it back. **Today**, the field user has no platform mechanism to be told what to fix or to re-open the submission. They submit a second DR (duplicate) or wait to be phoned.

A secure revision-delivery channel must:

1. Identify the original submitter (or designated proxy) cryptographically — not by free text.
2. Carry the kickback reason in a way that does not require the user to log in.
3. Time-bound the revision window (expiry after the correction deadline).
4. Single-use or rate-limited to prevent token-replay.
5. Survive a device change (token can be regenerated and redelivered).
6. Audit every read and every revision attempt.

---

## 2 · Option matrix

| Option | Delivery channel | Identity tie | Lifetime | iOS Safari friendly? | PII exposure | Implementation cost |
|---|---|---|---|---|---|---|
| **A. Signed URL via Email** | SES / SendGrid | Email at submit | 7 days | ✅ Yes | Email is captured | Lowest |
| **B. Signed URL via SMS** | Twilio | Phone at submit | 24-72 hrs | ✅ Yes | Phone is captured | Low |
| **C. Push notification w/ deep link** | Web Push (VAPID) | PushSubscription endpoint | Push lifetime | 🟡 iOS only inside installed PWA | Subscription endpoint | High |
| **D. QR code printed on the trailer with rotating daily code** | Wall-printed | Crew-bound; not person-bound | 24 hrs | ✅ | Lowest | Medium |
| **E. Magic-link via PM intermediary** | PM emails the link to the field user | Trust the PM | Bounded by PM diligence | ✅ | None new | Low — manual |
| **F. Authenticated portal account for every submitter** | Existing portal | Account credentials | Indefinite | ✅ | High (full user record) | Highest — onboarding burden |
| **G. Status check by submission-doc-id only (no auth)** | None — the user remembers the DR-2026-NNNNN | Identity not verified | Indefinite | ✅ | None | Lowest — but UNSAFE |

---

## 3 · Per-option deep-dive

### Option A · Signed URL via Email — RECOMMENDED FIRST TIER

**Flow:**

1. Field user fills DR. Form requires "Email for revision notices (optional but recommended)".
2. On submit, server generates a JWT `{sub: submission_id, exp: +7d, scope: "revise:dr"}`, signs with `REVISION_LINK_SECRET`.
3. URL: `https://mascidocs.com/revise/<jwt>`. Stored in `field_submitter_bindings.channels[]` for future re-issuance.
4. On kickback, `emit_notification` triggers `email_driver.send_revision(email, link, kickback_reason)`.
5. Field user clicks link → server validates JWT → renders a scoped revision UI (read-only DR + reason banner + edit form for the kicked-back content + resubmit button).
6. On resubmit, the JWT is consumed-marked OR rotates to a new JWT for the next kickback round.

**Pros:**
* Works on every device, every browser, no install required.
* Lowest cost.
* Email is a familiar surface for field crews and supervisors.

**Cons:**
* Field crews may not check email in real-time. Latency.
* Email bounces silently if the address was mistyped.
* Email is captured per-submission — privacy footprint grows.

**Privacy controls:**
* JWT must NOT include the email — only the submission_id.
* Email address stored in `field_submitter_bindings` with 90-day TTL.
* `REVISION_LINK_SECRET` rotated annually; old tokens fail validation.

### Option B · Signed URL via SMS — RECOMMENDED SECOND TIER

**Flow:**

1. Same as Option A but the form captures a US phone instead of email.
2. SMS body: `MASCI Daily Report DR-2026-00123 returned for correction. Reason: «short». Open: https://mascid.cc/r/<short>`
3. Short link redirects to `/revise/<jwt>`.

**Pros:**
* Sub-minute latency.
* Field crews carry phones; many do not regularly read email.
* No app install required (open the SMS link in Safari).

**Cons:**
* Twilio integration cost (~$0.0079 per outbound SMS US).
* TCPA compliance required — consent must be captured and revocable.
* 160-char payload limit forces a short-link shortener.

### Option C · Web Push with Deep Link — TIER 3

**Flow:**

1. Field user is prompted to install MASCI Docs as a PWA from the home screen of the first device they submit from.
2. After install, on first submit, `Notification.requestPermission()` runs.
3. Subscription endpoint stored in `push_subscriptions` and bound to the submission via `field_submitter_bindings`.
4. On kickback, push payload includes the signed URL.
5. User taps the push notification → opens directly into the standalone PWA at the revision UI.

**Pros:**
* Lowest friction once installed.
* Push payload can carry a click-through URL.
* No per-message cost.

**Cons:**
* iOS requires PWA install — significant first-visit UX overhead.
* Permission must be granted from inside the installed app on iOS.
* Shared-tablet scenario can deliver push to the wrong human.

### Option D · Daily Rotating QR — STRATEGIC, NOT URGENT

**Flow:**

1. A printed QR poster on the job-site trailer wall shows today's date + a daily-rotating short URL.
2. The URL routes to a `/today` page that surfaces the open kickbacks for that project's recent submissions.
3. No per-person identity — anyone with physical access to the trailer can see the kickbacks.

**Pros:**
* Zero per-user infrastructure.
* Crews already check the trailer wall.

**Cons:**
* Not person-specific.
* Requires daily print-and-pin discipline.
* Doesn't satisfy "responsible party reached" — satisfies "crew aware".

### Option E · Magic-Link via PM Intermediary — FALLBACK

**Flow:**

1. PM receives the standard kickback email (which already works).
2. Email includes a magic link the PM can forward to the field user.
3. PM is the trust anchor.

**Pros:**
* Works today with minor backend change (generate the link, embed it in the existing PM email template).
* Lowest engineering cost.

**Cons:**
* Latency depends on PM diligence.
* Not auditable that the field user actually got the message.

### Option F · Portal Account for Every Field User — REJECTED

* Onboarding burden too high.
* Defeats the operator-stated public-gate model.
* Listed only for completeness.

### Option G · Status Check by Submission Doc-ID — REJECTED

* No identity verification.
* Anyone who knows `DR-2026-NNNNN` can impersonate.
* Listed only as a cautionary example.

---

## 4 · Recommended tiered strategy

```
PRIMARY     →  Option A (Signed URL via Email)        target: ~70% of submitters
                ↓ if email missing or bounces
SECONDARY   →  Option B (Signed URL via SMS)          target: ~25%
                ↓ if SMS missing or carrier-rejected
TERTIARY    →  Option C (Push if PWA installed)        target: ~3%
                ↓ if push fails
FALLBACK    →  Option E (PM intermediary)              remaining ~2%
```

Each tier is independently shippable. The operator can scope **only Tier 1 (email) for an iter452.5 follow-on sprint**, defer Tiers 2-3 to a later phase, and still close the most-impactful 70% of the field-side accountability gap.

---

## 5 · Token contract (research)

A revision JWT must be self-contained and stateless to avoid a database round-trip on every link click:

```
header  : { alg: "HS256", typ: "JWT", kid: "rev-2026-q3" }
payload : {
  sub:    "<submission_id>",
  wf:     "daily_report" | "qaqc_inspection" | ...,
  scope:  "revise" | "view-only",
  iat:    1717200000,
  exp:    1717804800,                 // 7d
  jti:    "<random-uuid>",            // for replay-tracking in audit
  ver:    1,
  iss:    "mascidocs.com"
}
signature: HMAC-SHA256(secret, header.payload)
```

* `kid` allows secret rotation without invalidating old tokens prematurely.
* `jti` is logged on every read so replay attempts are visible.
* `scope` enables view-only links (e.g. to share a CAPA with a sub-rep) distinct from edit-able revision links.

---

## 6 · Audit trail addition

Every revision link issuance, click, and revision write must be appended to `workflow_state_events` with a new `to_state` value or a new `event_kind`:

| Event | Suggested encoding |
|---|---|
| Link issued | `kind=revision_link_issued · channel=email\|sms\|push · jti=<...>` |
| Link clicked | `kind=revision_link_consumed · jti=<...>` |
| Revision saved | normal state transition + `revision_via=<jti>` |
| Link expired without use | `kind=revision_link_expired · jti=<...>` |
| Replay attempt rejected | `kind=revision_link_replay_blocked · jti=<...>` |

Append-only, queryable via existing `workflow_state_events` indexes.

---

## 7 · Verdict

🟢 **Multiple viable options. Operator-driven decision required on tiering.**

* **Lowest-cost first move:** Option A (signed-email revision links). ~1 week engineering once authorized.
* **Highest-coverage stack:** A + B + E. ~3 weeks total.
* **Premium tier:** Add Option C (push) — see `PUSH_NOTIFICATION_FEASIBILITY_REPORT.md`.

Awaiting operator authorization. No code in this batch.
