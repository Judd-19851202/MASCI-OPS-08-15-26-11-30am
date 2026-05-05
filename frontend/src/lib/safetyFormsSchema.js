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
  "Safety Vest Type II",
  "Safety Vest Type III",
  "Traffic Gators",
  "Headlamp",
  "Gloves",
  "Gas Monitor",
  "Ladder",
  "Other",
];

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
    unit_value: 0,
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

export const ISSUANCE_LEGAL = `I acknowledge that all issued equipment remains the property of MASCI General Contractors. I agree to use all equipment in accordance with company policy and OSHA safety requirements.

I understand that I am responsible for the care and return of all issued equipment. Any equipment that is lost, stolen, misplaced, or damaged due to negligence or misuse may result in financial responsibility for replacement cost or fair market value.

Any reimbursement or payroll deduction will be handled in accordance with applicable Florida law and the Fair Labor Standards Act (FLSA), and will not occur without proper authorization where required.`;
