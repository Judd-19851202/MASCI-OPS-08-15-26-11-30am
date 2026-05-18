"""Contextual Operational Guidance — HelpTip Registry.

Operator directive (2026-05-18): build a unified contextual-guidance
architecture using reusable components instead of hard-coding help
text into every form. This is the backend half — a centralized,
RBAC-aware, bilingual registry of short coaching tips bound to
specific form_key contexts.

Design rules:
  • Tips are short (1-3 sentences). Coaching, not documentation.
  • Each tip is bound to a `form_key` (e.g., "daily-report.crew") and
    a `kind` (why · mistake · example · next · escalate · who · when).
  • `scopes` follows the same RBAC contract as guidance articles:
    "public" = anonymous OK; portal keys = portal-token-required;
    "admin" = admin-only.
  • EN body in `body`; Spanish in `body_es` (merged at runtime from
    tips_es.TIPS_ES — same pattern as articles).
  • Frontend can fetch all tips for a form_key in one call.

Initial seed: Daily Reports (operator's #1 ROI target). Subsequent
passes will add Safety Incidents, Pre-Op Forms, Equipment Checkout,
Time Verification, Write-Ups, Material Requests, Dispatch Requests.
"""

from __future__ import annotations

ALLOWED_KINDS = {"why", "mistake", "example", "next", "escalate", "who", "when"}


# ─────────────────────────────────────────────────────────────────────
# Initial seed — Daily Reports (Field Leadership form)
# Form keys group by section. Frontend fetches by form_key prefix.
# ─────────────────────────────────────────────────────────────────────
_TIPS: list[dict] = [
    # ── daily-report (top-level / general) ───────────────────────────
    {
        "form_key": "daily-report",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why Daily Reports matter",
        "body":
            "A Daily Report becomes the official record of the workday. HR uses it "
            "for time, PM for project status, Safety for incident context. Build it "
            "like someone will read it six months from now — because someone will.",
    },
    {
        "form_key": "daily-report",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who sees this",
        "body":
            "Your PM, HR, Safety, and admin. Owners on a project review may also pull "
            "it. Field staff outside the project usually cannot.",
    },
    {
        "form_key": "daily-report",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you submit",
        "body":
            "Hours flow to HR for time verification. Materials and equipment flow "
            "to PM cost-coding. Photos and notes attach to the project record. "
            "Edits after submission are tracked.",
    },
    {
        "form_key": "daily-report",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to escalate",
        "body":
            "If something happened on site that needs Safety attention — injury, "
            "near-miss, third-party — file the Safety Incident form too. The Daily "
            "Report alone is not enough.",
    },

    # ── daily-report.crew ────────────────────────────────────────────
    {
        "form_key": "daily-report.crew",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the crew section matters",
        "body":
            "This is the field's source of truth for hours worked. HR reconciles "
            "payroll against this. If a name or hour count is wrong here, "
            "someone's paycheck is wrong on Friday.",
    },
    {
        "form_key": "daily-report.crew",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Listing a worker who didn't show. Listing hours by 'feel' instead of "
            "by the actual time on site. Forgetting to remove someone who left "
            "early. Round to the nearest 15 minutes, not the nearest hour.",
    },
    {
        "form_key": "daily-report.crew",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example",
        "body":
            "'Smith, J — 6:00 to 14:30 (8.0h reg, 0.5h lunch)' is good. "
            "'Smith — full day' is not — payroll cannot verify it.",
    },

    # ── daily-report.equipment ───────────────────────────────────────
    {
        "form_key": "daily-report.equipment",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why equipment matters",
        "body":
            "This feeds project utilisation and equipment-allocation reports. If "
            "a unit isn't listed here, finance can't bill it to the project.",
    },
    {
        "form_key": "daily-report.equipment",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Listing equipment that wasn't actually used. Skipping idle hours "
            "(idle still counts against utilisation). Listing the wrong unit ID — "
            "always confirm from the side of the unit, not memory.",
    },

    # ── daily-report.materials ───────────────────────────────────────
    {
        "form_key": "daily-report.materials",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why materials matter",
        "body":
            "Materials drive cost-code allocation. The PM's project margin is "
            "calculated against what gets recorded here. Approximate is fine — "
            "guess wildly is not.",
    },
    {
        "form_key": "daily-report.materials",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example",
        "body":
            "'Stone, 3/4\" base — 18 tons placed at the north pad' is good. "
            "'Some stone' is not — finance can't cost-code it.",
    },

    # ── daily-report.photos ──────────────────────────────────────────
    {
        "form_key": "daily-report.photos",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why photos matter",
        "body":
            "Photos protect everyone. A photo of finished work today is "
            "incontestable evidence months later when a dispute lands. They're "
            "cheap to take and impossible to recreate after the fact.",
    },
    {
        "form_key": "daily-report.photos",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Taking photos from too far away (no scale). Photographing only "
            "finished work and not progress shots. Forgetting a photo of any "
            "damage you found at start of day — that's how you avoid being blamed "
            "for it.",
    },

    # ── daily-report.narrative ───────────────────────────────────────
    {
        "form_key": "daily-report.narrative",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the narrative matters",
        "body":
            "The narrative is what a PM or admin reads first when something looks "
            "off. Two sentences of context now save twenty minutes of phone calls "
            "in a week.",
    },
    {
        "form_key": "daily-report.narrative",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Writing 'business as usual' when it wasn't. Writing only what went "
            "well. Forgetting weather/conditions that slowed the crew — that "
            "context is exactly what defends against a 'why was production low?' "
            "question later.",
    },
    {
        "form_key": "daily-report.narrative",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example",
        "body":
            "'Wind 25+ mph all morning; crane work delayed 2.5h. Resumed 11:00, "
            "completed pour by 15:30. No incidents.' is excellent. It explains "
            "why production was low AND that nothing else went wrong.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter210 · Safety Incidents
    # High-risk, legally sensitive, emotionally charged, commonly
    # under-documented. Coaching here is the highest-value preventative
    # work in the platform.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "incident",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why this report matters",
        "body":
            "An incident report is a legal document the moment you submit it. "
            "OSHA, insurance, and any future investigation reads this. Calm, "
            "specific, factual now beats apologetic and vague later.",
    },
    {
        "form_key": "incident",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who sees this",
        "body":
            "Safety staff (immediately), PM and HR (within 24h), Admin, and any "
            "external party formally involved in the response. Treat every field "
            "as if a lawyer will read it tomorrow.",
    },
    {
        "form_key": "incident",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you submit",
        "body":
            "Safety opens an investigation. Corrective actions are assigned and "
            "tracked to closure. The incident attaches to the project and any "
            "involved equipment. You may be asked for more detail — that's normal.",
    },
    {
        "form_key": "incident",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to call before reporting",
        "body":
            "Serious injury, hospitalization, fatality, or any third-party "
            "involvement: call your supervisor AND Safety on the phone first. "
            "Don't wait for the form to load. The form is the record; the phone "
            "call is the response.",
    },

    # ── incident.location ────────────────────────────────────────────
    {
        "form_key": "incident.location",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why location must be specific",
        "body":
            "'On the job site' isn't enough. The exact location decides which "
            "supervisor responds, which jurisdiction reports go to, and whether "
            "a recurring hazard surfaces in a pattern review.",
    },
    {
        "form_key": "incident.location",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example",
        "body":
            "'Station 12+50 northbound lane, near the east drainage inlet' is "
            "good. 'Highway 30' is not — the project is 8 miles long.",
    },
    {
        "form_key": "incident.location",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Typing a vague location to save 30 seconds, then having to revise "
            "it under pressure when Safety calls back. Use GPS if you can — "
            "phones are accurate enough for incident documentation.",
    },

    # ── incident.narrative (Section 04 'What Happened') ──────────────
    {
        "form_key": "incident.narrative",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the narrative is the heart of the report",
        "body":
            "Investigators reconstruct the event from this paragraph. Speculation "
            "weakens the record; observed facts strengthen it. Write what you "
            "saw, heard, and did — in that order.",
    },
    {
        "form_key": "incident.narrative",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Guessing about causes ('he must have…'). Assigning blame in the "
            "narrative. Skipping the timeline. Using emotional language. Every "
            "one of those weakens the report when it matters most.",
    },
    {
        "form_key": "incident.narrative",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example",
        "body":
            "'14:22 — operator dismounted excavator. Stepped on uneven ground "
            "near track. Lost balance, fell to right knee. Reported pain. Crew "
            "stopped work. First aid applied. 14:35 — supervisor notified.' is "
            "exactly the right shape.",
    },

    # ── incident.severity (Section 02) ───────────────────────────────
    {
        "form_key": "incident.severity",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why severity is hard but important",
        "body":
            "Severity drives the response timeline. 'Minor' that's actually "
            "moderate delays Safety attention; 'Serious' that's actually minor "
            "creates a false-alarm pattern. When in doubt, go one level up "
            "and let Safety down-grade.",
    },
    {
        "form_key": "incident.severity",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Down-playing severity to avoid hassle. Marking 'Near-Miss' for "
            "something with first-aid response. Calling anything with an "
            "ambulance 'Minor'. Severity is a Safety judgement, not a personal "
            "embarrassment scale.",
    },

    # ── incident.witnesses (Section 06) ──────────────────────────────
    {
        "form_key": "incident.witnesses",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why witnesses matter even when you saw it",
        "body":
            "Memory fades fast and stories drift. A witness statement captured "
            "within hours is worth more than ten captured next week. Even a "
            "one-line 'I saw X' from a coworker beats no record.",
    },
    {
        "form_key": "incident.witnesses",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Coaching a witness on what to write. Combining two witnesses into "
            "one entry. Skipping a witness because 'they only saw the end'. "
            "Each witness gets their own row, their own words, in their order.",
    },
    {
        "form_key": "incident.witnesses",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When a witness refuses to give a statement",
        "body":
            "Document that they were present, that you asked, and that they "
            "declined. Do not pressure them. Note the refusal in the narrative "
            "and tell Safety verbally. They handle it from there.",
    },

    # ── incident.corrective (Section 07) ─────────────────────────────
    {
        "form_key": "incident.corrective",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why corrective actions close the loop",
        "body":
            "An incident without a corrective action is a recurring incident. "
            "Even a small note — 'cones added at uneven step', 'crew briefed' "
            "— prevents the same event next month.",
    },
    {
        "form_key": "incident.corrective",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you list actions",
        "body":
            "Safety reviews and may add more. Each action gets an owner and a "
            "due date. The incident does not close until every action is "
            "verified complete and signed off — that's the audit trail.",
    },
    {
        "form_key": "incident.corrective",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Writing 'be more careful' as a corrective action. It's not actionable, "
            "not verifiable, and not auditable. State a concrete change: new "
            "signage, new procedure, retraining, equipment fix.",
    },
]


def all_tips() -> list[dict]:
    return list(_TIPS)


def tips_for(form_key: str, granted_scopes: set[str]) -> list[dict]:
    """Return all tips whose form_key matches OR is a prefix-parent of
    the requested form_key, filtered by RBAC.

    Example: requesting "daily-report.crew" returns tips bound to
    "daily-report.crew" AND tips bound to "daily-report" (the parent
    context) — so callers always get the broad + narrow coaching in
    one fetch.
    """
    if not form_key:
        return []
    if not isinstance(granted_scopes, set):
        granted_scopes = set(granted_scopes or [])

    out: list[dict] = []
    parts = form_key.split(".")
    # Build parent ladder: ["daily-report.crew", "daily-report"]
    ladder = [".".join(parts[:i]) for i in range(len(parts), 0, -1)]
    for tip in _TIPS:
        if tip.get("form_key") in ladder:
            tip_scopes = set(tip.get("scopes") or [])
            if tip_scopes & granted_scopes:
                out.append(_render_tip(tip))
    return out


def _render_tip(tip: dict) -> dict:
    """Public-shaped projection of a tip dict (no internal fields)."""
    return {
        "form_key": tip["form_key"],
        "kind": tip["kind"],
        "title": tip.get("title"),
        "body": tip.get("body"),
        "title_es": tip.get("title_es"),
        "body_es": tip.get("body_es"),
    }


def validate_tips_registry(strict: bool = False) -> list[str]:
    """Sanity-check the registry. Raise on issues iff strict."""
    issues: list[str] = []
    for i, tip in enumerate(_TIPS):
        loc = f"tip #{i} ({tip.get('form_key', '?')}/{tip.get('kind', '?')})"
        if not tip.get("form_key"):
            issues.append(f"{loc}: missing form_key")
        if tip.get("kind") not in ALLOWED_KINDS:
            issues.append(f"{loc}: invalid kind {tip.get('kind')!r}")
        if not tip.get("scopes"):
            issues.append(f"{loc}: missing scopes")
        if not tip.get("title") or not tip.get("body"):
            issues.append(f"{loc}: missing title/body")
        if len((tip.get("body") or "").split()) > 80:
            issues.append(f"{loc}: body too long (>80 words; coaching, not docs)")
    if strict and issues:
        raise ValueError("Tips registry invalid:\n" + "\n".join(issues))
    return issues


# ─────────────────────────────────────────────────────────────────────
# Merge Spanish translations at import time (mirrors articles pattern).
# ─────────────────────────────────────────────────────────────────────
def _merge_es() -> None:
    try:
        from .tips_es import TIPS_ES
    except Exception:
        return
    for tip in _TIPS:
        key = (tip.get("form_key"), tip.get("kind"))
        es = TIPS_ES.get(key)
        if not es:
            continue
        if es.get("title_es"):
            tip["title_es"] = es["title_es"]
        if es.get("body_es"):
            tip["body_es"] = es["body_es"]


_merge_es()
