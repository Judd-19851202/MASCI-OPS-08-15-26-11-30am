# DR-ROI-001E · Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  FIELD ENTRY (Daily Report V1 / V2 · Photos · Safety Forms)  │
└─────────────────────────────────────────────────────────────┘
                        │  (single entry, no duplication)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  ODS Emission Layer (services/ods_spine/ingest.py)           │
│  · normalizes payload                                         │
│  · supersedes prior facts for (source_type, source_id)       │
│  · writes labor / equipment / production / delay / safety /  │
│    quality / photo / readiness / material / weather facts    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  operational_facts  (is_current=true rows are the truth)     │
│  operational_kpi_snapshots  (pre-rolled per project × date)  │
│  operational_fact_links  (photo → activity, etc.)            │
└─────────────────────────────────────────────────────────────┘
                        │  READ ONLY
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  routes/ods_intelligence.py                                  │
│  · /pm/dashboard          · /pm/attention                    │
│  · /pm/projects/{id}/kpis · /projects/{id}/attention · brief │
│  · /admin/dashboard       · /admin/delays · /admin/attention │
│  · /executive/brief       · /executive/health                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  services/ai_gateway  (pm_brief / executive_brief tasks)     │
│  · deterministic evidence hash → ods_briefs_cache            │
│  · provider-neutral envelope: narrative + confidence + refs  │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React)                                            │
│  · PmOperationalIntelligence.jsx                              │
│  · AdminOperationalIntelligence.jsx                           │
│  · ExecutiveOperationalIntelligence.jsx                       │
│  · HorizonPrimitives.jsx (Preset · Header · Kpi · Attention) │
│  Three horizons per page — What Happened / Is Happening /     │
│  Needs Attention. Every value cites a fact_id.                │
└─────────────────────────────────────────────────────────────┘
```

## Guarantees
- The intelligence layer never writes back to V1 collections.
- Only cache write: `ods_briefs_cache` (idempotent upsert keyed on
  `(audience, evidence_hash)`).
- Every KPI on the SPA maps to a canonical fact type — enumerated in
  `DR_ROI_001E_KPI_CONTRACT.md`.
