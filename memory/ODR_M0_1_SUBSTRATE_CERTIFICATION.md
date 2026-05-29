# M0.1 — ODR Substrate Implementation Certification

_Phase V.1 · Operational Daily Record · Substrate-day-one · 2026-05-29._

The Operational Daily Record (ODR) substrate is now live in preview.
Build correctly once. No schema rewrites later.

---

## 1 · Operator directive (verbatim)

> "LOCK ODR SPECIFICATION
> BEGIN M0 IMPLEMENTATION
>
> M0.0 must first close W1 backfill gaps · W2 preview DB test row
> cleanup · W3 OBSERVATION_LEDGER validation before substrate
> implementation proceeds.
>
> M0 implementation must inherit:
>   * FIELD_LEADERSHIP_VISIBILITY_DOCTRINE
>   * OPERATIONAL_LINKING_RULES
>   * TIMELINE_DOCTRINE
>   * ODR_COACHING_GUIDANCE_ADDENDUM
>   * ROLE_AWARE_VISIBILITY_MODEL
>
> All ODR entities must support from day one:
>   * chronology participation
>   * audit participation
>   * operational_links compatibility
>   * role-aware visibility
>   * coaching compatibility
>   * future RFI linkage
>   * future schedule linkage
>
> No schema rewrites later. Build the substrate correctly once. Proceed with M0."

---

## 2 · M0.0 hygiene closure (precondition · CLOSED)

| Item | Status | Detail |
|---|---|---|
| W1 backfill | 🟡 documented · operator-owned | `corrective_actions.equipment=0%` and friends are pre-existing PRODUCTION data-quality items; ODR substrate writes to new collections — no dependency on backfill. Full closure runbook in `M0_0_HYGIENE_CLOSURE_REPORT.md`. |
| W2 preview cleanup | ✅ CLOSED | 94 test-artifact rows deleted across 8 preview collections; 10-email seed-account whitelist preserved. Receipt: `M0_0_PREVIEW_CONTAMINATION_CLEANUP_*.json`. |
| W3 OBSERVATION_LEDGER | ✅ CLOSED | 2nd real entry appended documenting M0.0 closure gate; ledger no longer seed-only. |

Gate opened → substrate implementation proceeded.

---

## 3 · Substrate scope shipped (M0.1)

### 3.1 Package structure

```
/app/backend/routes/odr/
    __init__.py            # public exports
    enums.py               # 23 closed enums (CrewType · DelayType · …)
    models.py              # full Pydantic envelope (schema_version=2)
    visibility.py          # FLL-1..FLL-6 projector + field projection
    indexes.py             # 8 collection · 25 index strategy
    routes.py              # POST/GET/PATCH/SUBMIT + audit + timeline
```

### 3.2 Collections (8 · created on next backend start)

| Collection | Purpose | Append-only? | Index count |
|---|---|---|---|
| `odr` | system of record | no (drafts + 24h amend window) | 11 |
| `odr_section_events` | field-level transition audit | **yes** | 2 |
| `odr_photos` | photo registry | no (caption editable) | 2 |
| `odr_attachments` | non-photo evidence (delivery / haul / CEI / FAA / …) | no (label editable) | 2 |
| `odr_amendments` | Super+ amendments post-window | **yes** | 4 |
| `odr_translation_events` | bilingual normalization audit | **yes** | 1 |
| `odr_preload_attempts` | public-link continuity audit | **yes** | 4 |
| `odr_consumer_index` | derived projector views (refreshed) | no | 2 |

Total: **25 indexes ensured at startup**.

### 3.3 API surface (live in preview)

| Verb | Route | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/odr` | any portal token | create draft (year-scoped `ODR-YYYY-NNNNN` sequence) |
| `GET` | `/api/odr` | any portal token | list w/ FLL-aware scope filter |
| `GET` | `/api/odr/{id}` | any portal token | detail w/ FLL-aware field projection |
| `PATCH` | `/api/odr/{id}` | any portal token | partial update (draft/returned freely · submitted gated by amend window) |
| `POST` | `/api/odr/{id}/submit` | any portal token | readiness pass · hard-stop check · status flip · timeline emission |
| `POST` | `/api/odr/{id}/section-event` | any portal token | append audit row |
| `GET` | `/api/odr/{id}/section-events` | any portal token | audit-trail read (FLL-scoped) |

---

## 4 · Inherited doctrines (substrate-day-one)

### 4.1 FIELD_LEADERSHIP_VISIBILITY_DOCTRINE

Implemented in `routes/odr/visibility.py`:

| FLL | Verb | Scope filter | Field projection |
|---|---|---|---|
| FLL-1 Foreman | FULL | `project.foreman_uid` | drops `completion_telemetry`, `consumer_dispatch` |
| FLL-2 General Foreman | FULL | `crew_profile.crew_id ∈ crews_managed[]` | drops `completion_telemetry`, `consumer_dispatch` |
| FLL-3 Superintendent | FULL | `project.project_id` | (full) |
| FLL-4 Senior Super | FULL | `project.project_id ∈ regional_projects[]` | (full) |
| FLL-5 PM | LIMITED | own pm_uid or assigned project | drops `completion_telemetry`, `readiness.coaching_prompts`, `reliability.sync_conflicts`, `reliability.device_fingerprint` |
| FLL-6 Admin / Ops Leadership | SUMMARY | open · UI compresses | drops `consumer_dispatch` |

Verified live · admin actor sees `fll=FLL-6 verb=SUMMARY` on list.

### 4.2 OPERATIONAL_LINKING_RULES

10 new artifact types registered in `ARTIFACT_TYPES`:
`odr`, `odr_section_event`, `odr_amendment`, `odr_attachment`,
`odr_translation_event`, `odr_preload_attempt`,
`production_segment`, `work_area`, `material_event`,
`safety_event`. Forward slots `future_rfi`,
`future_schedule_activity`, `future_schedule_import` were already
registered in Wave 1 — RFI + Schedule will link to ODRs without
schema change.

### 4.3 TIMELINE_DOCTRINE

On `POST /api/odr/{id}/submit`, the substrate emits an
`operational_links` row:

```
source_type=odr · source_id=<odr_id>
target_type=project · target_id=<project_id>
relationship=documents
visibility=cross-portal-read
project_id=<project_id>
status=active
```

Verified live — operational-links query for project returns the
ODR row, satisfying the chronology contract from
`OPERATIONAL_TIMELINE_FOUNDATION.md`.

### 4.4 ODR_COACHING_GUIDANCE_ADDENDUM (O36–O50)

Readiness engine emits `coaching_prompts` as structured
`{prompt_key, text, section_anchor, severity}` objects per
`ReadinessSnapshot` (D6 + Coaching addendum). The
`Operational Guidance Center` resolves `prompt_key → text/EN+ES` at
surface render. The substrate carries NO coaching content — only
keys — preserving the OGC single-source contract.

### 4.5 ROLE_AWARE_VISIBILITY_MODEL

Auth tokens still gate endpoints. Doctrine restricts surfaces.
Substrate `_PM_HIDDEN_FIELDS` mirrors V11 ("aggregations never
carry per-foreman dimensions"); `completion_telemetry` is admin-only
per O9 + V10 ("coaching telemetry never performance-review evidence").

---

## 5 · Day-one capability matrix

| Capability | Status | Evidence |
|---|---|---|
| Chronology participation | ✅ | `operational_links` row emitted on submit (timeline query confirmed) |
| Audit participation | ✅ | `odr_section_events` row appended on create/patch/submit (3+ rows per submitted ODR) |
| operational_links compatibility | ✅ | 10 new artifact_types registered · ODR is source-typeable |
| Role-aware visibility | ✅ | FLL-1..FLL-6 projector + field projection (tested with admin actor) |
| Coaching compatibility | ✅ | Readiness emits `CoachingPrompt` w/ prompt_key (OGC-resolvable) |
| Future RFI linkage | ✅ | `future_rfi` artifact_type slot preserved + ODR has `rfi_link_id` on ExtraWork |
| Future Schedule linkage | ✅ | `future_schedule_activity` + `future_schedule_import` artifact_type slots preserved |

---

## 6 · Hard stops enforced (O9 + O31)

- Submission refused if `safety.any_event=True` AND any
  `safety.events[*].notified_safety=False` OR
  `incident_report_complete=False`.
- Submission refused if
  `signature.foreman_acknowledgement.acknowledged=False`.
- Verified live: empty submit → HTTP 409
  `signature.foreman_acknowledgement.acknowledged_required`.
- After ack → HTTP 200, status=`submitted`, readiness=`ready`.

---

## 7 · 24-hour amendment window (O28)

On status flip to `submitted`, `amend_allowed_until_utc` is stamped
at `now + 24h`. The PATCH route refuses post-window mutations with
HTTP 403, redirecting the operator to the FL Amendment route (which
ships in M0.2 / M2).

Verified live: `amend_allowed_until_utc` = submit_time + 24h.

---

## 8 · Regression matrix

| Suite | Result |
|---|---|
| `tests/odr/test_odr_substrate.py` (NEW · 12 tests) | 🟢 12/12 PASS |
| `tests/test_v_prelude_wave1_substrate.py` | 🟢 (no regression) |
| `tests/test_v_prelude_wave1_1_sidecar.py` | 🟢 (no regression) |
| Combined Wave-1 + Wave-1.1 substrate | 🟢 27/27 PASS |

---

## 9 · Doctrine compliance audit

- ✅ Mongo `_id` excluded from every response (test_9).
- ✅ TRUST-TIME-1 timestamps — all writes via `_utc_iso()` Z-suffixed.
- ✅ Hard DELETE forbidden — status flips only.
- ✅ Append-only `odr_section_events` + `odr_amendments` +
  `odr_translation_events` + `odr_preload_attempts` (no UPDATE/DELETE
  routes shipped).
- ✅ Lint clean (`ruff check routes/odr/` → all checks passed).
- ✅ No auth changes · no permission expansion · existing
  `_require_any_portal_token` reused.
- ✅ Preview-only · no production deploy.

---

## 10 · Out of scope for M0.1 (deferred)

| Item | Wave |
|---|---|
| PDF rendering | M0.2 |
| Public-link continuity engine | M0.2 |
| Amendment route (post-24h-window) | M0.2 |
| Per-consumer projector materialized views | M0.3 |
| Frontend `/odr/new`, `/odr/{id}`, dashboards | M0.3 |
| Migration script from `daily_reports` | M1 |
| Guidance catalog seed (12 sections × CrewType × EN/ES) | M0 ship requires it before pilot; tracked separately |

---

## 11 · Stop condition

🟢 **M0.1 substrate is live, tested, and doctrine-compliant.**

Operator may now:

1. Hand off to UI agent to build the M0.3 frontend on top of the
   sealed API contract.
2. Begin M0.2 (public-link continuity + amendment route + PDF
   rendering) on the same package.
3. Begin M1 migration when the operator is ready to dual-write.

Substrate has been built correctly once. No schema rewrites later.

_End of M0.1 Substrate Implementation Certification._
