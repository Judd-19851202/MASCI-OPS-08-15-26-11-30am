"""
dispatch_assignment_seeds.py · iter408 · Phase 14.1 + 14.2.

Canonical seeded operational vocabulary for the Dispatch Assignment
Issuance drawer. Lives in a tiny standalone module so it can be reused
by the lookups endpoint, tests, and any future estimating / cycle
intelligence work — without coupling to server.py.

Doctrine
--------
- Seeded values are the operational floor. Dispatch never starts with
  an empty dropdown.
- Historical values from `dispatch_assignments` are merged in at
  request time so the more the platform is used, the richer the
  vocabulary becomes.
- "Add temporary" handles everything that isn't seeded or historical
  yet — the seed list is intentionally NOT a closed enum.
- Operator language only. No engineering vocabulary, no ERP wording.
"""
from __future__ import annotations

from typing import List

# ── Haul types · iter408 + iter410 Phase 14.2 / 15.1 ───────────────
# Drives conditional fields in the Create Assignment drawer.
HAUL_TYPES: List[str] = [
    "Material",
    "Equipment Move",
    "Tanker / Liquid Asphalt",
    "Spoils / Dump",
    "Support / Misc",
]

# ── Source / load points ───────────────────────────────────────────
SEEDED_SOURCES: List[str] = [
    "MASCI Hot Plant 1",
    "415 Yard",
    "Port",
    "Job Site",
    "Shop",
]

# ── Destinations ───────────────────────────────────────────────────
SEEDED_DESTINATIONS: List[str] = [
    "MASCI Hot Plant 1",
    "415 Yard",
    "Port",
    "Job Site",
    "Shop",
    "Dump",
]

# ── Pickup / drop-off (equipment-move locations) ───────────────────
SEEDED_PICKUP_LOCATIONS: List[str] = [
    "MASCI Hot Plant 1",
    "415 Yard",
    "Port",
    "Job Site",
    "Shop",
    "Other Yard",
    "Vendor",
    "Rental Yard",
]

SEEDED_DROPOFF_LOCATIONS: List[str] = SEEDED_PICKUP_LOCATIONS + ["Dump"]

# ── Material catalog · grouped for the drawer dropdown ─────────────
# Categories are display-only; the wire field is a single string label.
MATERIAL_CATALOG: List[dict] = [
    {
        "category": "Asphalt / Plant",
        "items": [
            "Hot Mix Asphalt",
            "Asphalt Base",
            "Asphalt Structural Course",
            "Asphalt Surface Course",
            "SP-9.5",
            "SP-12.5",
            "FC-9.5",
            "FC-12.5",
            "Type S Asphalt",
            "RAP",
            "Millings",
            "Asphalt Grindings",
            "Asphalt Tack",
            "Asphalt Sand",
            "Plant Waste",
        ],
    },
    {
        "category": "Aggregate / Base",
        "items": [
            "Limerock",
            "Crushed Concrete",
            "Recycled Concrete Aggregate",
            "#57 Stone",
            "#89 Stone",
            '3/4" Rock',
            '1/2" Rock',
            "Ballast Rock",
            "Rip Rap",
            "FDOT Base",
            "Shell Base",
            "Stabilized Base",
            "Bedding Stone",
            "Drainage Stone",
        ],
    },
    {
        "category": "Earthwork / Soils",
        "items": [
            "Common Fill",
            "Structural Fill",
            "Select Fill",
            "Clean Fill",
            "Borrow Material",
            "Topsoil",
            "Unsuitable Material",
            "Muck",
            "Clay",
            "Sand",
            "Washed Sand",
            "Fill Sand",
            "Screened Sand",
            "Spoils",
        ],
    },
    {
        "category": "Concrete / Demo",
        "items": [
            "Broken Concrete",
            "Demo Debris",
            "Concrete Washout",
            "Concrete Rubble",
            "Curb Debris",
            "Sidewalk Debris",
        ],
    },
    {
        "category": "Utility / Roadway",
        "items": [
            "Pipe",
            "RCP Pipe",
            "HDPE Pipe",
            "Structures",
            "Inlets",
            "Manholes",
            "Utility Bedding",
            "Utility Backfill",
        ],
    },
    {
        "category": "Job Support / Misc",
        "items": [
            "Equipment Move",
            "Barricades",
            "MOT Devices",
            "Signage",
            "Pallets",
            "Forms",
            "Scrap",
            "Trash",
            "Other Material",
        ],
    },
]

# Flat list view — preserves category order, lets the lookups
# endpoint return a single ordered array consumers can group by hint.
def flat_material_options() -> List[dict]:
    out: List[dict] = []
    for group in MATERIAL_CATALOG:
        for item in group["items"]:
            out.append({"label": item, "category": group["category"]})
    return out


# ── Equipment categories that ride on lowboys / are typical moves ──
# Used as a non-truck / non-trailer filter against equipment_master.
EQUIPMENT_MOVE_CATEGORIES: List[str] = [
    "Excavators",
    "Dozers",
    "Loaders",
    "Rollers / Compactors",
    "Pavers",
    "Skid Steers",
    "Backhoes",
    "Graders",
    "Milling Machines",
    "Light Plants",
    "Generators",
    "Attachments",
    "Misc Equipment",
]

# Fallback labels for "Add temporary equipment" UX.
EQUIPMENT_MOVE_EXAMPLE_LABELS: List[str] = [
    "Excavator",
    "Dozer",
    "Loader",
    "Roller",
    "Paver",
    "Skid Steer",
    "Backhoe",
    "Grader",
    "Milling Machine",
    "Light Plant",
    "Generator",
    "Attachment",
    "Other Equipment",
]

__all__ = [
    "HAUL_TYPES",
    "SEEDED_SOURCES",
    "SEEDED_DESTINATIONS",
    "SEEDED_PICKUP_LOCATIONS",
    "SEEDED_DROPOFF_LOCATIONS",
    "MATERIAL_CATALOG",
    "flat_material_options",
    "EQUIPMENT_MOVE_CATEGORIES",
    "EQUIPMENT_MOVE_EXAMPLE_LABELS",
    # iter410 · Phase 15.1 · Tanker continuity
    "SEEDED_TANKER_SOURCES",
    "SEEDED_TANKER_DESTINATIONS",
    "LIQUID_PRODUCT_CATALOG",
    "flat_liquid_product_options",
]


# ════════════════════════════════════════════════════════════════════
# iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity
# ════════════════════════════════════════════════════════════════════
# Seeded terminal / source list for tanker operations. Mirrors the
# operational floor doctrine: real tankers ALWAYS have a starting list
# to pick from on the very first day a tenant uses the platform.
SEEDED_TANKER_SOURCES: List[str] = [
    "MASCI Hot Plant 1",
    "Terminal",
    "Asphalt Terminal",
    "Port",
    "Storage Yard",
    "Vendor Plant",
    "Fuel Depot",
    "Job Site",
    "Shop",
]

# Seeded destinations include the operational plant + tank receivers
# that tanker operations typically deliver to.
SEEDED_TANKER_DESTINATIONS: List[str] = [
    "MASCI Hot Plant 1",
    "Asphalt Plant",
    "Other Plant",
    "Storage Tank",
    "Fuel Tank",
    "Job Site",
    "Yard",
    "Shop",
    "Terminal",
]

# Liquid product catalog · grouped for the drawer dropdown.
# Categories are display-only; the wire field is a single string label.
LIQUID_PRODUCT_CATALOG: List[dict] = [
    {
        "category": "Asphalt Binders",
        "items": [
            "AC-20",
            "AC-30",
            "PG 64-22",
            "PG 67-22",
            "PG 70-22",
            "PG 76-22",
            "Polymer Modified Binder",
            "Modified Binder",
            "Rubberized Binder",
        ],
    },
    {
        "category": "Emulsions / Tack",
        "items": [
            "CRS-1",
            "CRS-2",
            "RS-1",
            "RS-2",
            "SS-1",
            "CSS-1",
            "Tack Oil",
            "Prime Oil",
            "Emulsion",
        ],
    },
    {
        "category": "Fuel / Support",
        "items": [
            "Diesel",
            "DEF",
            "Fuel Oil",
            "Gasoline",
            "Hydraulic Oil",
            "Liquid Lime",
            "Water",
            "Waste Oil",
            "Other Liquid",
        ],
    },
]


def flat_liquid_product_options() -> List[dict]:
    out: List[dict] = []
    for group in LIQUID_PRODUCT_CATALOG:
        for item in group["items"]:
            out.append({"label": item, "category": group["category"]})
    return out
