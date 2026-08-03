# WP-18A Import / Export Capability Audit

Date: 2026-08-03

## Governing rule
Shared terminology or integration references are not enough. This audit only records what source actually proves.

## Confirmed capability
- `backend/routes/integrations/imports_exports.py` is a real route module.
- It documents a **manual CSV import/export fallback** for MASCI mapping workflows.
- Its stated purpose is to operate before Motive / MaintainX credentials are available.

## What is proven

### Manual import exists
- The route module supports import of CSV rows for mapping/normalization.
- It reads anchor records from existing stores such as `equipment_master` and `employees`.
- It writes mapping artifacts to mapping collections rather than pretending the external provider is already connected.

### Manual export exists
- The same module supports exporting normalized/mapped records back out as CSV.

### Mapping is platform-internal, not vendor-native by default
- Source explicitly frames this as fallback behavior before external credentials exist.
- Therefore the capability is real, but the external-provider integration posture is intentionally incomplete.

## What is not proven
- No evidence in this audit proves active live credentialed sync with Motive.
- No evidence in this audit proves active live credentialed sync with MaintainX.
- No evidence in this audit proves scheduled bi-directional synchronization.

## Trace posture

CSV upload operator  
→ import/export route normalization  
→ mapping collections / sync log  
→ downstream operations intelligence or mapping consumers

## Trust classification
- Manual mapping fallback: **real and reusable**
- External live-provider sync: **not proven in this audit**

## WP-18 disposition
- Current fallback capability: `REUSE_AS_IS`
- Future provider connection: `CONNECT`

## Executive conclusion
The platform already has a defensible import/export fallback layer. WP-18B should treat it as an honest manual bridge, not overstate it as a fully connected external integration.