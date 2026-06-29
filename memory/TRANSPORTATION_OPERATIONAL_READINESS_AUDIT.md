TRANSPORTATION OPERATIONAL READINESS AUDIT (Track 19.02)
=========================================================

DATE      : 2026-06-29
ENV       : preview Atlas (`masci_safety_preview`)
DOCTRINE  : Powerful · Simple · Beautiful · Trusted · Proven · Operational

EXECUTIVE
─────────
Transportation Operations runs on a deep, healthy backend (44+ collections,
44+ endpoints, real dispatch + orientation engines). The product is NOT
hollow — but a single operational gap dwarfs everything else: the Trucks
view shows 12 rows when MASCI's actual fleet is 484-705 assets. Fixing
that one wiring is the P0 of P0s.

The Track 18.x + 19.00 + 19.01A workstreams are intact: 11-module
Academy is active, 12 legacy modules cleanly retired, Visible = Usable
dispatch acceptance holds, HR → Transportation link works.

VERDICT: GO WITH WATCH. Production-safe today; fleet-wiring is the
next operator-blocking item.

OPERATIONAL INVENTORY (preview DB, live)
────────────────────────────────────────
Driver & people:
  · transport_persons          172   (1 masci_employee · 171 leased_driver)
  · transport_invites           45
  · transport_eligibility_state 409
  · transport_dispatch_overrides 82

Carriers:
  · carriers                   225   (active 177 · pending_review 47 · inactive 1)
  · carrier_documents            8

Fleet — Transportation view (THIN):
  · transport_trucks            12   (all pending_review)
  · transport_truck_inspections 14

Fleet — Underlying MASCI ecosystem (THICK):
  · equipment_master           705
  · equipment_units            484
  · equipment_inspections      870
  · fleet_audit                979
  · fleet_defects              170
  · fleet_status               385
  · field_leadership_equipment_catalog  41
  · field_leadership_equipment_makes    20

Dispatch & operations:
  · dispatch_assignments       482
  · dispatch_state_events    1,377
  · dispatch_broadcasts         25
  · dispatch_continuity_events  31
  · dispatch_users              12

Automation / intelligence:
  · transport_action_items     253
  · transport_automation_events 253
  · transport_automation_runs  160
  · transport_command_digest_runs 81
  · transport_intelligence_audit 152
  · transport_notifications    180

Orientation / Academy (Track 19.01A · clean):
  · transport_orientation_modules        23 (11 Academy + 12 retired)
  · transport_orientation_assignments    45  (all historic E2E)
  · transport_orientation_certificates   45  (matched)
  · transport_orientation_questions      90

Motive integration (real):
  · motive_events              468
  · motive_geofences            67

Packets, rates, asset spine:
  · transport_packet_requirements 16
  · transport_packet_submissions   9
  · transport_rate_schedules       20
  · asset_mappings              191
  · asset_holds                 116
  · asset_transfers             138

KEY ENDPOINT INVENTORY
──────────────────────
  · transportation.py                       18 endpoints
  · transportation_orientation.py           26 endpoints
  · transportation_dispatch_command_center  *
  · transportation_search                   *
  · transportation_relationships            *

Six pillars verdict per surface
───────────────────────────────
| Surface                       | Powerful | Simple | Beautiful | Trusted | Proven | Operational |
|-------------------------------|----------|--------|-----------|---------|--------|-------------|
| Mission Control               | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Dispatch Board                | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Drivers (Track 19.00)         | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Carriers (Track 19.00)        | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Fleet / Trucks                | ✗ (12)   | ✓      | ✓         | ✓       | ✗      | **P0**      |
| Compliance                    | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Orientation                   | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Transportation Academy (19.01)| ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Automation / Morning Queue    | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Search                        | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Right Rail                    | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |
| Cleanup                       | ✓        | ✓      | ✓         | ✓       | ✓      | ✓           |

OVERALL : 11 of 12 surfaces are operational today. Fleet is the single P0.

PRIORITIZED FOLLOW-ON BACKLOG
─────────────────────────────
P0 — Fleet single-source-of-truth (`equipment_units` → Transportation
     Trucks view). See `TRANSPORTATION_FLEET_ARCHITECTURE_AUDIT.md`
     for the proposed implementation.

P1 — Run the Track 19.00 HR-CDL backfill script (`--commit`) so
     `transport_persons` (kind=masci_employee) climbs from 1 to the
     full CDL roster.

P1 — Carrier pending_review purge — 47 carriers in pending_review.
     Add a dispatcher checklist UI (link drivers, attach insurance,
     promote to active or close).

P2 — Performance review of the Orientation dashboard. Pre-Academy
     timings unmeasured; post-Academy bootstrap added ~30ms.
P2 — Search · cross-collection ranking across drivers + carriers +
     trucks + academy modules + certificates.
P2 — Mobile QA for the new Academy detail prev/next nav cards.
