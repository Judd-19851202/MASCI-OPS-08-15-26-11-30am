# ODR Substrate Reuse Map

_Phase V.1 · 2026-05-29 · catalog of ODR-era assets retargeted at the Daily Report uplift._

> Every asset built between M0.1 and M1 is reused. Nothing is thrown
> away. The Daily Report becomes elite by **inheriting** the
> intelligence layer, not by being replaced.

---

## 1 · Reuse summary

| Asset | Built in | Now powers (Daily Report side) |
|---|---|---|
| `operational_links` substrate | Pre-M0 | DR ↔ photo ↔ constraint ↔ production cross-references |
| Operational timeline | M0.1 (sidecar) | Mixed-substrate timeline already at `/operational-records` |
| Audience projection (5-mode) | M0.35 | DR PDF audience modes (foreman / pm / executive / external / legal_audit) |
| Public/external PDF redaction | M0.35 + M0.4 | DR external PDFs strip foreman_uid / GPS / device meta + embed photo thumbnails |
| Continuity IDs (`DR-YYYY-NNNNN`) | Pre-M0 | Unchanged · already in place · `doc_ids.ensure_doc_id` |
| Photo governance (`job_photos`) | Pre-M0 | DR photos remain indexed there · new linkage adds tag/context |
| Archive system + `<ArchiveBadge>` | M1 | Already in place for historical DRs |
| Unified operational records projector | M1 | Already at `/api/operational-records` |
| Role-aware visibility (FLL verb dispatch) | M0.1 | Existing DR list gains the same dispatch |
| Low/no signal foundation | Phase J | Daily Report's submit idempotency + photo retry already use it |
| Device recognition | Phase J | Already on the DR mount path |
| Auto-save | Pre-M0 | Already present on the DR draft |
| Draft recovery | Pre-M0 | Already present |
| Offline queue foundation | Phase J / SW | Already present · needs strengthening (see `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md`) |
| Coaching / guidance engine (14 keys) | M0.2A | Same 14 keys, now surfaced on DR steps 4 + 6 |
| PDF SHA / audit footer doctrine | M0.2 + M0.35 | Backported to DR PDF renderer (currently no SHA footer on DR PDFs) |
| Platform Inheritance Doctrine Lock #2 | M0.35 | Governs every DR-side change going forward |
| Simplicity Doctrine Lock #1 | M0.35 | Same test applies — "mud, gloves, 5:30 PM" |

## 2 · By layer

### 2.1 Backend

| File / Module | What it gives the Daily Report uplift |
|---|---|
| `routes/odr/pdf.py` · `_project_for_audience` | Audience projection logic to copy into the DR PDF renderer (or refactor into a shared module · TBD per build authorization) |
| `routes/odr/pdf.py` · `_section_photos` + `_resolve_photo_assets` | Photo embedding code path; works against any photo collection |
| `routes/odr/pdf.py` · `_strip_external_photo_meta` | External-audience photo_id stripping |
| `routes/odr/pdf.py` · `_FooterCanvas` + envelope SHA256 | Audit footer doctrine |
| `routes/odr/guidance_catalog.py` (M0.2A) | 14 EN/ES OGC prompts — surface on DR step 4 (production unit) + step 6 (constraint type) |
| `routes/odr/continuity.py` · `mint_link` | Public link minting for DR external sharing |
| `routes/odr/observation.py` | `odr_observation_events` collection → repurposed for DR completion-time / queue-depth telemetry |
| `routes/operational_links.py` | DR ↔ photo / constraint / production / activity linking |
| `routes/operational_records.py` (M1) | Already merges DR + ODR; will surface the elite DR fields |
| `doc_ids.py` | `DR-YYYY-NNNNN` issuance · unchanged |
| `photo_governance.py` | Photo lifecycle · unchanged |
| `lib/idempotency.py` (Phase J) | Submit idempotency for the DR write path |

### 2.2 Frontend

| File / Module | What it gives the Daily Report uplift |
|---|---|
| `components/odr/ArchiveBadge.jsx` (M1) | Archive treatment for legacy rows · already in place |
| `components/odr/OdrTrustBanner.jsx` (M0.3) | Re-usable trust banner pattern · adapt copy to "Daily Report · official record" |
| `pages/operational_records/OperationalRecords.jsx` (M1) | Unified mixed dashboard · already in place |
| `lib/odrApi.js` (M0.3) | Pattern for `listOperationalRecords` / `resolveDocId` · re-applied to DR endpoints |
| `lib/idempotency.js` (existing) | Submit retry safety on the client |

### 2.3 Probes / governance

| Probe | What it does for the DR uplift |
|---|---|
| `scripts/odr_completion_time_drift_probe.py` (M0.4 advisory) | Repurpose to read from a DR-equivalent observation event (e.g. `dr_submit_success`) once the DR telemetry is wired |
| `scripts/odr_simplicity_drift_probe.py` (M0.4 advisory) | Targets `OdrNew.jsx` today — add the DR form file to the target list |
| `scripts/odr_inheritance_drift_probe.py` (M0.4 advisory) | Targets `pages/odr/` today — add the DR pages directory |
| `scripts/cross_portal_consistency_drift_probe.py` (M0.4 advisory) | Already cross-portal — DR pages are already included in the scan |
| `scripts/odr_public_link_continuity_probe.py` (M0.2) | Extend invariants to DR doc_ids (already supports the shape) |
| `scripts/odr_bilingual_probe.py` (M0.2A) | Extend to scan the DR form for EN/ES OGC parity |

## 3 · What to refactor into a shared module (build decision · pending operator approval)

When build is authorized, the cleanest move is to extract the
following from `routes/odr/pdf.py` into a shared module (e.g.,
`routes/_shared/audience_projection.py`) so both ODR and DR PDFs
use the same code:

- `_project_for_audience` (rename: `project_envelope_for_audience`)
- `_strip_external_photo_meta` (rename: `strip_external_envelope`)
- `_resolve_photo_assets` (rename: `resolve_photo_thumbnails`)
- `_render_thumbnail_jpeg` (rename: `render_jpeg_thumbnail`)
- `_FooterCanvas` (rename: `AuditFooterCanvas`)
- `_envelope_sha256` (rename: `envelope_sha256`)

**This refactor is OPTIONAL for wave 1.** A simpler path is to call
the existing helpers in-place (cross-import) for v1, then refactor in
a later wave. Operator decision required.

## 4 · What is intentionally NOT reused

| ODR-only asset | Why we keep it ODR-only |
|---|---|
| `OdrNew.jsx` (9-step wizard) | The DR has its own existing form — we are not creating a parallel wizard |
| `routes/odr/routes.py` · `POST /api/odr` | DR uses its own write path; ODR write may be retired or kept for internal/admin tests |
| `routes/odr/amendments.py` | DR amendment lifecycle (if needed) follows the existing DR PUT/PATCH paths — not the ODR amendment engine |
| `M0.35 audience_profile` strings (`internal_pm`, `external_dot`, etc.) | DR PDFs can adopt these labels OR keep DR's existing audience labels — operator decision |

## 5 · The "Daily Report becomes elite" mental model

```
                ┌─────────────────────────────────────────┐
                │  FOREMAN-FACING                         │
                │                                         │
                │  Daily Report form (unchanged shape)    │
                │  · 9 steps                              │
                │  · < 5 min target                       │
                │                                         │
                │  + production rows (new · step 4)       │
                │  + constraint rows (new · step 6)       │
                │  + photo linkage (new · step 5)         │
                │  + RFI/schedule flags (advisory)        │
                └─────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────────────┐
        │  INTELLIGENCE LAYER (reused from M0.1 → M1)        │
        │                                                    │
        │  · operational_links · operational_records         │
        │  · audience projection · external redaction        │
        │  · photo governance · continuity IDs               │
        │  · OGC guidance catalog (14 EN/ES prompts)         │
        │  · audit footer + SHA256                           │
        │  · idempotency + offline queue                     │
        │  · device recognition · auto-save · recovery       │
        │  · archive · unified dashboard                     │
        │  · doctrine locks #1 + #2                          │
        └────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────────────────┐
        │  PM / SUPER / EXECUTIVE / EXTERNAL CONSUMERS       │
        │                                                    │
        │  Audience-projected PDFs                           │
        │  Operational timeline                              │
        │  Cross-substrate search                            │
        │  Risk / exposure tiles                             │
        │  Cross-portal coaching parity                      │
        └────────────────────────────────────────────────────┘
```

The foreman sees one form. The platform sees the full intelligence.
**That is elite.**

---

_End of ODR_SUBSTRATE_REUSE_MAP.md._
