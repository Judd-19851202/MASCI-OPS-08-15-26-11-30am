// Track 19.31 · Shop Sidebar V2 domain map
//
// Sourced from the Shop HubV2 tile audit (Track 19.31 · Phase 1).
// All routes are ones that ALREADY exist in /app/frontend/src/App.js — no new
// routes introduced. This is a pure visual re-grouping of the Shop workflows
// operators already use daily.
//
// Follows the identical shape as Admin V2's and PM V2's domainMap.js (same
// Tier-1/Tier-2 model, same stripe-color contract, same findActiveDomainId
// helper) so an operator with Shop + Admin + PM tokens experiences the
// identical mental model on the sidebar in every portal.
//
// Asset Administrator lane (Historical Records) is emitted as a separate
// domain but filtered out for non-`is_asset_admin` users. Admins (via
// getAdminToken) always see it — same visibility rule as ShopHubV2 section 09
// established in Track 19.28.

import {
  Activity, Wrench, Truck, Fuel, Boxes, ClipboardList, ListTodo, Radar,
  ShieldCheck, GraduationCap, ClipboardCheck, Package, History, Archive,
  ShieldAlert, KeyRound, FileText, Layers, Calendar, HardHat,
} from "lucide-react";

// Domains a normal Shop user sees. Asset Administrator lane is appended
// conditionally by ShopSideNavV2 based on the runtime asset-admin flag.
export const DOMAINS_V2 = [
  {
    id: "recovery-attention",
    label: "Recovery & Attention",
    subline: "OOS · defects · active recovery · what needs Shop now.",
    stripe: "#dc2626", // red-600
    icon: Radar,
    routes: [
      { to: "/shop",                                   label: "Shop Command Center", desc: "Overview · live signals · daily rhythm.",           icon: Activity, end: true },
      { to: "/shop/fleet?focus_filter=oos",            label: "Out-of-Service",       desc: "OOS units awaiting recovery.",                       icon: ShieldAlert },
      { to: "/shop/fleet?focus_filter=defects",        label: "Open Defects",         desc: "Defects across the fleet.",                          icon: ShieldAlert },
      { to: "/shop/fleet?focus_filter=defect_open_units", label: "Units with Defects", desc: "Distinct units carrying open defects.",           icon: Truck },
      { to: "/shop/fleet?focus_filter=rts_pending",    label: "RTS Pending",          desc: "Units awaiting Return-To-Service verification.",     icon: ShieldCheck },
      { to: "/shop/fleet?focus_filter=defects_acked",  label: "Acknowledged Defects", desc: "Defects seen and being worked.",                     icon: ClipboardCheck },
    ],
  },
  {
    id: "work-assignments",
    label: "Work Assignments",
    subline: "Manager queue · my work · active recovery.",
    stripe: "#d97706", // amber-600
    icon: ClipboardList,
    routes: [
      { to: "/shop/manager/queue", label: "Manager Queue",    desc: "Route work · assign mechanics · triage.",          icon: ListTodo },
      { to: "/shop/me",            label: "My Assignments",   desc: "What's on my plate today.",                        icon: ClipboardList },
      { to: "/shop/equipment",     label: "Active Recovery",  desc: "Equipment currently being recovered.",              icon: Wrench },
    ],
  },
  {
    id: "fleet-equipment",
    label: "Fleet & Equipment",
    subline: "Per-unit visibility · pre-ops · history.",
    stripe: "#2563eb", // blue-600
    icon: Truck,
    routes: [
      { to: "/shop/fleet",         label: "Fleet Visibility", desc: "Per-unit DVIR + defect state.",                    icon: Truck },
      { to: "/shop/equipment",     label: "Equipment Pre-Ops", desc: "Pre-op inspection list.",                          icon: ClipboardCheck },
      { to: "/shop/units/history", label: "Unit History",     desc: "Per-unit lifetime archive.",                       icon: History },
    ],
  },
  {
    id: "preventive-maintenance",
    label: "Preventive Maintenance",
    subline: "PM schedules · templates · work orders.",
    stripe: "#7c3aed", // violet-600
    icon: Calendar,
    routes: [
      { to: "/shop/pm",              label: "PM Dashboard",   desc: "Scheduled maintenance signal.",                    icon: Calendar },
      { to: "/shop/pm/schedules",    label: "PM Schedules",   desc: "Recurring maintenance cadence per unit.",          icon: Calendar },
      { to: "/shop/pm/templates",    label: "PM Templates",   desc: "Reusable PM plan templates.",                      icon: Layers },
      { to: "/shop/pm/work-orders",  label: "Work Orders",    desc: "Active + completed PM work orders.",               icon: ClipboardList },
    ],
  },
  {
    id: "service-support",
    label: "Service & Support",
    subline: "Fuel · lube · service-truck reconciliation · trench repairs.",
    stripe: "#0d9488", // teal-600
    icon: Fuel,
    routes: [
      { to: "/shop/fuel-lube/new",                        label: "New Fuel/Lube Visit",       desc: "Log a fuel or lube visit.",                        icon: Fuel },
      { to: "/shop/fuel-lube",                            label: "Fuel/Lube Records",         desc: "Submitted visit archive.",                         icon: Archive },
      { to: "/shop/service-truck-reconciliation/new",     label: "New Truck Reconciliation",  desc: "Reconcile a service-truck day.",                   icon: ClipboardList },
      { to: "/shop/service-truck-reconciliation",         label: "Reconciliation Records",    desc: "Truck-day variance archive.",                      icon: Archive },
      { to: "/shop/trench-safety-repairs",                label: "Trench Safety Repairs",     desc: "Trench asset repair queue.",                       icon: HardHat },
    ],
  },
  {
    id: "asset-care",
    label: "Asset Care",
    subline: "Asset Care & Readiness workspace.",
    stripe: "#64748b", // slate-500
    icon: Boxes,
    routes: [
      { to: "/shop/asset-care", label: "Asset Care & Readiness", desc: "Lifecycle · condition · readiness signals.", icon: Boxes },
    ],
  },
];

// Asset Administrator lane — appended to the sidebar only when the runtime
// asset-admin flag is true (masci.is_asset_admin === "true"), or an admin
// token is present. Matches the Track 19.28 visibility rule on ShopHubV2's
// Section 09.
export const ASSET_ADMIN_DOMAIN = {
  id: "asset-admin",
  label: "Asset Administrator",
  subline: "Historical records · classify · approve.",
  stripe: "#0891b2", // cyan-600
  icon: KeyRound,
  routes: [
    { to: "/hr/historical-records/intake",   label: "Records Intake",     desc: "Upload signed acknowledgements · PPE · tools.",       icon: FileText },
    { to: "/hr/historical-records/queue",    label: "Records Queue",      desc: "Approve · reject · reassign staged Asset-lane records.", icon: ClipboardCheck },
    { to: "/hr/historical-records/batches",  label: "Bulk Historical Intake", desc: "Many files · one session · one lane.",             icon: Package },
  ],
};

export const FOOTER_RAIL_V2 = [
  { to: "/tasks",       label: "My Tasks",    desc: "Action items across all domains.",  icon: ClipboardCheck },
  { to: "/guidance",    label: "Training Center",    desc: "How-to guides and troubleshooting.",       icon: GraduationCap },
];

// Returns the domain id whose routes contain the given pathname, or null.
export function findActiveDomainId(pathname, domains = DOMAINS_V2) {
  if (!pathname) return null;
  const bare = pathname.split("?")[0];
  const exact = domains.find((d) =>
    d.routes.some((r) => {
      const routeBare = r.to.split("?")[0];
      return r.end ? bare === routeBare : bare === routeBare || bare.startsWith(routeBare + "/");
    })
  );
  return exact ? exact.id : null;
}
