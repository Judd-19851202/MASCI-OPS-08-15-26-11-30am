/**
 * PmHomeRedirect.jsx — PM portal landing page redirector.
 *
 * Wave 2 repair (2026-07-30): `/pm` returns to the approved PM home
 * denominator at `/pm/hub`. The deeper PM Command Center remains
 * reachable at `/pm/command-center`.
 */
import React from "react";
import { Navigate } from "react-router-dom";

export default function PmHomeRedirect() {
  return <Navigate to="/pm/hub" replace />;
}
