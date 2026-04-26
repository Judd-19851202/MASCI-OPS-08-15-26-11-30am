"""OSHA-compliant daily inspection checklists for heavy construction equipment.

Items are organized by section. Operators mark each item PASS / FAIL / N/A.
References: OSHA 1926 Subpart O (Motor Vehicles, Mechanized Equipment, and Marine Operations),
1926.602 (Material handling equipment), and manufacturer pre-shift inspection guidance.
"""

# Common items shared across most heavy equipment
_COMMON_FLUIDS = [
    "Engine oil level",
    "Engine coolant level",
    "Hydraulic fluid level",
    "Fuel level",
    "Transmission / drivetrain fluid",
    "Visible fluid leaks (engine, hydraulic, fuel, coolant)",
]

_COMMON_WALKAROUND = [
    "Overall machine condition - no visible damage",
    "Steps, grab handles, ladders secure & clean",
    "Engine compartment - no debris / oil buildup",
    "Belts and hoses - no cracks, fraying, or leaks",
    "Battery - secure, terminals clean, no corrosion",
    "Air filter / pre-cleaner condition",
]

_COMMON_OPERATOR_STATION = [
    "Seat & seat belt - functional, not torn",
    "ROPS / FOPS structure - no cracks or damage",
    "Mirrors - clean, adjusted, no cracks",
    "Windows / windshield - clean, no cracks",
    "Cab door latches and locks",
    "All gauges & warning lights functional",
    "Horn operational",
    "Backup alarm operational",
    "Operator manual present in cab",
]

_COMMON_LIGHTS_ELECTRICAL = [
    "Headlights - both sides functional",
    "Work lights functional",
    "Tail lights / brake lights functional",
    "Turn signals / hazard flashers",
    "Strobe / beacon light (if equipped)",
    "Wiring - no exposed or damaged wires",
]

_COMMON_SAFETY = [
    "Fire extinguisher present, charged & inspected",
    "First aid kit present and stocked",
    "Wheel chocks present",
    "SDS / safety decals legible",
    "Slow-moving vehicle emblem (if road use)",
    "Three points of contact decals visible",
]

_COMMON_CONTROLS_BRAKES = [
    "Service brakes - firm pedal, holds machine",
    "Parking brake - holds machine on grade",
    "Steering - responsive, no excessive play",
    "All control levers / pedals - free movement, return to neutral",
    "Throttle / decelerator pedal",
    "Emergency / kill switch operational",
]


def _section(title, items):
    return {"title": title, "items": items}


CHECKLISTS = {
    "Dozer": [
        _section("Fluids & Leaks", _COMMON_FLUIDS),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks / undercarriage - tension, wear, no missing pads",
            "Track rollers, idlers, sprockets",
            "Final drives - no leaks",
            "Blade & C-frame - no cracks, pins secure",
            "Cutting edge & end bits - wear acceptable",
            "Ripper / shanks (if equipped) - secure, no cracks",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Excavator": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Swing drive / slew gear oil",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks / undercarriage - tension, wear",
            "Track rollers, idlers, sprockets",
            "Boom, stick, bucket - no cracks at pivot points",
            "Bucket teeth / cutting edge - wear & secure pins",
            "Hydraulic cylinders - rod condition, no leaks",
            "Hydraulic hoses - no chafing or bulges",
            "Counterweight - secure, no cracks",
            "Swing bearing - no abnormal noise / play",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Joystick controls - smooth, return to neutral",
            "Travel pedals / levers",
            "Pilot control lockout lever functional",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", [
            "Travel brakes - hold machine on grade",
            "Swing brake / lock",
            "Hydraulic response - no jerky movement",
            "Emergency / kill switch operational",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Loader": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Axle / differential oil",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, sidewall damage, tread wear",
            "Wheel lug nuts torqued, no missing",
            "Articulation joint / center pin - no excessive play",
            "Bucket / fork attachment - secure, pins & retainers",
            "Bucket cutting edge / teeth - wear acceptable",
            "Lift arms & linkage - no cracks",
            "Hydraulic cylinders & hoses",
            "Quick coupler (if equipped) - locked & pinned",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Bucket / loader joystick - return to neutral",
            "Ride control (if equipped)",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Motor Grader": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Tandem drive oil",
            "Circle drive lubrication",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, tread wear",
            "Wheel lug nuts torqued",
            "Tandem chains - tension & lubrication",
            "Moldboard / blade - cutting edge wear",
            "Circle, drawbar, ball joint - lubricated, no cracks",
            "Scarifier / ripper (if equipped) - shanks secure",
            "Articulation joint - no excessive play",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Blade lift, sideshift, tilt controls",
            "All-wheel drive engagement (if equipped)",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Skid Steer": [
        _section("Fluids & Leaks", _COMMON_FLUIDS),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires / tracks - condition & wear",
            "Wheel lug nuts (if wheeled) torqued",
            "Lift arms - no cracks, pivot pins secure",
            "Quick attach plate - latches functional",
            "Attachment securely mounted & pinned",
            "Hydraulic couplers / auxiliary lines - no leaks",
            "Chain case / drive chains (if accessible)",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Restraint bar / lap bar functional",
            "Operator presence switch / interlock functional",
            "Front door / cab interlock (if equipped)",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", [
            "Drive controls (joystick / hand-foot) return to neutral",
            "Park brake / interlock holds machine",
            "Loader / lift control return to neutral",
            "Auxiliary hydraulic control",
            "Emergency / kill switch operational",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Paver": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Auger & conveyor gearbox oil",
            "Screed heat system fluid (if applicable)",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks or tires - condition & wear",
            "Hopper, wings, flow gates - no damage, operate freely",
            "Conveyor chains / slats - tension and condition",
            "Augers - flighting wear, secure",
            "Screed plates - flatness, wear, heat elements",
            "Tow arms / tow points - no cracks",
            "Spray-down / release agent system functional",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Screed operator stations - controls functional",
            "Walkways & handrails secure",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL + [
            "Screed heat indicators / generator functional",
        ]),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Conveyor and auger controls",
            "Screed lift / float controls",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Burn / heat warning decals legible",
            "Emergency stop buttons - all stations functional",
        ]),
    ],
    "Other": [
        _section("Fluids & Leaks", _COMMON_FLUIDS),
        _section("Walk-Around", _COMMON_WALKAROUND),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Shuttle Buggy / Transfer Machine": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Conveyor / drag chain gearbox oil",
            "Auger gearbox oil",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks / undercarriage - tension & wear",
            "Receiving hopper - no damage, hinges work",
            "Drag conveyor / slat chain - tension, no broken links",
            "Discharge / swing conveyor - belt condition, tracking",
            "Augers / remix paddles - flighting wear, secure",
            "Hopper insert / storage bin - no damage",
            "Hydraulic hoses & cylinders",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Walkways, rails, ladders secure",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Conveyor / auger / swing controls",
            "Emergency stops at each station",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Burn / hot surface decals legible",
        ]),
    ],
    "Steel Drum Asphalt Roller": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Vibratory bearing / eccentric oil",
            "Drum water spray tank level",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Front & rear drums - no dents, scrapers seated",
            "Drum scrapers - clean, properly tensioned",
            "Water spray nozzles - clear, no clogs",
            "Water filters - clean",
            "Articulation joint - no excessive play",
            "Drum drive motors - no leaks",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Sliding seat / dual operator stations functional",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Vibration on/off control",
            "Vibration frequency / amplitude selector",
            "Water spray system on/off & timer",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Rubber Tired Asphalt Roller": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Tire ballast / water level (if equipped)",
            "Release agent tank level",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, condition, no cuts (front & rear)",
            "Wheel lug nuts torqued",
            "Rear tire skirts / scrapers",
            "Release agent spray nozzles - clear",
            "Pickup / lift cylinders for skirts",
            "Articulation joint - no excessive play",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Release agent spray on/off",
            "Tire ballast water valve",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Asphalt Milling Machine": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Cutter drum drive gearbox oil",
            "Conveyor gearbox oil",
            "Water spray tank level",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks / undercarriage - condition & wear",
            "Cutter drum - housing intact, no cracks",
            "Cutter teeth / picks - check wear, missing or broken teeth",
            "Tooth holders / blocks secure",
            "Side plates / moldboard - no excessive wear",
            "Primary & discharge conveyor belts/slats",
            "Conveyor belt scrapers / wipers",
            "Water spray bar nozzles - all clear",
            "Vacuum / dust suppression system",
            "Leg / track jacks - no leaks, hold position",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Operator platform / canopy secure",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Cutter drum on/off & depth control",
            "Conveyor swing / lift / lower controls",
            "Leg lift / depth controls",
            "Water spray system on/off",
            "Emergency stops - all stations",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Pinch-point / rotating drum decals legible",
        ]),
    ],
    "Dirt Roller": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Vibratory bearing / eccentric oil",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Drum - no cracks, padfoot pads (if equipped) intact",
            "Drum scrapers (smooth drum) - clean, tensioned",
            "Drum drive motor - no leaks",
            "Articulation joint - no excessive play",
            "Tires (rear, if smooth-drum) - inflation, wear",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Vibration on/off control",
            "Vibration amplitude selector",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Broom": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Broom drive motor / gearbox oil",
            "Water spray tank level (if equipped)",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, tread",
            "Wheel lug nuts torqued",
            "Broom bristles - wear, missing tufts",
            "Broom housing / shroud - no damage",
            "Broom angle / lift cylinders - no leaks",
            "Dust suppression spray nozzles clear",
            "Hopper / collection bin (if equipped) secure",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Broom on/off & rotation direction",
            "Broom angle, lift, down-pressure controls",
            "Water spray on/off",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Water Truck": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Water pump oil / lubrication",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, tread depth (all positions)",
            "Wheel lug nuts torqued, no missing studs",
            "Mud flaps secure",
            "Water tank - no leaks, baffles intact",
            "Tank fill hatch secured & vented",
            "Tank mounting / straps tight",
            "Spray bars - all nozzles clear, no leaks",
            "Spray valves & ball valves - operate freely",
            "Rear cannon / spray monitor (if equipped)",
            "PTO / pump drive shaft - guards in place",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Tank level gauge functional",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL + [
            "DOT marker lights & reflectors",
        ]),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Spray bar on/off & flow control",
            "Pump engage / disengage",
            "Air brake reservoir drained (if applicable)",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Triangle / road flare kit",
            "DOT inspection sticker current",
        ]),
    ],
    "Backhoe": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Front axle / differential oil",
            "Rear axle oil",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, tread (front & rear)",
            "Wheel lug nuts torqued",
            "Front loader bucket - cutting edge, teeth",
            "Loader arms, pins, retainers secure",
            "Backhoe boom, dipper, bucket - no cracks at pivots",
            "Backhoe bucket teeth / pins secure",
            "Stabilizer pads / outriggers - operate, no leaks",
            "Swing post / king pin - no excessive play",
            "Hydraulic cylinders & hoses - no leaks or chafing",
            "Quick coupler (if equipped) - locked & pinned",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Reversible / rotating seat functional",
            "Loader & backhoe joystick lockout",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Loader joystick - return to neutral",
            "Backhoe controls - return to neutral",
            "Stabilizer / outrigger controls",
            "4WD engagement (if equipped)",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Curb Machine": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Auger / extruder gearbox oil",
            "Vibrator oil (if equipped)",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks - tension, drive sprockets, idlers",
            "Hopper - clean, no buildup, no damage",
            "Auger / extrusion screw - wear, secure",
            "Mold / form - bolts tight, plates clean",
            "Slip-form mold trim - correct profile, no cracks",
            "Vibrator / consolidation system",
            "Stringline sensor mounts - secure & calibrated",
            "Trim / finishing tools secure",
            "Hydraulic cylinders, hoses & lift legs",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Operator platform / step secure",
            "Stringline sensor display functional",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Auger / extruder on-off",
            "Vibration / consolidation control",
            "Steering / stringline auto-steer mode",
            "Leg / mold lift controls",
            "Emergency stop functional",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Pinch / auger guards in place",
        ]),
    ],
    "Plate Compactor": [
        _section("Engine & Fluids", [
            "Engine oil level & condition",
            "Fuel level & fresh fuel",
            "Air filter - clean, properly seated",
            "Spark plug & wire (gas) / fuel injector (diesel)",
            "No fuel or oil leaks",
        ]),
        _section("Inspection", [
            "Base plate - no cracks, securely bolted",
            "Vibrator housing / shock mounts intact",
            "Drive belt - tension and condition",
            "Belt guard / cover in place",
            "Handle & vibration isolators secure",
            "Throttle / kill cable not frayed",
            "Lift bail / hook (if equipped) intact",
            "Water tank & drip system (if equipped) functional",
            "Optional pad / overlay attached securely",
        ]),
        _section("Controls", [
            "Throttle returns to idle",
            "Engine kill / stop switch operational",
            "Recoil starter or electric start works",
            "Forward / reverse selector (if reversible) returns to neutral",
        ]),
        _section("Safety Equipment", [
            "Hand / arm vibration PPE available",
            "Hearing protection available",
            "Operator manual / decals legible",
            "Fire extinguisher accessible at job site",
        ]),
    ],
    "Walk Behind Saw": [
        _section("Engine & Fluids", [
            "Engine oil level & condition",
            "Coolant level (if liquid-cooled)",
            "Fuel level & fresh fuel",
            "Air filter - clean, properly seated",
            "No fuel, oil, or coolant leaks",
            "Water tank level / supply hose (wet saws)",
        ]),
        _section("Blade & Cutting Head", [
            "Blade specified for material being cut",
            "Blade not cracked, warped, or excessively worn",
            "Blade flanges clean & seated; arbor nut torqued",
            "Blade rotation arrow matches direction of travel",
            "Blade guard - present, secure, adjustable",
            "Water spray nozzles - clear, both sides of blade",
            "Drive belt(s) - tension & condition",
            "Belt guard / shroud in place",
            "Depth indicator / pointer aligned",
        ]),
        _section("Frame & Wheels", [
            "Wheels / casters - tight, free spinning, locks work",
            "Front pointer / blade alignment guide secure",
            "Push handle & vibration isolators",
            "Lift point / hoist eye intact",
            "Frame welds - no cracks",
        ]),
        _section("Controls", [
            "Throttle returns to idle",
            "Engine kill / stop switch operational",
            "Blade clutch / engagement lever returns to OFF",
            "Blade lower / depth control - smooth, holds position",
            "Water valve operates; auto-shut-off (if equipped) works",
            "Emergency stop / dead-man (if equipped) functional",
        ]),
        _section("Safety Equipment", [
            "Eye / face protection available",
            "Hearing protection available",
            "Respirator / dust mask (silica) available",
            "Hand / arm protection available",
            "Operator manual / decals legible",
            "Fire extinguisher accessible at job site",
            "Silica water-suppression system functional",
        ]),
    ],
    "Haul Truck": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Differential / final drive oil (front & rear)",
            "Suspension strut nitrogen / oil charge",
            "Air system - tank drained, no leaks",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, sidewall damage, tread (all positions)",
            "Wheel lug nuts torqued, no missing studs",
            "Mud flaps secure",
            "Suspension struts - oil weeping acceptable, no major leaks",
            "Frame & cross-members - no cracks",
            "Articulation joint / hitch (if articulated) - no excessive play",
            "Dump body - no cracks, liner secure",
            "Tailgate / pivot pins, latches, retainers",
            "Body prop / safety pin in place when raised",
            "Hoist cylinders - rod condition, no leaks",
            "Driveline U-joints, slip yokes - secure",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Air pressure gauges - build to operating range",
            "Body up indicator / alarm functional",
            "Payload / haul cycle monitor (if equipped)",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL + [
            "DOT marker lights & reflectors",
        ]),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Service brake low-air warning",
            "Retarder / engine brake operational",
            "Hoist (dump) lever - return to neutral / float",
            "Body lower control - smooth",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Body prop / safety brace tagged & functional",
            "Triangle / road flare kit",
        ]),
    ],
    "Dirt Mixer": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Mixing rotor gearbox oil",
            "Cement / binder pump fluid (if equipped)",
            "Water spray tank level",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires or tracks - condition & wear",
            "Wheel lug nuts torqued (if wheeled)",
            "Mixing chamber / rotor housing - no cracks",
            "Mixing teeth / picks - check wear, missing teeth",
            "Tooth holders / blocks secure",
            "Rotor drive belts / chain & guards in place",
            "Hood / chamber doors latch securely",
            "Water spray bar - all nozzles clear, no leaks",
            "Binder spreader / vane (if equipped) - secure",
            "Articulation joint - no excessive play",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Rotor depth / position indicator functional",
            "Water flow / metering display",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Rotor on/off & rotation direction",
            "Rotor depth control - smooth, holds position",
            "Water spray on/off & flow control",
            "Hood lift / lower control",
            "Emergency stop functional",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Rotating-part / pinch-point decals legible",
        ]),
    ],
    "Road Widener": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Auger / conveyor gearbox oil",
            "Strike-off vibrator oil (if equipped)",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tracks or tires - condition & wear",
            "Wheel lug nuts torqued (if wheeled)",
            "Receiving hopper - clean, no damage",
            "Conveyor / belt - tension, no broken slats, no tears",
            "Auger flighting - wear, secure",
            "Strike-off plate / moldboard - profile correct, edge wear",
            "Adjustable width extensions / wing - operate freely",
            "Hopper gates / flow valves operate freely",
            "Hydraulic cylinders, hoses, lines",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Side-mounted operator platform / handrails secure",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Conveyor / auger on-off & speed",
            "Strike-off vibration on/off",
            "Width extension / wing control",
            "Material flow gate control",
            "Emergency stop functional",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY),
    ],
    "Telehandler / Forklift": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Boom extension / chain lubrication",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, tread (all positions)",
            "Wheel lug nuts torqued",
            "Boom sections - no cracks, wear pads in place",
            "Boom extension chains / cables - tension, no broken strands",
            "Carriage / quick coupler - locked & pinned",
            "Forks - no cracks, heel wear acceptable, retaining pins",
            "Fork positioner / side-shift cylinders, hoses",
            "Stabilizer / outrigger pads (if equipped) operate freely",
            "Frame leveling cylinder (if equipped)",
            "Load-moment / capacity indicator decals legible",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "Load-moment indicator (LMI) functional",
            "Tilt / level indicator visible",
            "ROPS / FOPS structure intact",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Boom raise / lower / extend / retract - smooth",
            "Fork tilt - return to neutral",
            "Stabilizer / frame-level controls",
            "Drive direction selector return to neutral",
            "Parking brake - holds machine on grade",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "Capacity / load chart visible in cab",
            "Seat belt / restraint mandatory decal legible",
        ]),
    ],
    "Tractor": [
        _section("Fluids & Leaks", _COMMON_FLUIDS + [
            "Front / rear differential oil",
            "PTO gearbox oil",
        ]),
        _section("Walk-Around", _COMMON_WALKAROUND + [
            "Tires - inflation, cuts, tread (front & rear)",
            "Wheel lug nuts torqued",
            "3-point hitch - lift arms, top link, pins, lynch pins",
            "Drawbar - secure, hitch pin & retainer",
            "PTO shaft - guard / shield in place, U-joints secure",
            "Implement attached securely (if applicable)",
            "Front loader / bucket (if equipped) - cutting edge, pins",
            "Rear hydraulic remotes - couplers clean, no leaks",
            "Fenders & guards in place",
        ]),
        _section("Operator Station", _COMMON_OPERATOR_STATION + [
            "ROPS / cab structure - no cracks",
            "PTO engaged / disengaged indicator visible",
        ]),
        _section("Lights & Electrical", _COMMON_LIGHTS_ELECTRICAL + [
            "Slow-moving vehicle (SMV) emblem clean & visible",
            "Flashing amber warning beacon (if road use)",
        ]),
        _section("Controls & Brakes", _COMMON_CONTROLS_BRAKES + [
            "Independent left/right brake pedals - latched together for road",
            "PTO clutch / engagement - return to neutral",
            "3-point hitch lift / lower / draft control",
            "Hydraulic remote levers - return to neutral",
            "Differential lock engagement / disengagement",
            "Range / shuttle shift - functional",
        ]),
        _section("Safety Equipment", _COMMON_SAFETY + [
            "PTO master shield in place",
            "Operator presence / seat-switch interlock functional",
        ]),
    ],
}

EQUIPMENT_TYPES = [
    "Dozer",
    "Excavator",
    "Loader",
    "Motor Grader",
    "Skid Steer",
    "Paver",
    "Backhoe",
    "Tractor",
    "Telehandler / Forklift",
    "Haul Truck",
    "Water Truck",
    "Shuttle Buggy / Transfer Machine",
    "Steel Drum Asphalt Roller",
    "Rubber Tired Asphalt Roller",
    "Asphalt Milling Machine",
    "Dirt Roller",
    "Dirt Mixer",
    "Road Widener",
    "Broom",
    "Curb Machine",
    "Plate Compactor",
    "Walk Behind Saw",
    "Other",
]
