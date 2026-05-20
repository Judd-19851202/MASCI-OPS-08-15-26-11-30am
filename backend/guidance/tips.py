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
    # iter216 · deepening — field-side equipment-needed and broken-unit
    # coaching. The Daily Report is where Dispatch first learns what
    # you need tomorrow. Surprise requests at 6:30am are the enemy.
    {
        "form_key": "daily-report.equipment",
        "kind": "next",
        "scopes": ["public"],
        "title": "What Dispatch reads tomorrow",
        "body":
            "Dispatch pulls every Daily Report by 5pm to set tomorrow's "
            "moves. A note here saying 'need the skid steer back Tuesday' "
            "is what makes Tuesday smooth. A no-note Daily Report makes "
            "tomorrow a phone-call scramble for everybody.",
    },
    {
        "form_key": "daily-report.equipment",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When the unit is down or going down",
        "body":
            "If a unit broke today, or you saw something today that says "
            "it WILL break tomorrow, say it here AND tell Shop directly. "
            "The Daily Report alerts everyone passively; a verbal heads-up "
            "to Shop gets a mechanic moving before sunrise.",
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
    # iter215 · deepening — accuracy, shortages, change-before-dispute
    {
        "form_key": "daily-report.materials",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Vague entries like 'pallet of fittings' (which fittings, how "
            "many?). Rounding wildly to a clean number ('about 20 tons') "
            "when the ticket reads 18.4. Forgetting to log material that "
            "showed up short — that's the conversation PM needs to have "
            "with the supplier, not next week's surprise.",
    },
    {
        "form_key": "daily-report.materials",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after PM sees this",
        "body":
            "Quantities post to the project's cost code. If the recorded "
            "use is well above plan, PM gets a margin flag. If well below, "
            "the inventory team gets a 'where did the rest go' question. "
            "Either way, your note is the first explanation read.",
    },
    {
        "form_key": "daily-report.materials",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to flag a change BEFORE it becomes a dispute",
        "body":
            "If the field used something different from the plan — "
            "substituted, swapped a spec, ran out and grabbed from another "
            "job — write it in plain words here AND tell PM verbally same "
            "day. Quiet substitutions are how a job gets a billing "
            "dispute six weeks later.",
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

    # ─────────────────────────────────────────────────────────────────
    # iter211 · Pre-Op Equipment Inspection
    # Highest-frequency operational coaching surface on the platform.
    # Tone direction: operational realism + accountability, not OSHA-robot.
    # The operator before you signed in good faith; return the favor.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "preop",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why this Pre-Op matters",
        "body":
            "Pre-ops are not paperwork. The operator before you trusted theirs; "
            "the operator after you trusts yours. Mark only what you've "
            "physically checked.",
    },
    {
        "form_key": "preop",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who sees this",
        "body":
            "Your Shop foreman, Dispatch, your supervisor, and the next operator "
            "who runs this unit. If something fails on this machine today, this "
            "is the first record anyone reads.",
    },
    {
        "form_key": "preop",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you submit",
        "body":
            "Pass → unit stays operational. Fail → routes to Shop. Major fail "
            "(brakes, steering, ROPS, hose leak) → Out of Service until "
            "cleared. Your sign-off is this unit's release for the day.",
    },
    {
        "form_key": "preop",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to stop and call",
        "body":
            "Major safety items failing — brakes, steering, hydraulics with an "
            "active leak, missing or damaged ROPS — stop. Call your supervisor "
            "before signing anything. Don't try to run it 'just for today'.",
    },

    # ── preop.fluids ─────────────────────────────────────────────────
    {
        "form_key": "preop.fluids",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why fluid checks matter",
        "body":
            "Leaks today are repairs tomorrow are breakdowns next week. "
            "Catching a seep at the cylinder while it's a wet spot is the "
            "cheapest fix this machine will ever get.",
    },
    {
        "form_key": "preop.fluids",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Marking 'good' because the dipstick checked out. Fluid checks are "
            "visual AND a look at the ground under the unit. Wet ground under "
            "a parked machine almost never means rain.",
    },
    {
        "form_key": "preop.fluids",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example entry",
        "body":
            "'Hydraulic seep at left tilt cylinder — operational, monitor "
            "daily.' is good. 'OK' is not — there's nothing in that for the "
            "mechanic to act on.",
    },

    # ── preop.tires-tracks ───────────────────────────────────────────
    {
        "form_key": "preop.tires-tracks",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why tires and tracks matter",
        "body":
            "Tires and tracks are the only thing between the machine and the "
            "ground. A worn cleat or low PSI shows up first as a 'feels weird' "
            "day — log it before it shows up as a recovery call.",
    },
    {
        "form_key": "preop.tires-tracks",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Walking past one side. Operators favor the same side every day. "
            "Walk all four corners on every Pre-Op — that's how you catch what "
            "the routine misses.",
    },

    # ── preop.controls ───────────────────────────────────────────────
    {
        "form_key": "preop.controls",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why controls matter",
        "body":
            "Every control you skip checking is something you'll discover at the "
            "wrong moment. Two minutes in the seat now beats two hours waiting "
            "for a mechanic later.",
    },
    {
        "form_key": "preop.controls",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example entry",
        "body":
            "'Backup alarm intermittent — works when cold, silent after warm-up.' "
            "is exactly what Shop needs. 'Backup alarm broken' tells Shop "
            "nothing about when or how.",
    },

    # ── preop.defects (fail flow) ────────────────────────────────────
    {
        "form_key": "preop.defects",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why honest defect logging matters",
        "body":
            "A defect honestly logged is a defect that gets fixed. A defect "
            "hidden becomes the next operator's incident. Pre-ops are the "
            "platform's most-read safety record.",
    },
    {
        "form_key": "preop.defects",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after a Fail",
        "body":
            "Failed items route to Shop/Fleet within the hour. Photo + a "
            "specific note speeds the response by hours. Vague notes slow it "
            "down — Shop can't dispatch a part on 'something's wrong'.",
    },
    {
        "form_key": "preop.defects",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Marking 'fail' without a photo. Skipping the note because 'they'll "
            "see it'. They won't see what you can't show them. Photo + one "
            "sentence is the rule.",
    },

    # ── preop.signoff ────────────────────────────────────────────────
    {
        "form_key": "preop.signoff",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the sign-off is your word",
        "body":
            "Your signature on a Pre-Op is your word. The operator before you "
            "signed in good faith — return the favor. If you didn't physically "
            "check it, don't sign for it.",
    },
    {
        "form_key": "preop.signoff",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When pressure to sign feels wrong",
        "body":
            "If your supervisor pressures you to sign for something you didn't "
            "check, or to mark a failed item as passing, tell Safety. That's "
            "not a personality issue — it's a safety culture issue, and Safety "
            "wants to know.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter212 · Equipment Checkout
    # The accountability handshake. Operator-stated priority anchors:
    # trust, accountability, operational integrity, good-faith,
    # crew-reliance, equipment stewardship.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "checkout",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why this Checkout matters",
        "body":
            "Checkout is the handshake: you say 'I have this', the system "
            "says 'you have this'. When something goes missing or gets "
            "damaged, the Checkout is the first record anyone reads. Your "
            "name is on it.",
    },
    {
        "form_key": "checkout",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who sees this",
        "body":
            "Your foreman, Shop (asset whereabouts tracking), Dispatch "
            "(availability), HR (employee accountability), and Admin. Your "
            "supervisor sees it within a minute of you signing.",
    },
    {
        "form_key": "checkout",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you sign",
        "body":
            "The unit leaves Dispatch's availability and enters your "
            "personal accountability record. It stays there until you "
            "officially return or transfer it — no return sign-off, still "
            "your responsibility.",
    },
    {
        "form_key": "checkout",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When NOT to sign yet",
        "body":
            "If the unit comes to you with undocumented damage, stop and "
            "document before signing. Once you sign, that damage is "
            "operationally yours unless you can prove it was there first.",
    },

    # ── checkout.condition ───────────────────────────────────────────
    {
        "form_key": "checkout.condition",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why receiving condition matters",
        "body":
            "The condition record at checkout is the only thing separating "
            "'it came to me this way' from 'I did it'. Thirty seconds of "
            "notes and photos now saves hours of explaining when a dispute "
            "lands.",
    },
    {
        "form_key": "checkout.condition",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Marking 'good' without walking the unit. Skipping photos "
            "because 'it looks fine'. Taking the previous operator's word "
            "without verifying. Trust the unit yourself — the operator "
            "before you signed in good faith, but it's your turn now.",
    },
    {
        "form_key": "checkout.condition",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example entry",
        "body":
            "'Existing scuff — rear left fender, ~6 inches. Photo attached. "
            "Right side mirror dust-covered but intact.' is good. "
            "'Condition OK' is not — there's no record to return against.",
    },

    # ── checkout.signature ───────────────────────────────────────────
    {
        "form_key": "checkout.signature",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why signature is accountability, not formality",
        "body":
            "Your signature is the moment the system passes operational "
            "responsibility to you. It's not just another field. It's the "
            "commitment to treat this equipment like it's yours — because "
            "for every practical purpose, it is now.",
    },
    {
        "form_key": "checkout.signature",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Signing first, checking after. Signing with a scrawled name "
            "that isn't clearly yours. Signing for someone else 'because "
            "they're driving right now'. All three break the audit trail "
            "when it matters.",
    },
    {
        "form_key": "checkout.signature",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When NOT to sign",
        "body":
            "If Shop or Dispatch insists you sign for gear you haven't "
            "physically seen or walked, don't. That isn't a shortcut — "
            "it's shifting blame in advance. Call your supervisor.",
    },

    # ── checkout.return-expectations ─────────────────────────────────
    {
        "form_key": "checkout.return-expectations",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why return expectations matter now",
        "body":
            "Checkout is the front half of a pair. Return closes the loop. "
            "Knowing what's expected at return — cleanliness, fluid "
            "documentation, photos — turns the final day into 30 seconds "
            "instead of a week of disputes.",
    },
    {
        "form_key": "checkout.return-expectations",
        "kind": "next",
        "scopes": ["public"],
        "title": "What comes when you return it",
        "body":
            "A return sign-off + photo close the checkout. Damage found at "
            "return opens a damage case — your original condition note at "
            "checkout is what decides if it's yours or not. Document well "
            "up front to avoid disputes at the end.",
    },

    # ── checkout.photos ──────────────────────────────────────────────
    {
        "form_key": "checkout.photos",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why photos at checkout matter",
        "body":
            "Photos aren't optional — they're the only objective record. "
            "Memory fades; words get interpreted; photos don't. A quick "
            "photo now saves a complicated conversation later.",
    },
    {
        "form_key": "checkout.photos",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "A single photo from across the lot. Skipping the areas that "
            "actually matter (wheels/tires, windshield, decks, mirrors). "
            "Taking photos with the sun behind the unit and getting "
            "silhouettes. Four sides + cab + any pre-existing damage is "
            "the minimum.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter213 · Time Verification (HR review surface — Tier 2)
    # Where supervisor-reported crew hours become paychecks. The tone
    # anchor: HR is the bridge between the field and the paycheck. A
    # quiet "cleanup" of a number — without calling the supervisor —
    # is how a $40 discrepancy becomes a grievance. Coach toward
    # good-faith correction at the source, never silent overwrites.
    # Scope: ["hr","admin"] — Tier-2 HR-portal coaching.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "time-verification",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why Time Verification matters",
        "body":
            "This is where field hours become paychecks. Get it right and "
            "supervisors stop hearing 'my check is short' on Monday morning. "
            "Get it wrong — quietly — and trust with the crew takes months "
            "to rebuild. Your job is the bridge between the field and the "
            "paycheck.",
    },
    {
        "form_key": "time-verification",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who depends on this",
        "body":
            "The crew first — their pay rides on these numbers. Then the "
            "supervisor who reported the hours, then PM (project cost), "
            "then payroll (Exact). Owners see weekly OT rollups. If a "
            "number is off here, every downstream record is off.",
    },
    {
        "form_key": "time-verification",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What happens after you verify",
        "body":
            "Verified hours roll to the Exact payroll export. Any flagged "
            "anomaly stays on the supervisor's Monday-morning list. "
            "Corrections happen at the source — the Daily Report — not "
            "by silently overwriting numbers here.",
    },
    {
        "form_key": "time-verification",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When to escalate, not fix",
        "body":
            "If a number looks wrong, call the supervisor before you change "
            "anything. Quiet edits are how a $40 discrepancy becomes a "
            "grievance. The supervisor edits the Daily Report; you verify "
            "the result. That order matters.",
    },

    # ── time-verification.overtime ───────────────────────────────────
    {
        "form_key": "time-verification.overtime",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why OT is weekly, not daily",
        "body":
            "Overtime is the rollup above 40 hours in the workweek — not "
            "'over 8 in a day'. A 10-hour Tuesday isn't OT if Friday brings "
            "the week to 38. OT shows up here once the weekly total crosses "
            "40; the daily column stays regular.",
    },
    {
        "form_key": "time-verification.overtime",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Flagging a long Tuesday as OT before the week is closed. "
            "Splitting OT across jobs without asking the supervisor which "
            "project carries it. Reading the OT column on day 3 and "
            "assuming it's final — the week isn't over.",
    },

    # ── time-verification.lunch ──────────────────────────────────────
    {
        "form_key": "time-verification.lunch",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why lunch is tracked but unpaid",
        "body":
            "Lunch is the 30 minutes the crew owes themselves and the "
            "company. It's unpaid, but it has to be on the record — both "
            "for compliance and so the supervisor's hours math actually "
            "adds up. Missing lunch isn't a data-entry shortcut; it's a "
            "missing meal break worth asking about.",
    },
    {
        "form_key": "time-verification.lunch",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Silently filling in 0.5 lunch on every row because 'they "
            "always take it'. That hides the days they didn't, which is "
            "exactly the data the supervisor and Safety need. If lunch is "
            "missing, ask — don't backfill.",
    },

    # ── time-verification.discrepancy ────────────────────────────────
    {
        "form_key": "time-verification.discrepancy",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why discrepancies are conversations, not fixes",
        "body":
            "Every Daily-Report-vs-payroll mismatch is a story the "
            "supervisor knows and you don't yet. The number isn't wrong "
            "because someone was lazy — it's wrong because the day was "
            "long, the timesheet was rushed, or the crew swapped jobs "
            "mid-shift. Ask first.",
    },
    {
        "form_key": "time-verification.discrepancy",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What the right correction looks like",
        "body":
            "Call the supervisor, get the story, agree on the right "
            "number, and have them fix the Daily Report at the source. "
            "Then re-run verification — the corrected number flows back "
            "here and the audit trail shows who changed what and why.",
    },
    {
        "form_key": "time-verification.discrepancy",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When the pattern is the problem",
        "body":
            "One-off discrepancies happen. A crew that posts 8.00 every "
            "day for two weeks straight — including a known rain day — "
            "is a rounding pattern, not a math error. That's an HR "
            "conversation with the supervisor, not a silent correction "
            "here.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter214 · Write-Ups (Field Leadership disciplinary documentation)
    # Tone anchor: a write-up is the record of a conversation that
    # already happened. The supervisor coached, the employee heard it,
    # both agreed to a next step. Write-ups are NEVER the conversation
    # itself — they're the documented evidence afterward. Coach toward
    # facts-not-feelings, due-process discipline, and the truth that
    # documentation protects the SUPERVISOR's word every bit as much as
    # the employee's. Scope: public (this is a public-form workflow
    # template; the actual records are portal-scoped on access).
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "writeup",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why a write-up matters",
        "body":
            "A write-up is the record of a conversation that already "
            "happened — never a substitute for it. If the employee learns "
            "about a write-up before you've talked to them, you skipped "
            "the part that actually changes behavior. The paper is the "
            "evidence; the conversation is the work.",
    },
    {
        "form_key": "writeup",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who reads this later",
        "body":
            "HR, the employee, the supervisor (you), and — if the pattern "
            "continues — a future manager deciding next steps. Months "
            "from now, anyone reading should be able to picture the "
            "incident from your words alone. Write for that reader.",
    },
    {
        "form_key": "writeup",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you submit",
        "body":
            "HR reviews and files it. The employee receives a copy. If "
            "this is a repeat pattern, it joins the prior records and may "
            "trigger an HR conversation. If it's a first occurrence, it "
            "sits on file as the baseline for any future pattern call.",
    },
    {
        "form_key": "writeup",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to call HR before submitting",
        "body":
            "Safety violation that put a crew at risk. Theft, harassment, "
            "or anything that touches a protected class. Anything where "
            "you're not sure if it's a write-up or a termination. Call "
            "HR first — they'd rather coach you through it than read "
            "about it Monday morning.",
    },

    # ── writeup.facts (facts, not feelings) ──────────────────────────
    {
        "form_key": "writeup.facts",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why facts, not feelings",
        "body":
            "'Arrived 22 minutes late, 3rd time this month, no call' is a "
            "fact. 'Has an attitude problem' is a feeling. Facts hold up; "
            "feelings don't. The same write-up read by a different person "
            "should yield the same conclusion — that's only possible "
            "with facts.",
    },
    {
        "form_key": "writeup.facts",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Loaded language ('lazy', 'doesn't care', 'thinks he runs the "
            "place'). Vague timeframes ('lately', 'always', 'never'). "
            "Skipping the witness names. Editorializing what the "
            "employee 'must have been thinking'. None of those help the "
            "next person reading the file.",
    },
    {
        "form_key": "writeup.facts",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example entry",
        "body":
            "'2026-05-12, 6:38am — Employee arrived at the yard at 6:38, "
            "scheduled start 6:15. No call, no text. This is the 3rd late "
            "arrival in 14 working days (2026-04-29, 2026-05-06, "
            "2026-05-12). Foreman Davis was on-site at start time. "
            "Conversation held 6:40am.' is good. 'Late again' is not.",
    },

    # ── writeup.conversation (the talk before the paper) ─────────────
    {
        "form_key": "writeup.conversation",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the conversation comes first",
        "body":
            "Surprising someone with a write-up they didn't see coming "
            "ends the relationship. The conversation gives the employee a "
            "fair shot to explain, agree on what's expected, and own the "
            "fix. The write-up just records what was already said and "
            "agreed.",
    },
    {
        "form_key": "writeup.conversation",
        "kind": "next",
        "scopes": ["public"],
        "title": "What 'agreed next step' looks like",
        "body":
            "Specific, time-bound, and verifiable. 'Be on time' is not "
            "agreed — 'arrive at the yard at 6:15 or earlier for the "
            "next 30 days, with a call to me by 5:45 if anything is "
            "going to make that late' is agreed. The employee should be "
            "able to repeat it back.",
    },

    # ── writeup.due-process (employee's right to respond) ────────────
    {
        "form_key": "writeup.due-process",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why due process protects both sides",
        "body":
            "An employee who reads a write-up and disagrees has a right "
            "to add their side. That isn't a loss for the supervisor — "
            "it's the file telling the whole truth instead of half of "
            "it. A write-up where only one voice is on the page is "
            "weaker, not stronger.",
    },
    {
        "form_key": "writeup.due-process",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When the employee won't sign",
        "body":
            "Document that you offered, that they declined, and that you "
            "explained signing means 'I received this', not 'I agree'. "
            "Then submit anyway — refusal doesn't void the record. Tell "
            "HR verbally so they're not surprised.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter215 · Material Calculator (pre-job planning surface)
    # The calculator is the moment before materials are ordered. Coach
    # toward: waste factors are not optional, lead times are real, and
    # NO calculator replaces a field measurement. Scope: public — the
    # calculator itself is a public tool, so the coaching is public.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "material-calculator",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why this calculation matters",
        "body":
            "This number drives the order. Order short and the crew "
            "stops at 2pm waiting on a second delivery; order long and "
            "the surplus gets billed to the job for cubic yards nobody "
            "ever placed. The five minutes spent here saves a day of "
            "scrambling.",
    },
    {
        "form_key": "material-calculator",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Treating the calculator number as final — it's a planning "
            "estimate, not a measurement. Setting waste at 0% because "
            "'this crew is clean'. Forgetting the calculator doesn't "
            "know your subgrade is soft, your trench widened, or the "
            "supplier sells full pallets only.",
    },
    {
        "form_key": "material-calculator",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example",
        "body":
            "'24×40 pad, 6\" lime rock, 1.45 density, 10% waste → 14.5 "
            "tons → order 15 tons' is a real number. Then verify against "
            "the supplier's pallet/truck minimum and the foreman's "
            "field measurement before you sign the PO.",
    },

    # ── material-calculator.waste ────────────────────────────────────
    {
        "form_key": "material-calculator.waste",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why waste factor is not optional",
        "body":
            "Cut waste, spill, edge loss, compaction settling, and "
            "supplier short-counts are real on every job. A 0% waste "
            "estimate is a 0% honest estimate. Use the job's history "
            "— if last quarter ran 12%, plan for 12%, not 5%.",
    },
    {
        "form_key": "material-calculator.waste",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Picking a waste percent that 'feels right' instead of using "
            "the job-type historical number. Setting waste high to pad "
            "the order (now PM thinks the project's bleeding margin). "
            "Setting it low to win the bid (now the foreman is short on "
            "Tuesday).",
    },

    # ── material-calculator.lead-time ────────────────────────────────
    {
        "form_key": "material-calculator.lead-time",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why lead time is part of the calculation",
        "body":
            "The calculator solves quantity. Lead time solves WHEN. A "
            "perfect 14.5-ton number is worthless if you order it Friday "
            "afternoon for a Monday pour and the supplier's plant is "
            "closed Sunday. Check the supplier's calendar before "
            "committing to a schedule.",
    },
    {
        "form_key": "material-calculator.lead-time",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to call the supplier first",
        "body":
            "Specialty mixes, oversize loads, anything coming from "
            "outside the regional plant, and any order placed within 24h "
            "of need. Call before you commit a delivery date on a Daily "
            "Report or schedule. The supplier's 'yes' on the phone "
            "beats the calculator's confidence every time.",
    },

    # ── material-calculator.field-verify ─────────────────────────────
    {
        "form_key": "material-calculator.field-verify",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why no calculator replaces a field measurement",
        "body":
            "The plan said the trench is 80 feet at 24 inches. The field "
            "found rock at 50 feet and the trench widened to 36 to get "
            "around it. The calculator can't know that. Walk the job, "
            "measure what's actually there, then calculate — not the "
            "other way around.",
    },
    {
        "form_key": "material-calculator.field-verify",
        "kind": "next",
        "scopes": ["public"],
        "title": "What to do with the calculated number",
        "body":
            "Cross-check against the foreman's gut. Confirm the supplier "
            "can deliver it on time. Then on Daily Report day, log what "
            "ACTUALLY got placed (not what was ordered). The calculator "
            "is for planning; the Daily Report is for truth.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter216 · Dispatch Transfers (Tier-2 · dispatcher surface)
    # The dispatcher fields requests from the field, juggles
    # availability, and makes the moves that keep crews working.
    # Tone anchor: dispatch is operational referee — they protect the
    # schedule, equipment utilization, and the crew's day. Coach
    # toward lead time, exact jobsite access, load specifics, and
    # respecting the dispatcher's calendar.
    # Scope: ["dispatch","admin"] — Tier-2 portal-scoped.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "dispatch.transfers",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why transfers are the dispatcher's leverage",
        "body":
            "Every transfer either saves a job a day or costs one. A "
            "well-routed move turns one truck into three productive "
            "stops; a rushed move wastes the truck and frustrates two "
            "foremen. Dispatch is the operational referee — protect the "
            "schedule, the equipment, and the crew's day.",
    },
    {
        "form_key": "dispatch.transfers",
        "kind": "who",
        "scopes": ["dispatch", "admin"],
        "title": "Who's affected by this move",
        "body":
            "The sending foreman (lost the unit), the receiving foreman "
            "(got it — or didn't, on time), the driver (route and "
            "load), Shop (any defects en route), PM (cost code), and "
            "Safety (any DOT-touchy move). One transfer card lands on "
            "six people's radar.",
    },
    {
        "form_key": "dispatch.transfers",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What happens after you queue it",
        "body":
            "The receiving foreman gets visibility on tomorrow's "
            "availability. The driver gets the load sheet. Shop sees the "
            "unit's last-known location for parts/PM scheduling. If "
            "the move slips, everyone downstream needs to know within "
            "the hour — not at start-of-shift the next day.",
    },
    {
        "form_key": "dispatch.transfers",
        "kind": "escalate",
        "scopes": ["dispatch", "admin"],
        "title": "When the request doesn't add up",
        "body":
            "Foreman asks for a unit you don't have. The move requires "
            "a permit, escort, or after-hours window. A unit is being "
            "asked to leave a job that's still active per the Daily "
            "Report. Don't just say 'no' — call the requesting foreman "
            "AND the PM, talk through it, and document the decision.",
    },

    # ── dispatch.transfers.lead-time ─────────────────────────────────
    {
        "form_key": "dispatch.transfers.lead-time",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why lead time is the whole game",
        "body":
            "24 hours' notice = you can route efficiently and avoid "
            "deadhead miles. 4 hours' notice = a rushed truck and a "
            "frustrated driver. 30 minutes' notice = somebody's day "
            "burns. Coach foremen to think one work-day ahead, not one "
            "smoke-break.",
    },
    {
        "form_key": "dispatch.transfers.lead-time",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common mistakes",
        "body":
            "Accepting a 'need it now' as the default response time. "
            "Not asking the requester WHEN they actually need it — most "
            "'now' requests have a real deadline 4-6 hours out. "
            "Quoting an aspirational time you can't hit. Better to "
            "commit late and deliver early than the reverse.",
    },

    # ── dispatch.transfers.access ────────────────────────────────────
    {
        "form_key": "dispatch.transfers.access",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why jobsite access details matter",
        "body":
            "A driver who shows up to a gate without a code, a soft "
            "lot that won't hold a lowboy, or an overhead the truck "
            "can't clear — those aren't driver mistakes, they're "
            "dispatch information failures. Get the access specifics "
            "from the foreman before you commit a delivery slot.",
    },
    {
        "form_key": "dispatch.transfers.access",
        "kind": "example",
        "scopes": ["dispatch", "admin"],
        "title": "Example",
        "body":
            "Good access note: 'Site is 1450 Industrial Pkwy, gate code "
            "8842, foreman Diaz on 555-0117, gravel lot east of trailer, "
            "11'6\" overhead at gate (no high decks).' Bad: 'Industrial "
            "Parkway, ask for Diaz.' — the second one creates the call.",
    },

    # ── dispatch.transfers.load-specs ────────────────────────────────
    {
        "form_key": "dispatch.transfers.load-specs",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why load specifics protect everybody",
        "body":
            "Weight, height, length, attachments still on/off, fluids "
            "topped or drained — those decide which trailer goes, "
            "whether a permit is needed, and whether DOT can be a "
            "problem. The driver and the foreman both need them right "
            "the first time.",
    },
    {
        "form_key": "dispatch.transfers.load-specs",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common mistakes",
        "body":
            "Trusting equipment-master spec sheets without verifying "
            "with the sending foreman ('we left the bucket on'). "
            "Skipping fluids/fuel notes (a full tank can be the "
            "difference between legal and overweight). Forgetting "
            "attachments — they ride separately if they're not "
            "factored in.",
    },

    # ── dispatch.transfers.utilization ───────────────────────────────
    {
        "form_key": "dispatch.transfers.utilization",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why utilization is the long-game scorecard",
        "body":
            "Every idle unit on a yard is money sitting still. Every "
            "double-booked unit is a fight. Utilization isn't an admin "
            "report you read once a month — it's the daily score you're "
            "playing for. A good transfer pushes utilization up; a "
            "rushed one pushes it down.",
    },
    {
        "form_key": "dispatch.transfers.utilization",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What the utilization dashboard tells you",
        "body":
            "A unit sitting on a yard while another job calls for the "
            "same model is a routing opportunity. Multiple swaps of the "
            "same unit between two jobs in one week says the projects "
            "weren't planned together. Surface both to PM — they'd "
            "rather hear it from Dispatch than from finance.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter218 · Coaching gaps surfaced by iter217 walkthroughs.
    # Authored to close four operator-validated P0 gaps. Re-running the
    # affected walkthroughs after this iter should drop the actionable
    # finding count by ≥4 (self-validating editorial loop).
    # ═════════════════════════════════════════════════════════════════

    # ─────────────────────────────────────────────────────────────────
    # iter218 · field-leadership.records — REVIEWER-side coaching for
    # the records list page. This is a NEW operational class of tip:
    # not coaching the FILER, but coaching the REVIEWER (super / PM /
    # admin) reading a filing they didn't create. Voice anchor:
    # reviewing isn't auditing — it's the supervisor's reading of the
    # crew's report, the moment where blind-spots get caught.
    # Scope: leadership + admin + pm (the three roles that read records).
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "field-leadership.records",
        "kind": "why",
        "scopes": ["leadership", "admin", "pm"],
        "title": "Why review the records, not just file them",
        "body":
            "A daily report you skim is a daily report nobody read. The "
            "crew can tell which supers actually read what got filed — "
            "they hear it the next morning when you ask about the "
            "specific note that mattered. Reviewing isn't auditing; "
            "it's the supervisor's reading of the crew's work.",
    },
    {
        "form_key": "field-leadership.records",
        "kind": "who",
        "scopes": ["leadership", "admin", "pm"],
        "title": "Who else reads this same record",
        "body":
            "PM (project margin), HR (any people note), Safety (any "
            "incident reference), Dispatch (equipment notes), and "
            "Owners (the weekly rollup). When you push back on a vague "
            "entry, you're not nitpicking — you're protecting the "
            "five readers who come after you.",
    },
    {
        "form_key": "field-leadership.records",
        "kind": "next",
        "scopes": ["leadership", "admin", "pm"],
        "title": "What to do when something doesn't add up",
        "body":
            "Open the record. Read the foreman's narrative. If the math "
            "between crew hours, equipment hours, and material notes "
            "doesn't tell a coherent story of the day — that's a "
            "conversation with the foreman, not a silent edit. Same "
            "principle as Time Verification: fix at the source.",
    },
    {
        "form_key": "field-leadership.records",
        "kind": "escalate",
        "scopes": ["leadership", "admin", "pm"],
        "title": "When to push back, when to escalate",
        "body":
            "Pattern across multiple records from the same foreman — "
            "vague entries, missing dispatch needs, ghost equipment — "
            "is an HR-coaching conversation, not a single-record fix. "
            "A safety reference buried in a Daily Report instead of an "
            "Incident is an immediate Safety call. Don't sit on either.",
    },

    # ── field-leadership.records.review-tone ─────────────────────────
    {
        "form_key": "field-leadership.records.review-tone",
        "kind": "why",
        "scopes": ["leadership", "admin", "pm"],
        "title": "Why HOW you push back matters",
        "body":
            "The first foreman who got their daily report 'corrected' "
            "without a phone call is the same foreman who stops writing "
            "detailed notes the next month. Reviewers protect the "
            "filing culture by calling, not by editing. A 30-second "
            "phone call buys six months of honest reporting.",
    },
    {
        "form_key": "field-leadership.records.review-tone",
        "kind": "mistake",
        "scopes": ["leadership", "admin", "pm"],
        "title": "Common reviewer mistakes",
        "body":
            "Quietly correcting the foreman's narrative because 'it's "
            "easier.' Asking 'why didn't you write XYZ?' instead of "
            "'tell me about the morning so I can fix the report.' "
            "Treating the record as the truth instead of as the "
            "foreman's account OF the truth.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter218 · crew_eval — migrated from legacy WhyItMattersPanel to
    # the modern HelpTip engine. Voice anchor: a crew evaluation is the
    # super's read of an operator's last 6 months — calibration matters
    # more than scoring. The eval that says "he's fine" the same way
    # for every operator is the eval that taught nobody anything.
    # Scope: leadership + admin (the roles that write evals).
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "crew_eval",
        "kind": "why",
        "scopes": ["leadership", "admin"],
        "title": "Why this evaluation matters",
        "body":
            "An honest crew eval is the only formal moment when an "
            "operator's last 6 months gets put on the record. Vague "
            "evals make later promotions, raises, and (rarely) "
            "discipline indefensible. The super who writes evals the "
            "crew can trust is the super whose feedback the crew "
            "actually hears.",
    },
    {
        "form_key": "crew_eval",
        "kind": "who",
        "scopes": ["leadership", "admin"],
        "title": "Who reads this 6 months from now",
        "body":
            "HR (promotions, raises), the next super inheriting the "
            "operator, PM (project-staffing decisions), and the "
            "operator themselves (when they ask why they didn't get "
            "the raise). Write it so the answer is in the file, not "
            "in your memory.",
    },
    {
        "form_key": "crew_eval",
        "kind": "next",
        "scopes": ["leadership", "admin"],
        "title": "What happens after you submit",
        "body":
            "HR files it. The operator receives a copy. It joins the "
            "operator's record alongside prior evals — patterns over "
            "time become visible. If this is the third 'meets "
            "expectations' in a row on someone you've been "
            "considering for foreman, the file says you haven't "
            "actually moved them.",
    },
    {
        "form_key": "crew_eval",
        "kind": "escalate",
        "scopes": ["leadership", "admin"],
        "title": "When to write less, talk more",
        "body":
            "If the honest eval would be 'we need to part ways,' "
            "write nothing here yet — call HR. Same for any harassment "
            "or safety pattern. The eval form is for the steady-state "
            "operator on your crew, not for the conversation that's "
            "about to change someone's employment.",
    },

    # ── crew_eval.calibration ────────────────────────────────────────
    {
        "form_key": "crew_eval.calibration",
        "kind": "why",
        "scopes": ["leadership", "admin"],
        "title": "Why calibration beats scoring",
        "body":
            "If every operator on your crew is a 4-out-of-5, the eval "
            "tells HR nothing. Calibration is asking: compared to the "
            "average operator on similar work, where does this person "
            "fall? Below, at, or above? That's the question the eval "
            "is really asking.",
    },
    {
        "form_key": "crew_eval.calibration",
        "kind": "mistake",
        "scopes": ["leadership", "admin"],
        "title": "Common calibration mistakes",
        "body":
            "Scoring everyone the same to avoid conflict. Letting one "
            "great day inflate the whole 6 months. Letting one bad day "
            "tank it. Comparing your B-team operator to your A-team "
            "lead instead of to the average. Rate against the real "
            "average, not against your favorite or your frustration.",
    },

    # ── crew_eval.evidence ───────────────────────────────────────────
    {
        "form_key": "crew_eval.evidence",
        "kind": "why",
        "scopes": ["leadership", "admin"],
        "title": "Why specific examples beat generalizations",
        "body":
            "'Good attitude' is a feeling. 'Stayed late three Fridays "
            "in May to help finish the McCray pad' is evidence. The "
            "operator can argue with a feeling; they can't argue with "
            "a specific day. And HR can act on evidence; they can't "
            "act on a vibe.",
    },
    {
        "form_key": "crew_eval.evidence",
        "kind": "example",
        "scopes": ["leadership", "admin"],
        "title": "Example evidence",
        "body":
            "Good: 'Caught a hydraulic seep on Unit 217 during pre-op "
            "2026-03-14 — flagged Shop before sunrise, prevented a "
            "blown line on the McCray pour.' Bad: 'Pays attention to "
            "his equipment.' The first one is the eval; the second is "
            "the wallpaper.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter218 · dispatch.idle-alerts — Tier-2 dispatcher coaching for
    # the Idle Alerts tab. Voice anchor: idle alerts aren't a "bad
    # foreman" detector — they're a routing-opportunity discovery
    # surface. Don't move units that are idle for good reasons; move
    # units that are idle for forgotten reasons.
    # Scope: dispatch + admin.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "dispatch.idle-alerts",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why idle alerts are opportunity, not blame",
        "body":
            "An idle alert isn't 'this foreman is wasting equipment.' "
            "It's 'this unit hasn't produced an operations event in N "
            "days — is that on purpose, or did everyone forget?' "
            "Treat it as discovery, not gotcha — most idle units have "
            "a story; the alert just makes you ask.",
    },
    {
        "form_key": "dispatch.idle-alerts",
        "kind": "who",
        "scopes": ["dispatch", "admin"],
        "title": "Who you call before you move",
        "body":
            "The assigned foreman first — they know if the unit is "
            "staged for next week's pour, broken and waiting on a "
            "part, or genuinely forgotten. Then PM if the answer is "
            "'we still need it' so utilization gets re-checked at "
            "project level. Never auto-recall.",
    },
    {
        "form_key": "dispatch.idle-alerts",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What turns an alert into a move",
        "body":
            "The foreman confirms the unit is genuinely available. "
            "Another job has a confirmed need for the same model. "
            "Lead time covers the transfer. PM is told before the "
            "move, not after. If any of those four are missing, the "
            "alert is information — not yet an action.",
    },
    {
        "form_key": "dispatch.idle-alerts",
        "kind": "escalate",
        "scopes": ["dispatch", "admin"],
        "title": "When the pattern is the story",
        "body":
            "One unit idle on a job is normal. A whole job's "
            "equipment trending toward idle for three weeks is a "
            "project-status conversation with PM — the job may be "
            "winding down, stalled, or quietly losing scope. Surface "
            "it to PM as a question, not a complaint.",
    },

    # ── dispatch.idle-alerts.thresholds ──────────────────────────────
    {
        "form_key": "dispatch.idle-alerts.thresholds",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why 7 / 14 / 30 days, not one number",
        "body":
            "7 days catches genuine recent forgetting. 14 days catches "
            "the unit-staged-for-next-week pattern. 30 days catches "
            "the season-on, season-off equipment cycle. One threshold "
            "would either flood you with false alerts or hide the "
            "real ones.",
    },
    {
        "form_key": "dispatch.idle-alerts.thresholds",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common mistakes",
        "body":
            "Setting threshold to 30 because it's quieter — now you "
            "miss the 10-day idle that another foreman is actively "
            "calling for. Treating the 7-day count as 'units to "
            "recall' instead of 'units to ask about'. The threshold "
            "is a conversation-starter, not a verdict.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter218 · dispatch.holds — Tier-2 dispatcher coaching for the
    # Holds tab. Voice anchor: holds are the multi-team coordination
    # surface — Safety puts a unit on hold, Shop releases it, Dispatch
    # is the visibility layer in between. Holds aren't dispatch's
    # decision; they're dispatch's read of what Safety/Shop are saying.
    # Scope: dispatch + admin.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "dispatch.holds",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why holds exist (and why Dispatch can't release them)",
        "body":
            "A hold means Safety or Shop has decided this unit isn't "
            "fit for the field right now. Dispatch's job is to SEE "
            "the hold and route around it — not to second-guess the "
            "decision. If the hold seems wrong, the conversation is "
            "with the team who placed it, not a workaround.",
    },
    {
        "form_key": "dispatch.holds",
        "kind": "who",
        "scopes": ["dispatch", "admin"],
        "title": "Who placed which kind of hold",
        "body":
            "Safety holds = Safety put it down (usually post-incident "
            "or audit finding). Maintenance holds = Shop put it down "
            "(usually a failed PM, broken part, or operator-reported "
            "defect). Pending holds = someone requested one and it "
            "needs approval. Dispatch reads all three; releases none "
            "of them.",
    },
    {
        "form_key": "dispatch.holds",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What Dispatch does while a unit is on hold",
        "body":
            "Don't queue the unit for any transfer. Tell the "
            "requesting foreman the unit is unavailable AND the "
            "reason class (Safety / Maintenance) — they need to "
            "know which team to chase if they think the hold is "
            "wrong. Watch the queue for the release event; that's "
            "when routing resumes.",
    },
    {
        "form_key": "dispatch.holds",
        "kind": "escalate",
        "scopes": ["dispatch", "admin"],
        "title": "When to surface a hold pattern",
        "body":
            "Same unit on hold three times in a quarter is a Shop "
            "conversation about retirement. A whole job's equipment "
            "trending toward holds is a Safety walk-the-job "
            "conversation. Dispatch doesn't fix either — Dispatch is "
            "the team that NOTICES first because the routing queue "
            "shows the pattern.",
    },

    # ── dispatch.holds.pending ───────────────────────────────────────
    {
        "form_key": "dispatch.holds.pending",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why pending holds need fast review",
        "body":
            "A pending hold is a request that hasn't been approved "
            "yet — the unit is still routable, but somebody on the "
            "team thinks it shouldn't be. Sit on it too long and the "
            "unit goes out the gate the next morning before the "
            "approval lands. Dispatch's job: get eyes on pending the "
            "same day.",
    },
    {
        "form_key": "dispatch.holds.pending",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common mistakes",
        "body":
            "Dismissing a pending hold without reading the request "
            "context. Approving without asking the requester whether "
            "it should be Safety-class or Maintenance-class — those "
            "route to different release authorities. Treating pending "
            "as a 'review when there's time' queue instead of a "
            "today-action queue.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter222 · time-off-review · Tier-2 HR-scoped review-side coaching.
    #
    # Highest cultural-drift-risk surface in the platform. The right
    # response to a time-off request is rarely a single binary answer.
    # Bereavement is granted, never debated. Patterns are conversations,
    # not denials. Vacations are yes-with-timing, not no.
    #
    # OPERATIONAL LEADERSHIP GUIDANCE, NOT LEGAL ADVICE. Coaching never
    # cites policy sections, EEOC, FMLA, or any statutory framework —
    # those belong to HR's training and the employee handbook, not to
    # the contextual coaching surface.
    #
    # Scope: hr + admin (review-side only — Tier-2).
    # ═════════════════════════════════════════════════════════════════

    # ── time-off-review (canonical 4) ────────────────────────────────
    {
        "form_key": "time-off-review",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why this review matters",
        "body":
            "Time off is where the company's character shows up. The "
            "crew watches how HR handles these requests — fairly, "
            "humanly, on time — and decides whether the place is "
            "worth working for. Most of these are judgment calls, not "
            "policy calls. Read the request, ask the questions, then "
            "decide.",
    },
    {
        "form_key": "time-off-review",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who's affected by your decision",
        "body":
            "The employee first (their day off, their family, their "
            "trust in the company). Their supervisor (who has to "
            "cover the work). The crew (who watches whether the "
            "decision matches the last 10 like it). PM if it affects "
            "project staffing. Payroll if it changes the week's "
            "totals.",
    },
    {
        "form_key": "time-off-review",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What happens after you decide",
        "body":
            "The employee gets the answer — same day if at all "
            "possible. The supervisor gets visibility so they can "
            "plan coverage. Approved time hits the time-verification "
            "queue automatically. If you needed more info, the "
            "request stays open with a note explaining what you "
            "asked for and when.",
    },
    {
        "form_key": "time-off-review",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When to call before deciding",
        "body":
            "Anything that could be a medical disability question, "
            "anything that touches a protected class, anything where "
            "the same employee has 3+ open requests this quarter, or "
            "anything where the supervisor pushes back hard on "
            "approval. Call up before deciding — HR Director hears "
            "about it Monday morning either way.",
    },

    # ── time-off-review.bereavement ──────────────────────────────────
    # OPERATOR-STATED ANCHOR: "Bereavement is granted, never debated."
    {
        "form_key": "time-off-review.bereavement",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Bereavement is granted, never debated",
        "body":
            "Someone died. Approve the time. The conversation later "
            "is about the return date and what they need when they "
            "come back — not about whether they 'really' need to be "
            "off. The 3-day standard is the floor, not the ceiling; "
            "extend it if they ask, on the spot.",
    },
    {
        "form_key": "time-off-review.bereavement",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Asking for a death certificate before approving. Calling "
            "the supervisor 'just to check' before granting. Pushing "
            "back on which family member 'counts' — the employee "
            "decides who's family. Treating the request like a "
            "policy puzzle instead of a person in grief.",
    },
    {
        "form_key": "time-off-review.bereavement",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When something looks off",
        "body":
            "If a pattern is forming (multiple bereavement requests "
            "for the same person · clearly fabricated names · timing "
            "that maps to known shift dodges), that's an HR Director "
            "conversation AFTER the time off is already approved. "
            "You don't deny bereavement to investigate it. You "
            "approve, then talk.",
    },

    # ── time-off-review.pattern ──────────────────────────────────────
    # OPERATOR-STATED ANCHOR: "A pattern is a conversation, not a denial."
    {
        "form_key": "time-off-review.pattern",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "A pattern is a conversation, not a denial",
        "body":
            "One sick day is a sick day. Three Mondays in a row is a "
            "pattern. The pattern doesn't change whether the current "
            "request gets approved — it changes whether the "
            "conversation that should be happening, IS happening. "
            "Denying the request to 'send a message' just teaches "
            "the crew that HR plays games.",
    },
    {
        "form_key": "time-off-review.pattern",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Denying the request as a stand-in for the conversation "
            "you don't want to have. Approving for the 30th time "
            "without ever flagging the pattern to the supervisor. "
            "Letting the pattern become a 'reputation' before anyone "
            "has actually said the words to the employee.",
    },
    {
        "form_key": "time-off-review.pattern",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What the right conversation looks like",
        "body":
            "Approve the current request. Then, separately, you or "
            "the supervisor sits with the employee and says what "
            "you've observed — specific dates, no editorializing. "
            "Ask if anything's going on. Hear them out. Most "
            "'patterns' have a real story behind them; some don't. "
            "The conversation finds out.",
    },

    # ── time-off-review.vacation ─────────────────────────────────────
    # OPERATOR-STATED ANCHOR: "Vacation is a yes with timing."
    {
        "form_key": "time-off-review.vacation",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Vacation is a yes with timing",
        "body":
            "Pre-planned vacation isn't a privilege HR grants — it's "
            "earned time the employee owns. The question is rarely "
            "'yes or no' — it's 'this week or that week?'. Check the "
            "project schedule, talk to the supervisor about coverage, "
            "and confirm a window that works. Saying 'no' outright is "
            "almost always the wrong answer.",
    },
    {
        "form_key": "time-off-review.vacation",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Saying 'no' instead of 'not that week'. Failing to "
            "check the project schedule before deciding. Approving "
            "without notifying the supervisor — coverage gets "
            "discovered the morning of, not the week before. "
            "Letting requests sit for 5 days while the employee "
            "wonders if it counts as a 'no'.",
    },

    # ── time-off-review.medical ──────────────────────────────────────
    {
        "form_key": "time-off-review.medical",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Medical leave: plan around it, don't dig into it",
        "body":
            "Surgery, appointments, recovery — the employee tells "
            "you when, you plan around it. The diagnosis is not your "
            "business unless the employee chooses to share it. "
            "Coordinate the schedule, confirm coverage, and respect "
            "the privacy. 'What's wrong?' is not a question HR "
            "asks here.",
    },
    {
        "form_key": "time-off-review.medical",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Asking what the appointment is for. Pushing back on "
            "timing because 'we have a busy week' — they didn't "
            "schedule surgery around your pour schedule. Telling "
            "the supervisor what the medical issue is. Treating a "
            "medical note as a permission slip you get to evaluate.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter223 · employee-accountability · Tier-2 HR-scoped.
    #
    # "My check is short." "Where's my last paystub?" "I didn't get
    # the bonus." Highest-trust-impact operational moment in HR's day.
    # How leadership responds here determines credibility, escalation
    # likelihood, morale, retention, and the crew's perception of
    # fairness.
    #
    # OPERATOR-STATED ANCHOR: "The answer lives in the record — read
    # first, respond second."
    #
    # Coaching principles (operator-stated):
    #   • read first · verify first · understand context first
    #   • respond human-first
    #   • avoid defensiveness · avoid bureaucracy · avoid escalation reflexes
    #
    # Scope: hr + admin (HR's review-side surface).
    # ═════════════════════════════════════════════════════════════════

    # ── employee-accountability (canonical 4) ────────────────────────
    {
        "form_key": "employee-accountability",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why this conversation matters",
        "body":
            "When an employee asks about their pay, their stub, or a "
            "missing bonus, they're not picking a fight — they're "
            "extending trust to HR to make it right. How you respond "
            "in the next 90 seconds decides whether they leave the "
            "counter believing the company has their back or "
            "believing they're on their own.",
    },
    {
        "form_key": "employee-accountability",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who's listening to your response",
        "body":
            "The employee in front of you. The two coworkers in the "
            "break room who will hear about it within the hour. The "
            "supervisor (if it turns out to be a Daily Report fix). "
            "Payroll (if it's a system issue). The crew — because "
            "fairness stories travel faster than any company "
            "communication ever will.",
    },
    {
        "form_key": "employee-accountability",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What happens after you've read the record",
        "body":
            "Tell the employee what you found in plain words. If "
            "they're right, fix it today and tell them when the "
            "corrected check arrives. If they're wrong, walk them "
            "through the numbers so they understand. If you need "
            "more time, give them a specific callback time — and "
            "honor it.",
    },
    {
        "form_key": "employee-accountability",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When to call HR Director before responding",
        "body":
            "Anything that sounds like it could become a complaint "
            "beyond pay (harassment, discrimination, retaliation). "
            "Anything where multiple employees are asking the same "
            "question this week (system issue, not employee issue). "
            "Anything where you can already feel yourself getting "
            "defensive — that's the moment to pause and call up.",
    },

    # ── employee-accountability.read-first ───────────────────────────
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    # "The answer lives in the record — read first, respond second."
    {
        "form_key": "employee-accountability.read-first",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "The answer lives in the record — read first, respond second",
        "body":
            "Resist the reflex to answer from memory or from what "
            "feels right. Open the time-verification record. Open "
            "the Daily Report. Open the prior paystub. The answer "
            "is sitting in those documents. Reading first costs you "
            "60 seconds and buys you a response the employee can "
            "actually verify.",
    },
    {
        "form_key": "employee-accountability.read-first",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Answering 'that can't be right' before opening anything. "
            "Quoting policy numbers instead of showing the actual "
            "record. Saying 'I'll check on that' and then forgetting "
            "for two days. Looking at the screen but not actually "
            "reading what's on it.",
    },
    {
        "form_key": "employee-accountability.read-first",
        "kind": "example",
        "scopes": ["hr", "admin"],
        "title": "What 'reading first' looks like",
        "body":
            "Employee: 'My check is short by about $80.' You: 'Let "
            "me pull your last week — give me a minute.' [Open "
            "Daily Reports, time-verification, paystub.] You: 'You "
            "logged 42.5 hours, paid for 40 — looks like 2.5 OT "
            "didn't roll through. I see what happened. Let me fix "
            "it and you'll have the correction by Friday.' That's "
            "the whole interaction.",
    },

    # ── employee-accountability.tone ─────────────────────────────────
    {
        "form_key": "employee-accountability.tone",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why the calm response wins",
        "body":
            "The employee came to you because they trusted HR over "
            "the supervisor, the rumor mill, or just going home "
            "frustrated. Defensiveness ends that trust. Calm, "
            "specific, evidence-based — that's the tone that lets "
            "the conversation actually solve something. The "
            "frustration is rarely about you; don't take it that way.",
    },
    {
        "form_key": "employee-accountability.tone",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common defensiveness mistakes",
        "body":
            "Matching the employee's frustration with your own. "
            "Saying 'that's not how it works' before listening. "
            "Reaching for the handbook before reaching for the "
            "actual record. Treating the question as an accusation. "
            "Reading 'I think there's a mistake' as 'I think you "
            "made a mistake' — they're not the same sentence.",
    },

    # ── employee-accountability.verify ───────────────────────────────
    {
        "form_key": "employee-accountability.verify",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Verifying without making it feel like an interrogation",
        "body":
            "You need facts to answer: what week, what job, what "
            "hours. The employee needs to feel that you're "
            "investigating WITH them, not investigating THEM. Ask "
            "open questions ('walk me through that week') rather "
            "than closed ones ('do you have proof of those hours?'). "
            "The same fact-gathering, half the friction.",
    },
    {
        "form_key": "employee-accountability.verify",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What 'good verification' produces",
        "body":
            "A short note in the record: 'Employee inquired about "
            "shortage in pay period 2026-05-12, claimed 42.5 hrs. "
            "Cross-checked Daily Reports + time-verification: 42.5 "
            "confirmed. Correction issued 2026-05-19, employee "
            "notified verbally.' Anyone reading that note three "
            "months later understands exactly what happened and why.",
    },

    # ── employee-accountability.followup ─────────────────────────────
    {
        "form_key": "employee-accountability.followup",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why closing the loop matters more than the resolution",
        "body":
            "A correction the employee never hears about is the same "
            "as no correction. After payroll runs, send a quick "
            "confirmation — 'your check should reflect the fix this "
            "Friday, let me know if it doesn't' — and mean the last "
            "five words. The follow-through is the part the crew "
            "remembers, not the original conversation.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter224 · employee-lifecycle · Tier-2 HR-scoped.
    #
    # New-hire onboarding is the highest long-term culture-shaping
    # operational surface in the company. The first day decides:
    # retention, morale, trust, operational confidence, perception of
    # leadership, perception of professionalism.
    #
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    # "Get it right and they hear about the company; get it wrong and
    #  they hear about the bureaucracy."
    #
    # Coaching principles (operator-stated):
    #   • first-impression matters more than paperwork accuracy
    #   • human-first welcome, not forms-first welcome
    #   • collect documents WITHOUT making it feel like an interrogation
    #   • the hand-off to the supervisor is the actual onboarding moment
    #
    # Scope: hr + admin.
    # ═════════════════════════════════════════════════════════════════

    # ── employee-lifecycle (canonical 4) ─────────────────────────────
    {
        "form_key": "employee-lifecycle",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why the first day matters more than the paperwork",
        "body":
            "Years from now, the employee won't remember which form "
            "they signed first. They will remember whether the place "
            "felt organized, welcoming, and serious about its people. "
            "Onboarding isn't a checklist — it's the first message "
            "the company sends about how it treats the crew.",
    },
    {
        "form_key": "employee-lifecycle",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who else makes Day-1 work",
        "body":
            "The hiring supervisor (who needs to know they're "
            "coming, with the right name and start time). The "
            "crew they're joining (a heads-up beats a surprise "
            "introduction). Payroll (banking info, deductions). "
            "Shop or Dispatch if equipment assignment is needed. "
            "Owners don't see this — but they will hear about it "
            "if it goes badly.",
    },
    {
        "form_key": "employee-lifecycle",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What happens after you finish onboarding",
        "body":
            "Send the supervisor the start-time confirmation same "
            "day. Make sure the new hire knows where to park, where "
            "to find you, and who their supervisor's face looks "
            "like. Schedule a 14-day check-in on your calendar "
            "before you let them out the door — that's when the "
            "real questions start coming.",
    },
    {
        "form_key": "employee-lifecycle",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When to call HR Director before completing",
        "body":
            "Missing or expired I-9 documents that won't be "
            "resolved by start date. Background check flags that "
            "weren't expected. Discovery that this hire was "
            "previously employed and left under conditions worth "
            "knowing. Anything where you find yourself uncomfortable "
            "but the form is asking you to click Submit anyway.",
    },

    # ── employee-lifecycle.first-impression ──────────────────────────
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    # "Get it right and they hear about the company; get it wrong and
    #  they hear about the bureaucracy."
    {
        "form_key": "employee-lifecycle.first-impression",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Get it right and they hear about the company; get it wrong and they hear about the bureaucracy",
        "body":
            "The new hire is going to tell someone tonight how "
            "their first day went. They'll either describe a place "
            "that had its act together and treated them like a "
            "person, or a place that handed them a stack of forms "
            "and pointed at a chair. You're choosing which story "
            "gets told.",
    },
    {
        "form_key": "employee-lifecycle.first-impression",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common first-impression mistakes",
        "body":
            "Making them wait at the front desk for 20 minutes "
            "because nobody was told they were coming. Starting "
            "with the I-9 instead of a handshake and their name. "
            "Treating onboarding like data entry. Sending them to "
            "the field without telling the supervisor they exist.",
    },
    {
        "form_key": "employee-lifecycle.first-impression",
        "kind": "example",
        "scopes": ["hr", "admin"],
        "title": "What a good first impression looks like",
        "body":
            "You meet them at the door by name. Coffee or water "
            "is already out. The supervisor's face is on a sticky "
            "note so they know who to look for. Paperwork comes "
            "AFTER the welcome conversation, not before it. They "
            "leave knowing where to park tomorrow, what to bring, "
            "and that you're who they call if something's unclear.",
    },

    # ── employee-lifecycle.welcome ───────────────────────────────────
    {
        "form_key": "employee-lifecycle.welcome",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why the welcome comes before the forms",
        "body":
            "If the first 60 seconds of the conversation is 'I "
            "need your SSN and a copy of your driver's license,' "
            "the employee already knows what kind of place this "
            "is. Lead with their name, where they're from, what "
            "shift they're starting on. The paperwork takes the "
            "same five minutes whether it happens at minute one or "
            "minute ten — minute ten lands better.",
    },
    {
        "form_key": "employee-lifecycle.welcome",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common welcome mistakes",
        "body":
            "Asking for documents before introducing yourself. "
            "Reading them the policy stack instead of explaining "
            "what the day looks like. Talking past them to the "
            "form on the screen. Treating it like a transaction "
            "instead of the beginning of a working relationship.",
    },

    # ── employee-lifecycle.documents ─────────────────────────────────
    {
        "form_key": "employee-lifecycle.documents",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Collecting documents without making it feel like an interrogation",
        "body":
            "You need the I-9 docs, the bank info, the emergency "
            "contact. They need to feel like you're helping them "
            "join the company, not screening them at a border. "
            "Explain WHY each one is needed in plain words, accept "
            "what they bring, and resolve gaps with a follow-up "
            "appointment — never with an attitude.",
    },
    {
        "form_key": "employee-lifecycle.documents",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common document-collection mistakes",
        "body":
            "Reciting the list without explaining why each one is "
            "needed. Sighing when they're missing something. "
            "Making them feel like the missing document is their "
            "fault rather than a 'no problem, let's figure out "
            "the fastest path' moment. Treating the document "
            "checklist as a test they're passing or failing.",
    },

    # ── employee-lifecycle.day-one ───────────────────────────────────
    {
        "form_key": "employee-lifecycle.day-one",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What a good Day 1 hand-off looks like",
        "body":
            "Confirm with the supervisor by phone (not just text) "
            "that the new hire is on their way and what time to "
            "expect them. Walk the new hire out personally if you "
            "can, or at minimum point them at the right entrance. "
            "Make sure they have your number for the inevitable "
            "'I'm here — where do I go?' call on the actual first "
            "morning.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter225 · document-expirations · Tier-2 (hr + safety + admin).
    #
    # Document-expiration handling is one of the clearest operational
    # indicators of whether a company feels HUMAN or BUREAUCRATIC.
    # The list shows expiring CDLs, training certs, safety
    # certifications, medical cards — but those rows are PEOPLE, and
    # the choice between a phone call and a bulk email signals how
    # the company actually treats them.
    #
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    #   "Phone call beats email blast."
    #
    # Coaching principles (operator-stated):
    #   • direct leadership engagement over passive bureaucracy
    #   • accountability through proactive communication
    #   • operational respect (the operator's CDL is their livelihood,
    #     not a row on a list)
    #   • triage with judgment — not everything expiring is urgent,
    #     and not everything urgent is on a 30-day window
    #   • when the same person keeps expiring, fix the system, not
    #     the symptom
    #
    # Scope: hr + safety + admin. Shop has its own asset-management
    # voice for equipment expirations — out of scope here.
    # ═════════════════════════════════════════════════════════════════

    # ── document-expirations (canonical 4) ───────────────────────────
    {
        "form_key": "document-expirations",
        "kind": "why",
        "scopes": ["hr", "safety", "admin"],
        "title": "Why this list is people, not paperwork",
        "body":
            "Every row on this page is somebody's CDL, medical "
            "card, OSHA-10, or first-aid cert — the things they "
            "need to keep working. How the company chases them down "
            "before the expiration is how the company tells them "
            "whether they matter. A phone call says 'we know your "
            "name.' A bulk email says 'you're on a list.'",
    },
    {
        "form_key": "document-expirations",
        "kind": "who",
        "scopes": ["hr", "safety", "admin"],
        "title": "Who else depends on this getting handled",
        "body":
            "The employee (whose paycheck stops if the cert lapses). "
            "Their supervisor (who has to redeploy the crew around "
            "the gap). Dispatch (if a CDL drops, the truck doesn't "
            "roll). Safety (if the OSHA card lapses, the site can't "
            "use them). Owners hear about it when a job slows down "
            "because nobody renewed a card on time.",
    },
    {
        "form_key": "document-expirations",
        "kind": "next",
        "scopes": ["hr", "safety", "admin"],
        "title": "What happens after you finish today's outreach",
        "body":
            "The renewal isn't done until you've talked to a human "
            "and they've told you when they're going to the clinic, "
            "the DOL, the testing center. Note the date in the "
            "record. Mark a follow-up for the day after their "
            "appointment so you can confirm the new card. Don't "
            "close the row just because you 'sent the reminder.'",
    },
    {
        "form_key": "document-expirations",
        "kind": "escalate",
        "scopes": ["hr", "safety", "admin"],
        "title": "When to call up before the cert lapses",
        "body":
            "When the employee won't respond after two attempts and "
            "the deadline is inside 14 days. When the renewal "
            "requires money the employee can't front and the "
            "company hasn't decided whether it covers it. When the "
            "same person has expired three quarters in a row — "
            "that's a system problem, not a reminder problem.",
    },

    # ── document-expirations.outreach (ANCHOR SURFACE) ───────────────
    # OPERATOR-STATED ANCHOR (verbatim · test-enforced):
    #   "Phone call beats email blast."
    {
        "form_key": "document-expirations.outreach",
        "kind": "why",
        "scopes": ["hr", "safety", "admin"],
        "title": "Phone call beats email blast",
        "body":
            "A bulk email about expiring CDLs gets opened, glanced "
            "at, and forgotten between three other notifications. A "
            "phone call — even a 90-second one — gets the renewal "
            "on their calendar. The phone call says 'this is "
            "between you and me, and I'm not letting it lapse.' "
            "The email says 'this is a system event.' Pick the one "
            "that gets the cert renewed.",
    },
    {
        "form_key": "document-expirations.outreach",
        "kind": "mistake",
        "scopes": ["hr", "safety", "admin"],
        "title": "Common outreach mistakes",
        "body":
            "Sending the same auto-generated email three weeks in a "
            "row and counting that as 'doing outreach.' Cc'ing the "
            "supervisor instead of calling the employee. Treating "
            "the renewal as the employee's problem alone. Marking "
            "the row 'notified' when nobody confirmed they received "
            "the message — much less that they have a plan.",
    },
    {
        "form_key": "document-expirations.outreach",
        "kind": "example",
        "scopes": ["hr", "safety", "admin"],
        "title": "What a good outreach call sounds like",
        "body":
            "'Hey Mike, your CDL renewal is due May 30 — three "
            "weeks. You got an appointment lined up? … Okay, I'll "
            "block out the morning of the 24th on your schedule so "
            "you've got time for the clinic. Bring the new card to "
            "me by the 31st. Call me if anything blows up in "
            "between.' Ninety seconds. The cert renews on time.",
    },

    # ── document-expirations.cdl ─────────────────────────────────────
    {
        "form_key": "document-expirations.cdl",
        "kind": "why",
        "scopes": ["hr", "safety", "admin"],
        "title": "Why the CDL renewal deserves its own playbook",
        "body":
            "A lapsed CDL doesn't just inconvenience the driver — "
            "it parks the truck. The whole crew slips a day, "
            "dispatch scrambles to reassign, and the customer hears "
            "about it. Build the CDL renewal sequence as a "
            "first-class operational moment, not a calendar "
            "reminder. The driver's livelihood is sitting on top of "
            "this date.",
    },
    {
        "form_key": "document-expirations.cdl",
        "kind": "mistake",
        "scopes": ["hr", "safety", "admin"],
        "title": "Common CDL-renewal mistakes",
        "body":
            "Waiting until 14 days out to start the conversation — "
            "the medical card alone can take longer than that to "
            "schedule. Not flagging the renewal to Dispatch ahead "
            "of time, so they're surprised when the truck doesn't "
            "roll. Forgetting the DOT medical card is a separate "
            "expiration from the CDL itself.",
    },

    # ── document-expirations.triage ──────────────────────────────────
    {
        "form_key": "document-expirations.triage",
        "kind": "why",
        "scopes": ["hr", "safety", "admin"],
        "title": "Not every expiration is this week's problem",
        "body":
            "A first-aid cert expiring in 90 days is not the same "
            "as a medical card expiring in 8 days. Read the list "
            "with judgment: which person is working a job that "
            "requires the cert today? Who can keep working until "
            "next month without it? Which driver is about to roll "
            "a truck where a lapsed card is a real shutdown? Sort "
            "the page by what stops work first, not by date.",
    },
    {
        "form_key": "document-expirations.triage",
        "kind": "mistake",
        "scopes": ["hr", "safety", "admin"],
        "title": "Common triage mistakes",
        "body":
            "Treating the 30-day filter as the only filter. "
            "Chasing a low-impact cert with the same energy as a "
            "CDL because the dates look similar. Skipping the "
            "Expiring Soon tile and only working the Expired tile "
            "— by then someone is already off the job.",
    },

    # ── iter225 · document-expirations.cadence ─────────────────────── 
    {
        "form_key": "document-expirations.cadence",
        "kind": "next",
        "scopes": ["hr", "safety", "admin"],
        "title": "Building the weekly rhythm that catches it early",
        "body":
            "Pick a fixed slot each week — Monday morning works for "
            "most HR coordinators — and walk the Expiring Soon list "
            "before anything else hits the calendar. Phone call to "
            "each person on the list, calendar block, follow-up "
            "date. Same time, same sequence, every week. The "
            "rhythm is what keeps the list from becoming a fire "
            "drill twice a year.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter226 · Dispatcher persona-loop closure (Tier-2 dispatch+admin)
    #
    # Three new families flesh out the dispatcher's operational day
    # surfaced by the iter226 fleshed walkthrough:
    #
    #   • dispatch.utilization       — read the fleet, decide redeploys
    #   • dispatch.daily-report-read — reviewer-side coaching for the
    #                                  cross-portal Daily Reports read
    #   • dispatch.handoff           — end-of-day communication
    #                                  discipline with foremen
    #
    # OPERATOR-STATED ANCHORS (verbatim · test-enforced):
    #   utilization:       "Utilization is a decision tool, not a
    #                      scoreboard."
    #   daily-report-read: "The Daily Report is the dispatcher's
    #                      routing intel — read it for movement, not
    #                      for blame."
    #   handoff:           "The handoff is a conversation, not a
    #                      calendar invite. If tomorrow's plan
    #                      changed, the foreman hears it from you
    #                      tonight — not from the gate guard at
    #                      06:00."
    #
    # Strategic hold preserved: operator mid-day-defect surface is
    # NOT addressed here. Communication-discipline coaching deliberately
    # stops at the end-of-day handoff and the cross-portal read — the
    # mid-day-defect routing philosophy remains an operator-driven
    # architectural decision per walkthrough_pass.md §10.
    # ═════════════════════════════════════════════════════════════════

    # ── dispatch.utilization (canonical 4) ───────────────────────────
    {
        "form_key": "dispatch.utilization",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why this page is a decision tool, not a scoreboard",
        "body":
            "Utilization is a decision tool, not a scoreboard. Read "
            "the page to find your next redeploy, your next "
            "rotation, and your next service pull — not to grade "
            "operators. A 38% utilization number on a unit doesn't "
            "mean the operator is lazy. It means the unit is "
            "available for another job, or it's headed for a "
            "breakdown the shop should know about now.",
    },
    {
        "form_key": "dispatch.utilization",
        "kind": "who",
        "scopes": ["dispatch", "admin"],
        "title": "Who else reads what you decide here",
        "body":
            "The foreman whose crew loses or gains a piece of "
            "equipment tomorrow. The shop, if the rotation surfaces "
            "a service interval. The PM, when a redeployed unit "
            "shows up on a different job's cost code. Don't make "
            "the decision in silence — the people downstream find "
            "out faster than you think and remember whether you "
            "told them first.",
    },
    {
        "form_key": "dispatch.utilization",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What happens after you decide to redeploy",
        "body":
            "Open a Transfer request from this page (don't move "
            "the unit by text message). Confirm the receiving "
            "foreman is expecting it before the truck rolls. Note "
            "the operational reason — 'underused at Site 23, "
            "Crew 12 needs a backup' — so the next dispatcher "
            "reading this in three months knows why the unit "
            "moved.",
    },
    {
        "form_key": "dispatch.utilization",
        "kind": "escalate",
        "scopes": ["dispatch", "admin"],
        "title": "When the number is telling you something bigger",
        "body":
            "A whole crew's units showing 25% across the board — "
            "that's a job-scheduling problem, not a redeploy "
            "problem. Talk to the super. A unit chronically at "
            "100%+ — that's a breakdown waiting to happen. Talk "
            "to the shop. When the page says the same thing for "
            "three weeks running and you've been chasing single "
            "rows, you're missing the pattern.",
    },

    # ── dispatch.utilization.scoreboard (anti-pattern surface) ───────
    {
        "form_key": "dispatch.utilization.scoreboard",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why utilization isn't a grade",
        "body":
            "A unit at 40% isn't a failing unit. It might be the "
            "right-sized backup for a crew that's running ahead of "
            "schedule, or the spare you keep on a job because the "
            "primary breaks down. Reading the number as a grade "
            "drives bad decisions — you pull working backups out "
            "of yards and put crews in a bind the next time the "
            "primary unit goes down.",
    },
    {
        "form_key": "dispatch.utilization.scoreboard",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common scoreboard mistakes",
        "body":
            "Naming and shaming operators by utilization number in "
            "front of supers. Reassigning units based on the "
            "number alone without asking the foreman why it's low. "
            "Treating the utilization tab like a performance "
            "review. Quoting last week's percent at this week's "
            "operator without checking whether the job changed.",
    },

    # ── dispatch.utilization.redeploy (operational read surface) ─────
    {
        "form_key": "dispatch.utilization.redeploy",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why redeploys land better when you call first",
        "body":
            "The receiving foreman doesn't want a unit they didn't "
            "ask for, and the sending foreman doesn't want one "
            "pulled mid-job without a heads-up. Pick up the phone "
            "before you open the Transfer ticket. Ninety seconds "
            "of conversation turns a 'why is my equipment gone?' "
            "phone call into a 'thanks for the back-up' one.",
    },
    {
        "form_key": "dispatch.utilization.redeploy",
        "kind": "example",
        "scopes": ["dispatch", "admin"],
        "title": "What a clean redeploy decision looks like",
        "body":
            "You see Unit 247 at 32% on Site 14 for the second "
            "week. You call Mike on Site 14: 'Hey, the mini's been "
            "quiet — you good if I move it to Crew 8?' Mike says "
            "yes. You call Crew 8's foreman: 'I've got the mini "
            "coming over tomorrow.' THEN you open the Transfer. "
            "Three calls, two minutes total, and tomorrow morning "
            "nobody is surprised.",
    },

    # ── dispatch.daily-report-read (canonical 4 · reviewer-side) ─────
    {
        "form_key": "dispatch.daily-report-read",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why the Daily Report is your routing intel",
        "body":
            "The Daily Report is the dispatcher's routing intel — "
            "read it for movement, not for blame. The notes about "
            "what equipment got used, what sat idle, what came "
            "back damaged, what's needed tomorrow — that's the "
            "input to today's redeploys. Read it the way a "
            "dispatcher reads the morning load board, not the way "
            "an auditor reads a timecard.",
    },
    {
        "form_key": "dispatch.daily-report-read",
        "kind": "who",
        "scopes": ["dispatch", "admin"],
        "title": "Who else is reading the same report differently",
        "body":
            "HR is reading it for hours. PM is reading it for cost "
            "codes. Safety is reading it for incidents. You're the "
            "only one reading it for where the equipment actually "
            "ended up. That's the dispatcher's job — translate "
            "what the foreman wrote into 'what do I move tomorrow.'",
    },
    {
        "form_key": "dispatch.daily-report-read",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What happens after you read today's reports",
        "body":
            "Mark the units you saw flagged for return or service "
            "before you leave the page. Open a Transfer or a Hold "
            "for the obvious ones. Note the foreman's name on any "
            "report where the equipment notes were thin — that's "
            "a coaching conversation, not a write-up, for "
            "tomorrow.",
    },
    {
        "form_key": "dispatch.daily-report-read",
        "kind": "escalate",
        "scopes": ["dispatch", "admin"],
        "title": "When to stop reading and call",
        "body":
            "A report describing a unit going down hard mid-shift "
            "and the foreman still has it on the job — call the "
            "super, not the foreman. A report missing the "
            "equipment section entirely two days in a row from "
            "the same crew — call the foreman now, not after the "
            "third miss. A report contradicting the checkout "
            "record — call HR before redeploying anything from "
            "that crew.",
    },

    # ── dispatch.daily-report-read.routing-intel (anchor surface) ────
    {
        "form_key": "dispatch.daily-report-read.routing-intel",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Read it for movement, not for blame",
        "body":
            "The foreman's note 'mini ran rough most of the day' "
            "is dispatcher gold — that's a service pull tomorrow, "
            "not a blame conversation today. The note 'didn't use "
            "the second roller, sat in yard' is a redeploy "
            "candidate, not a reprimand. Translate the operational "
            "language into routing decisions. The blame frame is "
            "somebody else's job, not yours.",
    },
    {
        "form_key": "dispatch.daily-report-read.routing-intel",
        "kind": "example",
        "scopes": ["dispatch", "admin"],
        "title": "What a good routing-intel read looks like",
        "body":
            "Daily Report from Crew 12: 'Used both excavators, "
            "roller idle 60% of shift, generator quit twice.' "
            "Routing decisions in 90 seconds: leave excavators "
            "alone, mark roller as redeploy candidate (call Crew "
            "8 in the morning), open a Maintenance Hold on the "
            "generator with a note for Shop. One report, three "
            "decisions, nobody got blamed for anything.",
    },

    # ── dispatch.daily-report-read.return-drift (anti-ghost surface) ──
    {
        "form_key": "dispatch.daily-report-read.return-drift",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Catching the checkout vs return drift",
        "body":
            "A unit is on the checkout list but the Daily Report "
            "doesn't mention it for three days running — that's "
            "a ghost rental. Either it came back and nobody "
            "closed the checkout, or it's sitting on a job where "
            "the foreman isn't logging it. Cross-checking the two "
            "lists is the dispatcher's job; nobody else does it.",
    },
    {
        "form_key": "dispatch.daily-report-read.return-drift",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common ghost-rental mistakes",
        "body":
            "Assuming a unit is still in the field because the "
            "checkout says so. Assuming a unit came back because "
            "the foreman didn't mention it. Treating a missing "
            "report as 'nothing to worry about' instead of as a "
            "data gap worth a phone call. Letting the checkout "
            "list and the field reality drift for a week before "
            "reconciling.",
    },

    # ── dispatch.handoff (canonical 4 · end-of-day discipline) ───────
    {
        "form_key": "dispatch.handoff",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why tonight's handoff prevents tomorrow's scramble",
        "body":
            "The handoff is a conversation, not a calendar invite. "
            "If tomorrow's plan changed, the foreman hears it from "
            "you tonight — not from the gate guard at 06:00. "
            "Every minute you spend on the 16:30 confirm call "
            "saves three minutes of next-morning confusion, two "
            "trucks pointed at the wrong yard, and one foreman "
            "who starts the day frustrated.",
    },
    {
        "form_key": "dispatch.handoff",
        "kind": "who",
        "scopes": ["dispatch", "admin"],
        "title": "Who's depending on the call going out",
        "body":
            "Every foreman with a crew rolling in the morning. "
            "Operators who set their alarms based on which yard "
            "they're reporting to. Shop, if the morning plan "
            "includes a service window. The next dispatcher on "
            "shift, who reads tomorrow's plan from your notes "
            "and inherits whatever you left unsaid.",
    },
    {
        "form_key": "dispatch.handoff",
        "kind": "next",
        "scopes": ["dispatch", "admin"],
        "title": "What a clean handoff leaves behind",
        "body":
            "Tomorrow's plan written down, not just remembered. "
            "Each affected foreman confirmed by voice (text-only "
            "doesn't count as confirmed). Open transfers either "
            "closed for the day or annotated with what's still "
            "pending and why. A short note for the next "
            "dispatcher about anything that isn't going to be "
            "obvious from the screens.",
    },
    {
        "form_key": "dispatch.handoff",
        "kind": "escalate",
        "scopes": ["dispatch", "admin"],
        "title": "When the handoff has to go up, not out",
        "body":
            "A unit is down and won't be back tomorrow — the super "
            "needs to know before the foreman calls. A foreman "
            "isn't answering and tomorrow's plan changed — call "
            "the super to backstop the message. A staffing gap "
            "you can't fix from the dispatch seat alone — that's "
            "a 17:00 call to ops oversight, not a problem you "
            "leave for tomorrow morning.",
    },

    # ── dispatch.handoff.communication (the discipline) ──────────────
    {
        "form_key": "dispatch.handoff.communication",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why a call beats a text beats a silent plan",
        "body":
            "Phone calls confirm receipt; texts get scrolled past; "
            "silent plans get discovered at 06:00. The 90-second "
            "phone call to each foreman is the discipline that "
            "keeps the morning calm. Text after the call if you "
            "need a written record — but the conversation is "
            "where the agreement actually happens.",
    },
    {
        "form_key": "dispatch.handoff.communication",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common communication mistakes",
        "body":
            "Group-texting the dispatch sheet and calling that "
            "the handoff. Assuming the calendar invite counts. "
            "Skipping the foreman whose plan didn't change "
            "(they still want to know what everyone else is "
            "doing). Calling at 17:45 when the foreman is "
            "driving home — too late to plan around any of it.",
    },
    {
        "form_key": "dispatch.handoff.communication",
        "kind": "example",
        "scopes": ["dispatch", "admin"],
        "title": "What a 90-second handoff call sounds like",
        "body":
            "'Hey Tony, quick one — tomorrow you're still on "
            "Site 23 with the same crew. Two changes from today: "
            "the second roller's coming back to the yard "
            "overnight for service, and the new operator Alex "
            "is reporting to you at 07:00 instead of 06:30. "
            "Anything else you need from me before tomorrow? "
            "Cool — call if anything blows up overnight.' Done.",
    },

    # ── dispatch.handoff.changes (when the plan moved today) ─────────
    {
        "form_key": "dispatch.handoff.changes",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why the change call goes out first",
        "body":
            "The foreman whose plan moved between 14:00 and 16:30 "
            "is the one most likely to start tomorrow on the "
            "wrong foot. Call those foremen FIRST in your "
            "handoff sequence — not the ones whose day is "
            "unchanged. A change unspoken at 16:30 becomes a "
            "crew standing around at 06:30, paid to wait for an "
            "answer.",
    },
    {
        "form_key": "dispatch.handoff.changes",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Common change-communication mistakes",
        "body":
            "Sequencing the handoff by foreman name instead of by "
            "what changed. Burying the change inside a long "
            "summary of unchanged plans. Telling the operator "
            "but not the foreman, or the foreman but not the "
            "super. Sending the change as 'FYI' when it actually "
            "requires a decision the foreman should weigh in on.",
    },

    # ─────────────────────────────────────────────────────────────────
    # FLEET / TRUCKING DVIR · iter251 · Phase 1-5 contextual coaching
    # ─────────────────────────────────────────────────────────────────
    # form_key hierarchy:
    #   fleet.dvir              · Daily Driver Vehicle Inspection
    #   fleet.weekly-lead       · Weekly Lead Inspection
    #   fleet.weekly-emergency  · Weekly Emergency Equipment Check
    #   fleet.repair            · Shop repair drawer (Phase 4)
    #   fleet.rts               · Dispatch Return-to-Service drawer
    #   fleet.visibility        · Shop / Dispatch / Safety unit cards
    # Public scope · drivers and inspectors are often anonymous-submit.
    {
        "form_key": "fleet.dvir",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the DVIR matters",
        "body":
            "An honest DVIR is the moment the driver, the Shop, and "
            "Dispatch are looking at the same truck. Caught at 6:30 a.m. "
            "it's a Shop ticket. Caught at 50 mph it's a tow bill.",
    },
    {
        "form_key": "fleet.dvir",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who sees what you submit",
        "body":
            "Shop sees every defect grouped by your truck within seconds. "
            "Dispatch sees the unit's status (OOS / Available). Safety "
            "reads the audit trail. Your name stays on the inspection "
            "for accountability, not blame.",
    },
    {
        "form_key": "fleet.dvir",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Easy mistakes to avoid",
        "body":
            "Marking N/A on items the truck actually has. FAIL with no "
            "note (Shop can't act on 'something is wrong'). Skipping the "
            "trailer walk-around when pulling one. Holding the inspection "
            "until you're already on the road.",
    },
    {
        "form_key": "fleet.weekly-lead",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the Weekly Lead pass",
        "body":
            "Leads see patterns drivers stop noticing because they swap "
            "trucks. The slow leak, the gradual mirror crack, the door "
            "seal that's been letting in dust for three weeks. Small "
            "problems · before they become Out of Service.",
    },
    {
        "form_key": "fleet.weekly-lead",
        "kind": "when",
        "scopes": ["public"],
        "title": "When to complete it",
        "body":
            "Once per week per active unit · ideally a day the truck is "
            "in the yard. Doesn't replace the daily DVIR · complements it.",
    },
    {
        "form_key": "fleet.weekly-emergency",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why emergency equipment matters",
        "body":
            "The fire extinguisher you don't notice missing in the yard "
            "is the one you reach for at 2 a.m. in a work zone. Missing "
            "or expired emergency equipment automatically classifies as "
            "Out of Service · this isn't paperwork, it's readiness.",
    },
    {
        "form_key": "fleet.weekly-emergency",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Easy mistakes to avoid",
        "body":
            "Marking 'present' without checking the extinguisher tag "
            "date. Skipping the spill kit on a truck that hauls "
            "hydraulics. Treating an expired tag as Monitor · the system "
            "classifies correctly automatically.",
    },
    {
        "form_key": "fleet.repair",
        "kind": "why",
        "scopes": ["shop", "admin"],
        "title": "Why log the repair here",
        "body":
            "Marking the defect repaired flips the unit to 'Repair in "
            "progress · awaiting RTS'. The truck doesn't roll until "
            "Dispatch confirms Return-to-Service. Your note and timestamp "
            "are the audit trail Safety reads.",
    },
    {
        "form_key": "fleet.repair",
        "kind": "next",
        "scopes": ["shop", "admin"],
        "title": "What happens after you log a repair",
        "body":
            "Dispatch sees the unit appear in their Awaiting-RTS queue. "
            "When they confirm, the unit returns to Available and the "
            "audit log stamps both names — yours and the dispatcher's.",
    },
    {
        "form_key": "fleet.rts",
        "kind": "why",
        "scopes": ["dispatch", "admin"],
        "title": "Why this confirmation is intentional",
        "body":
            "The Shop owns the wrench, but Dispatch owns the operational "
            "decision to put the truck back in rotation. The intentional "
            "checkbox is the moment the platform records that a human "
            "made a decision · not that a button got tapped on the way "
            "to somewhere else.",
    },
    {
        "form_key": "fleet.rts",
        "kind": "mistake",
        "scopes": ["dispatch", "admin"],
        "title": "Easy mistakes to avoid",
        "body":
            "Confirming RTS without reading the Shop note · you lose the "
            "operational context. Skipping the Dispatch note when "
            "something's unusual · brief context helps Safety later.",
    },
    {
        "form_key": "fleet.visibility",
        "kind": "why",
        "scopes": ["shop", "dispatch", "safety", "admin"],
        "title": "How severity works on these cards",
        "body":
            "Drivers don't classify severity · the system does, from a "
            "published table reviewed against FMCSA and DOT baselines. "
            "Out of Service means the unit doesn't roll. Monitor means "
            "Shop owns the repair on a planned cadence · the unit can "
            "operate safely until then.",
    },
    {
        "form_key": "fleet.visibility",
        "kind": "who",
        "scopes": ["shop", "dispatch", "safety", "admin"],
        "title": "What each scope sees here",
        "body":
            "Shop sees the unit grouped with the driver note, photos, "
            "and severity · acts on the repair. Dispatch sees availability "
            "and confirms RTS. Safety reads the full audit trail with "
            "the regulatory reference where applicable.",
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
