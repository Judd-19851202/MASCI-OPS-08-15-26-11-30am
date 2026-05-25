"""iter416 · Phase 19.1 · Day-1 Live Ops Debrief Capture endpoint.
iter429.1 · Phase 28.1 · Extended to support Week-1 debriefs as well.

Admin-only POST that writes a single markdown file to /app/memory/
DLS_{DAY1|WEEK1}_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md.

Doctrine guard:
  - Admin only · NO database storage · NO analytics · NO scoring.
  - Idempotent same-day: re-submission overwrites the file with the
    latest version (operational reality > append-only audit log here).
  - Markdown file = operational memory · no schema, no parsing.
  - Day-1 and Week-1 share the SAME endpoint surface · the only knob
    is `debrief_type` ("day-1" or "week-1"). Two question sets, one
    submit path. Calm + simple per Phase 28.1 doctrine.
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


# ─── Canonical question lists · DOCTRINE-LOCKED ───────────────────────
# Day-1: Phase 19.1 directive · 10 doctrine-approved + 2 anti-creep.
# Week-1: Phase 28.1 directive · 14 questions targeting REPEATED patterns
#         after a week of real production usage.
# Modifying either list requires a new phase directive — operators answer
# the SAME questions every review so observations are comparable across
# deploys.
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

WEEK1_QUESTIONS: List[Dict[str, str]] = [
    {"id": "q1",  "label": "What friction repeated more than once?"},
    {"id": "q2",  "label": "Where did users still hesitate?"},
    {"id": "q3",  "label": "Which workflows felt natural after a week?"},
    {"id": "q4",  "label": "Which workflows still felt confusing?"},
    {"id": "q5",  "label": "Did dispatch trust DLS status?"},
    {"id": "q6",  "label": "Did drivers consistently update lifecycle states?"},
    {"id": "q7",  "label": "Did Shop recovery continuity work?"},
    {"id": "q8",  "label": "Did PM haul awareness help production?"},
    {"id": "q9",  "label": "Did attachments/photos reduce calls or confusion?"},
    {"id": "q10", "label": "Did passkey/device sign-in reduce login friction?"},
    {"id": "q11", "label": "Were any Spanish translations confusing in real use?"},
    {"id": "q12", "label": "What should remain simple and untouched?"},
    {"id": "q13", "label": "What should NOT be built even if requested?"},
    {"id": "q14", "label": "What is the highest-value surgical improvement now?"},
]

# Lookup table — every debrief variant is a (canonical-questions, title,
# filename-prefix) triple. Adding a third variant later is a matter of
# extending this map; the router code stays identical.
_DEBRIEF_VARIANTS = {
    "day-1": {
        "questions": DAY1_QUESTIONS,
        "title": "DLS Day-1 Live Ops Debrief",
        "kicker": "Day-1 review",
        "filename_prefix": "DLS_DAY1_LIVE_OPS_DEBRIEF",
        "intro": ("Capture real operational friction while it is still fresh. "
                  "Only document repeated hesitation, confusion, downstream "
                  "continuity problems, or operational slowdowns."),
    },
    "week-1": {
        "questions": WEEK1_QUESTIONS,
        "title": "DLS Week-1 Live Ops Debrief",
        "kicker": "Week-1 review",
        "filename_prefix": "DLS_WEEK1_LIVE_OPS_DEBRIEF",
        "intro": ("Capture repeated operational patterns from the first week "
                  "of real production usage. Focus on what REPEATED — not "
                  "isolated requests. Build from operational truth."),
    },
}


def _resolve_variant(debrief_type: Optional[str]) -> Dict[str, Any]:
    key = (debrief_type or "day-1").strip().lower()
    if key not in _DEBRIEF_VARIANTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown debrief_type: {debrief_type!r}. Use 'day-1' or 'week-1'.",
        )
    return _DEBRIEF_VARIANTS[key]


class Day1DebriefSubmit(BaseModel):
    answers: Dict[str, str] = Field(default_factory=dict)
    operational_notes: Optional[str] = ""
    doctrine_observations: Optional[str] = ""
    # iter429.1 · Phase 28.1 · variant selector. Default = "day-1" so
    # existing clients (Day-1-only) keep working unchanged.
    debrief_type: Optional[str] = "day-1"


def _safe_lang_value(s: Optional[str]) -> str:
    """Trim and bound a single answer to 4000 chars to prevent abuse."""
    if not s:
        return ""
    s = str(s).strip()
    return s[:4000] if len(s) > 4000 else s


def _render_markdown(
    variant: Dict[str, Any],
    date_str: str,
    iso_ts: str,
    actor_email: str,
    answers: Dict[str, str],
    operational_notes: str,
    doctrine_observations: str,
) -> str:
    """Render the debrief into clean, calm markdown."""
    lines: List[str] = []
    lines.append(f"# {variant['title']} — {date_str}")
    lines.append("")
    lines.append(f"**Captured**: {iso_ts}  ")
    lines.append(f"**Submitting admin**: {actor_email or 'admin'}")
    lines.append("")
    lines.append(f"> {variant['intro']}")
    lines.append("")
    lines.append(f"## {variant['kicker']} questions")
    lines.append("")
    for q in variant["questions"]:
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
    async def list_questions_day1(
        actor: Dict[str, Any] = Depends(require_admin_dep),  # noqa: ARG001
    ):
        """Return the canonical Day-1 question list so the FE never drifts."""
        return {"debrief_type": "day-1", "questions": DAY1_QUESTIONS}

    # iter429.1 · Phase 28.1 · Week-1 questions endpoint.
    @router.get("/week-1-debrief/questions")
    async def list_questions_week1(
        actor: Dict[str, Any] = Depends(require_admin_dep),  # noqa: ARG001
    ):
        """Return the canonical Week-1 question list."""
        return {"debrief_type": "week-1", "questions": WEEK1_QUESTIONS}

    async def _submit_impl(
        payload: Day1DebriefSubmit,
        actor: Dict[str, Any],
        *,
        forced_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        # `forced_type` lets the dedicated /week-1-debrief route override
        # whatever payload.debrief_type says — keeps URL = truth.
        variant_key = (forced_type or payload.debrief_type or "day-1").lower()
        variant = _resolve_variant(variant_key)

        # Sanitize input against the resolved question set.
        answers = {q["id"]: _safe_lang_value(payload.answers.get(q["id"], ""))
                   for q in variant["questions"]}
        ops_notes = _safe_lang_value(payload.operational_notes)
        doctrine_obs = _safe_lang_value(payload.doctrine_observations)

        # `require_admin` legacy dep returns True (bool) for the
        # break-glass /api/admin/login path; multi-login deps return
        # dicts. Handle both shapes gracefully.
        if isinstance(actor, dict):
            actor_email = actor.get("email") or actor.get("username") or "admin"
        else:
            actor_email = "admin"

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        iso_ts = now.isoformat()

        # Defensive: validate date_str (no path traversal)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise HTTPException(status_code=500, detail="Date format error")

        md = _render_markdown(variant, date_str, iso_ts, str(actor_email),
                              answers, ops_notes, doctrine_obs)

        # Write to /app/memory · idempotent same-day overwrite
        try:
            _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            file_path = _MEMORY_DIR / f"{variant['filename_prefix']}_{date_str}.md"
            file_path.write_text(md, encoding="utf-8")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Memory write failed: {e}")

        return {
            "ok": True,
            "debrief_type": variant_key,
            "filename": file_path.name,
            "path": f"/app/memory/{file_path.name}",
            "captured_at": iso_ts,
            "question_count": len(variant["questions"]),
            "captured_admin": actor_email,
        }

    @router.post("/day-1-debrief")
    async def submit_debrief_day1(
        payload: Day1DebriefSubmit,
        actor: Dict[str, Any] = Depends(require_admin_dep),
    ):
        # Force "day-1" so this URL is unambiguous regardless of payload.
        return await _submit_impl(payload, actor, forced_type="day-1")

    # iter429.1 · Phase 28.1 · Week-1 submit endpoint (mirror surface).
    @router.post("/week-1-debrief")
    async def submit_debrief_week1(
        payload: Day1DebriefSubmit,
        actor: Dict[str, Any] = Depends(require_admin_dep),
    ):
        return await _submit_impl(payload, actor, forced_type="week-1")

    return router
