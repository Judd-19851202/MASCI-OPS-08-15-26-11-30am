// MASCI Current Jobs — extracted from "MASCI Current Jobs.pdf"
// Each entry: { project_name (full label), project_number, location (suggested) }
// Used by JobPicker on every form (Inspections, Meetings, JHP, Incidents).

export const JOB_LIBRARY = [
  { project_name: "T5686 SR 15/SR600 (SANFORD, 17/92, LAKE MARY)", project_number: "20-07", location: "SANFORD, 17/92, LAKE MARY" },
  { project_name: "T5736 Oveido - (426, BROADWAY)", project_number: "21-06", location: "Oveido - (426, BROADWAY)" },
  { project_name: "T5749 SR 436 (ALTAMONTE SPRINGS)", project_number: "22-08", location: "ALTAMONTE SPRINGS" },
  { project_name: "T5824 - SR 46 (W 1ST ST.)", project_number: "24-06", location: "SR 46 (W 1ST ST.)" },
  { project_name: "E57B2 - SR 46 (MELLONVILLE AVE)", project_number: "24-08", location: "SR 46 (MELLONVILLE AVE)" },
  { project_name: "CC5744 - OXFORD RD Improvements (OXFORD)", project_number: "24-12", location: "OXFORD RD Improvements (OXFORD)" },
  { project_name: "T5841 - SR 401 (Brevard Co, Cape Canaveral)", project_number: "24-13 - CP", location: "SR 401 (Brevard Co, Cape Canaveral)" },
  { project_name: "T5832 - SR 430 (Mason Ave)", project_number: "25-01 - CP", location: "SR 430 (Mason Ave)" },
  { project_name: "E53F5 - SR 5 (Titusville)", project_number: "25-02", location: "SR 5 (Titusville)" },
  { project_name: "Vol. Co Resurface", project_number: "25-03", location: "" },
  { project_name: "Oxford Rd Surcharge Utility", project_number: "25-04", location: "Oxford Rd" },
  { project_name: "T5838 SR 500 (US441) (Mt Dora)", project_number: "25-08", location: "SR 500 (US441) (Mt Dora)" },
  { project_name: "Pavement Management Services", project_number: "25-10", location: "" },
  { project_name: "N. Atlantic Ave - Drainage", project_number: "25-12", location: "N. Atlantic Ave" },
  { project_name: "N. Atlantic Ave - Watermain Replacement", project_number: "25-13", location: "N. Atlantic Ave" },
  { project_name: "E8V62 Resurf Seminole Expressway (SR 417)", project_number: "25-14", location: "Seminole Expressway (SR 417)" },
  { project_name: "E53F1 - SR 404, Brevard Co (Pineda)", project_number: "25-15", location: "SR 404, Brevard Co (Pineda)" },
  { project_name: "T5842 - SR 600 Volusia County (Orange City)", project_number: "25-16 - CP", location: "SR 600 Volusia County (Orange City)" },
  { project_name: "SJR2C - Loop Trail - Spruce Creek", project_number: "25-21", location: "Loop Trail - Spruce Creek" },
  { project_name: "T5860 SR 9 (I-95)", project_number: "25-22 - CP", location: "SR 9 (I-95)" },
  { project_name: "T5861 A1A - Jimmy Buffet Hwy", project_number: "25-23 - CP", location: "A1A - Jimmy Buffet Hwy" },
  { project_name: "G2 & G11 Canal St Improvement", project_number: "25-24 - CP", location: "G2 & G11 Canal St" },
  { project_name: "NSB Corbin Park Stormwater Improvements", project_number: "26-01 - CP", location: "NSB Corbin Park" },
  { project_name: "Resurfacing Phase I", project_number: "26-02", location: "" },
  { project_name: "T5874 - SR 426 Winterhaven / Aloma", project_number: "26-03 - CP", location: "SR 426 Winterhaven / Aloma" },
  { project_name: "E58F7 - SR 5", project_number: "26-04", location: "SR 5" },
  { project_name: "Fillmore Ave Reconstruction", project_number: "26-05", location: "Fillmore Ave" },
  { project_name: "Knox McRae Master Pump Station", project_number: "26-06", location: "Knox McRae" },
  { project_name: "University High Parent Loop Ext", project_number: "26-07", location: "University High" },
  { project_name: "T5877 - SR 44 (from I-95 to Walker Dr)", project_number: "26-08 - CP", location: "SR 44 (from I-95 to Walker Dr)" },
  { project_name: "T5871 Sub to CARR", project_number: "26-09 - CP", location: "" },
];

export const CUSTOM_JOB_KEY = "__custom_job__";

export function findJob(projectNumber) {
  if (!projectNumber) return null;
  return JOB_LIBRARY.find((j) => j.project_number === projectNumber) || null;
}
