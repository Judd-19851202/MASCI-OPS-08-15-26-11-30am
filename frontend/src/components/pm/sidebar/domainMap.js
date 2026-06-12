// Phase IV-BETA.1 — PM Sidebar V2 domain map
//
// Sourced from /app/memory/PM_INFORMATION_PRIORITY_MAP.json — 6 domains, 23 routes.
// All routes are ones that ALREADY exist in /app/frontend/src/App.js — no new
// routes introduced this phase.
//
// Follows the identical shape as Admin V2's domainMap.js (same Tier-1/Tier-2
// model, same stripe-color contract, same findActiveDomainId helper) so that
// the cross-portal mental model is identical for operators with both tokens.

import {
  Activity, Briefcase, ClipboardList, ClipboardCheck, Users, Camera, UserCheck,
  Wrench, Truck, FileText, Box, AlertOctagon, ShieldCheck,
  Mail, KeyRound, FileImage, GraduationCap, Building2,
  NotebookPen, ListTodo,
} from "lucide-react";

export const DOMAINS_V2 = [
  {
    id: "project-operations",
    label: "Project Operations",
    subline: "Field activity across your assigned projects.",
    stripe: "#dc2626", // red-600
    icon: Activity,
    routes: [
      { to: "/pm",                   label: "Overview",          desc: "Today's signal across your projects.",         icon: Briefcase, end: true },
      { to: "/pm/jobs",              label: "Jobs",              desc: "Jobs assigned to you (read-only).",            icon: Building2 },
      { to: "/pm/daily",             label: "Daily Reports",     desc: "Field production, manpower, progress.",        icon: ClipboardList },
      { to: "/pm/inspections",       label: "Inspections",       desc: "Field safety and quality checks.",             icon: ClipboardCheck },
      { to: "/pm/meetings",          label: "Meetings",          desc: "Pre-shift, toolbox, project meetings.",        icon: Users },
      { to: "/pm/field-leadership",  label: "Field Leadership",  desc: "Crew documentation across your projects.",     icon: UserCheck },
      { to: "/pm/odr",               label: "Operational Daily Records", desc: "PM read-only consumption · today's risk picture.", icon: NotebookPen },
      { to: "/pm/photos",            label: "Job Photos",        desc: "Field photos by job and week.",                icon: Camera },
    ],
  },
  {
    id: "financials-cost",
    label: "Financials & Cost",
    subline: "Purchase orders, change exposure, budget signals.",
    stripe: "#2563eb", // blue-600
    icon: ClipboardCheck,
    routes: [
      { to: "/po-requests",       label: "PO Requests",       desc: "Pending approvals · receipts · spend.",        icon: ClipboardCheck },
      { to: "/project-health",    label: "Project Health",    desc: "Operational friction by job.",                 icon: Activity },
      { to: "/asset-transfers",   label: "Asset Transfers",   desc: "Equipment movement and lifecycle.",            icon: Truck },
    ],
  },
  {
    id: "field-coordination",
    label: "Field Coordination",
    subline: "Fleet, pre-op, suppliers, people.",
    stripe: "#d97706", // amber-600
    icon: Truck,
    routes: [
      { to: "/pm/fleet",     label: "Equipment Fleet",  desc: "Master roster and parts catalog (read-only).",  icon: Wrench },
      { to: "/pm/equipment", label: "Pre-Op Checks",    desc: "Today's pre-shift checks across your fleet.",  icon: ClipboardCheck },
      { to: "/pm/suppliers", label: "Suppliers",        desc: "Approved supplier roster (read-only).",        icon: Truck },
      { to: "/pm/people",    label: "People",           desc: "Employee master (read-only).",                 icon: Users },
    ],
  },
  {
    id: "document-control",
    label: "Document Control",
    subline: "JHAs, trench boxes, posters.",
    stripe: "#7c3aed", // violet-600
    icon: FileText,
    routes: [
      { to: "/pm/jha-plans",    label: "JHA Plans",    desc: "Job hazard analyses by asset and task.",       icon: FileText },
      { to: "/pm/trench-boxes", label: "Trench Boxes", desc: "Box specifications and inspections.",          icon: Box },
      { to: "/pm/posters",      label: "Site Posters", desc: "Printable JHA, trench box, inspection QRs.",   icon: FileImage },
    ],
  },
  {
    id: "compliance-risk",
    label: "Compliance & Risk",
    subline: "Incidents, QA/QC, crew compliance.",
    stripe: "#ea580c", // orange-600
    icon: AlertOctagon,
    routes: [
      { to: "/pm/incidents",          label: "Incidents",         desc: "Open and recent safety/quality deviations.",   icon: AlertOctagon },
      { to: "/pm/qaqc",               label: "QA/QC",             desc: "Quality records across your projects.",        icon: ShieldCheck },
      { to: "/pm/crew-compliance",    label: "Crew Compliance",   desc: "Training, PPE, CAPA exposure, expirations.",   icon: Users },
    ],
  },
  {
    id: "system-communications",
    label: "System & Communications",
    subline: "Sign-in credentials.",
    stripe: "#475569", // slate-600
    icon: Mail,
    routes: [
      { to: "/pm/change-password", label: "Change Password",   desc: "Rotate your sign-in credentials.",            icon: KeyRound },
    ],
  },
];

export const FOOTER_RAIL_V2 = [
  { to: "/tasks",    label: "My Tasks",  desc: "Action items across all domains.", icon: ClipboardCheck },
  { to: "/guidance", label: "Guidance",  desc: "Doctrine, SOPs, training.",        icon: GraduationCap },
];

// Returns the domain id whose routes contain the given pathname, or null.
// Identical shape to Admin V2's findActiveDomainId — preserves cross-portal
// mental model.
export function findActiveDomainId(pathname) {
  if (!pathname) return null;
  const exact = DOMAINS_V2.find((d) =>
    d.routes.some((r) => (r.end ? pathname === r.to : pathname.startsWith(r.to)))
  );
  return exact ? exact.id : null;
}
