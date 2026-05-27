# Terminology & Wording Doctrine — Phase IV-D

**Iteration:** iter437+ · Phase IV · 2026-02
**Status:** 🟡 DOCTRINE LOCKED · ENFORCEMENT INCREMENTAL
**Companion:** `/app/memory/COMMUNICATION_UNIFICATION_DOCTRINE.md`

Voice: **CALM · DIRECT · OPERATIONAL · TRUSTWORTHY · INDUSTRIAL · CONCISE · FIELD-FRIENDLY.**

---

## The seven rules

1. **No exclamation marks.** Ever. Not in errors, not in success messages, not in tooltips.
2. **No emoji as decoration.** Lucide-react icons only, and only when they communicate something the text cannot.
3. **No "AI-sounding" language.** Forbidden: "Let's", "Awesome!", "Oops!", "Looks like…", "I think…", "Great work!".
4. **No developer jargon in operator surfaces.** "Endpoint", "payload", "token expired", "500 internal server error" never appear on operator-facing screens.
5. **Operational present tense.** "Submitted", not "Has been submitted". "Approved", not "Got approved".
6. **Subject + verb + object.** "Driver assigned to truck 42", not "Truck 42 has driver assigned".
7. **One verb per action.** Pick one of {Submit, Approve, Decline, Open, Close, Send, Cancel} and use it everywhere for that action class.

---

## Canonical action verbs (use exactly these · no synonyms)

| Action | Canonical | Forbidden synonyms |
|---|---|---|
| Save a draft / persist | **Save** | Store, Record, Commit, Persist, Lock |
| Send to recipient | **Send** | Dispatch (verb), Push, Fire, Notify |
| Submit for approval | **Submit** | File, Forward, Hand off, Lodge |
| Grant approval | **Approve** | Accept, Sign off, OK, Greenlight |
| Reject | **Decline** | Reject, Refuse, Deny, Veto |
| Take to a sub-view | **Open** | View, See, Check, Look at, Inspect |
| Stop the action | **Cancel** | Abort, Quit, Back out, Never mind |
| Remove an item | **Delete** (irreversible) · **Remove** (reversible) | Erase, Wipe, Drop, Purge, Trash |
| Confirm a destructive step | **Confirm** | Yes, Sure, Go ahead, Proceed |
| Acknowledge an alert | **Dismiss** | Close, Hide, Got it, OK |

---

## Status / workflow vocabulary (single source of truth)

| State family | Canonical states |
|---|---|
| Approval lifecycle | `Draft → Submitted → Under review → Approved / Declined` |
| Operational lifecycle | `Open → In progress → Completed → Closed` |
| Incident lifecycle | `Reported → Investigating → Resolved → Closed` |
| Equipment lifecycle | `Active → In maintenance → Retired` |
| Document lifecycle | `Current → Expiring soon → Expired` |
| Session lifecycle | `Active → Idle → Inactive → Revoked` |
| Communication lifecycle | `Queued → Sent → Delivered → Bounced` |
| Backup lifecycle | `Pending → Running → Succeeded → Failed` |

These are the ONLY status labels permitted. New workflows must reuse one of these state families or formally extend it via a governance PR.

---

## Severity wording (matches the severity palette in the UX standard)

| Severity | Plain-language label | When to use |
|---|---|---|
| ok | `Healthy` / `On track` | All systems nominal |
| info | `Note` / `For reference` | Non-actionable context |
| pending | `Action needed` | Awaiting an operator |
| warning | `Attention required` | Approaching a threshold |
| overdue | `Past due` | A deadline was missed |
| critical | `Critical` | Immediate action required · field blocked |

**Never:** "URGENT!", "ASAP", "ERROR", "DANGER", "EMERGENCY". The severity color does the urgency communication — the words stay calm.

---

## Error messaging doctrine

| Pattern | Example |
|---|---|
| What happened (past tense · objective) | `Submission did not save.` |
| Why (operational reason, no jargon) | `The signal dropped during upload.` |
| What to do (single clear action) | `Tap Save again. Your entry is still here.` |
| Recovery code (small · monospace · last) | `code: net-409` |

No "Internal Server Error", "Unauthorized", "Bad Request" surfaces ever appear to an operator. Map every HTTP error to one of the four patterns above.

---

## Forbidden phrases (with replacements)

| ❌ Don't write | ✅ Write instead |
|---|---|
| "Something went wrong!" | "Did not save. Tap Save again." |
| "Please wait while we load your data…" | (just show the data when it arrives — no pre-loading copy) |
| "Are you sure you want to delete this?" | "Delete this record? This cannot be undone." |
| "User has been successfully added!" | "User added." |
| "We're sorry, but…" | (drop "we're sorry" — it sounds like a chatbot) |
| "Oops! Looks like…" | "Did not save." |
| "Click here to learn more" | "Open documentation" |
| "Submit your timesheet" | "Submit timesheet" (drop "your") |
| "Loading your dashboard…" | (just show the dashboard) |
| "Welcome back!" | "Signed in." (or nothing) |

---

## Tone calibration · 3 worked examples

**❌ Drift example (current state in some screens):**
> "Hey! 👋 Looks like your time-off request has been successfully submitted. We'll let you know as soon as your manager reviews it. Have a great day!"

**✅ Doctrine-conformant rewrite:**
> "Time-off request submitted. HR will respond in 1 business day."

---

**❌ Drift example:**
> "Oops! Something went wrong while uploading your photo. Please try again or contact support."

**✅ Doctrine-conformant rewrite:**
> "Photo did not upload. The signal dropped. Tap Retry — your photo is still on the device.
> code: r2-upload-net"

---

**❌ Drift example:**
> "Are you absolutely sure you want to permanently delete this incident report?? This action cannot be undone!"

**✅ Doctrine-conformant rewrite:**
> "Delete this incident report? This cannot be undone."
> Buttons: [Cancel] [Delete]

---

## Helper text doctrine

Help text appears below a field in `text-xs text-slate-500`. Maximum 12 words. Never explains what the field is named ("Email" doesn't need helper "Your email address" — drop it).

Acceptable helper text:

- ✅ `One per line. Wildcards allowed.`
- ✅ `Visible to PM only.`
- ✅ `Optional. Defaults to start of week.`

Unacceptable:

- ❌ `Please enter your email address so we can contact you.`
- ❌ `We will use this to keep you informed about your account.`

---

## Coaching / empty-state language

Empty states explain **what to do**, not **why it's empty**.

- ❌ "You don't have any time-off requests yet."
- ✅ "Submit a time-off request to get started."

Or, if the empty state IS the success state (e.g., "no overdue items"):

- ✅ "All caught up."

---

## Field-vs-office vocabulary

Some words mean different things in the office vs the field. Use the FIELD meaning by default since most users are foremen on iPads:

| Word | Field meaning | Office meaning |
|---|---|---|
| "Job" | The project | The role |
| "Run" | A trucking route | An execution |
| "Driver" | The operator behind the wheel | A software driver |
| "Shop" | The maintenance facility | A store |
| "Hold" | A status flag on equipment | A pause action |

If an office-meaning use is unavoidable, qualify it ("software driver", "pause execution").

---

## Bilingual contract (EN + ES)

When Spanish strings exist, they follow these rules:

- Same character count ±20% so layouts don't break.
- Same urgency language (no softer/harder Spanish word for the same English word).
- Action verbs always in the imperative: `Guardar`, `Enviar`, `Aprobar`, `Cancelar`.
- No emoji, no exclamations.

The `/admin/operational-language` page is the single source of truth for EN/ES pairs. New strings must land there before appearing in production.

---

## Enforcement

- A linter rule (custom, lives at `/app/scripts/lint_terminology.py` · to be written in implementation phase) scans `frontend/src/**/*.{jsx,tsx,js,ts}` and fails on:
  - Any string containing `!` outside code blocks
  - Any of the forbidden phrases above
  - Any action button label not in the canonical verb list
- The linter runs in `pre_deploy_check.sh` once written.

Until the linter ships, this doctrine is enforced at PR review.

---

## Verdict

🟡 **DOCTRINE LOCKED.** Existing copy will be brought into conformance incrementally. Every PR that touches a string is expected to either match the doctrine or include a justification comment if a deliberate variation is needed.
