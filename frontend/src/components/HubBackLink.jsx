import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";

/**
 * Auth-aware hub back-link. Routes to /admin when the user has an admin
 * token, /pm when they only have a PM token, /shop when they only have a
 * Shop token OR they are currently inside a /shop/* path (Track 13.30B
 * fix), / otherwise. Keeps the visible label honest so a PM never sees
 * "← Admin" in their own portal (which historically pushed them toward
 * /admin/login and was confusing).
 *
 * Also used to pick the logo home target via `useHubHome()` below.
 */
export default function HubBackLink({
  className = "inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide",
  testId = "hub-link",
}) {
  const { pathname } = useLocation();
  const admin = isAdmin();
  const pm = !admin && isPm();
  // Shop branch: respect explicit shop token OR any /shop/* current path.
  // Admin users browsing /shop/* still get /admin (consistent with PM rule).
  const shop = !admin && !pm && (isShop() || pathname.startsWith("/shop"));
  const to = admin ? "/admin" : pm ? "/pm" : shop ? "/shop" : "/";
  const label = admin ? "Admin" : pm ? "PM" : shop ? "Shop" : "Hub";
  return (
    <Link to={to} className={className} data-testid={testId}>
      <ArrowLeft className="w-4 h-4 mr-1" /> {label}
    </Link>
  );
}

/**
 * Route the logo lockup back to the user's own portal. Shared sub-pages
 * (inspections / meetings / etc.) used to hard-code `/admin` which, for
 * a PM, would try to load the Admin Hub and get bounced to /admin/login.
 */
export function useHubHome() {
  const { pathname } = useLocation();
  if (isAdmin()) return "/admin";
  if (isPm()) return "/pm";
  if (isShop() || pathname.startsWith("/shop")) return "/shop";
  return "/";
}
