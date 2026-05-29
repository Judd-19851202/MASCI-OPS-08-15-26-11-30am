# Guidance Intelligence Foundation

_Phase V.1 · M0.2A · 2026-05-29 · TRAINING MEMORY substrate · DETERMINISTIC._

## Mission

Provide an **operationally intelligent guidance layer** that surfaces
the right coaching content at the right moment in the ODR flow —
without invoking AI at runtime and without depending on opaque
heuristics.

> Guidance Intelligence ≠ AI. It is deterministic, auditable,
> testable, and probe-defended.

## Resolution path

```
Crew Type
   │
   ▼
ODR Section
   │
   ▼
Prompt Key                  (declared in guidance_catalog.CATALOG)
   │
   ▼
Guidance Catalog            (crew_overrides[crew_type] → bullets,
                             else base entry → bullets)
   │
   ▼
EN / ES Output              (≥ 4 bullets · field-usable copy)
```

## Determinism guarantees

| Guarantee | How |
|---|---|
| Same inputs always produce the same output | Pure dict lookup; no randomness, no time-dependence |
| Catalog content is reviewable in code | Lives in `guidance_catalog.py` (a single Python module) |
| Every prompt_key is reachable | Probe `B6` guarantees no orphan keys in live data |
| Every output meets the floor | Probe `B2` (≥4 EN + ≥4 ES per key) |
| Every crew has resolvable output | Probe `B5` (crew universe coverage) |

## API

| Verb | Route | Notes |
|---|---|---|
| `GET` | `/api/odr/guidance/prompts` | catalog index |
| `GET` | `/api/odr/guidance/resolve?prompt_key=…&crew_type=…&lang=…` | deterministic lookup |
| `GET` | `/api/odr/guidance/catalog-health` | coverage stats |
| `GET` | `/api/odr/guidance/crew-readiness/{crew_type}` | crew matrix (R/R/A) |
| `GET` | `/api/odr/guidance/crew-readiness` | full crew matrix |

## Downstream consumers (future)

| Wave | Consumer | Use |
|---|---|---|
| M0.3 | Foreman entry UI | Inline coaching tooltips on each section |
| M0.3 | FL ODR Center | Per-row "needs attention" badges with prompt_key |
| M0.3 | Readiness engine | Targeted prompts injected into `ReadinessSnapshot` |
| M0.4 | Onboarding | New-foreman walkthrough seeded with required topics |
| M1+ | FL Training Center | Curriculum mapped from Recommended/Advanced topics |
| M1+ | RFI MVP | Contextual hints when a draft RFI references a constraint |
| M1+ | Schedule | Crew-aware look-ahead readiness coaching |

## What this foundation is NOT

- ❌ NOT AI copilot logic (no LLM calls, no embeddings, no fuzzy match).
- ❌ NOT a dashboard expansion (no new charts, no new KPIs).
- ❌ NOT a new role model (the same FLL-1..FLL-6 doctrine governs
  whether a consumer SEES the prompt; this layer only RESOLVES it).
- ❌ NOT a content firehose (every entry is curated; the catalog is
  intentionally small at M0.2A so adding entries stays disciplined).

## Extending the catalog

To add a new prompt_key:

1. Edit `/app/backend/routes/odr/guidance_catalog.py` →
   add an entry to `CATALOG` with `section`, `severity`, `en`, `es`
   keys; optionally add `crew_overrides` for crew-specific variants.
2. Run `python3 scripts/odr_bilingual_probe.py --gate`.
3. Add a pytest at `tests/odr/test_odr_m02.py` if the new prompt_key
   needs surface-level coverage.
4. (Optional) Reference the new prompt_key from `routes/odr/routes.py`
   `_evaluate_readiness` so it surfaces in readiness.

## Doctrine boundary

This layer is the SOURCE OF TRUTH for "what should be coached when".
It is also the ONLY layer permitted to ship coaching content to
operators. UI components MUST resolve via the API — they may NOT
hardcode coaching strings.

This boundary is what makes the OGC catalog refactorable: when the
operator wants to rewrite a bullet, they edit ONE module, the probe
validates it, and every consumer surface updates at the next render.

## Verdict

🟢 **GUIDANCE INTELLIGENCE FOUNDATION LAID.** Deterministic,
bilingual, crew-aware coaching resolution is now live and
queryable. The foundation supports readiness, coaching,
onboarding, and the future FL Training Center without rework.

_End of GUIDANCE_INTELLIGENCE_FOUNDATION.md._
