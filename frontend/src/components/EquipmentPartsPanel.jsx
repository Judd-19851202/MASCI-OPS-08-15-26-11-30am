import React from "react";
import PartsCatalog from "@/components/PartsCatalog";

/**
 * EquipmentPartsPanel — admin / PM view of the per-unit parts catalog.
 *
 * Reuses the same rich PartsCatalog component the Shop tile uses, so all
 * three personas (admin, PM, mechanic) get one consistent interface for
 * adding, editing, deleting, searching, and ordering wear-item parts.
 *
 * The legacy bulk-XLSX uploader still lives at
 * `POST /api/admin/equipment-parts/upload` — it can be re-attached if a
 * spreadsheet seed becomes useful again. The day-to-day path the user
 * asked for is the per-unit drilldown, which PartsCatalog does natively.
 */
const EquipmentPartsPanel = () => (
  <div className="mb-8" data-testid="equipment-parts-panel">
    <PartsCatalog />
  </div>
);

export default EquipmentPartsPanel;
