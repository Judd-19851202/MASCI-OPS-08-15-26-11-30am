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
    # iter282 · Payroll Variance (HR Exact CSV cross-check)
    # Tone anchor: payroll variance review is not blame work — it is
    # reconciliation between two independent records of the same
    # workweek. Exact says one thing; the supervisor's Daily Reports
    # say another. The variance row is the conversation, not the
    # verdict. Coach toward documentation discipline, threshold-aware
    # decisions, and the truth that disputes are how HR proves the
    # cross-check is real rather than a silent rubber stamp. Scope:
    # hr + admin (this surface is HR portal only).
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "payroll-variance",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why we run this cross-check",
        "body":
            "Exact is what payroll paid. MASCI's Daily Reports are what "
            "the supervisor in the field said the crew worked. When the "
            "two disagree, somebody — payroll, the supervisor or the "
            "employee — has a wrong number. The variance batch is how "
            "HR catches that gap before it becomes a disputed paycheck.",
    },
    {
        "form_key": "payroll-variance",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who depends on this",
        "body":
            "HR runs the cross-check every payroll cycle. The supervisor "
            "is the person who has to answer when a row gets disputed — "
            "their Daily Report is the MASCI side of the comparison. "
            "Payroll downstream needs HR's approve/dispute decisions to "
            "finalize the run. Admin sees the audit trail of every "
            "approval and dispute.",
    },
    {
        "form_key": "payroll-variance",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What happens after you decide",
        "body":
            "Every row is persisted with its decision: approve, dispute "
            "or pending. Approved rows clear the variance. Disputed rows "
            "carry the HR note back to the supervisor for the Daily "
            "Report correction. Pending rows are what's still owed by "
            "the close of the cycle — the dashboard surfaces them so "
            "nothing slips silently past the pay run.",
    },
    {
        "form_key": "payroll-variance",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When the variance is bigger than a row",
        "body":
            "A single 30-minute miss is a row-level conversation. A "
            "whole crew that's off by hours, the same supervisor "
            "missing rows two weeks in a row, or a pattern of Exact "
            "rows with no MASCI hours at all — those are not "
            "row-level fixes. Escalate to Admin and the supervisor's "
            "PM; the variance is telling you something the row "
            "decisions can't resolve.",
    },

    # ── payroll-variance.upload ──────────────────────────────────────
    {
        "form_key": "payroll-variance.upload",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why the threshold matters",
        "body":
            "The threshold is the line between 'rounding noise' and "
            "'real variance.' 15 minutes is the default because that's "
            "roughly a clock-rounding cycle — anything under it is "
            "usually a punch artifact, anything over it is usually a "
            "real disagreement worth a conversation. Move the "
            "threshold up only if you know what you're tuning for.",
    },
    {
        "form_key": "payroll-variance.upload",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common mistakes",
        "body":
            "Pasting last week's Exact export against this week's "
            "ending date — the rows won't match anything in MASCI. "
            "Pasting a CSV with hours in a column the system can't "
            "find (Exact's export format does change). Setting the "
            "threshold to 1 minute and then drowning in 'flagged' "
            "rows that are all rounding noise.",
    },

    # ── payroll-variance.batches ─────────────────────────────────────
    {
        "form_key": "payroll-variance.batches",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why we keep every batch",
        "body":
            "Every batch is the cross-check record for a specific "
            "week. When a paycheck is disputed two months later, the "
            "stored batch is the evidence that HR looked at the "
            "variance, made a call and persisted the decision. "
            "Re-running the cross-check later is not a replacement "
            "for the original batch — both stay on the record.",
    },
    {
        "form_key": "payroll-variance.batches",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What happens on Sunday at 18:00 UTC",
        "body":
            "The weekly cron emails the most recent batch to "
            "hrmanager@mascigc.com and jaymn.judd@mascigc.com. That "
            "email is a backstop, not the primary review channel — "
            "HR should have already worked the batch in-platform "
            "during the week. The email exists so a forgotten batch "
            "still gets seen before the pay run closes.",
    },

    # ── payroll-variance.row-decision ────────────────────────────────
    {
        "form_key": "payroll-variance.row-decision",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why each row needs a decision",
        "body":
            "Pending rows are an open question. Approve says 'I saw "
            "this variance and it's acceptable.' Dispute says 'this "
            "needs a supervisor correction before payroll closes.' "
            "A row left pending is HR saying nothing — and silence "
            "downstream looks the same as approval, which is "
            "exactly the problem the cross-check is supposed to "
            "prevent.",
    },
    {
        "form_key": "payroll-variance.row-decision",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What approval actually means",
        "body":
            "Approve is not 'the numbers are equal' — it's 'HR has "
            "looked at this row, knows the variance and accepts it.' "
            "Use approve on rounding noise, on legitimate "
            "differences (training time, travel, etc.) and on rows "
            "you have already reconciled offline. Use it deliberately, "
            "not as a way to clear the screen.",
    },
    {
        "form_key": "payroll-variance.row-decision",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When the row is not yours to decide",
        "body":
            "If the Exact row has hours that the supervisor's Daily "
            "Report doesn't cover, HR can't fix that in this surface "
            "— that's a Daily Report problem the supervisor has to "
            "resolve. Dispute the row with a note that names the "
            "missing day or job, then ping the supervisor. Don't "
            "approve a row whose root cause lives in another portal.",
    },

    # ── payroll-variance.dispute ─────────────────────────────────────
    {
        "form_key": "payroll-variance.dispute",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why a dispute note is the evidence",
        "body":
            "The dispute note travels with the row. It's what the "
            "supervisor sees, what Admin sees when they audit and "
            "what HR remembers six weeks later when the question "
            "comes back. A note that says 'wrong hours' tells "
            "nobody anything. A note that says 'Exact shows 42.5; "
            "DR for 03/17 missing — supervisor confirmed crew left "
            "early' is a defensible record.",
    },
    {
        "form_key": "payroll-variance.dispute",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When dispute volume is the signal",
        "body":
            "One disputed row a week is normal operational friction. "
            "A pattern — the same supervisor, the same crew, the "
            "same kind of variance week after week — is not a row "
            "problem, it's a documentation discipline problem. Loop "
            "in the supervisor's PM and Admin; the fix lives "
            "upstream of the Exact export, not inside this screen.",
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
    # iter285 · employee-lifecycle.lifecycle-dates · structured
    # employment lifecycle dates (hire / leave / termination).
    # The audit (iter284) proved 0% hire_date coverage across 251
    # employees and ZERO leave-date / termination-date / separation-type
    # adoption. Coaching here exists to anchor the operational mindset:
    # these dates are not paperwork. They are how the platform answers
    # "how long has X been here?" and "is so-and-so back from leave
    # yet?" without HR pulling a spreadsheet. Tone anchor: structured
    # data IS the protection — for the employee and for the company.
    # ═════════════════════════════════════════════════════════════════
    {
        "form_key": "employee-lifecycle.lifecycle-dates",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why we keep these dates structured",
        "body":
            "Hire date, last day worked, termination date, leave start "
            "— these aren't HR paperwork. They are how the platform "
            "answers operational questions without anyone digging "
            "through a spreadsheet: how long has someone been with "
            "the company, when did they actually stop working, when "
            "do we expect them back from leave. Keep them in the "
            "fields, not in notes.",
    },
    {
        "form_key": "employee-lifecycle.lifecycle-dates",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "The hire-date overwrite trap",
        "body":
            "On a rehire, people instinctively want to update the "
            "hire date to the new start day. Don't. The platform "
            "treats `original_hire_date` as write-once on purpose — "
            "your tenure clock, your loyalty data, your historical "
            "record all live there. Rehire dates belong on their own "
            "field (coming later); the original stays preserved.",
    },
    {
        "form_key": "employee-lifecycle.lifecycle-dates",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What the dates feed downstream",
        "body":
            "Tenure shows up automatically in the employee drawer "
            "(derived from the hire date — never stored separately, "
            "so it can't go stale). Leave start + expected return "
            "make the Leave-of-Absence status useful instead of "
            "ornamental. Termination date + last day worked are the "
            "anchors for offboarding tasks, equipment return windows "
            "and the eventual unemployment-claim conversation.",
    },

    # ═════════════════════════════════════════════════════════════════
    # iter285 · employee-lifecycle.separation · separation type and
    # the offboarding transition. Tone anchor: documentation discipline
    # protects everyone, especially in the moments when nobody wants
    # to be careful about paperwork.
    # ═════════════════════════════════════════════════════════════════
    {
        "form_key": "employee-lifecycle.separation",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why separation type is structured, not free-text",
        "body":
            "Voluntary, involuntary, layoff — those three categories "
            "drive everything downstream. Unemployment-claim "
            "responses look different for each one. Rehire policy "
            "looks different for each one. Six months from now when "
            "HR has to remember why someone left, free-text reasons "
            "don't filter. A structured enum does.",
    },
    {
        "form_key": "employee-lifecycle.separation",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Common offboarding-transition mistakes",
        "body":
            "Marking someone Terminated without picking a separation "
            "type — the system will block it now, but in the past "
            "this was the #1 reason HR couldn't run a clean report. "
            "Using 'reason' to encode the type ('quit', 'fired', "
            "'reduction in force') — the reason field is fine for "
            "context, but it's NOT the structured signal. Pick one "
            "of the three; write context in the reason if you want.",
    },
    {
        "form_key": "employee-lifecycle.separation",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When the separation is contested",
        "body":
            "If the departing employee disputes the separation type "
            "(common: 'I quit before I got fired'), document it "
            "factually in the reason and loop in Admin before "
            "finalizing. The structured field is the answer of "
            "record; once set it carries real weight in any later "
            "unemployment hearing. Get the call right the first time.",
    },


    # ═════════════════════════════════════════════════════════════════
    # iter286 · driver-qualification coaching family.
    # Top family: the canonical 4 (why/who/next/escalate) anchored on
    # the operational distinction that the iter284 audit identified as
    # the single most important structural absence:
    #
    #     CDL Holder ≠ Approved Company Driver.
    #
    # Section keys:
    #   .cdl-vs-approved  — the distinction itself, in coaching form
    #   .expirations      — why CDL + medical card expirations matter
    #                       and how they reach the platform's
    #                       expiration scanner
    #
    # Scope: hr + admin (this surface is HR portal only; dispatch &
    # fleet will consume the data later — that's iter288, not now).
    # Tone anchor: this is not compliance theatre. It is operational
    # risk control. A foreman should never have to ask HR whether
    # someone can operate a truck.
    # ═════════════════════════════════════════════════════════════════
    {
        "form_key": "driver-qualification",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why driver qualification is structured data, not notes",
        "body":
            "Today, who can drive what is tribal knowledge — HR "
            "remembers, dispatch assumes, the foreman calls when "
            "they're not sure. That works until the day it doesn't, "
            "and 'doesn't' usually means an unqualified driver on "
            "the road or an asset assigned to someone whose CDL "
            "expired last week. Structured fields make the answer "
            "queryable; tribal knowledge makes it lucky.",
    },
    {
        "form_key": "driver-qualification",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who owns each field",
        "body":
            "HR owns the qualification record itself: CDL holder, "
            "license number/state, expiration dates, medical card. "
            "Admin owns the Approved Company Driver flag — that's "
            "the internal decision separate from whatever the state "
            "DMV says. Dispatch and fleet read the result; they "
            "don't edit it. Keeping write ownership narrow is what "
            "keeps the qualification record defensible.",
    },
    {
        "form_key": "driver-qualification",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What the qualification data feeds",
        "body":
            "CDL + medical card expiration dates auto-flow into the "
            "existing document-expirations tracker, so the same "
            "scanner that warns about every other expiring doc warns "
            "about these. Driver status surfaces in HR review. Later "
            "iterations bring endorsements (Tanker, Hazmat, etc.) "
            "and the dispatch / fleet read surfaces — but the "
            "foundation is the seven fields you set here.",
    },
    {
        "form_key": "driver-qualification",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When the record and the reality disagree",
        "body":
            "If an operator says they have a CDL but the field is "
            "empty, OR the system says approved but the operator "
            "tells the foreman they were just suspended — that's "
            "not a typo, that's a structural conflict. Pull the "
            "physical license, scan the medical card, fix the "
            "record with the actual documents in hand. Loop in "
            "Admin so the Approved Company Driver flag matches the "
            "decision that was actually made.",
    },

    # ── driver-qualification.cdl-vs-approved ─────────────────────────
    {
        "form_key": "driver-qualification.cdl-vs-approved",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why these are two separate fields",
        "body":
            "Holding a CDL is a fact about the person's license. "
            "Being an Approved Company Driver is a decision MASCI "
            "makes — based on their record, their insurance "
            "rating, their internal performance, what equipment "
            "they're cleared on, whether they're under restriction. "
            "Those two things look the same from outside; they are "
            "not the same. Modelling them as one field would erase "
            "the distinction that protects the company.",
    },
    {
        "form_key": "driver-qualification.cdl-vs-approved",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "The combination that gets people hurt",
        "body":
            "The combination to watch: CDL Holder = yes, Approved "
            "Company Driver = no. That's not a bug — it's the "
            "single most operationally important state, and it "
            "means 'this person has a license but MASCI is not "
            "putting them behind the wheel.' Suspended for "
            "telematics violations, under a doctor's restriction, "
            "any number of legitimate reasons. Don't let anyone "
            "talk you into clicking both true 'because they have "
            "a CDL.'",
    },

    # ── driver-qualification.expirations ─────────────────────────────
    {
        "form_key": "driver-qualification.expirations",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why expirations live in the document scanner",
        "body":
            "MASCI already runs an expiration scanner over the "
            "document-expirations collection (the same one that "
            "watches OSHA 30s, DOT annuals, etc.). When you set a "
            "CDL or medical-card expiration on the employee record, "
            "the system mirrors a row into that collection "
            "automatically. You don't manage two lists — you manage "
            "one canonical date, and the existing alerts work for "
            "free.",
    },
    {
        "form_key": "driver-qualification.expirations",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What 'expired' actually means downstream",
        "body":
            "Once the expiration scanner flags a CDL or medical "
            "card as expired, the row shows up in the existing "
            "compliance tracker just like any other expired doc. "
            "Today the platform doesn't auto-revoke the Approved "
            "Company Driver flag — that decision stays human, "
            "intentionally. But the alert is loud enough that HR "
            "will see it before dispatch does, which is the right "
            "order.",
    },
    {
        "form_key": "driver-qualification.expirations",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When an expiration sneaks past",
        "body":
            "If an expired CDL or medical card is discovered after "
            "the operator has already been driving, stop the "
            "assignment immediately, flip Approved Company Driver "
            "off until the record is current, and document the gap "
            "factually — when it expired, when MASCI noticed, what "
            "was being operated in between. The gap window is the "
            "thing that matters for insurance later.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter287 · driver-qualification endorsements + restrictions.
    #
    # Endorsements (N · H · X · T · P · S) and restrictions (air-brake,
    # manual-transmission) live as STRUCTURED CODES, not notes. Why:
    #   - Dispatch / Fleet visibility needs them filterable later.
    #   - Future Motive linkage will read these by code; if they sit in
    #     a free-text field nobody can build a clean map.
    #   - For MASCI specifically: Tanker (N) is the endorsement most
    #     frequently surfaced for asphalt-oil tanker assignments.
    #
    # The schema does NOT auto-collapse {N,H} into {X}; we record what
    # the license actually shows. Conflation is exactly the kind of
    # "helpful" logic that hides operator decisions later.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "driver-qualification.endorsements",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why endorsements are structured, not notes",
        "body":
            "An endorsement isn't trivia — it's an assignment "
            "capability. Tanker (N) means a person is legally cleared "
            "to operate an asphalt-oil tanker; nobody else is. "
            "Hazmat (H) opens a different set of loads. Putting that "
            "in the notes field means a dispatcher has to read prose "
            "before assigning a route. Putting it in a structured "
            "code list means the platform can ask the question "
            "directly: who has N? who has H? who has X? That answer "
            "is the whole point.",
    },
    {
        "form_key": "driver-qualification.endorsements",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who maintains this list",
        "body":
            "HR owns endorsement entry — the source of truth is the "
            "physical CDL document. When an endorsement is added or "
            "removed on the license, HR mirrors the change here. "
            "Dispatch and Fleet read this data later (downstream "
            "visibility, iter288). They do not edit it. Operators "
            "do not edit it. The flow is: license updated → HR "
            "records → everyone else consumes.",
    },
    {
        "form_key": "driver-qualification.endorsements",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What endorsements unlock operationally",
        "body":
            "N = tanker (the asphalt-oil load assignment for MASCI). "
            "H = hazmat. X = both, as one combined endorsement on "
            "the card. T = doubles/triples. P = passenger. S = "
            "school bus (rare here, recorded if present). Record "
            "exactly what the license shows — if the operator was "
            "issued X, record X, do not split it into N+H. The "
            "license entry is the legal source of truth.",
    },
    {
        "form_key": "driver-qualification.endorsements",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When the license and the record disagree",
        "body":
            "If a dispatcher finds an operator running a tanker "
            "route but no N (or X) is recorded here, stop the "
            "assignment, escalate to HR, and verify against the "
            "physical CDL. Either the record is stale (HR fix) or "
            "the operator was assigned a load they aren't endorsed "
            "for (Safety/HR review). Either way the assignment "
            "doesn't resume until the record and the license match.",
    },

    # ── driver-qualification.restrictions ────────────────────────────
    {
        "form_key": "driver-qualification.restrictions",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why restrictions are tracked structurally",
        "body":
            "A restriction is the inverse of an endorsement — it's "
            "what a CDL holder is NOT cleared to do. Air-brake "
            "restriction means the operator can't run vehicles with "
            "air brakes. Manual-transmission restriction means they "
            "can only run automatics. Both decisions matter at the "
            "moment of equipment assignment, not later. Tracking "
            "them as structured codes keeps that moment honest.",
    },
    {
        "form_key": "driver-qualification.restrictions",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "Restrictions ≠ Driver Status",
        "body":
            "Easy to conflate, important not to. Driver Status = "
            "MASCI's internal call on whether someone may operate "
            "(active / suspended / restricted / inactive). "
            "Restrictions = federal license-level constraints "
            "(air-brake, manual-transmission). A driver can be "
            "Active with restrictions; a driver can be Suspended "
            "with no restrictions. They are two independent layers, "
            "both worth recording.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter288 · driver-qualification.dashboard coaching family.
    #
    # The dashboard is operational visibility — it answers questions
    # at-a-glance, it does not assign work. Coaching here protects
    # the boundary: the page is a list, not a workflow engine.
    # ─────────────────────────────────────────────────────────────────
    {
        "form_key": "driver-qualification.dashboard",
        "kind": "why",
        "scopes": ["hr", "admin"],
        "title": "Why this dashboard exists",
        "body":
            "Driver qualification used to live in tribal knowledge — "
            "who has a CDL, who's tanker-capable, whose medical card "
            "is about to lapse. This dashboard puts those questions "
            "on one page so HR can answer them at a glance. It is "
            "visibility, not assignment logic. Dispatch and Fleet "
            "read this same data, but the decision to put someone "
            "on a route stays with the people who already make that "
            "decision today.",
    },
    {
        "form_key": "driver-qualification.dashboard",
        "kind": "who",
        "scopes": ["hr", "admin"],
        "title": "Who uses this page and how",
        "body":
            "HR uses it daily — who's expiring, who's restricted, "
            "who's suspended. Dispatch uses it before assignment — "
            "who has Tanker (N or X), who's approved, who's not. "
            "Safety uses it during incident review — was this "
            "operator legitimately cleared at the time. Read-only "
            "for everyone. Edits happen on the Employee record in "
            "the HR portal, never here.",
    },
    {
        "form_key": "driver-qualification.dashboard",
        "kind": "next",
        "scopes": ["hr", "admin"],
        "title": "What to do with the 30-day expiration cards",
        "body":
            "Two cards count CDLs and medical cards expiring in 30 "
            "days. Call those operators. The document-expirations "
            "scanner already alerts on the same dates, but the "
            "card here is the gut-check: is the number zero, one, "
            "or ten? A phone call beats a bulk email — that is the "
            "operator-stated standard and it holds here too.",
    },
    {
        "form_key": "driver-qualification.dashboard",
        "kind": "escalate",
        "scopes": ["hr", "admin"],
        "title": "When a row tells you to stop an assignment",
        "body":
            "If you see Suspended, or Restricted with an active "
            "assignment, or an expired CDL/medical card with someone "
            "still running, that is the escalation point. Phone "
            "call to the supervisor, flip Approved Company Driver "
            "off, document why and when. The dashboard surfaces "
            "the row — the human still makes the call.",
    },
    {
        "form_key": "driver-qualification.dashboard",
        "kind": "mistake",
        "scopes": ["hr", "admin"],
        "title": "What this dashboard is NOT",
        "body":
            "It is not a dispatch system. It is not a compliance "
            "platform. It does not auto-revoke approved-driver "
            "status when something expires (that decision stays "
            "human, intentionally). It does not assign loads. It "
            "does not enforce qualification at the moment of "
            "assignment. Read those guardrails — building any of "
            "that here would mean MASCI now owns a trucking-"
            "management product, which is exactly what we said no to.",
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

    # ─────────────────────────────────────────────────────────────────
    # iter270 · Safety Meeting / Toolbox Talk coaching family
    # Operator directive: close the operational coaching parity gap.
    # Highest-cadence safety artifact on the platform · 130+ topic
    # library across 21 domains · bilingual. The Safety Meeting form
    # was the only major workflow without an embedded coaching family.
    # Tone benchmark: incident.* and writeup.* — field-foreman voice,
    # incident-pattern oriented, NOT compliance-robot or LMS.
    # ─────────────────────────────────────────────────────────────────

    # ── meeting (top-level / form-root) ──────────────────────────────
    {
        "form_key": "meeting",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why Safety Meetings are operational discipline",
        "body":
            "If the meeting doesn't change what happens on the work, "
            "you held a meeting that didn't happen. The roster proves "
            "presence; the discussion proves the pattern was heard. "
            "Build it like the next incident investigator will read it — "
            "because if something goes wrong, they will.",
    },
    {
        "form_key": "meeting",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who reads this",
        "body":
            "Safety reviews the roster and topic against site patterns. "
            "PM uses it for project compliance. HR cross-checks the crew "
            "count against the Daily Report. Admin pulls it on owner "
            "audits. The signed roster is the legal record someone was "
            "there and heard the topic.",
    },
    {
        "form_key": "meeting",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you submit",
        "body":
            "The meeting attaches to the project, GPS, weather, and crew "
            "context. If crew_size here doesn't match the Daily Report "
            "headcount, HR sees the discrepancy. Edits after submit are "
            "tracked. If a real hazard surfaced, open a Safety Corrective "
            "Action — the meeting record alone won't close the loop.",
    },
    {
        "form_key": "meeting",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to stop the meeting and call",
        "body":
            "Crew refusing to sign. A hazard surfaced you can't control "
            "today. A language barrier you can't bridge with the bilingual "
            "topic. Stop the meeting, call Safety on the phone, and don't "
            "submit until it's handled. The form is the record; the call "
            "is the response.",
    },

    # ── meeting.context (Section 01 — crew, shift, weather, high-risk) ───
    {
        "form_key": "meeting.context",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why crew, shift, weather, and high-risk matter",
        "body":
            "Safety's pattern review filters by these fields. A heat-stress "
            "topic on a 95°F day with high-risk set surfaces for trend "
            "review. Wind 25+ during crane work gets flagged. The fields "
            "aren't paperwork — they're how this meeting gets compared to "
            "the next one in the same conditions.",
    },
    {
        "form_key": "meeting.context",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Leaving crew size blank 'to come back later'. Marking weather "
            "Clear when it was 40°F and raw at 5am. Not flipping high-risk "
            "on a critical lift, confined-space entry, shoring inspection, "
            "or live-traffic MOT setup. These flags drive Safety attention "
            "later — under-flagging buries the meeting in the noise.",
    },
    {
        "form_key": "meeting.context",
        "kind": "when",
        "scopes": ["public"],
        "title": "Timing — hold the meeting before the work",
        "body":
            "Pre-shift means the bullets land before the first cut, dig, or "
            "rollout. Holding it at lunch means half the crew already did "
            "the work the topic was supposed to cover. If you can't hold it "
            "before, hold it as a reset and say so in the discussion notes.",
    },

    # ── meeting.topic (Section 02 — the densest coaching surface) ────
    {
        "form_key": "meeting.topic",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the WHAT HAPPENS paragraph IS the meeting",
        "body":
            "The incident-pattern paragraph is the lesson. The bullets are "
            "how the crew avoids becoming the next one. Read the pattern "
            "first, out loud, in full. Skipping it to save 90 seconds and "
            "jumping to the bullets is pencil-whipping with bullet points.",
    },
    {
        "form_key": "meeting.topic",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Reading bullets without reading the pattern. Picking a generic "
            "topic instead of one tied to today's actual work sequence. "
            "Saying 'everybody knows this' and moving on. Using Custom "
            "Topic three weeks running when a library topic fits — that "
            "pattern flags for Safety review.",
    },
    {
        "form_key": "meeting.topic",
        "kind": "example",
        "scopes": ["public"],
        "title": "Example of a meeting that actually landed",
        "body":
            "'6-ft trench on west side today. Read the trenching pattern. "
            "Asked Carlos to walk the crew through the spoil-pile rule. "
            "Mike pointed out where the box stops if the utility crosses. "
            "Three questions came up — answered before we broke.' That's "
            "a meeting that changed how the work happened.",
    },
    {
        "form_key": "meeting.topic",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens with your discussion notes",
        "body":
            "Discussion notes feed Safety's pattern review. They look for "
            "topics tied to today's work versus generic. They look for "
            "actual crew questions in the notes versus 'reviewed and "
            "understood.' Notes that show participation get weighted "
            "higher when the next incident review pulls history.",
    },
    {
        "form_key": "meeting.topic",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When the topic surfaces a hazard you didn't know about",
        "body":
            "Silica meeting, but no respirators on the truck. Confined-space "
            "topic, but no rescue plan posted. Heat topic, but no shade or "
            "water on site. Stop the meeting, fix the gap before the crew "
            "starts, restart the talk. Note the gap and the fix in the "
            "discussion. Safety wants to see that you caught it.",
    },

    # ── meeting.attendees (Section 03) ───────────────────────────────
    {
        "form_key": "meeting.attendees",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why every attendee signs",
        "body":
            "The signature is the worker's acknowledgment they heard the "
            "pattern and the action drill. Without it, the record is your "
            "word against theirs. With it, the meeting becomes a defensible "
            "operational fact. Same standard in English or Spanish — the "
            "bilingual consent line above the pad says so explicitly.",
    },
    {
        "form_key": "meeting.attendees",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Signing for someone who stepped away. Adding a name without a "
            "signature 'to come back later' and never doing it. Skipping "
            "subcontractor crews because 'they're not ours' — for this "
            "meeting on this site, they are. Letting two people share one "
            "row to save time.",
    },
    {
        "form_key": "meeting.attendees",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who's required to be on the roster",
        "body":
            "Every person on the work today. That includes subs on your "
            "crew assignment and PMs who are on site for the meeting. "
            "Visitors who walked through (deliveries, inspectors, owners) "
            "don't sign. If you're not sure, add them — over-documenting "
            "presence is never the problem.",
    },
    {
        "form_key": "meeting.attendees",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When someone refuses to sign",
        "body":
            "Document the refusal in the discussion notes, don't pressure, "
            "and tell Safety verbally before the day ends. Stop Work "
            "Authority belongs to every signer; a refusal is a signal "
            "worth investigating — not a discipline trigger. Safety handles "
            "it from there.",
    },

    # ── meeting.photos (Section 04) ──────────────────────────────────
    {
        "form_key": "meeting.photos",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why two photos minimum",
        "body":
            "One photo of the crew gathered proves the meeting happened "
            "with density. One photo of the work area or hazard discussed "
            "proves it happened where it mattered. A trenching meeting "
            "with a parking-lot photo doesn't tell that story. Frame the "
            "photo so it would convince someone six months from now.",
    },
    {
        "form_key": "meeting.photos",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Selfie of just the foreman. Blurry photo of the sign-in sheet "
            "with no context. Photos of unrelated equipment. Taking the "
            "photos an hour after the crew dispersed. The timestamp on the "
            "photo is also part of the record — it should match the "
            "meeting time, not lunch.",
    },
    {
        "form_key": "meeting.photos",
        "kind": "example",
        "scopes": ["public"],
        "title": "A frame that does the job",
        "body":
            "Crew of 7 around the toolbox, trench behind them at station "
            "12+50, timestamp 6:42 AM. One frame proves where, when, and "
            "with whom. Add a second of the spoil pile and the trench box "
            "in position — that ties the topic to the work the crew "
            "actually walked into.",
    },

    # ── meeting.signoff (Section 05 — conductor signature) ───────────
    {
        "form_key": "meeting.signoff",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the conductor signs last",
        "body":
            "Your signature certifies the record is accurate as submitted — "
            "attendees, photos, discussion, all of it. Edits after submit "
            "are tracked and reviewed. Signing first and filling in after "
            "is the wrong order; the signature is the last act, not the "
            "first.",
    },
    {
        "form_key": "meeting.signoff",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Signing before photos and attendees are complete. Letting a "
            "non-foreman sign as conductor because the foreman left early. "
            "Forgetting to verify the Conducted By name in Section 01 "
            "matches who actually ran the meeting. Mismatches surface on "
            "Safety audits and slow the next review.",
    },
    {
        "form_key": "meeting.signoff",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after you sign and submit",
        "body":
            "PDF generates, attaches to the project, emails go out if "
            "AUTO_EMAIL is on. If a corrective action came out of the "
            "meeting — order respirators, fix shoring, retrain on backing "
            "— open a Safety Corrective Action. The meeting record is not "
            "the place to track follow-up; it's the place that triggered "
            "the follow-up.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter273 · Site Safety Inspection coaching family
    # Sequence #2 from PLATFORM_OPERATIONAL_MATURITY_MATRIX.md.
    # Mirrors iter270 meeting pattern. Voice: superintendent walking
    # the site with a clipboard and a stop-work radio in their pocket —
    # observational discipline, not regulatory theater.
    # ─────────────────────────────────────────────────────────────────

    # ── inspection (form-root) ───────────────────────────────────────
    {
        "form_key": "inspection",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why a site inspection is operational evidence",
        "body":
            "An inspection is a snapshot of how the site behaves when "
            "nobody thinks the camera is on. The score isn't the point. "
            "The pattern across the score is. PMs read these to see if "
            "the same Yes/No items drift week over week — that's where "
            "real risk lives.",
    },
    {
        "form_key": "inspection",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who reads this inspection",
        "body":
            "Safety reviews against trend. PM reviews against contract "
            "compliance. The GC or owner may pull it on audit. The "
            "foreman whose site this is reads it first — that's the "
            "operational handshake. Inspection without that handshake "
            "is filing, not coaching.",
    },
    {
        "form_key": "inspection",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after submit",
        "body":
            "Score and auto-fails compute on save. A FAIL or any "
            "auto-fail triggers Safety review. Hazards Observed + Stop "
            "Work flags route the record into the corrective-action "
            "queue. The PDF attaches to the project. Edits after "
            "submit are tracked — finish the walk before you sign.",
    },
    {
        "form_key": "inspection",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to stop the walk and call",
        "body":
            "Imminent danger — open trench without a box, lift over "
            "people, energized work without lockout. Stop the work "
            "first. Call the foreman. Call Safety. THEN come back and "
            "document the corrective action and what got fixed. The "
            "inspection is the receipt of the call, not the substitute.",
    },

    # ── inspection.context (Section 01 — project / inspection info) ──
    {
        "form_key": "inspection.context",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why every context field matters",
        "body":
            "Date, time, operation, weather, and crew make the "
            "inspection comparable to the one held last month and next "
            "month. A 6am PPE walk in 38°F rain reads different than a "
            "1pm sunny check. Trend review needs context to mean "
            "anything.",
    },
    {
        "form_key": "inspection.context",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Recording 'Operation' as just 'Construction' (use the "
            "actual task — paving station 4+50, lift on east tower, "
            "excavation 6-ft trench). Skipping subs from the personnel "
            "list because they're not MASCI. Skipping GPS because the "
            "field has cell coverage today.",
    },
    {
        "form_key": "inspection.context",
        "kind": "when",
        "scopes": ["public"],
        "title": "Timing",
        "body":
            "Hold the walk while the work is actually happening — not "
            "before crews mobilize, not after they break for lunch. "
            "What you see is the operational state under load. A site "
            "inspected during pre-task brief or cleanup tells you less "
            "than one inspected at peak production.",
    },

    # ── inspection.ppe (Section 03 — PPE compliance) ─────────────────
    {
        "form_key": "inspection.ppe",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why PPE is the first read on culture",
        "body":
            "PPE compliance shows yesterday's culture, not today's "
            "policy. If hard hats are inconsistent, the conversation "
            "isn't a memo — it's the foreman, today, before the next "
            "shift. PPE drift is the early warning for everything else "
            "this inspection will surface.",
    },
    {
        "form_key": "inspection.ppe",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Marking PPE Yes because the gear was on the truck. Yes "
            "means worn correctly, on every worker, during the work — "
            "not stored. Marking N/A when an item simply wasn't seen — "
            "if it wasn't seen, write it in the notes and follow up. "
            "N/A is for genuinely-doesn't-apply, not skipped.",
    },
    {
        "form_key": "inspection.ppe",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When PPE itself is the stop-work",
        "body":
            "Missing fall arrest at height. Missing eye/ear in active "
            "drilling, cutting, grinding. Missing respirator in known "
            "silica or chemical exposure. Don't finish the walk — fix "
            "it first. Note the gap, the fix, and who confirmed it. "
            "Then continue.",
    },

    # ── inspection.findings (Section 12 — safety issues + corrective) ─
    {
        "form_key": "inspection.findings",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why this section is the inspection's spine",
        "body":
            "A clean PPE row and a clean hazard row can still hide a "
            "real finding. The findings section is where the "
            "inspector says what the score can't: what was actually "
            "happening, what got corrected on site, what's still "
            "open, and who owns the close-out.",
    },
    {
        "form_key": "inspection.findings",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Writing 'see PPE section' as the corrective note — be "
            "specific. Naming a 'Responsible Party' as the crew "
            "instead of one name. Marking Corrected On Site = Yes "
            "without saying what changed. Leaving the description "
            "blank because the row count looks clean.",
    },
    {
        "form_key": "inspection.findings",
        "kind": "example",
        "scopes": ["public"],
        "title": "A finding that does the job",
        "body":
            "'Trench at station 12+50 had no protective system. Stop "
            "Work issued 7:18am. Trench box delivered and seated by "
            "7:55am. Foreman J. Cruz acknowledged. Photo attached. "
            "Corrected on site. No further action — coaching captured "
            "in toolbox-talk tomorrow.' Specific. Time-stamped. "
            "Closed.",
    },
    {
        "form_key": "inspection.findings",
        "kind": "next",
        "scopes": ["public"],
        "title": "How findings become actions",
        "body":
            "Photos here travel with the PDF — frame the hazard "
            "clearly. If Corrected On Site = No, the finding becomes "
            "an open Safety Corrective Action — open one from the "
            "Safety portal so the close-out is tracked separately. "
            "Don't let an open finding hide in an old inspection.",
    },

    # ── inspection.signoff (Section 13 — signatures) ─────────────────
    {
        "form_key": "inspection.signoff",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why both signatures matter",
        "body":
            "The inspector signs the observation. The foreman signs "
            "the acknowledgment. Two signatures on the same record "
            "mean both sides saw the same site at the same time. "
            "One-sided records read like surveillance reports — "
            "useful, but not coaching.",
    },
    {
        "form_key": "inspection.signoff",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Inspector signs and submits without the foreman present. "
            "Foreman signs without reviewing the findings (they should "
            "see the score and read every Open / No / Auto-Fail row "
            "before signing). A signature dated days after the walk.",
    },
    {
        "form_key": "inspection.signoff",
        "kind": "next",
        "scopes": ["public"],
        "title": "After both signatures",
        "body":
            "PDF generates with score, photos, and both signatures. "
            "It attaches to the project. AUTO_EMAIL ships it if "
            "enabled. The next inspection on this project starts with "
            "this record in the trend view — that's how patterns "
            "become visible across walks.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter273 · QA/QC Inspection coaching family
    # Quality discipline cousin of the safety inspection. Voice:
    # superintendent who's seen the punch list come back to bite the
    # project twice and will not let it happen a third time.
    # ─────────────────────────────────────────────────────────────────

    # ── qaqc (form-root) ─────────────────────────────────────────────
    {
        "form_key": "qaqc",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why catch it before it sets",
        "body":
            "QA/QC is the cheapest correction the project will ever "
            "make. Pre-pour, pre-cover, pre-close-out — every "
            "inspection caught here saves 10× the cost it takes to "
            "fix it after concrete cures, drywall closes, or the "
            "subgrade gets paved over.",
    },
    {
        "form_key": "qaqc",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who reads QA/QC",
        "body":
            "PM tracks contract compliance. The owner / engineer may "
            "pull it on punch walks. The sub whose work is inspected "
            "reads the deficiencies before they invoice. Future "
            "warranty claims start here — incomplete QA/QC records "
            "become incomplete defenses.",
    },
    {
        "form_key": "qaqc",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after submit",
        "body":
            "Photos and deficiencies attach to the project. Any FAIL "
            "or deficiency note routes for PM review. The PDF emails "
            "if AUTO_EMAIL is on. Open deficiencies should also be "
            "tracked on the punch list — the QA/QC record is the "
            "evidence, the punch list is the action.",
    },
    {
        "form_key": "qaqc",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to stop the work",
        "body":
            "Subgrade fails compaction and the paver is staged. "
            "Concrete slump fails and the truck is in the chute. "
            "Footing dimensions wrong and forms aren't stripped yet. "
            "Stop the work, call PM and the sub foreman, document, "
            "THEN restart. A QA/QC fail caught mid-pour is the cheap "
            "version of next month's tear-out.",
    },

    # ── qaqc.context (Job + Sub + Inspection meta) ───────────────────
    {
        "form_key": "qaqc.context",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why job + sub + location all matter here",
        "body":
            "Quality issues cluster by sub crew, by station, by "
            "weather window. PMs and engineers reading a year of QA/QC "
            "should be able to filter to 'crew X, station 4+00 to "
            "8+00, summer pours' and see the pattern. Generic location "
            "kills that lens.",
    },
    {
        "form_key": "qaqc.context",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Naming the subcontractor as 'sub' or 'the concrete guys' "
            "— use the company name and the foreman. Location as just "
            "'east side' — use the station, grid, or floor. Mix "
            "designs / quantities left blank because the truck ticket "
            "is in your other pocket. Stop and get it.",
    },
    {
        "form_key": "qaqc.context",
        "kind": "when",
        "scopes": ["public"],
        "title": "Timing",
        "body":
            "Pre-pour, pre-cover, pre-close-out — never after. "
            "Inspections done after the work is buried prove nothing "
            "and protect nothing. If you're inspecting it for "
            "deficiencies you can no longer see, the inspection is "
            "ceremonial.",
    },

    # ── qaqc.checklist (Checklist section) ───────────────────────────
    {
        "form_key": "qaqc.checklist",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why every item gets answered",
        "body":
            "Skipped items become assumed-passes when someone reads "
            "this later. Every Pass / Fail / N/A is a deliberate "
            "statement. N/A is reserved for items that genuinely don't "
            "apply to this discipline today — not items you didn't "
            "look at.",
    },
    {
        "form_key": "qaqc.checklist",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Marking Pass without verifying — visual + measurement + "
            "spec match. Marking Fail without writing the deficiency "
            "note (the form blocks this, don't fight it). Using N/A "
            "to make a clean row when the right answer is Fail. "
            "Calling 'within tolerance' a pass when you didn't pull a "
            "tape.",
    },
    {
        "form_key": "qaqc.checklist",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When a Fail isn't an inspection problem anymore",
        "body":
            "Repeat Fails on the same item from the same sub crew on "
            "the same project — that's a contract conversation, not "
            "an inspection note. Document the deficiency, but also "
            "flag the pattern to PM. One Fail is a finding. Three is "
            "a meeting.",
    },

    # ── qaqc.corrective (Notes & Corrective Action) ──────────────────
    {
        "form_key": "qaqc.corrective",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why corrective notes belong on the record",
        "body":
            "The deficiency is the finding. The corrective note is "
            "what someone reading this 6 months from now needs to "
            "know happened. 'Sub re-tied at station 6+20, "
            "re-inspected, photo attached' is a closed loop. "
            "'Will retie' is a future tense and a future problem.",
    },
    {
        "form_key": "qaqc.corrective",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Vague verbs (will fix, will address, will follow up). "
            "Passive voice that hides who owns the correction. Listing "
            "the corrective as a future task without an owner. Saying "
            "'see photo' when the photo doesn't show the corrective "
            "action — only the original deficiency.",
    },
    {
        "form_key": "qaqc.corrective",
        "kind": "next",
        "scopes": ["public"],
        "title": "How corrective notes link to the punch list",
        "body":
            "If the correction will happen later (sub returns "
            "tomorrow, materials ordered, engineer review needed), the "
            "corrective belongs ALSO on the punch list — not just "
            "here. The QA/QC record is the evidence. The punch list "
            "is the tracking system. Use both.",
    },

    # ── qaqc.photos (Photos section) ─────────────────────────────────
    {
        "form_key": "qaqc.photos",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why photos prove the location, not the effort",
        "body":
            "A QA/QC photo should let an engineer 18 months from now "
            "tell exactly where on the project this was, what spec it "
            "was supposed to meet, and what the visual condition was. "
            "Frame for that reader — include a tape, a grid mark, a "
            "station tag if there is one.",
    },
    {
        "form_key": "qaqc.photos",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Photos taken from too far away to see the deficiency. "
            "Photos with no reference point (no tape, no grid, no "
            "station). Four photos of the same angle. A clean photo "
            "of the work and no photo of the deficiency. After the "
            "correction, no follow-up photo of the closed item.",
    },
    {
        "form_key": "qaqc.photos",
        "kind": "example",
        "scopes": ["public"],
        "title": "A photo set that does the job",
        "body":
            "(1) Wide shot showing station and surrounding work. "
            "(2) Close-up of the deficiency with a tape in frame. "
            "(3) After the correction — same angle as #2 — showing "
            "the deficiency closed. Three frames prove the finding, "
            "the spec gap, and the resolution.",
    },

    # ── qaqc.signoff (Sign-Off section) ──────────────────────────────
    {
        "form_key": "qaqc.signoff",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why the inspector signs last",
        "body":
            "Your signature certifies the checklist, deficiencies, "
            "and photos are accurate AS SUBMITTED. If a deficiency "
            "closes after you sign, that's a punch-list event — open "
            "a new entry, don't re-edit this record. Edits after "
            "submit are tracked and reviewed.",
    },
    {
        "form_key": "qaqc.signoff",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after sign-off",
        "body":
            "PDF generates, attaches to the project, emails per "
            "AUTO_EMAIL. PM and engineer reviewers see the record in "
            "the QA/QC queue. Open deficiencies should now exist on "
            "the punch list — if they don't, this record is incomplete "
            "operationally even though it's complete legally.",
    },

    # ─────────────────────────────────────────────────────────────────
    # iter274 · Safety Corrective Actions coaching family
    # Sequence #3 from PLATFORM_OPERATIONAL_MATURITY_MATRIX.md.
    # Mirrors iter270/iter273 pattern. Voice: safety coordinator who
    # has seen too many "we'll get to it" findings die in old reports.
    # ─────────────────────────────────────────────────────────────────

    # ── corrective (page-root) ───────────────────────────────────────
    {
        "form_key": "corrective",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why corrective actions exist as their own record",
        "body":
            "A finding in an incident, inspection, or audit is a "
            "snapshot. A corrective action is the work that closes it. "
            "Separate record because the finding and the close-out "
            "rarely belong to the same person, the same week, or "
            "sometimes the same project phase.",
    },
    {
        "form_key": "corrective",
        "kind": "who",
        "scopes": ["public"],
        "title": "Who reads this queue",
        "body":
            "Safety reviews the Open and Overdue tabs daily. PM checks "
            "for items tied to their project number. The assigned "
            "owner reads it because their name is on it. Admin or "
            "owner audits pull the queue to see how findings actually "
            "resolve — not just how often they're found.",
    },
    {
        "form_key": "corrective",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens as the CA moves through the pipeline",
        "body":
            "Open means owner assigned, work not started. In Progress "
            "means work is underway. Pending Review means the owner "
            "says it's done — Safety verifies before closing. Closed "
            "means evidence on the record + signature acknowledged. "
            "Skipping Pending Review breaks the audit trail.",
    },
    {
        "form_key": "corrective",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "When to escalate or stop the work",
        "body":
            "Critical priority CA past due. Repeat finding on the same "
            "equipment, employee, or sub crew — third occurrence is a "
            "contract conversation, not another CA. Open CA with no "
            "owner for 48+ hours. Call Safety, raise to PM, document "
            "the escalation in the notes field.",
    },

    # ── corrective.create (dialog · new CA) ──────────────────────────
    {
        "form_key": "corrective.create",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why every field on this dialog matters",
        "body":
            "The title is what someone scanning the queue reads. The "
            "description is what the owner reads when they're confused. "
            "The source link is what the auditor reads in 18 months. "
            "Skipping any of them isn't saving time — it's pushing the "
            "work onto the next person.",
    },
    {
        "form_key": "corrective.create",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Titles like 'Safety follow-up' or 'Fix issue' — useless in "
            "a list of 80. Assigning to 'the crew' instead of one named "
            "owner. No source link to the originating record. Due date "
            "30 days out for a Critical priority. Project number left "
            "blank because the source already has it.",
    },
    {
        "form_key": "corrective.create",
        "kind": "example",
        "scopes": ["public"],
        "title": "A CA that closes itself",
        "body":
            "Title: 'Install eye-wash station at job 220 break trailer'. "
            "Source: Inspection 4A2C-… Priority: High. Owner: J. Cruz "
            "(name + email). Due: 5 days. Description: 'Required by "
            "OSHA per chemical exposure on the work plan. Ship to job "
            "by Friday, photo confirmation required.' One read, one "
            "owner, one deadline.",
    },
    {
        "form_key": "corrective.create",
        "kind": "escalate",
        "scopes": ["public"],
        "title": "Priority discipline",
        "body":
            "Critical = imminent danger or regulatory exposure. Same-"
            "day or next-shift due dates. High = real risk, this week. "
            "Medium = within 2 weeks. Low = within the month. Marking "
            "everything High flattens the signal — the next reader "
            "can't tell what to fix first.",
    },

    # ── corrective.close (dialog · edit mode close-out) ──────────────
    {
        "form_key": "corrective.close",
        "kind": "why",
        "scopes": ["public"],
        "title": "Why closure requires evidence",
        "body":
            "A CA closed with 'done' in the notes is a CA that's not "
            "closed — it's archived. Completion notes describe what "
            "actually changed, with date and reference. The employee "
            "signature is the acknowledgment that the person affected "
            "saw the close-out. Both make the record audit-ready.",
    },
    {
        "form_key": "corrective.close",
        "kind": "mistake",
        "scopes": ["public"],
        "title": "Common mistakes",
        "body":
            "Closing the CA before the work is actually verified on "
            "site (mark Pending Review instead — Safety closes after "
            "verification). Completion notes that say only 'completed' "
            "or 'done'. Skipping the employee signature because 'they "
            "already know'. Closing on a Friday without confirming "
            "the next-shift handoff.",
    },
    {
        "form_key": "corrective.close",
        "kind": "next",
        "scopes": ["public"],
        "title": "What happens after Closed",
        "body":
            "The CA stays on the project's compliance record. Trend "
            "review uses it to track close-out velocity by owner, "
            "priority, and source type. If the same finding recurs "
            "later, the closed record proves what was done last time — "
            "and exposes what didn't stick.",
    },
]


# ─────────────────────────────────────────────────────────────────────
# iter274 · Canonical-4 fills (Sequence #4)
# Plug two small holes flagged by the maturity matrix:
#   * fleet family missing kind=escalate (added under fleet.dvir)
#   * material-calculator missing kind=who (added at root)
# ─────────────────────────────────────────────────────────────────────
_TIPS.append({
    "form_key": "fleet.dvir",
    "kind": "escalate",
    "scopes": ["public"],
    "title": "When a DVIR defect stops the unit",
    "body":
        "Critical defects — brakes, steering, lights at night, fluid "
        "leaks under the cab, tires below tread — mean Out-of-Service. "
        "Don't roll. Don't 'just take it across the yard.' Call Shop, "
        "call Dispatch, document the defect with photo. The DVIR is "
        "the legal record that the call was made.",
})
_TIPS.append({
    "form_key": "material-calculator",
    "kind": "who",
    "scopes": ["public"],
    "title": "Who reads the takeoff numbers",
    "body":
        "PM uses them for budget and procurement. PE checks them "
        "against drawings. Super reads them to plan the day's "
        "deliveries and crew sizing. Owner / GC may see the rolled-up "
        "quantities on monthly billing. A wrong number here cascades "
        "into a wrong order, a wrong invoice, and a wrong forecast.",
})

# ─────────────────────────────────────────────────────────────────────
# iter275 · Bundled Sequences #5 + #6 from MATURITY MATRIX
# Five surfaces in one closure pass. Same HelpTipBlock architecture,
# same registry pattern, same tone gates. No new architecture.
#   • equipment-issuance   (PPE / gear handed to a worker)
#   • equipment-training   (toolbox-talk-grade equipment training)
#   • topic-library        (admin/safety topic library + PDF pack)
#   • fire-extinguisher    (NFPA 10 inspection cadence)
#   • jha                  (Job Hazard Analysis posting + working plan)
# ─────────────────────────────────────────────────────────────────────

# ── equipment-issuance ────────────────────────────────────────────────
_TIPS.extend([
    {"form_key": "equipment-issuance", "kind": "why", "scopes": ["public"],
     "title": "Why an issuance record is the operational handshake",
     "body": "Gear without a signature is gear that walked off the yard. "
             "The issuance record is the paper trail that proves the "
             "worker received it, was shown how to use it, and accepted "
             "responsibility for its condition. No record = no defense "
             "if it shows up damaged, missing, or in someone else's hands."},
    {"form_key": "equipment-issuance", "kind": "who", "scopes": ["public"],
     "title": "Who reads issuance records",
     "body": "Safety on returns and damage. HR on separations (the "
             "checkout list against the return list). Admin on inventory. "
             "If the same employee shows three damaged hard hats in six "
             "months, that's a pattern worth investigating — not another "
             "replacement."},
    {"form_key": "equipment-issuance", "kind": "next", "scopes": ["public"],
     "title": "What happens after submit",
     "body": "Record attaches to the employee profile. Acknowledgment "
             "signature is captured with the gear list. PDF generates "
             "and attaches to the project. On separation, this record "
             "is the basis for the return checklist — anything not "
             "returned can become a payroll deduction with proper notice."},
    {"form_key": "equipment-issuance", "kind": "escalate", "scopes": ["public"],
     "title": "When to refuse issuance",
     "body": "Worker has no current orientation. Equipment is the "
             "wrong size or fit (hard hat won't sit, harness won't "
             "cinch). PPE shows visible damage in the issuance moment "
             "— don't issue damaged gear and write 'as is'. Pull from "
             "stock, document the damage, replace the unit."},
    {"form_key": "equipment-issuance.employee", "kind": "why", "scopes": ["public"],
     "title": "Why the employee record link matters",
     "body": "Linking to the master employee record means future "
             "issuances, returns, and damage events line up under one "
             "name. Typing the name freeform breaks that lens. If "
             "the employee isn't in the master, that's the gap to "
             "fix first — not a workaround for today."},
    {"form_key": "equipment-issuance.employee", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Issuing to 'the crew' instead of a named person. "
             "Skipping the employee link because the picker is slow. "
             "Issuing to an employee on the wrong project. Forgetting "
             "to confirm the trade — the gear list should match the "
             "work the person actually does."},
    {"form_key": "equipment-issuance.equipment", "kind": "why", "scopes": ["public"],
     "title": "Why every item is its own line",
     "body": "One item per line means each unit is trackable on "
             "return. 'Standard PPE kit' as a single line means six "
             "months later nobody knows whether the harness came "
             "back. Hard hat, safety glasses, harness, lanyard, "
             "boots, vest — each gets a row."},
    {"form_key": "equipment-issuance.equipment", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Bulk-listing 'PPE set'. Skipping the serial number on "
             "items that have one (harnesses, hearing protection, "
             "respirators). Using 'Other' as a catch-all when the "
             "real item is in the master list. Quantity left blank "
             "because 'they only get one anyway'."},
    {"form_key": "equipment-issuance.equipment", "kind": "example", "scopes": ["public"],
     "title": "A clean issuance line",
     "body": "Hard hat · Class E · sz L · qty 1 · serial 224-887. "
             "Six months from now an auditor or replacement supervisor "
             "can answer: who got it, when, which one, in what size. "
             "That's the standard, not 'hat issued'."},
    {"form_key": "equipment-issuance.photos", "kind": "why", "scopes": ["public"],
     "title": "Why photos at issuance",
     "body": "Condition at handoff is the only fact that closes "
             "the 'it was already broken' argument later. A photo of "
             "the harness webbing, the hat shell, the boot tread — "
             "captured today — is what protects both the worker and "
             "the company when the equipment comes back damaged."},
    {"form_key": "equipment-issuance.photos", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "One photo of the pile. No photo of the serial number. "
             "Photos taken in poor light that hide defects. Skipping "
             "photos because the worker is in a hurry — that's "
             "exactly the moment to slow down. The handoff is when "
             "the record is set."},
    {"form_key": "equipment-issuance.photos", "kind": "example", "scopes": ["public"],
     "title": "A photo set that does the job",
     "body": "(1) Each item laid out flat on a clean surface. (2) "
             "Close-up of serial numbers / size tags. (3) Any "
             "pre-existing wear, scuff, or repair clearly framed. "
             "Three to five frames covering the whole issuance — "
             "that's the standard."},
    {"form_key": "equipment-issuance.acknowledgment", "kind": "why", "scopes": ["public"],
     "title": "Why the acknowledgment language is legal",
     "body": "The bilingual paragraph above the signature is what "
             "makes this a contract instead of a receipt. The worker "
             "accepts responsibility for the gear, agrees to report "
             "damage, and acknowledges the company's right to deduct "
             "for unreturned items. Skip reading it to the worker and "
             "the contract weakens."},
    {"form_key": "equipment-issuance.acknowledgment", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Signing without reading the acknowledgment aloud to the "
             "worker. Capturing the signature on the wrong side of "
             "the language. Letting the worker sign in pencil or in "
             "an unreadable scrawl — the signature has to look like "
             "the one on file."},
    {"form_key": "equipment-issuance.acknowledgment", "kind": "escalate", "scopes": ["public"],
     "title": "When a worker refuses to sign",
     "body": "Don't issue. Document the refusal in the notes field "
             "with the date and time. Tell Safety verbally before "
             "the day ends. A signature refusal during issuance is "
             "an early signal — investigate the cause, don't escalate "
             "to discipline as the first move."},
])

# ── equipment-training ────────────────────────────────────────────────
_TIPS.extend([
    {"form_key": "equipment-training", "kind": "why", "scopes": ["public"],
     "title": "Why equipment training is not a checkbox",
     "body": "A worker who runs a piece of equipment they were trained "
             "on yesterday will, statistically, do it the way they were "
             "trained. If the training was paperwork — they'll work "
             "from paperwork understanding. If the training was hands-on "
             "— they'll work from hands-on muscle memory. Pick which "
             "worker you want on site tomorrow."},
    {"form_key": "equipment-training", "kind": "who", "scopes": ["public"],
     "title": "Who reads training records",
     "body": "Safety on incident review (was the operator actually "
             "trained on this unit?). HR on hire/transfer eligibility. "
             "PM when a sub asks for proof of competency. OSHA, on "
             "audit. The trainee themselves — their name is on the "
             "record, this is part of their employment history."},
    {"form_key": "equipment-training", "kind": "next", "scopes": ["public"],
     "title": "What happens after submit",
     "body": "Record attaches to the employee profile and equipment "
             "competency list. Expiration date (per OSHA / manufacturer) "
             "tracks forward — Safety gets notice 30 / 7 days out. The "
             "signed acknowledgment becomes the legal record that "
             "training happened on this date for this person on this gear."},
    {"form_key": "equipment-training", "kind": "escalate", "scopes": ["public"],
     "title": "When to fail the trainee",
     "body": "Hands-on demonstration fails. Trainee can't articulate "
             "the top three hazards of the equipment. Trainee skipped "
             "the toolbox walk-around. Don't sign. Reschedule, retrain, "
             "document the gap, and notify Safety + PM. A failed "
             "training is operational — a falsified one is a liability."},
    {"form_key": "equipment-training.context", "kind": "why", "scopes": ["public"],
     "title": "Why every context field matters",
     "body": "Trainer, date, duration, location, equipment — these "
             "are what make the record audit-defensible. 'Training "
             "happened sometime in Q3' is not a record. 'Conducted "
             "by J. Cruz on 3/14 at the yard, 90 min, on Skid Steer "
             "234-A' is."},
    {"form_key": "equipment-training.context", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Duration as 'classroom' with no minutes — OSHA "
             "expects time-on-task. Location as 'yard' with no project "
             "number — training tied to a specific project is more "
             "defensible than 'somewhere'. Trainer name as the company "
             "instead of a person."},
    {"form_key": "equipment-training.acknowledgment", "kind": "why", "scopes": ["public"],
     "title": "Why the trainee acknowledges in writing",
     "body": "The signature is the trainee's statement that the "
             "training happened and was understood. Without it, the "
             "record is the trainer's word against the trainee's. With "
             "it, the trainee owns the competency claim on their own "
             "employment record."},
    {"form_key": "equipment-training.acknowledgment", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Signing for the trainee 'because they had to leave'. "
             "Capturing the signature before the hands-on portion is "
             "complete. Letting the trainee sign without first reading "
             "the acknowledgment language. Bilingual is required — "
             "use the language the trainee actually understands."},
    {"form_key": "equipment-training.acknowledgment", "kind": "escalate", "scopes": ["public"],
     "title": "When the trainee can't sign in their working language",
     "body": "Stop. Get a bilingual translator (foreman, peer, "
             "supervisor — anyone fluent). Re-deliver the key safety "
             "points in the trainee's language. Document who "
             "translated and confirm comprehension before signing. "
             "Don't continue with a language gap — that's an incident "
             "waiting to happen."},
    {"form_key": "equipment-training.signatures", "kind": "why", "scopes": ["public"],
     "title": "Why both signatures matter",
     "body": "Trainer signs that the training was delivered. Trainee "
             "signs that it was received and understood. Two signatures "
             "= a closed loop. One signature = an open question for "
             "the next investigator to ask."},
    {"form_key": "equipment-training.signatures", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Trainer signs and forgets the trainee. Trainee signs "
             "on the trainer line. Both signatures captured before "
             "the hands-on demo. Either signature dated wrong (back-"
             "dating training is a falsification — not a paperwork "
             "shortcut)."},
    {"form_key": "equipment-training.signatures", "kind": "next", "scopes": ["public"],
     "title": "What happens after both signatures",
     "body": "PDF generates, attaches to the project and employee "
             "record. Competency window starts today. Renewal notice "
             "schedules per the equipment-specific expiration rule. "
             "If a refresh is required (manufacturer or OSHA), Safety "
             "gets a heads-up 30 days out."},
    {"form_key": "equipment-training.signatures", "kind": "escalate", "scopes": ["public"],
     "title": "When training expires mid-project",
     "body": "Don't let the operator run on expired training. "
             "Schedule a renewal before the expiration date. If a "
             "renewal is missed and the operator runs anyway, that's "
             "a Safety Corrective Action — not a 'we'll catch up' "
             "moment. Document the gap, the renewal, and the bridge."},
])

# ── topic-library ─────────────────────────────────────────────────────
_TIPS.extend([
    {"form_key": "topic-library", "kind": "why", "scopes": ["public"],
     "title": "Why the library exists separate from meetings",
     "body": "A topic library is a curated catalog of incident-pattern "
             "talks. A safety meeting is the operational delivery of "
             "one of those talks today. Separate so the library can be "
             "maintained, versioned, and exported as packs — without "
             "depending on whether a specific meeting was held."},
    {"form_key": "topic-library", "kind": "who", "scopes": ["public"],
     "title": "Who reads the library",
     "body": "Admin / Safety manages it. Foremen pull from it via "
             "the New Meeting topic picker — they never browse the "
             "library directly. The PDF pack is read by Safety on "
             "client requests, OSHA audits, or training rotations. "
             "Subs and visiting trades may receive a pack at orientation."},
    {"form_key": "topic-library", "kind": "next", "scopes": ["public"],
     "title": "What happens when a topic moves to a meeting",
     "body": "Foreman selects the topic in New Meeting. The incident "
             "pattern, hazards, key points, and references prefill. "
             "Action items become the discussion drill. Meeting "
             "submits → record attaches to project + topic key — so "
             "the library knows which topics were actually delivered."},
    {"form_key": "topic-library", "kind": "escalate", "scopes": ["public"],
     "title": "When a library topic is missing or wrong",
     "body": "Don't write around it in a custom meeting. File the "
             "gap with Safety/Admin. New topics go through review — "
             "voice, incident-pattern accuracy, bilingual parity. "
             "Custom Topic exists for genuinely one-off situations, "
             "not for missing library coverage."},
    {"form_key": "topic-library.filter", "kind": "why", "scopes": ["public"],
     "title": "Why filters drive operational selection",
     "body": "21 domains × 6 severity levels × incident-pattern tags = "
             "a library that responds to today's work. Filter by domain "
             "for the trade you're running. Filter by severity to focus "
             "on high-consequence items. The library is built to be "
             "queried, not browsed."},
    {"form_key": "topic-library.filter", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Browsing the full library instead of filtering. Always "
             "exporting High-severity only and missing the everyday "
             "frequent topics. Forgetting the language filter when "
             "preparing for a Spanish-primary crew. Pulling the same "
             "5 topics repeatedly because the filter never changed."},
    {"form_key": "topic-library.filter", "kind": "example", "scopes": ["public"],
     "title": "A filter that surfaces today's risk",
     "body": "Domain = Excavation · Severity = High + Medium · "
             "Language = ES · Incident-pattern = trench collapse / "
             "spoil-pile encroachment. Three filter clicks. Result: "
             "the 4-6 talks that actually match the work the crew "
             "is doing this week."},
    {"form_key": "topic-library.pdf-pack", "kind": "why", "scopes": ["public"],
     "title": "Why the PDF pack is generated, not stored",
     "body": "Packs are generated on demand against the live library "
             "so the content is never stale. A pack you print today "
             "reflects every uplift, terminology fix, and ES correction "
             "merged through last night's deploy. Stored PDFs go stale "
             "the first time the library is updated."},
    {"form_key": "topic-library.pdf-pack", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Picking 30 topics to 'cover everything' — packs over 12 "
             "topics rarely get read. Mixing severities without context "
             "— the reader can't tell what to prioritize. Forgetting "
             "to set the language explicitly. Generating a pack for a "
             "Spanish crew but leaving the language toggle at EN."},
    {"form_key": "topic-library.pdf-pack", "kind": "next", "scopes": ["public"],
     "title": "What the pack is good for",
     "body": "OSHA audits (what topics were covered this quarter). "
             "New-hire orientation (here's the canon for your first "
             "30 days). Client requests (proof of coverage). "
             "Subcontractor onboarding. NOT a substitute for actual "
             "safety meetings — the pack is the receipt, the meeting "
             "is the work."},
])

# ── fire-extinguisher (NFPA 10 cadence) ───────────────────────────────
_TIPS.extend([
    {"form_key": "fire-extinguisher", "kind": "why", "scopes": ["public"],
     "title": "Why monthly visual + annual is the standard",
     "body": "NFPA 10 says monthly visual inspection, annual "
             "maintenance, 6-year teardown, 12-year hydrostatic. The "
             "tag on the bottle is the legal record that the "
             "inspections happened on schedule. Miss a month, the "
             "bottle is technically out of service until the next "
             "monthly is documented."},
    {"form_key": "fire-extinguisher", "kind": "who", "scopes": ["public"],
     "title": "Who reads extinguisher records",
     "body": "Safety on monthly walk-downs. PM on project handover. "
             "The fire marshal during inspection. Insurance auditors "
             "after any incident — the tag history is one of the first "
             "documents pulled. Sloppy tag history doesn't just "
             "embarrass — it raises premiums."},
    {"form_key": "fire-extinguisher", "kind": "next", "scopes": ["public"],
     "title": "What happens after an inspection log",
     "body": "Inspection date attaches to the unit. The next due "
             "date computes automatically — monthly visual, annual, "
             "6-year, 12-year. Safety dashboard shows the units due "
             "soon. The PDF history reflects every inspection in "
             "order, with inspector name and tag photo."},
    {"form_key": "fire-extinguisher", "kind": "escalate", "scopes": ["public"],
     "title": "When the bottle goes OUT-OF-SERVICE",
     "body": "Pressure gauge in the red. Pin missing or seal broken. "
             "Visible damage to the shell or hose. Past the annual "
             "service tag date. Tag the unit Out-of-Service, pull it "
             "from the wall/truck, requisition a replacement. Don't "
             "leave a non-functional bottle in service position."},
    {"form_key": "fire-extinguisher.add", "kind": "why", "scopes": ["public"],
     "title": "Why every field on the new-bottle dialog matters",
     "body": "Unit ID is what the tag will reference for the life of "
             "the bottle. Manufacture date sets the 12-year hydro "
             "schedule. Type (ABC, K, CO2) determines what hazards "
             "this bottle covers. Location is what the next inspector "
             "uses to find it. Skipping any of these breaks the "
             "lifetime audit trail."},
    {"form_key": "fire-extinguisher.add", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Unit ID free-typed with inconsistent format. Location "
             "as 'office' when the building has 6 offices. Type wrong "
             "(common: marking a Class K kitchen unit as ABC). "
             "Manufacture date left blank because the bottle is new "
             "and 'we'll add it later'. The clock starts at manufacture."},
    {"form_key": "fire-extinguisher.inspection", "kind": "why", "scopes": ["public"],
     "title": "Why monthly inspections must be photographed",
     "body": "A tag that says 'monthly visual · OK' was filled out, "
             "not inspected. A photo of the gauge in the green, the "
             "pin in place, the seal unbroken, the unit in position — "
             "that's the inspection. The tag is the receipt, the "
             "photo is the audit."},
    {"form_key": "fire-extinguisher.inspection", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Photo of the tag instead of the bottle. Backdating "
             "monthly inspections at the end of the quarter (this is "
             "falsification). Marking 'OK' on a bottle with a dirty "
             "gauge glass — clean it and re-check, don't skip. Logging "
             "an inspection without inspector name."},
    {"form_key": "fire-extinguisher.inspection", "kind": "example", "scopes": ["public"],
     "title": "An inspection log that does the job",
     "body": "Date · 3/14/25 · Inspector: J. Cruz · Type: Monthly "
             "Visual · Gauge: Green · Pin: in · Seal: intact · "
             "Hose: clean · Location: confirmed · Photos: 2 (gauge + "
             "wall mount). 30 seconds of work · 6 years of audit "
             "defensibility."},
    {"form_key": "fire-extinguisher.inspection", "kind": "escalate", "scopes": ["public"],
     "title": "When a monthly turns into a repair order",
     "body": "Gauge red or missing. Pin pulled or seal broken. "
             "Damage to shell, valve, or hose. Past annual service. "
             "Don't log this as a routine monthly — log it as a "
             "Failure and open a Safety Corrective Action to "
             "service/replace. The bottle is out-of-service starting "
             "now."},
])

# ── jha ───────────────────────────────────────────────────────────────
_TIPS.extend([
    {"form_key": "jha", "kind": "why", "scopes": ["public"],
     "title": "Why a JHA is the operational plan, not a poster",
     "body": "A JHA written before the work names the steps, the "
             "hazards, and the controls — in that order. Crews work "
             "from it. A JHA written after the work is a wall "
             "decoration. The one that gets posted is the one the "
             "crew was supposed to operate under — make sure they "
             "actually did."},
    {"form_key": "jha", "kind": "who", "scopes": ["public"],
     "title": "Who reads the JHA",
     "body": "Foreman on pre-task brief. Crew on the day. Safety "
             "during audits. The next investigator if something goes "
             "wrong — the JHA is one of the first documents pulled. "
             "A vague JHA in an incident packet reads as 'this crew "
             "didn't have a plan'."},
    {"form_key": "jha", "kind": "next", "scopes": ["public"],
     "title": "What happens with a submitted JHA",
     "body": "PDF generates, attaches to the project. The JHA "
             "Poster (large-format printable) goes up at the work "
             "area where the crew gathers. Anyone joining the work "
             "mid-day reads the poster before starting. Updates to "
             "the JHA mid-project mean a new poster — don't redline "
             "the printed copy."},
    {"form_key": "jha", "kind": "escalate", "scopes": ["public"],
     "title": "When the work doesn't match the JHA anymore",
     "body": "Conditions changed (weather, scope, sequence). New "
             "hazard surfaced (utility hit, adjacent crew, equipment "
             "swap). Stop the work, update the JHA, re-brief the "
             "crew, post the new version. A JHA that doesn't match "
             "today's work is more dangerous than no JHA at all — "
             "the crew is operating on stale information."},
    {"form_key": "jha.poster", "kind": "why", "scopes": ["public"],
     "title": "Why the poster format is large and visual",
     "body": "The poster lives at the work area, not in a binder. "
             "Crews read it on the wall, at a distance, in poor "
             "light, with dirty gloves. Large type, color-coded "
             "hazards, sequenced steps. Bilingual if the crew is "
             "bilingual. The poster is the operational reminder, "
             "not the legal record (that's the PDF)."},
    {"form_key": "jha.poster", "kind": "mistake", "scopes": ["public"],
     "title": "Common mistakes",
     "body": "Printing the standard JHA PDF and calling it the "
             "poster. Posting in a place the crew never walks past. "
             "Posting in EN only when the crew speaks ES. Letting "
             "the poster get rained on, faded, or torn — replace it. "
             "A faded poster reads as 'this safety doesn't matter'."},
    {"form_key": "jha.poster", "kind": "example", "scopes": ["public"],
     "title": "A poster that does the job",
     "body": "Work area: trench at station 12+50. Steps: 1) Spot "
             "and avoid utilities. 2) Set box. 3) Excavate within "
             "box footprint. 4) Spoil pile 4 ft minimum from edge. "
             "Hazards: collapse, falling debris, equipment swing. "
             "Controls: protective system, hard hats, spotter. "
             "Bilingual. Posted at the toolbox. Read at 6:30 AM."},
    {"form_key": "jha.poster", "kind": "escalate", "scopes": ["public"],
     "title": "When the poster needs to come down",
     "body": "Work area shifted (the trench moved). Crew rotated "
             "with significantly different competency mix. Major "
             "scope change. Don't leave yesterday's poster up for "
             "today's work. Take it down, file the PDF, post the "
             "current version. The wall reflects what's happening "
             "today, not what was planned last week."},
])


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
