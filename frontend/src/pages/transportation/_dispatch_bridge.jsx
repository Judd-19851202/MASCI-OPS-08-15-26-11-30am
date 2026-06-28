/**
 * TRACK 18.00 · Phase A · Operations group · Dispatch deep-link bridge.
 *
 * Strictly a navigation surface. It does NOT embed or replace any
 * dispatch board, dispatch command center, dispatch map, or
 * dispatch haul ledger. It exists so dispatchers, admins, and
 * leadership can launch into the existing /dispatch-portal/* live
 * surfaces from inside Transportation Operations.
 *
 * Dispatch URLs are unchanged. Dispatch lifecycle code untouched.
 */
import React from "react";
import { Link } from "react-router-dom";
import { ExternalLink, Truck, Map, BookOpen, Layers, UserRound } from "lucide-react";
import TransportationWorkspaceShell from "./TransportationWorkspaceShell";

const DISPATCH_LINKS = [
  {
    testid: "txops-dispatch-link-board",
    href: "/dispatch-portal/board",
    icon: Layers,
    title: "Dispatch Board",
    desc: "Live assignments + state machine. Primary dispatcher workspace.",
  },
  {
    testid: "txops-dispatch-link-command",
    href: "/dispatch-portal/command",
    icon: Truck,
    title: "Command Center",
    desc: "Operational command rail · broadcasts · driver/job/fleet boards.",
  },
  {
    testid: "txops-dispatch-link-map",
    href: "/dispatch-portal/map",
    icon: Map,
    title: "Live Operations Map",
    desc: "GPS · routes · proximity. Read-only situational awareness.",
  },
  {
    testid: "txops-dispatch-link-ledger",
    href: "/dispatch-portal/haul-ledger",
    icon: BookOpen,
    title: "Haul Ledger",
    desc: "Daily haul-cycle ledger and exports.",
  },
  {
    testid: "txops-dispatch-link-driverq",
    href: "/dispatch-portal/driver-qualification",
    icon: UserRound,
    title: "Driver Qualification",
    desc: "Dispatcher-side driver qualification view.",
  },
];

export default function DispatchBridgeWorkspace() {
  return (
    <TransportationWorkspaceShell
      workspace="Operations"
      title="Dispatch"
      subtitle="Dispatch is the operational system of record. Transportation Operations links into Dispatch — it never replaces it."
    >
      <section
        data-testid="txops-dispatch-bridge"
        className="grid grid-cols-1 md:grid-cols-2 gap-3"
      >
        {DISPATCH_LINKS.map((link) => (
          <a
            key={link.testid}
            href={link.href}
            data-testid={link.testid}
            className="block rounded-md border border-slate-200 bg-white hover:border-amber-300 hover:bg-amber-50 p-4 transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2 text-slate-900 font-medium">
                <link.icon className="h-4 w-4 text-slate-600" />
                {link.title}
              </div>
              <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <p className="text-xs text-slate-600">{link.desc}</p>
          </a>
        ))}
      </section>

      <div
        data-testid="txops-dispatch-bridge-note"
        className="text-[10px] uppercase tracking-wide text-slate-400"
      >
        Source · Dispatch portal · `/dispatch-portal/*` (preserved, unmodified)
      </div>
    </TransportationWorkspaceShell>
  );
}
