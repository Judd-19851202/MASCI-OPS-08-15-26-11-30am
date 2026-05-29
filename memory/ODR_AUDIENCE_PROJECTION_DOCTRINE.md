# M0.35 · ODR Audience Projection Doctrine

_Phase V.1 · 2026-05-29 · LOCKED · pre-M1._

## The simple rule

> **The user chooses the audience. The system chooses the projection.**

PMs do NOT pick redaction options. Foremen do NOT pick redaction
options. Admins do NOT pick redaction options. The platform asks
ONE question — *"Who is this for?"* — and applies the audience-safe
projection automatically.

## Audience profiles (4 categories · 11 entry points)

| Category | Entry profile | Mapped projection |
|---|---|---|
| Internal | `internal_foreman` | foreman |
| Internal | `internal_superintendent` | superintendent |
| Internal | `internal_pm` | pm |
| Internal | `internal_operations` | executive |
| External | `external_owner` | external |
| External | `external_cei` | external |
| External | `external_dot` | external |
| External | `external_faa` | external |
| External | `external_consultant` | external |
| Executive | `executive_leadership` | executive |
| Legal / Audit | `legal_audit` | superintendent (full internal record · admin-only) |

The mapping lives in `routes/odr/pdf.py::AUDIENCE_PROFILES` and is
re-exported in this doctrine. **No new audience profile may be
added without updating this doctrine + the audit log.**

## Public link rule (immutable)

Every public link issued by `POST /api/odr/{id}/link` is **automatically
audience-locked to `external`**. The `audience_profile_locked="external"`
field is written on the registry row and surfaced on every read.

```
odr_public_links {
  ...
  audience_profile_locked: "external"
  projection_audience: "external"
  ...
}
```

The public resolver `GET /api/odr/public/{doc_id}` already strips
all internal fields per the existing continuity engine; the
audience lock is the parallel doctrine commitment that the public
URL never carries an internal projection — even if a developer adds
a new internal field tomorrow.

## What External NEVER receives

Per operator directive (locked):

- ❌ Coaching prompts (any prompt_key)
- ❌ Readiness signals (score · hard_stops · missing_required · coaching_prompts)
- ❌ Internal comments
- ❌ Internal chronology notes
- ❌ Risk scoring of any kind
- ❌ Amendment rationale (the `reason` field on `odr_amendments`)
- ❌ Internal guidance / FL Training references
- ❌ Future planning references (tomorrow's `concerns`, internal RFI hints)

These are stripped at the projection layer in
`routes/odr/pdf.py::_project_for_audience("external")` and at the
public envelope builder in `routes/odr/continuity.py`. Probes
defend the boundary.

## What every PDF render writes (audit lock)

```
odr_pdf_renders {
  render_id            uuid4
  odr_id               uuid4
  doc_id               ODR-YYYY-NNNNN
  audience             foreman | superintendent | pm | executive | external
  audience_profile     internal_pm | external_cei | … | (null if direct audience)
  sha256               64-char hex (deterministic per (envelope, audience))
  actor_uid            email/uid of generator
  actor_portal         admin | pm | fl | …
  at_utc               Z-suffixed UTC ISO
  byte_size            int
}
```

Every render writes one row. Append-only. Indexed by
`(odr_id, at_utc)` and `(audience, at_utc)`.

## Public link audit lock

The `odr_public_links` registry row stores
`audience_profile_locked="external"` at mint time. Revocation never
changes the lock — once issued, the audience is permanent for that
link_id. Re-minting requires a NEW `link_id`.

## Why this matters

| Risk avoided | How |
|---|---|
| PM accidentally hands FAA a coaching note | External profile auto-strips coaching |
| CEI sees an amendment rationale that exposes internal QC concern | External profile auto-strips amendment reasons |
| DOT inspector requests a "complete record" and gets internal projection | Legal/Audit profile is admin-only and writes `legal_audit` to the audit log |
| Field foreman shares the wrong PDF link in WhatsApp | Public link is audience-locked at mint — not user-changeable |
| Future field surfaces a new internal column we forget to redact | The `_project_for_audience("external")` projection is the **single source of truth** — adding a column to the model never auto-leaks |

## Boundary enforcement (test surface)

| Test | Suite | Asserts |
|---|---|---|
| External PDF audit log on render | `tests/odr/test_odr_m02.py` | every render produces `X-ODR-Audience` header |
| Public envelope strips internal fields | `tests/odr/test_odr_m03.py::test_public_resolve_strips_internal_fields` | `completion_telemetry`, `consumer_dispatch`, `readiness`, `reliability` absent |
| Audience profile maps to projection | `tests/odr/test_odr_m035.py::test_audience_profile_external_dot_maps_to_external` (added in M0.35) | `external_dot` profile → `audience=external` |
| Public link audience-locked | `tests/odr/test_odr_m035.py::test_public_link_audience_locked` (added in M0.35) | `audience_profile_locked=="external"` on registry |
| Reality validation (4 scenarios) | `scripts/odr_reality_validation.py` | 0 leaks across all 4 real-world scenarios |

## Operator behavior (UI)

The PDF action surfaces in `/odr/:id` and `/pm/odr` ask:
*"Who is this for?"* — they do NOT show a checkbox grid of
redaction options. The frontend buttons map 1-to-1 to audience
profiles; the projection happens server-side.

## Verdict

🟢 **AUDIENCE PROJECTION DOCTRINE LOCKED.** The platform asks one
question. The platform answers the rest. PMs never guess.
Foremen never leak. CEI/DOT/FAA always receive the same audience-
safe projection regardless of who clicked Generate.

_End of ODR_AUDIENCE_PROJECTION_DOCTRINE.md._
