# Transportation Fleet Classification Standard

Track 19.02A · Standard for which MASCI equipment surfaces in
Transportation Operations.

## Included categories (`TRANSPORT_CAPABLE_CATEGORIES`)

These `equipment_master.category` values are included in the
Transportation Fleet projection and are eligible for adoption:

* Dump Trucks
* Tractor Trailer Trucks
* Service Trucks
* Water Trucks
* Misc Trucks
* Flatbed Trucks
* Trailers

## Explicitly excluded categories

Per the Track 19.02A directive ("NOT Passenger pickups, Office vehicles,
HR vehicles, Executive vehicles, Rental cars, Anything that should not
participate in Transportation"):

| Category | Why excluded |
| --- | --- |
| Pickup Trucks | Light-duty passenger vehicles |
| Supervisor / Mgmt Trucks | Management / executive vehicles |
| Excavators · Loaders · Backhoes · Dozers · Skid Steers | Yard equipment, not road haulers |
| Rollers · Sweepers · Road Graders · Paving Equipment · Compactors | Construction equipment |
| Pumps · Generators · Light Towers · Welders · Air Compressors | Power / support equipment |
| Storage / Containers · Trench Safety · Attachments · Misc Equipment | Non-mobile or specialty support |

## Transportation Classification enum

When an asset is adopted, the engine assigns a default
`transportation_classification` derived from `category` +
`preop_equipment_type`. Allowed values:

```
heavy_haul · end_dump · transfer · day_cab · sleeper · lowboy ·
equipment_hauler · equipment_trailer · tag_trailer · flatbed ·
water_truck · fuel_truck · service_truck · pole_trailer ·
jeep_dolly · other
```

## Derivation rules

| Category match | Default classification |
| --- | --- |
| Dump Trucks | `end_dump` |
| Tractor Trailer Trucks | `day_cab` |
| Water Trucks (or `preop_equipment_type=Water Truck`) | `water_truck` |
| Service Trucks | `service_truck` |
| Flatbed Trucks | `flatbed` |
| Trailers | `equipment_trailer` |
| Misc Trucks / unmatched | `other` (preview flags as `unknown_classification`) |

Operators refine the classification post-adoption via
**Edit Transportation Details** on each row.

## Validation enforcement

* `POST /equipment/{id}/adopt` — rejects non-listed categories with
  HTTP 422.
* `PATCH /equipment/{id}/overlay` — rejects
  `transportation_classification` values outside the enum with HTTP 422.

## Extending the standard

Adding a new transport-capable category requires:

1. Add the category string to `TRANSPORT_CAPABLE_CATEGORIES` in
   `/app/backend/routes/transportation.py`.
2. (Optional) Add a derivation branch to
   `_derive_transportation_classification`.
3. No schema migration. No frontend change required — the Fleet
   projection auto-surfaces it.
