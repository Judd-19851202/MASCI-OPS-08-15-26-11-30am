# DR-ROI-001E · Architecture

## Layered View

```
┌───────────────────────────────────────────────────────────┐
│  React SPA (three horizon-oriented dashboards)             │
│  ┌─────────────┐ ┌────────────────┐ ┌──────────────────┐   │
│  │ PM Intel    │ │ Admin Intel    │ │ Executive Intel  │   │
│  └─────────────┘ └────────────────┘ └──────────────────┘   │
│  Shared: components/ods/HorizonPrimitives.jsx              │
│  Client:  lib/odsIntelligenceApi.js                        │
└───────────────────────────────────────────────────────────┘
                       ▲ HTTP (JSON)
                       │
┌───────────────────────────────────────────────────────────┐
│  FastAPI · routes/ods_intelligence.py                      │
│  · read-only aggregation over snapshots + facts            │
│  · attention endpoints project facts → attention buckets   │
│  · brief endpoints call the AI Provider Gateway            │
│  · deterministic evidence hash → ods_briefs_cache          │
└───────────────────────────────────────────────────────────┘
        │                                    │
        ▼                                    ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ services/ods_spine        │   │ services/ai_gateway        │
│ (facts + snapshots + KPIs)│   │ (pm_brief · executive_brief│
│                           │   │  tasks · provider-neutral) │
└───────────────────────────┘   └───────────────────────────┘
```

## Design Principles
1. **Snapshot-first reads.** All KPIs are aggregated from
   `operational_kpi_snapshots` — pre-computed per project × day. This
   keeps the hot path off `daily_reports` entirely.
2. **Facts-first attention.** Attention items pull directly from
   `operational_facts` (is_current=true) so severity, category, and
   free-text summary come from the field entry — no AI interpretation.
3. **Cache-first briefs.** LLM briefs are keyed by a sorted-JSON
   SHA-256 of the input payload. Reflow of a page with the same range
   is free.
4. **Three horizons everywhere.** PM / Admin / Executive all use the
   same visual grammar (What Happened / Is Happening / Needs Attention)
   so operators only learn one dashboard shape.
5. **Provider-neutral.** The route module never mentions Claude,
   OpenAI, Gemini, or any model/version. The gateway envelope carries
   only `{narrative, confidence, evidence_refs, sources_used,
   uncertainties, ai_available, generated_at}`.

## Collections Used
- Reads: `operational_facts`, `operational_kpi_snapshots`.
- Writes (this phase only): `ods_briefs_cache` (idempotent upserts).

## Zero-Drift Envelope
- No modifications to V1 collections.
- No modifications to V1 or V2 UI pages.
- Only three route lines added to `AppRoutes.jsx`.
- Only three attention endpoints appended to
  `routes/ods_intelligence.py`.
