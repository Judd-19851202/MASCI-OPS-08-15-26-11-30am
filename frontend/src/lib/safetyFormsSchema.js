// Safety Forms — shared constants for the Equipment Issuance + Training
// pages. Item-type list is intentionally hardcoded (per Justin) so the
// form stays clean and offline-capable; the "Other" choice reveals a
// free-text field for write-ins.

export const ITEM_TYPES = [
  "Harness",
  "SRL Type 1",
  "SRL Type 2",
  "Lanyard",
  "Hard Hat",
  "Safety Glasses — Clear",
  "Safety Glasses — Tinted",
  "Safety Glasses — Premium / Branded",
  "Safety Vest Type II",
  "Safety Vest Type III",
  "Traffic Gators",
  "Headlamp",
  "Gloves",
  "Gas Monitor",
  "Two-Way Radio",
  "FAA Radio",
  "Ladder",
  "Other",
];

// Price book — replacement / fair-market value per item at NEW or GOOD
// condition. Fair / Damaged conditions unlock the field for the
// supervisor to enter a depreciated value, and "Other" is always
// open-text. Keep this list in sync with ITEM_TYPES.
export const PRICE_BOOK = {
  "Harness": 225,
  "SRL Type 1": 350,
  "SRL Type 2": 550,
  "Lanyard": 100,
  "Hard Hat": 45,
  "Safety Glasses — Clear": 10,
  "Safety Glasses — Tinted": 15,
  "Safety Glasses — Premium / Branded": 30,
  "Safety Vest Type II": 25,
  "Safety Vest Type III": 40,
  "Traffic Gators": 60,
  "Headlamp": 50,
  "Gloves": 8,
  "Gas Monitor": 900,
  "Two-Way Radio": 150,
  "FAA Radio": 500,
  "Ladder": 350,
};

// Conditions that lock the unit-value input to the price-book value.
// Anything else (Fair, Damaged) makes the field editable so the
// supervisor can capture a depreciated/agreed-upon value.
const LOCKED_CONDITIONS = new Set(["New", "Good"]);

/**
 * Returns true if the unit-value field should be auto-filled and
 * locked for this combination of item type + form-level condition.
 * "Other" is never locked because there's no price-book entry.
 */
export function isUnitValueLocked(itemType, condition) {
  if (!itemType || itemType === "Other") return false;
  if (PRICE_BOOK[itemType] == null) return false;
  return LOCKED_CONDITIONS.has(condition);
}

/**
 * Resolve the unit value to apply to an item. When the field is
 * locked, return the price-book value. Otherwise leave whatever the
 * user has entered (preserves manual edits when condition is Fair/Damaged).
 */
export function resolveUnitValue(itemType, condition, currentValue) {
  if (isUnitValueLocked(itemType, condition)) {
    return PRICE_BOOK[itemType];
  }
  return currentValue;
}

export const CONDITIONS = ["New", "Good", "Fair", "Damaged"];

export const TRAINING_TYPES = ["Initial Training", "Refresher", "Retraining"];

// Keep the keys in sync with TRAINING_TOPICS in safety_forms.py.
export const TRAINING_TOPICS = [
  { key: "proper_use", label: "Proper Use" },
  { key: "inspection", label: "Inspection Requirements" },
  { key: "maintenance", label: "Maintenance" },
  { key: "storage", label: "Storage" },
  { key: "limitations", label: "Limitations of Equipment" },
  { key: "osha", label: "OSHA Compliance" },
  { key: "other", label: "Other" },
];

import { todayLocalIso } from "@/lib/dateUtils";

export function blankIssuanceItem() {
  return {
    item_type: "Harness",
    item_type_other: "",
    description: "",
    quantity: 1,
    // Default condition is New → Harness locks at price-book ($225).
    unit_value: PRICE_BOOK["Harness"],
    asset_id: "",
  };
}

export function blankTrainingItem() {
  return {
    equipment_type: "Harness",
    equipment_type_other: "",
    description: "",
    training_type: "Initial Training",
    manufacturer_model: "",
    notes: "",
  };
}

const LAST_SUPERVISOR_KEY = "masci.safetyforms.lastSupervisor";

export function rememberSupervisor(name) {
  try {
    if (name) localStorage.setItem(LAST_SUPERVISOR_KEY, name);
  } catch {
    /* ignore */
  }
}

export function recallSupervisor() {
  try {
    return localStorage.getItem(LAST_SUPERVISOR_KEY) || "";
  } catch {
    return "";
  }
}

export function buildIssuanceDefaults() {
  return {
    employee_name: "",
    employee_id: "",
    employee_email: "",
    position: "",
    project_name: "",
    project_number: "",
    location: "",
    issued_by: recallSupervisor(),
    issued_date: todayLocalIso(),
    items: [blankIssuanceItem()],
    condition: "New",
    condition_note: "",
    photos: [],
    acknowledgment: false,
    employee_signature: "",
    supervisor_signature: "",
  };
}

export function buildTrainingDefaults() {
  return {
    employee_name: "",
    employee_id: "",
    employee_email: "",
    position: "",
    project_name: "",
    project_number: "",
    training_date: todayLocalIso(),
    instructor_name: recallSupervisor(),
    training_location: "",
    items: [blankTrainingItem()],
    topics: [],
    topic_other: "",
    acknowledgment: false,
    employee_signature: "",
    instructor_signature: "",
  };
}

export function totalIssuanceValue(items) {
  let total = 0;
  for (const it of items || []) {
    const q = parseFloat(it.quantity) || 0;
    const u = parseFloat(it.unit_value) || 0;
    total += q * u;
  }
  return total;
}

export function fmtMoney(v) {
  const n = parseFloat(v) || 0;
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
  });
}

export const ISSUANCE_LEGAL = `I acknowledge that all issued equipment remains the property of MASCI General Contractors Inc. I agree to use all equipment in accordance with manufacturer guidelines, company policy, and applicable OSHA safety requirements.`;

export const ISSUANCE_RESPONSIBILITY = `I understand that I am responsible for the proper use, care, maintenance, and return of all issued equipment. I further understand that I am responsible for promptly reporting any loss, damage, or malfunction.

Equipment that is lost, stolen, misplaced, or damaged due to negligence, misuse, or failure to follow manufacturer guidelines, company policy, or OSHA requirements may result in financial responsibility for the reasonable replacement cost or fair market value of the equipment, to the extent permitted by law.

I understand that I will not be held responsible for normal wear and tear resulting from proper use.

Any reimbursement or payroll deduction will be handled in accordance with applicable Florida law and the Fair Labor Standards Act (FLSA), and will only occur with proper written authorization where required.

I understand that failure to follow these requirements may also result in disciplinary action, up to and including termination, in accordance with company policy.`;

export const RETURN_STATUSES = [
  { key: "returned", label: "Returned OK", tone: "emerald" },
  { key: "damaged", label: "Damaged", tone: "amber" },
  { key: "lost", label: "Lost / Not Returned", tone: "red" },
];

export function blankReturnRow(issuedItem) {
  return {
    // Snapshot of the original issued item so chargebacks stay stable
    // even if the issuance is edited later.
    source_item_type: issuedItem.item_type || "",
    source_item_type_other: issuedItem.item_type_other || "",
    source_description: issuedItem.description || "",
    source_asset_id: issuedItem.asset_id || "",
    source_quantity: parseFloat(issuedItem.quantity) || 0,
    source_unit_value: parseFloat(issuedItem.unit_value) || 0,

    status: "returned", // one of RETURN_STATUSES keys
    returned_quantity: parseFloat(issuedItem.quantity) || 0,
    note: "",
  };
}

export function buildReturnDefaults(issuanceDoc) {
  return {
    items: (issuanceDoc?.items || []).map(blankReturnRow),
    check_in_date: todayLocalIso(),
    received_by: recallSupervisor(),
    return_notes: "",
    // Pre-fill from the parent issuance so the supervisor doesn't
    // have to retype it; still editable in case it changed.
    employee_email: issuanceDoc?.employee_email || "",
    acknowledgment: false,
    employee_signature: "",
    supervisor_signature: "",
  };
}

// Chargeback = (lost qty × unit) + (damaged qty × unit). A partial
// return (returned_quantity < source_quantity) for status="returned"
// is also treated as a loss on the missing count.
export function computeChargeback(items) {
  let lost = 0;
  let damaged = 0;
  for (const it of items || []) {
    const src = parseFloat(it.source_quantity) || 0;
    const ret = parseFloat(it.returned_quantity) || 0;
    const uv = parseFloat(it.source_unit_value) || 0;
    if (it.status === "lost") {
      lost += src * uv;
    } else if (it.status === "damaged") {
      damaged += src * uv;
    } else if (it.status === "returned" && ret < src) {
      lost += (src - ret) * uv;
    }
  }
  return { lost, damaged, total: lost + damaged };
}
