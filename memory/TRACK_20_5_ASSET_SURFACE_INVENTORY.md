# TRACK 20.5 · Asset / Equipment Surface Inventory

Every asset-adjacent surface in the platform, catalogued once, before any
promotion. No new surfaces introduced by this track.

## 1 · Data surfaces (backend collections)

| Collection | Purpose | Owner track |
|---|---|---|
| `equipment_master` | Canonical asset record — one row per unit | 13.31B · FORGEDOPS P0.1 |
| `assets` (view / spine) | `asset_spine` fused profile over `equipment_master` | 13.31B P0.1 |
| `asset_service_events` (projected) | Timeline projector — Pre-Op, DVIR, defects, repairs, OOS, transfers, photos, docs, PO, incident links | 13.26 |
| `asset_documents` (attachments) | Asset-owned document vault + required-docs + missing-photos dashboards | 13.31B D3/D4 |
| `asset_transfers` | Transfer state machine — request → approve → in-transit → receive → close | 15.79c |
| `equipment_inspections` | Pre-op / DVIR / equipment inspections (structured) | 13.31B D5.1/5.2/5.4 |
| `safety_equipment_issuances` | PPE / phone / iPad / tool issuance to employees | 19.13 · 19.14 |
| `safety_equipment_trainings` | Training records associated with issued equipment | 19.13 |
| `pm_schedules` / `pm_work_orders` | PM engine — schedules, templates, work orders | 13.31 |
| `fuel_lube_visits` | Fuel / lube servicing on assets | 13.29 |
| `service_truck_reconciliations` | Service truck end-of-day reconciliation | 13.30 |
| `field_leadership_records` | Overview counters (rolls up issuance / training totals) | 15.9 |
| `employee_records` | Historical Records vault (employee + vendor lanes; **asset lane TBD in 19.61**) | 19.21 · 19.59 |
| `po_requests` | Purchase orders (asset acquisition, vendor link) | 15.75c |

## 2 · Backend route surfaces (all pre-existing)

| Router | Prefix | What it serves |
|---|---|---|
| `asset_spine.py` | `/api/asset-spine` | `assets`, `assets/{id}`, `assets/{id}/profile`, PATCH/retire/activate/transfer, onboarding |
| `asset_service_events.py` | `/api/assets` | `{unit_number}/timeline` — timeline backbone |
| `asset_documents.py` | `/api/asset-spine` | Docs (upload/list/patch/delete/file), required-documents, missing-photos, dashboards, exports |
| `asset_care.py` | `/api/asset-care` | `summary`, `readiness`, `work-queue`, `alerts`, `notifications-matrix` |
| `asset_transfers.py` | `/api/asset-transfers` | Full transfer workflow |
| `fleet_ops.py` | `/api/fleet` + fleet lenses | Units, inspections, defects, OOS, dispatch fleet status, safety fleet emergency-equipment |
| `shop_intel.py` | `/api/shop` | Unit search, mechanic workload, parts, projects |
| `safety_forms.py` | `/api/safety-forms` | Equipment issuances, returns, trainings + PDFs |
| `shop_command_feed.py` | `/api/shop` | Shop command centre feed |
| `equipment.py` | (equipment lookup helpers) | Equipment master helpers |
| `equipment_detection.py` | (equipment matching) | Master lookup / typeahead |
| `promo_assets.py` | (branding) | Not an operational asset router — unrelated |
| `site_inspection_lifecycle.py` | (safety trailer / site inspection) | Safety trailer lifecycle |

## 3 · Frontend surfaces (all pre-existing)

### Fleet-oriented
- `FleetVisibility.jsx` (scope=shop|fleet|safety|dispatch)
- `pages/fleet/FleetUnitThread.jsx` — **the pilot thread** (`/fleet/unit/:unit_number`)
- `NewFleetDVIR.jsx`, `FleetDVIRConfirmation.jsx`

### Shop-oriented
- `ShopHub.jsx` (legacy), `ShopHubV2.jsx`
- `shop/ShopAssetCare.jsx`, `shop/ShopManagerQueue.jsx`, `shop/ShopMyAssignments.jsx`
- `shop/PmDashboard.jsx`, `shop/PmSchedules.jsx`, `shop/PmTemplates.jsx`, `shop/PmWorkOrders.jsx`
- `shop/FuelLubeVisit(*)`
- `shop/ServiceTruckReconciliation(*)`
- `shop/UnitHistoryLanding.jsx`, `shop/UnitHistoryTimeline.jsx`
- `shop/ShopTrenchSafetyRepairs.jsx`

### Equipment / inspection surfaces
- `EquipmentDashboard.jsx` (mounted under multiple routes: `/admin/equipment-inspections`, `/pm/equipment`, `/shop/equipment`)
- `NewEquipmentInspection.jsx`, `ViewEquipmentInspection.jsx`
- `NewInspection.jsx`, `ViewInspection.jsx`
- `NewQaqcInspection.jsx`, `ViewQaqcInspection.jsx`

### Admin / spine
- `admin/AdminEquipment.jsx`
- `admin/AdminAssetSpine*` (asset admin surfaces)
- `AdminLeadershipEquipment.jsx`
- `AssetTransfers.jsx`

### Safety / issuance
- `NewSafetyEquipmentIssuance.jsx`
- `NewSafetyEquipmentTraining.jsx`
- `ReturnEquipment.jsx`
- `ViewSafetyForm.jsx` (kind="issuance" | "training")

## 4 · Canonical asset classes covered (from `services/asset_taxonomy.py`)

- Heavy Equipment: Excavator, Dozer, Motor Grader, Loader, Roller,
  Milling Machine, Paver, Skid Steer, Backhoe, Sweeper, Forklift, Crane,
  Compactor, Other Heavy Equipment.
- Truck: Pickup, Dump, Fuel, Lube, Service, Water, Flatbed, Crew,
  Roll-Off, Semi Tractor, Other Truck.
- Trailer: Equipment, Lowboy, Tag, Utility, Office, Storage, Other Trailer.
- **Trench Safety: Trench Box, Trench Plate, Road Plate, Shoring, Other.**
- Roadway / Traffic Control: Message Board, Arrow Board, Traffic Signal,
  Cone Package, Barricade, Light Tower, Generator, Other.
- **Survey Equipment: Total Station, Robotic Total Station, Rover, Base
  Station, Data Collector, Controller, Optical/Automatic/Dumpy/Builder's/
  Digital/Laser Level, Rotating/Dual-Slope/Grade/Pipe/Alignment Laser,
  Transit, Theodolite, Prism, Tripod, Bipod, Grade/Level/Survey Rod,
  Measuring Wheel, Utility Locator (Pipe · Cable · Sonde · GPR ·
  Magnetic · Valve · Electronic Marker), Other Survey.**
- GPS / Machine Control: GPS Rover · Base · GNSS · Topcon Hiper XR/VR ·
  Machine Receiver / Display / Antenna / Mast · Radios · Antennas.
- **Technology Equipment: Laptop, Desktop, Workstation, Monitor, Tablet,
  iPad, Phone, Smartphone, Hotspot, Printer, Scanner, Camera, Drone
  (Controller · Battery Set), Handheld/Mobile/Base Radio, Repeater,
  Satellite Communicator/Phone, Radio Charger/Dock/Battery Bank, Other.**
- **Safety Equipment (PPE): Harness, Gas Monitor, Confined Space
  Equipment, Respirator, Fall Protection, Other.**
- Support Equipment: Tool, Specialty Tool, Pump, Compressor, Welder,
  Other.
- Facility Asset: Office / Shop / Yard Equipment, Other.
- Temporary Asset: Rental / Loaner / Temporary Device, Other.
- Other Asset.

Every single item in the user's enumeration is already a canonical class
in taxonomy 1.0.0. **No new taxonomy branch is required.**

## 5 · Surfaces that DO NOT belong in this inventory (out of scope)

- `promo_assets.py` — marketing/branding, not operational assets.
- `site_inspection_lifecycle.py` — safety trailer, tracked as a project
  surface not per-unit.
- Corporate / Executive dashboards — consume assets read-only; not
  authoritative surfaces.

## 6 · Count summary

- **13** authoritative collections
- **12** backend routers
- **20+** frontend pages (fleet · shop · equipment · admin · safety)
- **1** existing 10-section thread pilot (Fleet Unit Thread)
- **13** canonical asset classes covering **≥ 130 asset types**
