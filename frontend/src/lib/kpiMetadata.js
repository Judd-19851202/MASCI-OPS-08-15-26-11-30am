function formatValue(value) {
  if (value === null || value === undefined || value === "") return null;
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === "object" ? JSON.stringify(item) : String(item))).join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, val]) => `${key}: ${typeof val === "object" ? JSON.stringify(val) : String(val)}`)
      .join(" · ");
  }
  return String(value);
}

export function buildKpiHelpContent(metadata, fallbackLabel = "Why this number?") {
  if (!metadata || typeof metadata !== "object") return null;

  const definition = formatValue(metadata.business_definition || metadata.definition);
  const source = formatValue(metadata.source_of_truth || metadata.source);
  const formula = formatValue(metadata.formula);
  const freshness = formatValue(metadata.freshness);
  const reason = formatValue(metadata.status_reason);

  const body = [
    definition,
    source ? `Source: ${source}` : null,
    formula ? `Formula: ${formula}` : null,
    freshness ? `Freshness: ${freshness}` : null,
    reason ? `Why it matters: ${reason}` : null,
  ].filter(Boolean).join(" ");

  if (!body) return null;
  return {
    label: metadata.kpi_name || fallbackLabel,
    body,
  };
}

export default buildKpiHelpContent;