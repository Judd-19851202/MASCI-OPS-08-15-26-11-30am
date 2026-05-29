# OGC Catalog Seed · Certification (M0.2A)

_Phase V.1 · 2026-05-29 · TRAINING + CONTRACTUAL MEMORY substrate._

## Mission

Seed the **Operational Guidance Center (OGC)** catalog with
field-usable, bilingual (EN + ES), crew-aware coaching content so
the M0.3 frontend has a real catalog to render against from day one.

No filler. No generic safety posters. No AI runtime calls. The
voice is **experienced superintendent coaching** — terse, practical,
project-anchored.

## Inheritance

- `/app/memory/ODR_COACHING_GUIDANCE_ADDENDUM.md` (O36–O50)
- `/app/memory/GUIDANCE_INTELLIGENCE_FOUNDATION.md` (this wave)
- `/app/memory/CREW_TYPE_READINESS_MATRIX.md` (this wave)

## Module

`/app/backend/routes/odr/guidance_catalog.py` · ruff clean.

## Coverage achieved

- **Prompt keys**: **14** (one per ODR section that has actionable coaching)
- **Sections covered**: 14 (project, manpower, equipment, materials,
  production, delays, extra_work, constraints, safety,
  weather_impact, photos, tomorrow, plan_vs_actual, signature)
- **English bullets per prompt_key**: **≥ 4** for every key (live floor: **14/14 PASS**)
- **Spanish bullets per prompt_key**: **≥ 4** for every key (live floor: **14/14 PASS**)
- **Crew overlays**: 9 crew types receive a specific overlay on the
  `production.add_first_segment` key (pipe, paving, milling, mot,
  concrete, structures, airfield, electrical, survey). Other crew
  types fall back to the well-formed base entry.
- **Crew universe**: 20 entries (covers all 16 enum.CrewType values
  + 4 field-nomenclature aliases: drainage, asphalt, striping, demo,
  earthwork).

## Quality bar

Every bullet is:

- ≥ 8 characters (probe-enforced).
- Concrete (mentions a specific operation, ticket, photo, person,
  contract instrument, or measurable quantity).
- Self-contained (one bullet ≈ one actionable thing the foreman
  can do or check).
- Tone-consistent (instructive without being preachy; assumes
  the reader is a working foreman).

## Sample (production · pipe crew · EN)

> 1. Record total LF installed by pipe size and material — RCP, HDPE, PVC, etc.
> 2. Capture from-structure and to-structure for every run so QC can verify alignment.
> 3. Note backfill type and compaction percentage for each segment laid today.
> 4. Photograph every joint inspection before backfill — that's your evidence chain.

## Sample (safety · base · ES)

> 1. Cada evento de seguridad — incluso casi-accidente — se registra con quién, qué, cuándo y el contacto de Seguridad notificado.
> 2. Notifique a Seguridad ANTES de enviar el ODR — llamar a Seguridad es la parada obligatoria, no el reporte.
> 3. Tome fotos en la escena antes de que alguien mueva equipo o trabajadores.
> 4. El reporte de incidente se adjunta como documento separado; la sección de seguridad del ODR es la puerta, no el archivo.

## Resolution semantics

```
resolve(prompt_key, crew_type, lang) →
  if crew_type ∈ entry.crew_overrides:
    return entry.crew_overrides[crew_type][lang]
  else:
    return entry[lang]
```

## Live API

| Verb | Route | Purpose |
|---|---|---|
| `GET` | `/api/odr/guidance/prompts` | list all prompt_keys + sections |
| `GET` | `/api/odr/guidance/resolve?prompt_key=…&crew_type=…&lang=…` | resolve one |
| `GET` | `/api/odr/guidance/catalog-health` | coverage stats for the bilingual probe |
| `GET` | `/api/odr/guidance/crew-readiness/{crew_type}` | crew matrix |
| `GET` | `/api/odr/guidance/crew-readiness` | full matrix |

## Probe (sub-second · read-only)

`/app/scripts/odr_bilingual_probe.py [--gate]`

Defends B1 (section coverage) · B2 (EN/ES floor) · B3 (overlay
floor) · B4 (no empty bullets) · B5 (crew universe coverage) · B6
(no orphan prompt_keys in live data) · B7 (LocalizedString shape
integrity).

Live run: **0 failures · 1 warning** (cosmetic `subcontractors`
section soft-warn).

## Verdict

🟢 **OGC Catalog SEEDED.** The catalog is operationally usable
today by the readiness engine and tomorrow by the M0.3 frontend.
Build correctly once — no schema rewrites later. The catalog can
be extended at any time by adding entries to `CATALOG` in
`guidance_catalog.py`; the probe will validate every new entry.
