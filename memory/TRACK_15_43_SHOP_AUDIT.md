# TRACK 15.43 · Shop Audit

**Verdict:** 🟢 **GREEN**

## Lifecycle coverage

| Workflow | Page(s) | Backend |
|---|---|---|
| Equipment assignment | `EquipmentDashboard.jsx`, `AssetTransfers.jsx` | `routes/asset_documents`, `routes/shop_intel` |
| Equipment return | `ReturnEquipment.jsx` (Safety form path) + asset transfer | `routes/safety_forms`, `routes/asset_documents` |
| Maintenance — Work Orders | `shop/PmWorkOrders.jsx` | `routes/shop_intel` (PM = Preventive Maintenance) |
| Maintenance — Schedules | `shop/PmSchedules.jsx` | `routes/shop_intel` |
| Maintenance — Templates | `shop/PmTemplates.jsx` | `routes/shop_intel` |
| Shop Manager Queue | `shop/ShopManagerQueue.jsx` | `routes/shop_intel` |
| Shop My Assignments | `shop/ShopMyAssignments.jsx` | `routes/shop_intel` |
| Fuel/Lube Visit | `shop/FuelLubeVisitForm.jsx`, `FuelLubeVisitRecords.jsx`, `FuelLubeVisitDetail.jsx` | `routes/shop_intel` |
| Service Truck Reconciliation | `ServiceTruckReconciliationForm/Records/Detail.jsx` | `routes/shop_intel` |
| Trench Safety Shop Repairs | `shop/ShopTrenchSafetyRepairs.jsx` | `routes/trench_safety` |
| Unit History Timeline | `shop/UnitHistoryTimeline.jsx`, `UnitHistoryLanding.jsx` | `routes/master_history` |
| Equipment Inspection | `NewEquipmentInspection.jsx` | `routes/equipment` |
| Asset Profile PDF | (via Equipment Dashboard) | `routes/asset_documents._render_asset_profile_pdf` ✅ Track 15.42 |
| Fleet Severity Reference | `AdminLeadershipEquipment.jsx` (PDF download) | `routes/fleet_ops.severity_reference_card_pdf` ✅ Track 15.42 |
| Master History PDF | unit timeline page → "PDF" button | `routes/master_history` ✅ Track 15.41/42 |
| Notifications | Bell drawer | `linked_source_module=fleet.*` / `assets.*` |

## Pass Criteria
* End-to-end equipment lifecycle: ✅
* Documentation: ✅ (Asset Profile + Master History + PM records all PDF-certified)
* Notifications routed to shop scope: ✅ (`recipient_role=shop`)
* PDF audit blocks: ✅

🟢 **GREEN — Shop can operate entirely from the platform.**
