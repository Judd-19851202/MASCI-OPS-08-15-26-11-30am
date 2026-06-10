/**
 * PmHomeRedirect.jsx — PM portal landing page redirector.
 *
 * Phase 4C (2026-02-10): `/pm` now lands directly on the PM Command
 * Center (single operational source of truth). The legacy PmHub
 * remains accessible at `/pm/hub` for tile-based navigation.
 */
import React from "react";
import { Navigate } from "react-router-dom";

export default function PmHomeRedirect() {
  return <Navigate to="/pm/command-center" replace />;
}
