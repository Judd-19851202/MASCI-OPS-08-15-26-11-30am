"""
routes/odr/indexes.py — Mongo index management for the ODR substrate.

Index strategy from ODR_DATA_MODEL.md §1 + addenda §A9 + §P8.

Collections owned by this substrate:
  odr                       — system of record
  odr_section_events        — append-only field-level transitions
  odr_photos                — photo registry (refs from ODR.photos)
  odr_attachments           — non-photo evidence registry
  odr_amendments            — Super+ amendments (append-only)
  odr_translation_events    — bilingual audit (append-only)
  odr_preload_attempts      — public-link continuity audit (append-only)
  odr_consumer_index        — derived projector views (refreshed)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def ensure_odr_indexes(db) -> None:
    # ── odr (the system of record) ───────────────────────────────────
    await db.odr.create_index("id", unique=True)
    await db.odr.create_index("doc_id", unique=True)
    await db.odr.create_index(
        [("project.project_number", 1), ("project.report_date", -1), ("crew_profile.crew_id", 1)]
    )
    await db.odr.create_index([("project.report_date", -1)])
    await db.odr.create_index(
        [("crew_profile.crew_type", 1), ("project.report_date", -1)]
    )
    await db.odr.create_index([("status", 1), ("project.report_date", -1)])
    await db.odr.create_index([("project.foreman_uid", 1), ("project.report_date", -1)])
    await db.odr.create_index([("project.pm_uid", 1), ("project.report_date", -1)])
    await db.odr.create_index(
        [("work_areas.work_area_id", 1), ("project.report_date", -1)]
    )
    await db.odr.create_index(
        [("production_segments.crew_type", 1), ("project.report_date", -1)]
    )
    await db.odr.create_index(
        [("safety.any_event", 1), ("project.report_date", -1)]
    )
    await db.odr.create_index(
        [("public_access.link_id", 1), ("project.report_date", -1)]
    )

    # ── odr_section_events (append-only) ─────────────────────────────
    await db.odr_section_events.create_index("event_id", unique=True)
    await db.odr_section_events.create_index([("odr_id", 1), ("at_utc", 1)])

    # ── odr_photos ───────────────────────────────────────────────────
    await db.odr_photos.create_index("photo_id", unique=True)
    await db.odr_photos.create_index([("odr_id", 1), ("tag", 1)])

    # ── odr_attachments ──────────────────────────────────────────────
    await db.odr_attachments.create_index("attachment_id", unique=True)
    await db.odr_attachments.create_index([("odr_id", 1), ("kind", 1)])

    # ── odr_amendments (append-only) ─────────────────────────────────
    await db.odr_amendments.create_index("amendment_id", unique=True)
    await db.odr_amendments.create_index([("odr_id", 1), ("at_utc", -1)])
    await db.odr_amendments.create_index([("actor_uid", 1), ("at_utc", -1)])
    await db.odr_amendments.create_index([("actor_role", 1), ("at_utc", -1)])

    # ── odr_translation_events (append-only) ─────────────────────────
    await db.odr_translation_events.create_index([("odr_id", 1), ("at_utc", 1)])

    # ── odr_preload_attempts (append-only) ───────────────────────────
    await db.odr_preload_attempts.create_index("attempt_id", unique=True)
    await db.odr_preload_attempts.create_index(
        [("project_id", 1), ("requested_at_utc", -1)]
    )
    await db.odr_preload_attempts.create_index(
        [("public_link_id", 1), ("requested_at_utc", -1)]
    )
    await db.odr_preload_attempts.create_index(
        [("outcome", 1), ("requested_at_utc", -1)]
    )

    # ── odr_consumer_index (derived projector views) ────────────────
    await db.odr_consumer_index.create_index([("consumer", 1), ("odr_id", 1)], unique=True)
    await db.odr_consumer_index.create_index(
        [("project_id", 1), ("report_date", -1), ("consumer", 1)]
    )

    logger.info("ODR substrate indexes ensured (8 collections).")
