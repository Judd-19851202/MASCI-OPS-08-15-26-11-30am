# Track 19.15 · 03 · Incident Type Intelligence Map

Every incident type gets its own branching question set. Field operators are asked ONLY the questions that matter for their type. Irrelevant questions never appear.

## Utility Strike
- Active locate ticket? (Yes/No/Unsure) — PresenceGate
- Ticket number
- Ticket expiration date
- Utility type (gas / electric / water / telecom / sewer / other)
- Utility owner
- Marked at the surface? (Yes/No)
- Marks accurate? (Yes/No/Unknown)
- Shown on plans? (Yes/No)
- Potholing / test holes performed? (Yes/No)
- Vacuum excavation used? (Yes/No)
- Hand digging used? (Yes/No)
- Service interrupted? (Yes/No — customers affected count if Yes)
- Utility company notified? (Yes/No — timestamp + who called)
- 811 / Sunshine notified? (Yes/No — timestamp)
- Damage description (structured)
- Immediate actions taken
- Photos (locate marks · exposure · damage · repair)

## Vehicle Accident
- Vehicles involved (count + list — MASCI + third party)
- Drivers (names, license status)
- Passengers (count + roster)
- Police called? Yes/No — report number if available
- Injuries? Yes/No — routes to Employee Injury / Public Injury sub-flow
- Damage? Yes/No — severity chip
- Tow required? Yes/No — tow company
- Insurance info collected? Yes/No
- Photos (scene · damage · plates · IDs · road conditions)

## Equipment Accident
- Equipment involved (unit + type)
- Operator name
- Spotter present? (Yes/No — who)
- Ground conditions (dry / wet / muddy / uneven / slope)
- Equipment damage description
- Third-party damage? Yes/No
- Hydraulic / fluid release? Yes/No — spill sub-flow trigger
- Rollover? Yes/No
- Attachment involved? Yes/No — which
- Out-of-Service needed? Yes/No — trigger DVIR OOS record
- Photos

## Employee Injury
- Injured person (roster picker)
- Body part(s)
- Nature of injury (cut / strain / fall / crush / burn / other)
- Treatment (none / first aid / clinic / hospital / ambulance)
- Sent home? Yes/No — timestamp
- Ambulance? Yes/No
- Clinic / hospital destination
- Witnesses (names, contact)
- Immediate actions
- Photos (only if operator-appropriate; PPE / equipment / scene, not injuries)

## Public Injury (Third Party)
- Injured person name + contact
- Age / minor?
- Injury description
- Treatment
- Ambulance? Yes/No
- Statement collected? Yes/No
- Witnesses
- Police called? Yes/No
- Photos of scene

## Property Damage
- Owner (MASCI / third party)
- Property description
- Estimated value if known
- Repair path (in-house / vendor)
- Photos

## Near Miss
- What almost happened?
- Potential severity (near_miss → catastrophic slider)
- Contributing factors (multi-select)
- Immediate correction taken
- Prevention action recommendation

## Environmental Spill
- Substance
- Estimated quantity + units
- Containment status (contained / partial / uncontained)
- Waterway / storm-drain impact? Yes/No
- Cleanup action taken
- Environmental agency notified? Yes/No — which agency
- Photos

## Fire
- What ignited
- Extinguished by (worker / extinguisher / fire department)
- Fire department called? Yes/No — station
- Injuries / evacuations
- Photos

## Workplace Violence / Threat
- Threat only? Physical contact? Weapon? (three PresenceGates)
- Police called? Yes/No — report number
- Employees separated? Yes/No
- HR notified? Yes/No — timestamp
- Witness statements collected? Yes/No — how many
- Trespass? Yes/No
- Media / social media exposure? Yes/No

## Theft / Vandalism / Security
- What was taken / damaged
- Estimated value
- Police report filed? Yes/No — report number
- Security footage? Yes/No — retention
- Photos

## Safety Concern / Hazard (report without incident)
- Hazard description
- Location
- Recommended correction
- Photo

## Material Failure
- Material / equipment
- Failure mode
- Vendor / supplier
- Photos + failed part retention

## Other
- Free-form description with a mandatory "please add to the type list if this recurs" flag for admin.

**Every question has EN + ES translation locked in the future track's i18n update.**
