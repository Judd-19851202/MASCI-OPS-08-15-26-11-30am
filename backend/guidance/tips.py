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
