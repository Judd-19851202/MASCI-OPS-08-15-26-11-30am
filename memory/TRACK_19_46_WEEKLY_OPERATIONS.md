# TRACK 19.46 · Weekly Operations Digest

**Status:** IMPLEMENTED · shipped in Track 19.46 (2026-07-04).

## Purpose
Answer one question in five minutes:
**What changed operationally this week?**

Distinct from Corporate Intelligence:
- **Corporate** — "How is the company?" (weighted snapshot)
- **Weekly Operations** — "What changed operationally this week?" (WoW deltas)

## Product identity
- product_id: `weekly_operations_digest`
- Display name: **Weekly Operations Digest**
- Permission role: `admin_only`
- Template: `executive_v1`
- Schedule: weekly · Monday 13:00 UTC
- Aggregator: `_agg_weekly_operations` in `operational_intelligence/products.py`
- Section contract: canonical 14-section layout (Track 19.41)
- Score model: universal 0-100 (Track 19.41 · WoW-delta contributors)

## Cross-domain scope
Weekly Operations composes 9 implemented domain digests via
`engine.compose(...)` — it never re-queries raw data. Domains folded
into the weekly view:

- `safety_morning_digest`
- `project_intelligence`
- `fleet_intelligence`
- `shop_intelligence`
- `transportation_intelligence`
- `hr_intelligence`
- `training_intelligence`
- `po_weekly_digest`
- `executive_operations_brief`

Corporate Intelligence is **intentionally excluded** — it already
composes everything, so including it would double-count and violate
the "every section must earn its place" rule.

## The WoW delta engine
Each domain's current `overall_score` is diffed against its most recent
prior score row in the shared `operational_intelligence_history`
collection. From that diff we produce:

- **Improvers** — domains with a positive delta.
- **Decliners** — domains with a negative delta.
- **HIGH/CRITICAL now** — domains that need Monday-morning attention.

If no prior history exists (first-run bootstrap), Weekly Operations
still produces a valid digest, honestly labels the state as
"first-run bootstrap", and lets deltas engage next period. Never fakes
history.

## Six-Pillar audit
- **Powerful** — three signal classes (improvers, decliners, current
  HIGH/CRITICAL) drive every downstream section.
- **Simple** — five minutes to read.
- **Beautiful** — shared executive layout · deep links included.
- **Trusted** — first-run bootstrap disclosed honestly · every section
  earns its place · concrete WoW point deltas attached to every win
  and every attention item.
- **Proven** — 8 lock tests + registry / API / documentation locks.
- **Operational** — every recommendation is specific and actionable
  ("Executive review of X (score N · HIGH) at the Monday operations
  meeting"), never "monitor" / "keep watching".

## No-Auto-Decision
Weekly Operations is an attention signal only. Every recommendation is
a discussion prompt for the Monday operations meeting — never an
automatic executive decision.
