"""iter329 · Scheduled Cultural Banner Calendar.

Lightweight, deterministic auto-activation of major cultural banners.
No cron, no calendar UI, no recurring-event system — a tiny config
list of annual dates and an idempotent ensure-fn invoked lazily from
``GET /api/banners/active``.

Design rules:
  • Holidays are computed each year (some are fixed-date, some
    floating like "last Monday of May" for Memorial Day).
  • Each holiday has a `template_id` matching the frontend cultural
    template, plus the curated EN + ES copy (mirrored from
    ``frontend/src/lib/hubBannerTemplates.js`` so the scheduler has
    zero frontend dependency).
  • Activation window: 24 h BEFORE the holiday → 24 h AFTER.
  • Duplicate prevention: before inserting, the function checks for an
    active banner with the same ``template_id`` whose
    ``expires_at`` ≥ this year's window end. If one exists, no-op.
  • Operational severity precedence is UNCHANGED — cultural banners
    sort at priority 9 (see ``routes/hub_banners.py · sev_rank``).
    They cannot outrank hurricanes, heat warnings, lightning
    advisories, stand-downs, or any other operational alert.

To freeze banner development after this iter, the contract is:
  • Add a holiday → append one entry to ``CULTURAL_CALENDAR`` below
    with the matching ``template_id`` from the frontend templates.
  • Retire a holiday → remove the entry. Already-posted banners
    expire naturally via their stored ``expires_at`` and are
    purged by the existing cleanup invariant.
"""
from __future__ import annotations

import calendar
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

log = logging.getLogger("masci.cultural_banner_calendar")


# ────────────────────────────── Date helpers ──────────────────────────


def _utc_today() -> datetime:
    return datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> datetime:
    """`weekday` = 0..6 (Mon..Sun). `n` = 1..5 → nth occurrence."""
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday_of_month(year: int, month: int, weekday: int) -> datetime:
    last_day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, last_day, tzinfo=timezone.utc)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)


# ─────────────────────────── Holiday resolvers ───────────────────────


def _new_year(year: int) -> datetime:
    return datetime(year, 1, 1, tzinfo=timezone.utc)


def _memorial_day(year: int) -> datetime:
    # Last Monday of May.
    return _last_weekday_of_month(year, 5, 0)


def _independence_day(year: int) -> datetime:
    return datetime(year, 7, 4, tzinfo=timezone.utc)


def _labor_day(year: int) -> datetime:
    # First Monday of September.
    return _nth_weekday_of_month(year, 9, 0, 1)


def _veterans_day(year: int) -> datetime:
    return datetime(year, 11, 11, tzinfo=timezone.utc)


def _thanksgiving(year: int) -> datetime:
    # Fourth Thursday of November.
    return _nth_weekday_of_month(year, 11, 3, 4)


def _christmas(year: int) -> datetime:
    return datetime(year, 12, 25, tzinfo=timezone.utc)


# ─────────────────────────── Calendar entries ────────────────────────


@dataclass(frozen=True)
class CulturalEntry:
    template_id: str            # matches frontend hubBannerTemplates.js id
    resolver: Callable[[int], datetime]
    title_en: str
    title_es: str
    body_en: str
    body_es: str
    pre_hours: int = 24         # activate this many hours BEFORE
    post_hours: int = 24        # remain active this many hours AFTER

    def window(self, year: int) -> tuple[datetime, datetime]:
        anchor = self.resolver(year)
        return (
            anchor - timedelta(hours=self.pre_hours),
            anchor + timedelta(hours=self.post_hours),
        )


# Mirrors the curated copy in /app/frontend/src/lib/hubBannerTemplates.js
# (cultural tier). Keep these two in sync — the frontend templates also
# power the admin "compose from template" picker.
CULTURAL_CALENDAR: tuple[CulturalEntry, ...] = (
    CulturalEntry(
        template_id="new_year",
        resolver=_new_year,
        title_en="New Year — Forward Together",
        title_es="Año Nuevo — Adelante Juntos",
        body_en="Another year of work behind us. Another year of opportunity ahead. Thank you for the standards you held in the past year, and for the standards we will hold together in the next one.",
        body_es="Otro año de trabajo detrás de nosotros. Otro año de oportunidad por delante. Gracias por los estándares que mantuvieron en el año pasado, y por los estándares que mantendremos juntos en el próximo.",
    ),
    CulturalEntry(
        template_id="memorial_day",
        resolver=_memorial_day,
        title_en="Memorial Day — In Remembrance",
        title_es="Día de los Caídos — En Memoria",
        body_en="Memorial Day reminds us that freedom and opportunity were secured through sacrifice. We honor the men and women who gave their lives in service to our nation. Have a safe weekend, and look out for one another.",
        body_es="El Día de los Caídos nos recuerda que la libertad y la oportunidad se aseguraron mediante el sacrificio. Honramos a los hombres y mujeres que dieron su vida en servicio a nuestra nación. Tengan un fin de semana seguro, y cuídense unos a otros.",
    ),
    CulturalEntry(
        template_id="independence_day",
        resolver=_independence_day,
        title_en="Independence Day",
        title_es="Día de la Independencia",
        body_en="Independence Day is a moment to recognize the country that gives MASCI the opportunity to build, employ, and contribute. Thank you for the work you do. Travel safe, stay hydrated, and look out for your crew.",
        body_es="El Día de la Independencia es un momento para reconocer al país que da a MASCI la oportunidad de construir, emplear y contribuir. Gracias por el trabajo que hacen. Viajen seguros, manténganse hidratados, y cuiden a su cuadrilla.",
    ),
    CulturalEntry(
        template_id="labor_day",
        resolver=_labor_day,
        title_en="Labor Day — In Recognition of the Trade",
        title_es="Día del Trabajo — Reconocimiento al Oficio",
        body_en="Labor Day recognizes the people who build the country with their hands. That is every operator, laborer, foreman, mechanic, and superintendent at MASCI. Thank you for the standards you hold and the work you deliver.",
        body_es="El Día del Trabajo reconoce a las personas que construyen el país con sus manos. Eso es cada operador, obrero, capataz, mecánico y superintendente en MASCI. Gracias por los estándares que mantienen y el trabajo que entregan.",
    ),
    CulturalEntry(
        template_id="veterans_day",
        resolver=_veterans_day,
        title_en="Veterans Day — Thank You for Your Service",
        title_es="Día del Veterano — Gracias por su Servicio",
        body_en="To every veteran on our crews and to every veteran in our families — thank you. The discipline, professionalism, and accountability you carry into this work makes MASCI better. We are proud you are with us.",
        body_es="A cada veterano en nuestras cuadrillas y a cada veterano en nuestras familias — gracias. La disciplina, profesionalismo y responsabilidad que traen a este trabajo hace mejor a MASCI. Estamos orgullosos de tenerlos con nosotros.",
    ),
    CulturalEntry(
        template_id="thanksgiving",
        resolver=_thanksgiving,
        title_en="Thanksgiving — From the MASCI Family",
        title_es="Día de Acción de Gracias — De la Familia MASCI",
        body_en="Thanksgiving is a moment to recognize what we have built together. Whatever your tradition, take the time to be with the people who matter to you. Travel safe, drive rested, and we will see you back on the work.",
        body_es="El Día de Acción de Gracias es un momento para reconocer lo que hemos construido juntos. Sea cual sea su tradición, tomen el tiempo de estar con las personas que les importan. Viajen seguros, conduzcan descansados, y nos veremos de regreso en el trabajo.",
    ),
    CulturalEntry(
        template_id="christmas",
        resolver=_christmas,
        # Christmas runs longer — pre 48h / post 48h — covering Christmas Eve & Day 2.
        pre_hours=48,
        post_hours=48,
        title_en="Christmas — From the MASCI Family",
        title_es="Navidad — De la Familia MASCI",
        body_en="From every superintendent, PM, mechanic, foreman, and crew at MASCI — Merry Christmas to you and your family. Drive carefully through the holiday traffic. We will see you back on the work in the new year.",
        body_es="De cada superintendente, PM, mecánico, capataz, y cuadrilla en MASCI — Feliz Navidad a ustedes y a sus familias. Conduzcan con cuidado durante el tráfico de las fiestas. Nos veremos de regreso en el trabajo en el año nuevo.",
    ),
)


# ─────────────────────────── Idempotent ensure ───────────────────────


def _active_now(entry: CulturalEntry, now: datetime) -> Optional[tuple[datetime, datetime]]:
    """Return the (start, end) window if `now` falls inside the entry's
    activation range for either the current or next calendar year.
    Otherwise None.
    """
    for year_off in (0, 1, -1):
        start, end = entry.window(now.year + year_off)
        if start <= now <= end:
            return (start, end)
    return None


async def ensure_cultural_banners(db, now: Optional[datetime] = None) -> list[dict]:
    """Idempotent — call as often as you like. Posts any cultural
    banner whose 24-hour activation window contains ``now`` and is
    not already represented by an active banner with the same
    ``template_id`` and an ``expires_at`` >= window end.

    Async — uses the motor pattern of the surrounding banner module.

    Returns the list of newly-inserted banner dicts (typically empty
    except on the boundary minute when a banner activates).

    Failure modes:
      • DB unavailable → caught and logged; returns [].
      • Duplicate (already active) → no-op, returns [].
      • Stale matching template with different expires_at → still
        treated as active (we trust the existing record's expiry).
    """
    inserted: list[dict] = []
    now = now or datetime.now(tz=timezone.utc)
    try:
        coll = db.hub_banners
    except Exception as e:  # pragma: no cover — defensive
        log.warning("cultural calendar: db unavailable (%s)", e)
        return inserted

    for entry in CULTURAL_CALENDAR:
        window = _active_now(entry, now)
        if window is None:
            continue
        start, end = window
        # iter329 · duplicate protection — match by template_id and
        # an expires_at that overlaps this year's window. Manual
        # admin-posted matches are honored (we don't re-post).
        try:
            existing = await coll.find_one({
                "template_id": entry.template_id,
                "expires_at": {"$gte": start.isoformat()},
            })
        except Exception as e:
            log.warning("cultural calendar: lookup failed (%s)", e)
            continue
        if existing:
            continue

        doc = {
            "id": uuid.uuid4().hex,
            "title_en": entry.title_en,
            "title_es": entry.title_es,
            "body_en": entry.body_en,
            "body_es": entry.body_es,
            "severity": "cultural",
            "require_ack": False,
            "auto_posted": True,            # mark as scheduler-posted
            "auto_posted_iter": "iter329",
            "template_id": entry.template_id,
            "created_at": now.isoformat(),
            "expires_at": end.isoformat(),
            "created_by": "cultural-calendar",
        }
        try:
            await coll.insert_one(doc)
        except Exception as e:
            log.warning("cultural calendar: insert failed for %s (%s)",
                        entry.template_id, e)
            continue
        doc.pop("_id", None)
        inserted.append(doc)
        log.info("cultural calendar: auto-posted %s (window %s → %s)",
                 entry.template_id, start.isoformat(), end.isoformat())

    return inserted
