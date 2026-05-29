"""
routes/odr — Phase V.1 · Operational Daily Record · M0.1 substrate.

⛔ READ FIRST:
  /app/memory/ODR_DATA_MODEL.md
  /app/memory/ODR_MIGRATION_PLAN.md
  /app/memory/FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md
  /app/memory/ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md
  /app/memory/OPERATIONAL_LINKING_RULES.md
  /app/memory/OPERATIONAL_TIMELINE_FOUNDATION.md
  /app/memory/ODR_COACHING_GUIDANCE_ADDENDUM.md

The ODR substrate is the system of record for all field-day
intelligence. One document per (project_number, crew_id,
report_date). Multiple consumers, zero duplicate reporting.

Doctrine inheritance (substrate-day-one):
  * FIELD_LEADERSHIP_VISIBILITY_DOCTRINE — FLL-1..FLL-6 projector
  * OPERATIONAL_LINKING_RULES — chronology + audit participation
  * TIMELINE_DOCTRINE — emits via operational_links
  * ODR_COACHING_GUIDANCE_ADDENDUM — prompt_key refs in readiness
  * ROLE_AWARE_VISIBILITY_MODEL — restrict at projector + UI

Substrate gates (M0.1):
  * Pydantic envelope covering D1–D8 + continuity + governance + coaching
  * Collections + indexes (8 total: odr, odr_section_events,
    odr_translation_events, odr_preload_attempts, odr_amendments,
    odr_attachments, odr_photos, odr_consumer_index)
  * Append-only events protected by trendline integrity probe
  * Mongo `_id` excluded from every response
  * TRUST-TIME-1 timestamps (Z-suffixed UTC ISO)
  * Hard DELETE forbidden (status flips only)

Substrate scope:
  * POST /api/odr                  create draft
  * PATCH /api/odr/{id}             partial update
  * POST /api/odr/{id}/submit       transition draft → submitted (readiness pass)
  * GET /api/odr                    list (FLL-aware scope)
  * GET /api/odr/{id}               full record (FLL-aware projector)
  * POST /api/odr/{id}/section-event  append telemetry row
  * GET /api/odr/{id}/section-events  audit trail read

Out of scope for M0.1 (deferred to M0.2+):
  * PDF rendering
  * Public link preload + continuity engine
  * Amendment service post-24h-window
  * Per-consumer projector materialized views
  * Frontend forms / dashboards
  * Migration script from daily_reports
"""
from .routes import build_odr_router
from .indexes import ensure_odr_indexes
from .continuity import build_odr_continuity_router, ensure_continuity_indexes
from .amendments import build_odr_amendments_router
from .pdf import build_odr_pdf_router
from .guidance_routes import build_odr_guidance_router

__all__ = [
    "build_odr_router",
    "ensure_odr_indexes",
    "build_odr_continuity_router",
    "ensure_continuity_indexes",
    "build_odr_amendments_router",
    "build_odr_pdf_router",
    "build_odr_guidance_router",
]
