# RFI External Access Model
## Phase V.0 · Architecture & Governance · 2026-05-27

> Tokenized read/respond pattern for CEI / Engineer / Owner / DOT / FAA
> / Utility. No full accounts initially. Audit-first. Doctrine-locked.

---

## 1 · Why Tokens, Not Accounts

DOT, FAA, CEI, and Owner staff:

- **Churn fast.** Cycling project assignments make user-provisioning lifecycle expensive.
- **Are already trained** on the "email + PDF + reply" pattern.
- **Don't want another login.** Friction here directly degrades operational response time.
- **Audit just as cleanly via tokens** when the envelope is right.

Full external accounts will arrive only after demand justifies the
identity-management overhead. Tokens come first.

---

## 2 · Token Lifecycle

```
PM issues token  →  Email delivered with link  →  External opens link
                                                          │
                                                          ▼
                                            Token validated · session bound
                                                          │
                                                          ▼
                                            View RFI · download PDF
                                                          │
                                                          ▼
                                            Optionally · submit response /
                                                         clarification request
                                                          │
                                                          ▼
                                            Audit entry per action
                                                          │
                                                          ▼
                                            Token expires (default) or
                                            revoked by PM / Admin
```

---

## 3 · Token Envelope (collection: `rfi_external_tokens`)

| Field | Type | Notes |
|---|---|---|
| `token_id` | uuid | public id surfaced in URLs |
| `token_hash` | bcrypt | the URL slug binds to this · constant-time compare |
| `rfi_id` | uuid | always required |
| `distribution_id` | uuid · nullable | when issued for a multi-party distribution |
| `recipient_name` | str | as captured by PM |
| `recipient_email` | str | required · indexed |
| `recipient_role` | enum | `cei` · `engineer` · `owner` · `dot` · `faa` · `utility` |
| `permissions` | list | subset of `read`, `respond`, `request_clarification`, `download_pdf` |
| `issued_by` | user_id | PM or Admin |
| `issued_at` | ts | UTC ISO |
| `expires_at` | ts | required · default = response_due + 30 days · clamp ≤ 90 days |
| `max_uses` | int | 0 = unlimited (default) |
| `use_count` | int | monotonic |
| `last_used_at` | ts | nullable |
| `last_used_ip` | str | nullable |
| `revoked_at` | ts | nullable |
| `revoked_by` | user_id | nullable |
| `revoke_reason` | str | required when revoked |

A token is valid only when:

- `revoked_at` is null
- `expires_at` > now
- `use_count` < `max_uses` (when `max_uses` > 0)

---

## 4 · URL Pattern

```
https://mascidocs.com/rfi/ext/<token_id>/<token_slug>
```

- `token_id` is public.
- `token_slug` is a 32-char random URL-safe value bound to `token_hash` via bcrypt.
- The combination is required. Bare `token_id` cannot be guessed past the bcrypt verification step.

External landing page must render in **≤ 2 seconds** on mobile. PDF
download must be one tap.

---

## 5 · Audit Discipline

Every external action creates an `rfi_external_audit` entry:

```json
{
  "token_id": "...",
  "rfi_id": "...",
  "action": "open" | "download_pdf" | "respond" | "clarification" | "expired_attempt" | "revoked_attempt",
  "actor_email": "...",
  "actor_role": "cei",
  "ip": "...",
  "user_agent": "...",
  "occurred_at": "..."
}
```

Audit entries are append-only. Failed / expired / revoked attempts are
recorded too — they are operationally and legally meaningful.

---

## 6 · Email Doctrine

External delivery emails:

- Sent via Resend (existing transport).
- Plain operational tone. No marketing chrome.
- Subject: `RFI #<number> · <project> · Response requested by <date>`
- Body: project · RFI summary · response due date · one CTA link · contact for questions.
- PDF attached **and** linked. Some agencies block external links; some block attachments. We provide both.
- `Reply-To` set to the PM's email so a reply-by-email still reaches a human if the recipient ignores the portal.

---

## 7 · Revocation

PM can revoke any token they issued. Admin can revoke any token. A
revoked token returns a calm operational page: *"This link is no longer
active. Contact <PM name · phone · email> to receive an updated link."*
Audit entry is created on the attempt.

---

## 8 · Rate Limiting & Abuse Discipline

- Per-IP attempt cap: 30 failed token verifications / hour.
- Per-token open cap: 200 opens / day (well above legitimate use; blocks scraping).
- Bot signatures (no JS, no cookie support) are served PDF-only and rate-limited.

---

## 9 · Privacy

External tokens reveal **only** the data needed to act on the RFI:

- Project / contract identifiers
- RFI body
- Plan / spec / pay-item references
- Attachments / photos relevant to the RFI
- Distribution list (other recipients · names + roles only · no contact details)
- PM contact information

External tokens **never** expose: other RFIs, daily reports, payroll,
safety records, employee profiles, or anything outside the assigned
RFI's data envelope.

---

## 10 · Future · Full External Accounts (deferred)

If operator demand emerges for first-class CEI / Engineer / Owner
accounts (multi-RFI dashboards, persistent identity, MFA), the path is:

1. New token `X-RFI-External-Token` with per-org scope.
2. New `rfi_external_users` collection.
3. New `/rfi/ext/login` portal.
4. Migration plan that keeps **existing one-shot tokens working**.

This is **not** in V.0–V.2 scope. Phase V.0 ships the one-shot
tokenized envelope only.

---

## 11 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Doctrine-grade
- **Implementation gate:** Envelope locks during V.2 (External RFI collaboration).
