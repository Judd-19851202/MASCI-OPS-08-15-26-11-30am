// Track 19.32 · Transportation / Fleet Sidebar V2 visual metadata.
//
// This file DOES NOT duplicate the Transportation route list. The
// authoritative list is `TX_OPS_NAV_GROUPS` in `_shared.jsx` (used by
// the existing top-strip TransportationSubNav). This file only adds
// Sidebar V2 visual metadata (stripe color · subline · display icon)
// keyed by the same `group.key` values.
//
// Keeping it separate preserves the single source of truth for routes
// and permission gating (`visibleTxOpsNavGroups()`) while letting us
// evolve the Sidebar V2 visual language independently.

import {
  Radar, Truck, UserRound, ShieldCheck, Activity, Shield,
} from "lucide-react";

// Map from group.key (defined in TX_OPS_NAV_GROUPS) → Sidebar V2 chrome.
// If a new group is added to TX_OPS_NAV_GROUPS without a matching entry
// here, the sidebar falls back to a neutral slate stripe + default icon.
export const TX_DOMAIN_META = {
  overview: {
    stripe: "#dc2626", // red-600
    icon: Radar,
    subline: "Mission Control · what needs Transportation now.",
  },
  operations: {
    stripe: "#d97706", // amber-600
    icon: Truck,
    subline: "Dispatch · live operations · fleet visibility.",
  },
  people: {
    stripe: "#2563eb", // blue-600
    icon: UserRound,
    subline: "Drivers · carriers · qualifications.",
  },
  compliance: {
    stripe: "#0d9488", // teal-600
    icon: ShieldCheck,
    subline: "Compliance · orientation · academy.",
  },
  intelligence: {
    stripe: "#7c3aed", // violet-600
    icon: Activity,
    subline: "Intelligence · automation · cleanup.",
  },
  administration: {
    stripe: "#475569", // slate-600
    icon: Shield,
    subline: "Reports · audit trail · admin-only.",
  },
};

export const TX_DOMAIN_DEFAULT_META = {
  stripe: "#64748b",
  icon: Truck,
  subline: "",
};
