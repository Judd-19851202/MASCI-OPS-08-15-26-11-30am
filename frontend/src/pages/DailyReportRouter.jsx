// TRACK 23.1 · Route-level wrapper that picks V1 vs V3 Daily Report.
//
// Reads the `dr_v3` feature flag from the backend and renders the
// matching shell. While the flag is loading it renders nothing (blank
// screen for ~200 ms) so we never flash-of-V1 before promoting a pilot
// operator to V3. Every downstream (submit endpoint, ODS, PDF, email)
// is identical either way — the flag ONLY controls which React tree
// renders here.
import React from "react";
import NewDailyReportV3 from "@/pages/NewDailyReportV3";

export default function DailyReportRouter({ publicMode = false }) {
  return <NewDailyReportV3 publicMode={publicMode} />;
}
