# TRACK 19.38 · PERMISSION MATRIX

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_38_CROSS_PORTAL_READ_FANOUT.md`

## Endpoint → Actor → Payload

| Endpoint | Safety | Admin | PM | Field / Public |
|---|---|---|---|---|
| `GET /api/incident-intelligence/portfolio-attention` | ✅ full (portfolio view) | ✅ full (portfolio view) | ❌ 401 | ❌ 401 |
| `GET /api/incident-intelligence/safety-priority` | ✅ full + safety_preview | ❌ 401 | ❌ 401 | ❌ 401 |
| `GET /api/incident-intelligence/pm-project-cases` | ✅ PM-safe view (strict allow-list) | ✅ PM-safe view | ✅ PM-safe view | ❌ 401 |

## Per-view field visibility

### Portfolio view (Safety + Admin)
Contains attention level, attention score, top 3 firing signals **including their rationales and source_fields**, readiness band, CAPA/task counts, days open, case reference fields. **No safety_block preview.** **No regulatory review fields.**

### Safety-priority view (Safety only)
Portfolio view **plus** a small `safety_preview` object with three boolean/string fields:
- `root_cause_documented` — boolean derived from `safety_block.root_cause_summary` presence.
- `executive_reviewer_present` — boolean derived from `safety_block.executive_reviewer` presence.
- `investigator_name` — string.

These are the only Safety-block fields ever surfaced outside a full Case Workspace load. They are still gated behind the Safety-only token — Admin does not see them via this endpoint.

### PM-project view (Safety / Admin / PM)
Strict allow-list of 15 keys:
```
case_id · case_number · state · incident_type · job_number · location_label ·
occurred_at · submitted_at · days_open · capa_open · capa_total · tasks_open ·
readiness_band · attention_level · (attention_score omitted; only band is shown)
```
Wait — code actually keeps `attention_score` numeric on PM too (safe: it's just a number). See `_PM_ALLOWED_KEYS` in `portfolio_intelligence.py` for the canonical list.

**Forbidden in PM payload (locked by pytest grep + runtime `_assert_pm_safe`):**
`safety_block` · `regulatory_review` · `osha_recordable` · `root_cause` · `liability` · `discipline` · `preventability` · `insurance` · `signal_rationale` · `rationale`.

If any of those tokens ever appears in a PM response, the endpoint raises a 500 with `code=pm_projection_leak` — the aggregator refuses to serve rather than leak.

## Why this shape

- **Safety** owns investigation. Full visibility.
- **Admin** owns platform + executive rollups. Portfolio visibility but not Safety preview fields — Admin doesn't have Safety-portal training and should not see partial investigation state without the surrounding context.
- **PM** owns project schedule + budget. Sees that an incident exists on their job, its state, its readiness band, its attention level (so they know to escalate to Safety) — but never sees Safety-owned investigation content.
- **Field / Public** — no visibility here. Field workers submit incidents; they do not see other people's portfolio state.

## Doctrine locks preserved
- **Track 19.34** (field intake protection): forbidden field-intake vocabulary not surfaced anywhere in this track's payloads.
- **Track 19.35** (Field Facts immutability): no write path introduced anywhere; every endpoint is read-only.
- **Track 19.36** (Executive Intelligence Model): unchanged.
- **Track 19.37** (No-auto-decision doctrine): scorer reused verbatim; attention_signals are the same shape as v1.
