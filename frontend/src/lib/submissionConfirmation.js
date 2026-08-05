const WORKFLOW_RULES = {
  "daily-report": {
    familyLabel: "Project Controls",
    familyMeta: "Daily report workflow",
    title: "Daily Report Submitted Successfully",
    description: "Your daily report is on file and routed for project review.",
    documentTypeLabel: "Daily Report #",
    routedTo: ["Project Leadership", "Operations", "Payroll"],
    whatHappensNext: [
      "Project leadership can review today's work, production, and notes.",
      "Office teams can use this report for payroll, cost tracking, and daily records.",
    ],
    expectedProcessingStatus: "Filed and ready for review",
    startAnother: { label: "Start Another", to: "/daily/submit" },
    returnToPortal: { label: "Return to Portal", to: "/daily" },
  },
  "equipment-preop": {
    familyLabel: "Equipment Operations",
    familyMeta: "Pre-operation inspection workflow",
    title: "Equipment Inspection Submitted Successfully",
    description: "This inspection is on file and the equipment history has been updated.",
    documentTypeLabel: "Equipment Inspection #",
    routedTo: ["Equipment Records"],
    whatHappensNext: [
      "This inspection stays with the equipment history for the next crew and office review.",
    ],
    expectedProcessingStatus: "Filed in equipment records",
    startAnother: { label: "Start Another", to: "/equipment/submit" },
    returnToPortal: { label: "Return to Portal", to: "/equipment" },
  },
  "safety-inspection": {
    familyLabel: "Safety Operations",
    familyMeta: "Safety inspection workflow",
    title: "Safety Inspection Submitted Successfully",
    description: "This inspection is on file and routed into Safety review.",
    documentTypeLabel: "Inspection #",
    routedTo: ["Safety Department", "Project Manager"],
    whatHappensNext: [
      "Safety can review the inspection and any noted hazards.",
      "Project leadership can see project visibility on the submitted inspection.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/inspections/submit" },
    returnToPortal: { label: "Return to Portal", to: "/audits" },
  },
  meeting: {
    familyLabel: "Safety Operations",
    familyMeta: "Safety meeting workflow",
    title: "Safety Meeting Submitted Successfully",
    description: "This meeting record is on file and ready for Safety review.",
    documentTypeLabel: "Safety Meeting #",
    routedTo: ["Safety Department"],
    whatHappensNext: [
      "Safety can review the attendance, topic, and supporting photos.",
      "This meeting stays available as the crew's training record for the day.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/meetings/submit" },
    returnToPortal: { label: "Return to Portal", to: "/meetings" },
  },
  incident: {
    familyLabel: "Safety Operations",
    familyMeta: "Incident reporting workflow",
    title: "Incident Report Submitted Successfully",
    description: "Your field report is on file and Safety has the case.",
    documentTypeLabel: "Incident #",
    routedTo: ["Safety Department", "Project Manager"],
    whatHappensNext: [
      "Safety begins intake, review, and follow-up from the case record.",
      "Project leadership receives project visibility on the submitted incident.",
    ],
    expectedProcessingStatus: "Filed and under Safety intake review",
    startAnother: { label: "Start Another", to: "/incidents/report" },
    returnToPortal: { label: "Return to Portal", to: "/incidents" },
  },
  "near-miss": {
    familyLabel: "Safety Operations",
    familyMeta: "Near-miss workflow",
    title: "Near Miss Submitted Successfully",
    description: "Your near miss is on file and routed for Safety review.",
    documentTypeLabel: "Near Miss #",
    routedTo: ["Safety Department"],
    whatHappensNext: [
      "Safety reviews the report and follows up if more detail is needed.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/near-miss" },
    returnToPortal: { label: "Return to Portal", to: "/" },
  },
  dvir: {
    familyLabel: "Fleet Operations",
    familyMeta: "DVIR workflow",
    title: "DVIR Submitted Successfully",
    description: "Your daily vehicle inspection is on file and routed to the fleet teams.",
    documentTypeLabel: "DVIR #",
    routedTo: ["Dispatch", "Shop"],
    whatHappensNext: [
      "Dispatch can see the unit status from this filing.",
      "Shop can review logged defects and repair needs from the same DVIR.",
    ],
    expectedProcessingStatus: "Filed in fleet records",
    startAnother: { label: "Start Another", to: "/fleet/dvir/new" },
    returnToPortal: { label: "Return to Portal", to: "/field" },
  },
  "safety-issuance": {
    familyLabel: "Safety Operations",
    familyMeta: "Equipment issuance workflow",
    title: "Equipment Issuance Submitted Successfully",
    description: "This issuance record is on file and Safety has the document.",
    documentTypeLabel: "Equipment Issuance #",
    routedTo: ["Safety Department"],
    whatHappensNext: [
      "Safety can review the issued items, signatures, and attached photos.",
      "The record remains available in Safety Forms for future check-in and accountability.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/safety/forms/equipment-issuance/new" },
    returnToPortal: { label: "Return to Portal", to: "/safety-portal/forms-records" },
  },
  "safety-training": {
    familyLabel: "Safety Operations",
    familyMeta: "Training documentation workflow",
    title: "Training Record Submitted Successfully",
    description: "This training record is on file and Safety has the document.",
    documentTypeLabel: "Training Record #",
    routedTo: ["Safety Department"],
    whatHappensNext: [
      "Safety can review the training topics, signatures, and equipment details.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/safety/forms/equipment-training/new" },
    returnToPortal: { label: "Return to Portal", to: "/safety-portal/forms-records" },
  },
  "safety-return": {
    familyLabel: "Safety Operations",
    familyMeta: "Equipment return workflow",
    title: "Equipment Return Submitted Successfully",
    description: "This return record is on file and Safety has the check-in.",
    documentTypeLabel: "Equipment Return #",
    routedTo: ["Safety Department"],
    whatHappensNext: [
      "Safety can review the returned items, condition notes, and any chargeback details.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/safety/forms/equipment-issuance/new" },
    returnToPortal: { label: "Return to Portal", to: "/safety-portal/forms-records" },
  },
  qaqc: {
    familyLabel: "Quality Control",
    familyMeta: "QA/QC workflow",
    title: "QA/QC Inspection Submitted Successfully",
    description: "This QA/QC inspection is on file and routed for project review.",
    documentTypeLabel: "QA/QC Inspection #",
    routedTo: ["Assigned Project Manager"],
    whatHappensNext: [
      "The assigned Project Manager can review the inspection and attached evidence.",
    ],
    expectedProcessingStatus: "Filed and pending PM review",
    startAnother: { label: "Start Another", to: "/qaqc" },
    returnToPortal: { label: "Return to Portal", to: "/qaqc" },
  },
  odr: {
    familyLabel: "Field Leadership",
    familyMeta: "Operational daily record workflow",
    title: "Daily Work Record Submitted Successfully",
    description: "This daily work record is on file and ready for PM review.",
    documentTypeLabel: "Daily Work Record #",
    routedTo: ["Assigned Project Manager"],
    whatHappensNext: [
      "The Project Manager can review the submitted work record from the PM panel.",
      "The 24-hour amendment window stays open for the submitted record.",
    ],
    expectedProcessingStatus: "Filed and pending PM review",
    startAnother: { label: "Start Another", to: "/odr/new" },
    returnToPortal: { label: "Return to Portal", to: "/odr" },
  },
  "field-leadership": {
    familyLabel: "Field Leadership",
    familyMeta: "Field leadership workflow",
    title: "Field Leadership Record Submitted Successfully",
    description: "This record is on file and routed to the operating team.",
    documentTypeLabel: "Record #",
    routedTo: ["Assigned Project Manager", "Safety Department"],
    whatHappensNext: [
      "The operating team can review the submitted record and attached signatures.",
    ],
    expectedProcessingStatus: "Filed and under review",
    startAnother: { label: "Start Another", to: "/leadership" },
    returnToPortal: { label: "Return to Portal", to: "/leadership" },
  },
  "time-off": {
    familyLabel: "Human Resources",
    familyMeta: "Time-off request workflow",
    title: "Time-Off Request Submitted Successfully",
    description: "Your request is on file and Human Resources has it for review.",
    documentTypeLabel: "HR Request #",
    routedTo: ["Human Resources"],
    whatHappensNext: [
      "Human Resources reviews the request and sends a decision after review.",
    ],
    expectedProcessingStatus: "Filed and pending HR review",
    startAnother: { label: "Start Another", to: "/time-off/public" },
    returnToPortal: { label: "Return to Portal", to: "/" },
  },
  "po-request": {
    familyLabel: "Field Purchasing",
    familyMeta: "PO request workflow",
    title: "PO Request Submitted Successfully",
    description: "Your purchase request is on file and routed for approval.",
    documentTypeLabel: "PO Request #",
    routedTo: ["Assigned Project Manager", "Human Resources"],
    whatHappensNext: [
      "The assigned approval team reviews the request and issues the official PO if approved.",
      "You can return to the PO page to watch approval, clarification, and receipt status.",
    ],
    expectedProcessingStatus: "Filed and pending approval",
    startAnother: { label: "Start Another", to: "/po-requests?new=1" },
    returnToPortal: { label: "Return to Portal", to: "/po-requests" },
  },
  excavation: {
    familyLabel: "Trench Safety",
    familyMeta: "Excavation workflow",
    title: "Excavation Record Submitted Successfully",
    description: "Your excavation record is on file and Safety has the submission.",
    documentTypeLabel: "Excavation Record #",
    routedTo: ["Safety Department"],
    whatHappensNext: [
      "Safety can review the excavation status, linked records, and any coaching flags.",
    ],
    expectedProcessingStatus: "Filed and under Safety review",
    startAnother: { label: "Start Another", to: "/trench-safety/excavation/new" },
    returnToPortal: { label: "Return to Portal", to: "/trench-safety" },
  },
  "trench-report": {
    familyLabel: "Trench Safety",
    familyMeta: "Public trench report workflow",
    title: "Asset Report Submitted Successfully",
    description: "Your asset report is on file and routed for review.",
    documentTypeLabel: "Asset Report #",
    routedTo: ["Shop", "Safety Department"],
    whatHappensNext: [
      "Shop reviews the reported condition before changing any asset status.",
      "Safety keeps visibility on the reported condition and follow-up.",
    ],
    expectedProcessingStatus: "Filed and open for review",
    startAnother: { label: "Start Another", to: "/trench-safety" },
    returnToPortal: { label: "Return to Portal", to: "/trench-safety" },
  },
};

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function uniqueList(items = []) {
  return [...new Set((items || []).filter(Boolean).map((item) => String(item).trim()).filter(Boolean))];
}

function resolveFieldLeadershipRule(kind) {
  if (kind === "time_off_request" || kind === "employee_termination") {
    return {
      title: kind === "time_off_request" ? "Time-Off Request Submitted Successfully" : "Termination Request Submitted Successfully",
      documentTypeLabel: kind === "time_off_request" ? "HR Request #" : "Termination Request #",
      routedTo: ["Human Resources"],
      whatHappensNext: [
        "Human Resources reviews the request and follows the next approval step from the queue.",
      ],
      expectedProcessingStatus: "Filed and pending HR review",
      returnToPortal: { label: "Return to Portal", to: "/leadership" },
    };
  }
  if (kind === "equipment_checkout") {
    return {
      title: "Equipment Checkout Submitted Successfully",
      documentTypeLabel: "Equipment Checkout #",
      routedTo: ["Assigned Project Manager", "Safety Department"],
      expectedProcessingStatus: "Filed and under team review",
    };
  }
  if (kind === "equipment_return") {
    return {
      title: "Equipment Return Submitted Successfully",
      documentTypeLabel: "Equipment Return #",
      routedTo: ["Assigned Project Manager", "Safety Department"],
      expectedProcessingStatus: "Filed and under team review",
    };
  }
  return {};
}

export function buildSubmissionConfirmation(input = {}) {
  const workflowKey = input.workflowKey || "field-leadership";
  const base = WORKFLOW_RULES[workflowKey] || WORKFLOW_RULES["field-leadership"];
  const fieldLeadershipRule = workflowKey === "field-leadership"
    ? resolveFieldLeadershipRule(input.recordKind)
    : {};

  const queued = Boolean(input.queued);
  const statusTone = input.statusTone || (queued ? "amber" : "emerald");
  const successStatus = input.successStatus || (queued ? "Saved on this device" : "Submitted Successfully");

  const routedTo = uniqueList([
    ...(Array.isArray(base.routedTo) ? base.routedTo : []),
    ...(Array.isArray(fieldLeadershipRule.routedTo) ? fieldLeadershipRule.routedTo : []),
    ...(Array.isArray(input.routedTo) ? input.routedTo : []),
  ]);

  const whatHappensNext = uniqueList([
    ...(Array.isArray(base.whatHappensNext) ? base.whatHappensNext : []),
    ...(Array.isArray(fieldLeadershipRule.whatHappensNext) ? fieldLeadershipRule.whatHappensNext : []),
    ...(Array.isArray(input.whatHappensNext) ? input.whatHappensNext : []),
  ]);

  const contextItems = (input.contextItems || []).filter((item) => item?.label && item?.value).map((item) => ({
    label: item.label,
    value: item.value,
    testId: item.testId || `submission-confirmation-${slugify(item.label)}`,
  }));

  return {
    workflowKey,
    accent: input.accent || statusTone,
    statusTone,
    familyLabel: input.familyLabel || base.familyLabel,
    familyMeta: input.familyMeta || base.familyMeta,
    title: input.title || fieldLeadershipRule.title || base.title,
    description: input.description || base.description,
    documentTypeLabel: input.documentTypeLabel || fieldLeadershipRule.documentTypeLabel || base.documentTypeLabel || "Document #",
    documentNumber: input.documentNumber || (queued ? "Will assign after submission" : ""),
    successStatus,
    submittedAt: input.submittedAt || "",
    submittedBy: input.submittedBy || "",
    project: input.project || "",
    routedTo,
    whatHappensNext,
    followUpRequired: input.followUpRequired || (queued
      ? "Keep this device online so the submission can send automatically."
      : "No further action is required from you at this time."),
    expectedProcessingStatus: input.expectedProcessingStatus || fieldLeadershipRule.expectedProcessingStatus || base.expectedProcessingStatus || "Filed",
    startAnother: input.startAnother || base.startAnother,
    returnToPortal: input.returnToPortal || fieldLeadershipRule.returnToPortal || base.returnToPortal,
    openRecord: input.openRecord || null,
    footerText: input.footerText || "MASCI Operations Platform · Submission filing standard",
    backTo: input.backTo || (input.returnToPortal?.to || base.returnToPortal?.to || "/"),
    backLabel: input.backLabel || (input.returnToPortal?.label || base.returnToPortal?.label || "Return to Portal"),
    note: input.note || "",
    contextItems,
    recordKind: input.recordKind || "",
  };
}

export function adaptLegacyThankYouState(state = {}) {
  const formType = String(state.formType || "").toLowerCase();
  const map = {
    "daily report": "daily-report",
    inspection: "safety-inspection",
    "site safety meeting": "meeting",
    incident: "incident",
    dvir: "dvir",
  };
  return buildSubmissionConfirmation({
    workflowKey: state.workflowKey || map[formType] || "field-leadership",
    documentNumber: state.documentNumber || state.recordId || state.reference || "",
    submittedAt: state.submittedAt || state.createdAt || new Date().toISOString(),
    submittedBy: state.submittedBy || state.preparedBy || state.driverName || state.reportedBy || "",
    project: state.project || state.projectName || "",
    queued: state.queued,
    successStatus: state.successStatus,
    expectedProcessingStatus: state.expectedProcessingStatus,
    followUpRequired: state.followUpRequired,
    routedTo: state.routedTo,
    whatHappensNext: state.whatHappensNext,
    startAnother: state.startAnother || (state.startAnotherTo ? { label: "Start Another", to: state.startAnotherTo } : undefined),
    returnToPortal: state.returnToPortal || (state.returnTo ? { label: "Return to Portal", to: state.returnTo } : undefined),
    openRecord: state.openRecord || (state.openRecordTo ? { label: "Open Submitted Record", to: state.openRecordTo } : undefined),
    contextItems: state.contextItems,
    note: state.note,
  });
}