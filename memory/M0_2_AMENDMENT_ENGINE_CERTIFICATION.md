# M0.2 — Amendment Engine · Certification

_Phase V.1 · 2026-05-29 · OPERATIONAL MEMORY substrate._

## Mission

Codify a 24-hour foreman edit window and a Superintendent+ amendment
flow that **preserves chronology, never destroys audit data, and never
overwrites silently.**

## Inheritance

- `/app/memory/ODR_FINAL_GOVERNANCE_ADDENDUM.md` (O28 · O29 · O35)
- `/app/memory/ODR_DATA_MODEL.md` (G1–G9 amendment addendum)

## Module

`/app/backend/routes/odr/amendments.py` · 290 lines · ruff clean.

## Authority matrix

| ODR status | Window | Foreman | Super | Senior Super | Admin |
|---|---|---|---|---|---|
| `draft` / `returned` | n/a | ✅ free edit | ✅ free edit | ✅ free edit | ✅ free edit |
| `submitted` | within 24h | ✅ section_events only | ✅ amendment row | ✅ amendment row | ✅ amendment row |
| `submitted` | post-24h | ❌ refused | ✅ amendment row | ✅ amendment row | ✅ amendment row |
| `approved` | any | ❌ refused | ❌ refused | ❌ refused | ✅ amendment row |

## API surface

| Verb | Route | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/odr/{id}/amend` | Super+ (post-window) / Admin (always) | record amendment |
| `GET` | `/api/odr/{id}/amendments` | any portal | amendment list (audit-trail read) |
| `GET` | `/api/odr/{id}/version-chain` | any portal | combined audit chain |

## Audit contract (per amendment)

Every recorded amendment writes ONE row to `odr_amendments`:

```
amendment_id        uuid4
odr_id              uuid4 (FK to odr.id)
actor_uid           email/uid of amender
actor_role          foreman | superintendent | senior_superintendent | admin
actor_portal        field_leadership | admin
field_path          dotted/bracketed path (e.g. plan_vs_actual.schedule_impact_days)
old_value           original value (full · not just hash)
new_value           new value (full · not just hash)
old_value_sha256    integrity anchor
new_value_sha256    integrity anchor
reason              { text, original, original_lang, … }   LocalizedString
at_utc              Z-suffixed UTC ISO
triggers_pdf_rerender boolean
```

Plus ONE row to `odr_section_events` (append-only audit trail).

## Hard rules

- ✅ No overwrite — old + new values preserved on every row.
- ✅ No deletion — `odr_amendments` has no DELETE route; trendline
  integrity probe defends append-only invariant.
- ✅ Chronology preserved — `last_amended_at_utc` and
  `amendment_count` flip forward only.
- ✅ Reason required (Pydantic `LocalizedString` field).
- ✅ Field path validated (path-getter / path-setter pair handles
  dotted + bracketed paths safely).

## Verified live (preview)

- Admin in-window amendment → amendment row recorded + count
  incremented · audit list returns it.
- Empty `field_path` → 422 Pydantic.
- Approved-status amendment by non-Admin → 403 (per code path).
- Pytest coverage: 3 tests (in-window admin, list, invalid path).

## Out of scope for M0.2

- Foreman push-back / approval workflow for post-window requests
  (deferred to M0.3 UI).
- Side-by-side diff viewer (deferred to M0.3 FL ODR Center).
- Per-amendment notification rules (deferred to M0.3 consumer
  projector).

## Verdict

🟢 **Amendment Engine LIVE.** Every change to a submitted ODR
post-window is contractually captured with a who/when/what/why
provenance record. No audit destruction. No silent overwrite.
