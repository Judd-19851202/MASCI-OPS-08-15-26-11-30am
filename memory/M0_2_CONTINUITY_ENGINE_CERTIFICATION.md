# M0.2 — Public Link Continuity Engine · Certification

_Phase V.1 · 2026-05-29 · CONTRACTUAL MEMORY substrate._

## Mission

An ODR generated today must remain accessible tomorrow, next month,
next year, and during future audits — without broken links, silent
URL mutations, or version-chain confusion.

## Inheritance

- `/app/memory/ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md` (O11–O20)
- `/app/memory/ODR_DATA_MODEL.md` (P1–P9 addendum)
- `/app/memory/FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md`

## Module

`/app/backend/routes/odr/continuity.py` · 320 lines · ruff clean.

## API surface

| Verb | Route | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/odr/{id}/link` | Admin or PM | mint a public link |
| `GET` | `/api/odr/public/{doc_id}` | **none** (public) | continuity-gated resolver |
| `GET` | `/api/odr/{id}/version-chain` | any portal | amendment chain read |
| `GET` | `/api/odr/public-links` | Admin only | registry index |
| `PATCH` | `/api/odr/public-links/{link_id}` | Admin or PM | revoke or re-scope |

## Continuity invariants (probe-defended)

| ID | Invariant | Probe check |
|---|---|---|
| C1 | Unique public `link_id` across registry | ✅ |
| C2 | Every `odr.public_access.link_id` resolves in registry | ✅ |
| C3 | Every registry row references an existing ODR | ✅ |
| C4 | `doc_id` format `ODR-YYYY-NNNNN` | ✅ |
| C5 | `doc_id` uniqueness across ODRs | ✅ |
| C6 | No two ODRs share an active `link_id` | ✅ |
| C7 | `odr_preload_attempts.outcome` in closed enum | ✅ |
| C8 | `odr_preload_attempts` count append-only (never shrinks) | ✅ |

## Public envelope (audience-safe)

The public resolver returns ONLY the public-safe field subset (no
`completion_telemetry`, no `consumer_dispatch`, no device
fingerprints, no `reliability.sync_conflicts`, no foreman raw uid
when external-audience PDF is requested instead).

## Append-only audit collections

| Collection | Append-only | Index count |
|---|---|---|
| `odr_public_links` | yes (revoke flips `revoked_at_utc`, never deletes) | 4 |
| `odr_preload_attempts` | yes (every resolve attempt logged) | 4 |

## Status flip semantics

ODR `status` evolves: `draft → submitted → approved`. Amended rows
write to `odr_amendments` — the head ODR row stays addressable at
its original `doc_id`. Public URLs never change as an ODR evolves
through `active → amended → superseded → archived` because the
addressable identifier (`doc_id`) is immutable.

## Verified live (preview)

- Mint link · returns `link_id` + `doc_id` + scope.
- Public resolve with valid `link_id` → 200 + public-safe envelope.
- Public resolve with wrong `link_id` → 403 + `denied_wrong_link`
  attempt logged.
- Public resolve unknown `doc_id` → 404 + `denied_no_prior` attempt.
- Version-chain returns amendment list ordered by `at_utc` desc.

## Probe (sub-second · read-only)

`/app/scripts/odr_public_link_continuity_probe.py [--gate]`

Wired into `/app/scripts/pre_deploy_check.sh` after the trendline
integrity probe.

## Verdict

🟢 **M0.2 Continuity Engine LIVE.** Public access for ODRs is now
operationally durable. URLs do not break. The doc_id contract is
enforced by index uniqueness AND by probe-level invariants. The
preload-attempt log is the operational eye on every public access.
