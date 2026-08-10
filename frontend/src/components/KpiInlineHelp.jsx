import React from "react";
import { HelpTip } from "@/components/ui/HelpTip";
import { buildKpiHelpContent } from "@/lib/kpiMetadata";

export function KpiInlineHelp({ metadata, fallbackLabel, testId }) {
  const help = buildKpiHelpContent(metadata, fallbackLabel);
  if (!help) return null;
  return <HelpTip label={help.label} body={help.body} testId={testId} />;
}

export default KpiInlineHelp;