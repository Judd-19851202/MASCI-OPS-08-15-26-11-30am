// Track 19.54 · Operational Guidance System (OGS).
//
// Universal mapping from OI product_id → operational owners.
// Purely presentational — role names surface on the Guidance Card's
// "Responsible Roles" section. Reflects the Track 19.51 audit's
// portal-by-portal ownership matrix; NOT a new permission engine.
//
// If a product is not listed the Guidance Card falls back to
// ["Operations"] which is the safe universal owner.

export const PRODUCT_RESPONSIBLE_ROLES = {
  safety_morning_digest:     ["Safety Director", "Superintendent"],
  incident_intelligence:     ["Safety Director", "Operations Manager"],
  shop_intelligence:         ["Shop Manager", "Fleet Manager"],
  fleet_intelligence:        ["Fleet Manager", "Shop Manager"],
  transportation_intelligence: ["Transportation Manager", "Dispatcher"],
  hr_intelligence:           ["HR Director", "Operations Manager"],
  training_intelligence:     ["HR Director", "Safety Director"],
  project_intelligence:      ["Project Manager", "Superintendent"],
  corporate_intelligence:    ["Executive", "COO"],
  weekly_operations_digest:  ["COO", "Operations Manager"],
  executive_operations_brief:["CEO", "Executive"],
};

// Universal deep-links for a product. Points at the existing
// Guidance Center article route (if any) and the Cockpit drill-down.
// Zero new routes — every URL below already exists in the app.
export const PRODUCT_DEEP_LINKS = {
  safety_morning_digest: [
    { label: "Open Safety Hub", to: "/safety-portal" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  incident_intelligence: [
    { label: "Open Safety Hub", to: "/safety-portal" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  shop_intelligence: [
    { label: "Open Shop Hub", to: "/shop" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  fleet_intelligence: [
    { label: "Open Fleet Visibility", to: "/shop/fleet" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  transportation_intelligence: [
    { label: "Open Dispatch Cockpit", to: "/dispatch-portal/command" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  hr_intelligence: [
    { label: "Open HR Hub", to: "/hr" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  training_intelligence: [
    { label: "Open HR Hub", to: "/hr" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  project_intelligence: [
    { label: "Open PM Command Center", to: "/pm/command-center" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  corporate_intelligence: [
    { label: "Open Admin Mission Control", to: "/admin" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  weekly_operations_digest: [
    { label: "Open Admin Mission Control", to: "/admin" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
  executive_operations_brief: [
    { label: "Open Leadership", to: "/leadership" },
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ],
};

export function rolesFor(productId) {
  return PRODUCT_RESPONSIBLE_ROLES[productId] || ["Operations"];
}

export function deepLinksFor(productId) {
  return PRODUCT_DEEP_LINKS[productId] || [
    { label: "Open OI Cockpit", to: "/admin/operational-intelligence" },
  ];
}
