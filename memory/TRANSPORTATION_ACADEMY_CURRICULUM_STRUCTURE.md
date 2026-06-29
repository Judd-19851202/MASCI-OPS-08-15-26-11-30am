TRANSPORTATION ACADEMY · CURRICULUM STRUCTURE
==============================================

VERSION  : v1 (Track 19.01A · 2026-06-29)
TRACK    : `curriculum_track="transportation_academy_v1"`
TOTAL    : 11 modules
LANGUAGE : English (Primary). Reserved slots for `es`, `es_CU`, `fr`.

────────────────────────────────────────────────────────────────────────────
TOP-LEVEL FLOW
────────────────────────────────────────────────────────────────────────────
A MASCI Transportation driver progresses through the Academy in order
1 → 11. Modules 1 and 2 are watchable today; Modules 3-11 are visible
in the Academy view with full metadata and a professional "Module in
production" state. The bootstrap is idempotent — adding new videos
later is a metadata patch (toggle `status: in_development → published`,
set `placeholders.en.video_url`), never a schema change.

────────────────────────────────────────────────────────────────────────────
THE 11 MODULES
────────────────────────────────────────────────────────────────────────────

1.  WELCOME TO MASCI TRANSPORTATION OPERATIONS
    key: welcome_to_masci · category: intro · runtime: 12 min · published
    Description: An introduction to MASCI heavy-civil Transportation
    Operations. Sets the tone for the Transportation Academy and
    explains how drivers fit into the broader operating system.
    Topics: MASCI Transportation overview · Operating principles ·
            Driver support resources.

2.  DRIVER EXPECTATIONS & PROFESSIONAL STANDARDS
    key: driver_expectations · category: expectations · runtime: 14 min · published
    Description: Sets professional expectations for MASCI drivers in
    the field, including conduct, customer interaction, and
    accountability.
    Topics: Professional conduct · Customer interaction · Personal
            accountability · MASCI driver image.

3.  TRANSPORTATION SAFETY FUNDAMENTALS
    key: safety_culture · category: safety · runtime: 20 min · in_development
    Description: Core transportation safety expectations covering PPE,
    vehicle inspections, hours-of-service, and driver fatigue management.
    Topics: PPE · Daily Vehicle Inspections · Pre-Trip Inspections ·
            Post-Trip Inspections · Hours of Service · Driver Fatigue ·
            Safe Operating Expectations.

4.  DRIVER QUALIFICATION & REGULATORY COMPLIANCE
    key: driver_qualification_compliance · category: compliance · runtime: 25 min · in_development
    Description: DOT / FMCSA driver qualification expectations,
    clearinghouse requirements, medical card maintenance, and
    accident / incident reporting standards.
    Topics: Driver Qualification Files · DOT Compliance · FMCSA
            Regulations · FMCSA Clearinghouse · Medical Cards · CDL
            Requirements · Accident Reporting · Incident Reporting.

5.  SAFE DRIVING OPERATIONS
    key: backing_procedures · category: operations · runtime: 18 min · in_development
    Description: Defensive driving, blind-spot management, safe
    following distances, and spotters for backing maneuvers.
    Topics: Defensive Driving · Load Securement · Spotters · Backing
            Procedures · Blind Spots · Safe Following Distance.

6.  JOBSITE TRAFFIC CONTROL & SITE OPERATIONS
    key: traffic_control · category: operations · runtime: 15 min · in_development
    Topics: Entering Job Sites · Exiting Job Sites · Internal Traffic
            Flow · Flagger Awareness · Public Traffic · Site Hazards ·
            Communication.

7.  EQUIPMENT LOADING, HEAVY HAUL & TRANSPORT OPERATIONS
    key: loading_procedures · category: operations · runtime: 20 min · in_development
    Topics: Equipment Loading · Equipment Unloading · Lowboy
            Operations · Heavy Haul · Tie Downs · Securement.

8.  DUMP TRUCK & END DUMP OPERATIONS
    key: dumping_procedures · category: operations · runtime: 18 min · in_development
    Topics: Dump Truck Operations · End Dump Operations · Safe
            Dumping · Tailgate Operations · Rollovers · Soft Ground ·
            Overhead Hazards.

9.  TRANSPORTATION COMMUNICATION & TECHNOLOGY
    key: communications · category: operations · runtime: 15 min · in_development
    Topics: Dispatch Communications · Motive · Electronic Logging
            Devices · Transportation Technology · Documentation ·
            Customer Service · Professionalism.

10. EMERGENCY RESPONSE & ENVIRONMENTAL RESPONSIBILITIES
    key: emergency_procedures · category: safety · runtime: 15 min · in_development
    Topics: Emergencies · Breakdowns · Accidents · Spill Response ·
            Environmental Protection · Emergency Notifications ·
            Incident Escalation.

11. TRANSPORTATION OPERATIONS FINAL REVIEW & CERTIFICATION
    key: final_review_certification · category: certification · runtime: 10 min · in_development
    Topics: Final Review · Operational Expectations · Knowledge
            Review · Final Certification.

────────────────────────────────────────────────────────────────────────────
FUTURE EVOLUTION
────────────────────────────────────────────────────────────────────────────
Adding a new module: insert into the `ACADEMY_CURRICULUM` array in
`transportation_orientation.py` with the next `curriculum_order` value
and full metadata. The idempotent bootstrap will pick it up on the
next boot.

Publishing an in-development module: patch the row's `status` to
`"published"`, set `placeholders.en.video_url`, and the new endpoint
returns it as Published on the next request. No frontend deploy
required.

Quiz engine: every module already carries `quiz_enabled`,
`quiz_required`, `question_count`, `passing_score`, and `quiz_status`.
A future Track 19.02 quiz engine attaches to these reserved fields
without an architectural change.
