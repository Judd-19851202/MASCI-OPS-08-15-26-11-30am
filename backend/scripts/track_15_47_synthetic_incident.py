"""
TRACK 15.47 · Synthetic public-interaction / workplace-violence
incident seed.

Creates ONE high-fidelity recreation of the triggering event for
certification. Includes every Track 15.47 field (G1-G10) so the PDF
renderer + notification fan-out + CAPA + state-timeline + linked-CAPA
blocks all get exercised end-to-end.

Mark: `_synthetic = True` so the record is identifiable. Safe to
delete after certification.

Run:
    cd /app/backend && python3 scripts/track_15_47_synthetic_incident.py
"""
import os
import sys
import uuid
import asyncio
import datetime as dt
from dotenv import load_dotenv

sys.path.insert(0, "/app/backend")
load_dotenv("/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    inc_id = str(uuid.uuid4())
    today = dt.date.today().isoformat()

    # Determine next doc_id sequence
    last = await db.incidents.find_one(
        {"doc_id": {"$regex": "^INC-2026-"}},
        sort=[("doc_id", -1)],
    )
    next_seq = 1
    if last and last.get("doc_id"):
        try:
            next_seq = int(str(last["doc_id"]).split("-")[-1]) + 1
        except Exception:
            next_seq = 99000
    doc_id = f"INC-2026-{next_seq:05d}"

    doc = {
        # === Identity ===
        "id": inc_id,
        "doc_id": doc_id,
        "_synthetic": True,
        "_synthetic_track": "15.47",
        "_synthetic_purpose": "Defensibility certification — public confrontation that escalated to physical contact.",

        # === Report metadata ===
        "project_name": "CC5744 - OXFORD RD Improvements (OXFORD)",
        "project_number": "24-12",
        "location": "6735 US 17; US 92 · Fern Park, Florida · 32730",
        "incident_date": today,
        "incident_time": "07:12",
        "reported_date": today,
        "reported_by": "Carlos Martinez (Foreman)",
        "supervisor_name": "JOE SPIKER",

        # === Classification ===
        "incident_type": "Public / Third Party",
        # G1 · multi-select classifications
        "classifications": [
            "Public Interaction",
            "Verbal Confrontation",
            "Threat",
            "Physical Contact",
            "Workplace Violence",
        ],
        "severity": "medical",
        "osha_recordable": "Yes",
        "work_stopped": "Yes",

        # === Person involved (MASCI side) ===
        "person_name": "Anthony Walker",
        "person_role": "Pipe Layer",
        "person_employer": "MASCI",
        "person_years_experience": "4",
        "body_part": "Shoulder",
        "injury_nature": "Bruise / Contusion",
        "treatment_provided": "First aid on-site · ice + transported to clinic for evaluation",
        "medical_facility": "AdventHealth Centra Care · Altamonte Springs",
        "sent_home": "Yes",

        # === Description ===
        "description": (
            "At approximately 07:12 a male resident (~55, white t-shirt, "
            "blue ball cap) walked from 6741 US 17 toward the work zone "
            "yelling about jackhammer noise from the previous day. Foreman "
            "Carlos approached calmly to acknowledge. Resident escalated, "
            "stepped past barricade, pointed finger in foreman's face, "
            "made threat 'I'll knock you out.' When pipe-layer Anthony "
            "Walker stepped in to position himself between resident and "
            "foreman, resident shoved Walker with both hands, striking "
            "Walker's left shoulder. Walker did not retaliate. Foreman "
            "called 911. Resident walked back to residence. Seminole "
            "County Sheriff's Office arrived ~07:24."
        ),
        "immediate_cause": "Resident frustration with prior-day jackhammer noise; no prior interaction with this crew.",
        "contributing_factors": "Pre-shift huddle did not cover de-escalation. Superintendent phone not posted in cab.",
        "root_causes": {"communication": True, "training": True},
        "root_cause_notes": "Crew had not run the new Track 15.46A 'Dealing With Angry Members of the Public' topic in pre-shift.",

        # === G4 · Extended witnesses ===
        "witnesses": [
            {
                "name": "Carlos Martinez",
                "role": "Foreman (MASCI)",
                "witness_type": "employee",
                "employer": "MASCI",
                "company": "MASCI",
                "phone": "(407) 555-0142",
                "email": "carlos.martinez@mascigc.com",
                "statement": (
                    "Resident approached aggressively from residence. I "
                    "stepped forward to acknowledge. He stepped past the "
                    "barricade and pointed in my face. When Anthony stepped "
                    "between us, the resident shoved Anthony in the chest "
                    "with both hands. I called 911 immediately."
                ),
                "signature": "",  # placeholder — would be signed on-site
            },
            {
                "name": "Maria Reyes",
                "role": "Operator (MASCI)",
                "witness_type": "employee",
                "employer": "MASCI",
                "company": "MASCI",
                "phone": "(407) 555-0181",
                "email": "maria.reyes@mascigc.com",
                "statement": (
                    "I was operating the mini-ex 30 ft away. I saw the "
                    "resident shove Anthony with both hands. Anthony "
                    "stumbled but did not fall, did not strike back."
                ),
                "signature": "",
            },
            {
                "name": "Janet Whitfield",
                "role": "Member of public (neighbor across street)",
                "witness_type": "public",
                "employer": "—",
                "company": "—",
                "phone": "(407) 555-0218",
                "email": "",
                "statement": (
                    "I was getting my mail. The man from 6741 walked up "
                    "yelling. He poked his finger at the foreman, then "
                    "shoved a worker. The worker did not hit him back."
                ),
                "signature": "",
            },
            {
                "name": "Dep. R. Holloway",
                "role": "Responding deputy",
                "witness_type": "police",
                "employer": "Seminole County Sheriff's Office",
                "company": "Seminole County Sheriff's Office",
                "phone": "(407) 665-6650",
                "email": "",
                "statement": (
                    "Responded 07:24. Suspect identified. Trespass warning "
                    "issued. Case report assigned for misdemeanor battery "
                    "follow-up."
                ),
                "signature": "",
            },
        ],

        # === Immediate actions ===
        "immediate_actions_taken": (
            "Foreman called 911. Crew stopped work. Anthony moved to crew "
            "truck for ice + welfare check. Superintendent Spiker notified "
            "by phone at 07:16. Crew leadership debriefed with deputy."
        ),
        "corrective_actions": (
            "1. All crews re-run 'Dealing With Angry Members of the "
            "Public' pre-shift topic this week. 2. Post superintendent "
            "phone in every cab. 3. Add second barricade at residence-"
            "adjacent side of work zone. 4. Confirm trespass warning is "
            "documented with SCSO."
        ),
        "responsible_party": "Superintendent JOE SPIKER · Safety Manager",
        "target_completion_date": (dt.date.today() + dt.timedelta(days=7)).isoformat(),

        # === G2 · Threat & contact ===
        "threat_made": True,
        "threat_description": "Verbal — 'I'll knock you out.' Made directly to foreman's face, finger pointed.",
        "physical_contact": True,
        "physical_assault": True,
        "weapon_displayed": False,
        "weapon_used": False,
        "weapon_description": "",
        "media_filmed": True,
        "social_media_posted": False,

        # === G3 · Police ===
        "police_called": True,
        "police_arrived": True,
        "police_agency": "Seminole County Sheriff's Office",
        "police_officer_name": "Deputy R. Holloway",
        "police_badge": "SCSO-4471",
        "police_case_number": "SCSO-26-104882",
        "police_report_number": "26-104882",
        "police_report_obtained": False,  # to be chased by safety
        "arrest_made": False,
        "citation_issued": True,
        # G5 · Damage
        "damage_description": "No vehicle / equipment damage. No property damage.",
        "damage_estimated_value": "0",
        "vehicle_make_model": "",
        "vehicle_vin": "",
        "vehicle_plate": "",
        "asset_number": "",
        "insurance_claim_number": "",
        "insurance_carrier": "",

        # === G7 · Attachments ===
        "attachments": [
            {
                "kind": "photo",
                "label": "Approach area + residence",
                "data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
                "uploaded_at": now_iso,
            },
            {
                "kind": "witness_statement",
                "label": "Janet Whitfield (public) — signed PDF",
                "data_url": "data:application/pdf;base64,JVBERi0xLjQK",
                "uploaded_at": now_iso,
            },
            {
                "kind": "police_report",
                "label": "SCSO Case 26-104882 — preliminary",
                "data_url": "data:application/pdf;base64,JVBERi0xLjQK",
                "uploaded_at": now_iso,
            },
            {
                "kind": "medical",
                "label": "AdventHealth Centra Care — Walker discharge note",
                "data_url": "data:application/pdf;base64,JVBERi0xLjQK",
                "uploaded_at": now_iso,
            },
            {
                "kind": "video",
                "label": "Crew dashcam (mini-ex front cam)",
                "data_url": "data:video/mp4;base64,AAAA",
                "uploaded_at": now_iso,
            },
        ],

        # === Notifications (operator's intent at submission) ===
        "notified_safety_manager": "Yes",
        "notified_pm": "Yes",
        "notified_gc": "No",
        "notified_owner": "No",
        "notified_osha": "Pending",
        "notified_other": "Operations · Executive · HR",

        # === Signatures (placeholders) ===
        "reporter_signature": "",
        "supervisor_signature": "",
        "distribution_list": [],

        # === Photos (legacy field — kept empty; attachments[] carries
        # the modern, typed payload) ===
        "photos": [],

        # === System ===
        "submit_language": "en",
        "status": "open",
        "resolution_status": "open",
        "created_at": now_iso,
    }

    await db.incidents.insert_one(doc)
    print(f"Inserted synthetic incident · id={inc_id} doc_id={doc_id}")

    # Seed a couple of state-event rows to exercise the timeline render.
    base = dt.datetime.now(dt.timezone.utc)
    state_events = [
        {
            "id": str(uuid.uuid4()),
            "incident_id": inc_id,
            "from_state": "",
            "to_state": "open",
            "actor_name": "Carlos Martinez",
            "actor_email": "carlos.martinez@mascigc.com",
            "reason": "Submitted via field form",
            "created_at": base.isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "incident_id": inc_id,
            "from_state": "open",
            "to_state": "investigating",
            "actor_name": "Safety Manager",
            "actor_email": "safety@mascigc.com",
            "reason": "Reviewed witness statements + SCSO case number",
            "created_at": (base + dt.timedelta(hours=1)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "incident_id": inc_id,
            "from_state": "investigating",
            "to_state": "review",
            "actor_name": "Safety Manager",
            "actor_email": "safety@mascigc.com",
            "reason": "CAPAs issued · awaiting verification",
            "created_at": (base + dt.timedelta(hours=2)).isoformat(),
        },
    ]
    await db.incident_state_events.insert_many(state_events)
    print(f"Inserted {len(state_events)} state events.")

    # Seed two linked CAPAs.
    capas = [
        {
            "id": str(uuid.uuid4()),
            "title": "All crews re-run 'Dealing With Angry Members of the Public' pre-shift this week",
            "description": "Foreman certifies topic delivered to crew before any work on 24-12.",
            "source_kind": "incident",
            "source_id": inc_id,
            "project_number": "24-12",
            "assigned_to_name": "JOE SPIKER",
            "assigned_to_email": "joe.spiker@mascigc.com",
            "priority": "Critical",
            "due_date": (dt.date.today() + dt.timedelta(days=3)).isoformat(),
            "status": "Open",
            "notes": "",
            "completion_notes": "",
            "completed_at": None,
            "closed_by_name": "",
            "related_entities": [],
            "created_at": base.isoformat(),
            "updated_at": base.isoformat(),
            "_synthetic": True,
            "_synthetic_track": "15.47",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Workplace-violence review — confirm witnesses + police data + media exposure",
            "description": (
                f"Auto-issued from incident {doc_id}. Confirm: police case # · "
                f"witness contact info · media/social media flags · employee "
                f"welfare check · insurance + legal notified."
            ),
            "source_kind": "incident",
            "source_id": inc_id,
            "project_number": "24-12",
            "assigned_to_name": "Safety Manager",
            "assigned_to_email": "safety@mascigc.com",
            "priority": "Critical",
            "due_date": (dt.date.today() + dt.timedelta(days=1)).isoformat(),
            "status": "In Progress",
            "notes": "",
            "completion_notes": "",
            "completed_at": None,
            "closed_by_name": "",
            "related_entities": [],
            "created_at": (base + dt.timedelta(minutes=2)).isoformat(),
            "updated_at": (base + dt.timedelta(minutes=2)).isoformat(),
            "_synthetic": True,
            "_synthetic_track": "15.47",
        },
    ]
    await db.corrective_actions.insert_many(capas)
    print(f"Inserted {len(capas)} linked CAPAs.")
    print()
    print(f"To delete: db.incidents.delete_one({{'id': '{inc_id}'}}); "
          f"db.incident_state_events.delete_many({{'incident_id': '{inc_id}'}}); "
          f"db.corrective_actions.delete_many({{'source_id': '{inc_id}'}})")


if __name__ == "__main__":
    asyncio.run(main())
