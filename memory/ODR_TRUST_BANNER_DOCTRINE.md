# ODR Trust Banner Doctrine

_Phase V.1 · M0.3 · 2026-05-29 · CONTINUITY MEMORY · TRUST BY DEFAULT._

## Purpose

Increase **operational trust without increasing cognitive load.**

Every ODR surface — foreman entry, FL center, PM panel, public
viewer, detail view — quietly displays one calm reminder:

> **Operational Record · Audit history protected · Amendments tracked.**

That single line tells every viewer:

1. This is a record, not a casual form.
2. What you write is preserved and auditable.
3. Changes are visible — not destructible.

It does NOT:

- shout legal language
- threaten with consequences
- use red, yellow, or any warning colour
- block any action
- collect or display any per-actor data
- imply surveillance

## Rules

| Rule | Implementation |
|---|---|
| Single calm line | One `<div role="note">` with slate-50 background |
| Neutral palette only | `border-slate-200 · bg-slate-50 · text-slate-500` |
| No warning colours | NEVER red / amber / rose / orange |
| No legal copy | NO "by submitting you agree", NO statutes, NO threats |
| No banners screaming | small text · short height · no animation |
| Dismissible per session | `sessionStorage` key, NOT persistent localStorage |
| One-line max | Title-case verbs, no marketing tone |
| Same copy on every surface | Reinforces identity — never localized variants for "audit visibility" elsewhere |

## Component

`/app/frontend/src/components/odr/OdrTrustBanner.jsx`

Public surface (no portal token required) STILL renders the banner —
DOT / FAA / CEI viewers should see the same trust language.

## Doctrine boundary

The banner is the **only** UI element that may speak about audit /
trust / record integrity in passive tone. Surfaces that NEED to
inform an operator about a hard-stop or amendment outcome must use
the active in-context surfaces (readiness block, amendment confirm
modal). Mixing the two voices dilutes the trust signal.

## Why this matters

Field foremen who feel watched stop writing the truth. Field foremen
who never see the audit reminder forget that records matter. The
quiet middle ground is the design objective — a banner that says
"this is preserved" without saying "you are being watched."

## Test surface

- `data-testid="odr-trust-banner"` — assertion target for playwright
  and pytest DOM probes.
- `data-testid="odr-trust-banner-dismiss"` — dismissal target.
- Frontend lint runs against the component on every commit
  (eslint clean).

## Verdict

🟢 **TRUST BANNER DOCTRINE LOCKED.** One line. One palette. One copy.
One purpose: operator trust without cognitive load.
