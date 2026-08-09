from __future__ import annotations

from fastapi import HTTPException


RELEASE_DEFERRED_SURFACES = {
    "daily_report_dedicated_ai_summary",
    "executive_monday_briefing_pdf",
    "internal_certification_route",
    "pm_schedule_email_review",
}


def is_release_deferred(surface_key: str) -> bool:
    return surface_key in RELEASE_DEFERRED_SURFACES


def raise_release_deferred_404(surface_key: str) -> None:
    raise HTTPException(
        status_code=404,
        detail={
            "code": "release_deferred_surface",
            "surface": surface_key,
            "message": "This surface is deferred and hidden in the current release bundle.",
        },
    )


__all__ = [
    "RELEASE_DEFERRED_SURFACES",
    "is_release_deferred",
    "raise_release_deferred_404",
]