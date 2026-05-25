"""iter416 · Phase 19.1 · Day-1 Live Ops Debrief Capture endpoint.

Admin-only POST that writes a single markdown file to /app/memory/
DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md.

Doctrine guard:
  - Admin only · NO database storage · NO analytics · NO scoring.
  - Idempotent same-day: re-submission overwrites the file with the
    latest version (operational reality > append-only audit log here).
  - Markdown file = operational memory · no schema, no parsing.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field


# Resolve repo memory directory · /app/memory
_MEMORY_DIR = Path(__file__).resolve().parents[2] / "memory"


# ─── Canonical question list · DOCTRINE-LOCKED ────────────────────────
# Phase 19.1 directive: 10 doctrine-approved Day-1 questions + 2 new
# anti-creep questions (#11, #12). Modifying this list requires a new
# phase directive — operators answer the SAME questions every Day-1
# review so observations are comparable across deploys.
DAY1_QUESTIONS: List[Dict[str, str]] = [
    {"id": "q1",  "label": "Where did dispatch hesitate?"},
    {"id": "q2",  "label": "What was difficult to find?"},
    {"id": "q3",  "label": "Did drivers understand shift start?"},
    {"id": "q4",  "label": "Did drivers understand assignment flow?"},
    {"id": "q5",  "label": "Was assignment issuance fast enough?"},
    {"id": "q6",  "label": "Did PM haul visibility help production awareness?"},
    {"id": "q7",  "label": "Did Shop breakdown continuity make sense?"},
    {"id": "q8",  "label": "Were any dropdowns confusing?"},
    {"id": "q9",  "label": "Were any wait states missing or unclear?"},
    {"id": "q10", "label": "Where did users pause too long or become uncertain?"},
    {"id": "q11", "label": "What felt unnecessary or overly complicated?"},
    {"id": "q12", "label": "What should remain simple and untouched?"},
]


class Day1DebriefSubmit(BaseModel):
    answers: Dict[str, str] = Field(default_factory=dict)
    operational_notes: Optional[str] = ""
    doctrine_observations: Optional[str] = ""


def _safe_lang_value(s: Optional[str]) -> str:
    """Trim and bound a single answer to 4000 chars to prevent abuse."""
    if not s:
        return ""
    s = str(s).strip()
    return s[:4000] if len(s) > 4000 else s


def _render_markdown(
    date_str: str,
    iso_ts: str,
    actor_email: str,
    answers: Dict[str, str],
    operational_notes: str,
    doctrine_observations: str,
) -> str:
    """Render the debrief into clean, calm markdown."""
    lines: List[str] = []
    lines.append(f"# DLS Day-1 Live Ops Debrief — {date_str}")
    lines.append("")
    lines.append(f"**Captured**: {iso_ts}  ")
    lines.append(f"**Submitting admin**: {actor_email or 'admin'}")
    lines.append("")
    lines.append("> Capture real operational friction while it is still fresh. "
                 "Only document repeated hesitation, confusion, downstream continuity "
                 "problems, or operational slowdowns.")
    lines.append("")
    lines.append("## Day-1 questions")
    lines.append("")
    for q in DAY1_QUESTIONS:
        ans = _safe_lang_value(answers.get(q["id"]))
        lines.append(f"### {q['label']}")
        lines.append("")
        lines.append(ans if ans else "_(no observation captured)_")
        lines.append("")
    if operational_notes.strip():
        lines.append("## Operational notes")
        lines.append("")
        lines.append(operational_notes.strip())
        lines.append("")
    if doctrine_observations.strip():
        lines.append("## Doctrine observations")
        lines.append("")
        lines.append(doctrine_observations.strip())
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Capture operational hesitation and continuity gaps — not feature "
                 "wishlists. Build from repeated operational patterns, not isolated requests._")
    lines.append("")
    return "\n".join(lines)


def build_day1_debrief_router(
    require_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/admin/dls", tags=["dispatch-lifecycle-debrief"])

    @router.get("/day-1-debrief/questions")
    async def list_questions(
        actor: Dict[str, Any] = Depends(require_admin_dep),  # noqa: ARG001
    ):
        """Return the canonical 12-question list so the FE never drifts."""
        return {"questions": DAY1_QUESTIONS}

    @router.post("/day-1-debrief")
    async def submit_debrief(
        payload: Day1DebriefSubmit,
        actor: Dict[str, Any] = Depends(require_admin_dep),
    ):
        # Sanitize input
        answers = {q["id"]: _safe_lang_value(payload.answers.get(q["id"], ""))
                   for q in DAY1_QUESTIONS}
        ops_notes = _safe_lang_value(payload.operational_notes)
        doctrine_obs = _safe_lang_value(payload.doctrine_observations)
        # `require_admin` legacy dep returns True (bool) for the break-glass
        # /api/admin/login path; multi-login deps may return dicts. Handle
        # both shapes gracefully — admin identity isn't required for the
        # markdown content beyond a label.
        if isinstance(actor, dict):
            actor_email = actor.get("email") or actor.get("username") or "admin"
        else:
            actor_email = "admin"

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        iso_ts = now.isoformat()

        # Defensive: validate date_str matches expected pattern (no path traversal)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise HTTPException(status_code=500, detail="Date format error")

        md = _render_markdown(date_str, iso_ts, str(actor_email), answers,
                              ops_notes, doctrine_obs)

        # Write to /app/memory · idempotent same-day overwrite
        try:
            _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            file_path = _MEMORY_DIR / f"DLS_DAY1_LIVE_OPS_DEBRIEF_{date_str}.md"
            file_path.write_text(md, encoding="utf-8")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Memory write failed: {e}")

        return {
            "ok": True,
            "filename": file_path.name,
            "path": f"/app/memory/{file_path.name}",
            "captured_at": iso_ts,
            "question_count": len(DAY1_QUESTIONS),
            "captured_admin": actor_email,
        }

    return router
