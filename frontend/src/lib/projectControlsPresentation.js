const isFiniteNumber = (value) => Number.isFinite(Number(value));

const roundPercent = (value, digits = 0) => {
  if (!isFiniteNumber(value)) return null;
  return `${Number(value).toFixed(digits)}%`;
};

const formatMoney = (value) => (
  isFiniteNumber(value)
    ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`
    : "—"
);

const formatRatio = (value) => (
  isFiniteNumber(value)
    ? Number(value).toFixed(3)
    : "—"
);

const formatPercent = (value, digits = 1) => (
  isFiniteNumber(value)
    ? `${(Number(value) * 100).toFixed(digits)}%`
    : "—"
);

const METRIC_META = {
  bac: {
    primaryLabel: { en: "Approved budget", es: "Presupuesto aprobado" },
    technicalLabel: { en: "Budget at Completion (BAC)", es: "Presupuesto al completar (BAC)" },
    kind: "currency",
  },
  pv: {
    primaryLabel: { en: "Planned work value", es: "Valor del trabajo planificado" },
    technicalLabel: { en: "Planned Value (PV)", es: "Valor planificado (PV)" },
    kind: "currency",
  },
  ev: {
    primaryLabel: { en: "Value of work completed", es: "Valor del trabajo completado" },
    technicalLabel: { en: "Earned Value (EV)", es: "Valor ganado (EV)" },
    kind: "currency",
  },
  ac: {
    primaryLabel: { en: "Actual cost to date", es: "Costo real a la fecha" },
    technicalLabel: { en: "Actual Cost (AC)", es: "Costo real (AC)" },
    kind: "currency",
  },
  cv: {
    primaryLabel: { en: "Cost difference vs completed work", es: "Diferencia de costo vs trabajo completado" },
    technicalLabel: { en: "Cost Variance (CV)", es: "Variación de costo (CV)" },
    kind: "currency",
  },
  sv: {
    primaryLabel: { en: "Schedule difference vs plan", es: "Diferencia de avance vs plan" },
    technicalLabel: { en: "Schedule Variance (SV)", es: "Variación del cronograma (SV)" },
    kind: "currency",
  },
  cpi: {
    primaryLabel: { en: "Cost performance", es: "Desempeño de costo" },
    technicalLabel: { en: "Cost Performance Index (CPI)", es: "Índice de desempeño de costo (CPI)" },
    kind: "ratio",
  },
  spi: {
    primaryLabel: { en: "Schedule performance", es: "Desempeño del cronograma" },
    technicalLabel: { en: "Schedule Performance Index (SPI)", es: "Índice de desempeño del cronograma (SPI)" },
    kind: "ratio",
  },
  etc: {
    primaryLabel: { en: "Estimated cost to finish", es: "Costo estimado para terminar" },
    technicalLabel: { en: "Estimate to Complete (ETC)", es: "Estimado para completar (ETC)" },
    kind: "currency",
  },
  eac: {
    primaryLabel: { en: "Current forecast at completion", es: "Pronóstico actual al finalizar" },
    technicalLabel: { en: "Estimate at Completion (EAC)", es: "Estimado al completar (EAC)" },
    kind: "currency",
  },
  tcpi: {
    primaryLabel: { en: "Required cost efficiency to hit target", es: "Eficiencia de costo requerida para cumplir la meta" },
    technicalLabel: { en: "To-Complete Performance Index (TCPI)", es: "Índice de desempeño para completar (TCPI)" },
    kind: "ratio",
  },
  planned_percent: {
    primaryLabel: { en: "Planned progress", es: "Avance planificado" },
    technicalLabel: { en: "Planned progress percent", es: "Porcentaje de avance planificado" },
    kind: "percent",
  },
  earned_percent: {
    primaryLabel: { en: "Completed progress", es: "Avance completado" },
    technicalLabel: { en: "Earned progress percent", es: "Porcentaje de avance completado" },
    kind: "percent",
  },
};

const copy = (lang, en, es) => (lang === "es" ? es : en);

export function operatorBandLabel(value, lang = "en") {
  const key = String(value || "").trim().toLowerCase();
  const labels = {
    green: copy(lang, "On track", "En camino"),
    amber: copy(lang, "Watch closely", "Vigilar de cerca"),
    red: copy(lang, "Immediate attention", "Atención inmediata"),
    blocked: copy(lang, "Not enough current information", "No hay suficiente información actual"),
    missing: copy(lang, "Missing information", "Falta información"),
    stale: copy(lang, "Older information", "Información desactualizada"),
    watch: copy(lang, "Check soon", "Revisar pronto"),
    partial: copy(lang, "Review before using", "Revisar antes de usar"),
    review_required: copy(lang, "Review before using", "Revisar antes de usar"),
    insufficient_evidence: copy(lang, "Not enough current information", "No hay suficiente información actual"),
    ready: copy(lang, "Ready to use", "Listo para usar"),
    high: copy(lang, "High confidence", "Alta confianza"),
    medium: copy(lang, "Medium confidence", "Confianza media"),
  };
  return labels[key] || (value ? String(value).replaceAll("_", " ") : copy(lang, "Unknown", "Desconocido"));
}

export function measurementMethodLabel(value, lang = "en") {
  const key = String(value || "").trim().toLowerCase();
  if (key === "quantity_based") return copy(lang, "Installed quantity", "Cantidad instalada");
  if (key === "schedule_based") return copy(lang, "Approved progress", "Avance aprobado");
  if (key === "blocked") return copy(lang, "Waiting on evidence", "En espera de evidencia");
  return value ? String(value).replaceAll("_", " ") : "—";
}

function normalizeMetricKey(metricKey) {
  const source = String(metricKey || "").trim().toLowerCase();
  if (!source) return "";
  return source.startsWith("c8-") ? source.slice(3) : source.replace(/^portfolio\s+/, "");
}

function defaultUnavailable(metricKey, lang = "en") {
  const reasons = {
    cpi: copy(lang, "Cost performance cannot be trusted until earned work and actual cost are both available.", "El desempeño de costo no es confiable hasta que existan el trabajo ganado y el costo real."),
    spi: copy(lang, "Schedule performance cannot be trusted until planned work value and completed work value are both available.", "El desempeño del cronograma no es confiable hasta que existan el valor planificado y el valor completado."),
    tcpi: copy(lang, "The remaining budget target does not leave a valid denominator for this calculation.", "La meta de presupuesto restante no deja un denominador válido para este cálculo."),
    bac: copy(lang, "The approved budget has not been published for this view yet.", "El presupuesto aprobado aún no se ha publicado para esta vista."),
    pv: copy(lang, "Planned work value is blocked until the current baseline timing is available.", "El valor del trabajo planificado está bloqueado hasta que exista el cronograma base vigente."),
    ev: copy(lang, "Completed work value is blocked until approved quantity or approved progress is available.", "El valor del trabajo completado está bloqueado hasta que exista cantidad aprobada o avance aprobado."),
    ac: copy(lang, "Actual cost is blocked until linked cost evidence is available.", "El costo real está bloqueado hasta que exista evidencia de costo vinculada."),
    etc: copy(lang, "The remaining-cost outlook is not available yet.", "La proyección del costo restante aún no está disponible."),
    eac: copy(lang, "The finish-cost outlook is not available yet.", "La proyección del costo final aún no está disponible."),
  };
  return reasons[metricKey] || copy(lang, "Not enough current information.", "No hay suficiente información actual.");
}

function describeCurrencyMetric(metricKey, value, lang = "en") {
  const amount = formatMoney(value);
  const explanations = {
    bac: copy(lang, "The approved total budget for the work currently in scope.", "El presupuesto total aprobado para el trabajo actualmente dentro del alcance."),
    pv: copy(lang, "How much budget value should have been completed by now according to plan.", "Cuánto valor presupuestado debería haberse completado a esta fecha según el plan."),
    ev: copy(lang, "How much budget value the completed work has actually earned so far.", "Cuánto valor presupuestado ha ganado realmente el trabajo completado hasta ahora."),
    ac: copy(lang, "Recognized cost recorded so far for this work.", "El costo reconocido registrado hasta ahora para este trabajo."),
    etc: copy(lang, "What it is currently expected to cost to finish the remaining work.", "Lo que actualmente se espera que cueste terminar el trabajo restante."),
    eac: copy(lang, "Where total cost is trending if the current outlook holds.", "Dónde se perfila el costo total si se mantiene la proyección actual."),
  };
  return {
    primaryValue: amount,
    shortValue: amount,
    explanation: explanations[metricKey] || amount,
  };
}

function describeVariance(metricKey, value, lang = "en") {
  const numeric = Number(value);
  if (!isFiniteNumber(value)) {
    return {
      primaryValue: copy(lang, "Not enough current information", "No hay suficiente información actual"),
      shortValue: copy(lang, "Need more records", "Faltan registros"),
      explanation: defaultUnavailable(metricKey, lang),
    };
  }
  if (numeric === 0) {
    return {
      primaryValue: copy(lang, "On plan", "Según el plan"),
      shortValue: copy(lang, "On plan", "Según el plan"),
      explanation: metricKey === "cv"
        ? copy(lang, "Spending is aligned with the value of work completed.", "El gasto está alineado con el valor del trabajo completado.")
        : copy(lang, "Completed work is aligned with the planned work value.", "El trabajo completado está alineado con el valor del trabajo planificado."),
    };
  }
  if (metricKey === "cv") {
    return numeric > 0
      ? {
        primaryValue: copy(lang, `${formatMoney(numeric)} favorable`, `${formatMoney(numeric)} favorable`),
        shortValue: copy(lang, `${formatMoney(numeric)} favorable`, `${formatMoney(numeric)} favorable`),
        explanation: copy(lang, "Completed work is worth more than the cost recognized so far.", "El trabajo completado vale más que el costo reconocido hasta ahora."),
      }
      : {
        primaryValue: copy(lang, `${formatMoney(Math.abs(numeric))} over earned value`, `${formatMoney(Math.abs(numeric))} por encima del valor ganado`),
        shortValue: copy(lang, `${formatMoney(Math.abs(numeric))} over`, `${formatMoney(Math.abs(numeric))} por encima`),
        explanation: copy(lang, "The job has spent more than the value of work completed.", "El trabajo ha gastado más que el valor del trabajo completado."),
      };
  }
  return numeric > 0
    ? {
      primaryValue: copy(lang, `${formatMoney(numeric)} ahead of plan`, `${formatMoney(numeric)} por delante del plan`),
      shortValue: copy(lang, `${formatMoney(numeric)} ahead`, `${formatMoney(numeric)} delante`),
      explanation: copy(lang, "Completed work value is ahead of the planned work value for this point.", "El valor del trabajo completado está por delante del valor planificado a esta fecha."),
    }
    : {
      primaryValue: copy(lang, `${formatMoney(Math.abs(numeric))} behind plan`, `${formatMoney(Math.abs(numeric))} por detrás del plan`),
      shortValue: copy(lang, `${formatMoney(Math.abs(numeric))} behind`, `${formatMoney(Math.abs(numeric))} detrás`),
      explanation: copy(lang, "Completed work value is behind the planned work value for this point.", "El valor del trabajo completado está por detrás del valor planificado a esta fecha."),
    };
}

function describeCpi(value, lang = "en") {
  if (!isFiniteNumber(value) || Number(value) <= 0) {
    return {
      primaryValue: copy(lang, "Not enough current information", "No hay suficiente información actual"),
      shortValue: copy(lang, "Need more records", "Faltan registros"),
      explanation: defaultUnavailable("cpi", lang),
    };
  }
  const numeric = Number(value);
  const spentPerDollar = 1 / numeric;
  if (Math.abs(numeric - 1) < 0.0001) {
    return {
      primaryValue: copy(lang, "On plan", "Según el plan"),
      shortValue: copy(lang, "On plan", "Según el plan"),
      explanation: copy(lang, "For every $1.00 of work completed, about $1.00 has been spent.", "Por cada $1.00 de trabajo completado, se ha gastado aproximadamente $1.00."),
    };
  }
  if (numeric < 1) {
    const percent = (spentPerDollar - 1) * 100;
    return {
      primaryValue: copy(lang, `${roundPercent(percent)} more spent than value earned`, `${roundPercent(percent)} más gastado que valor ganado`),
      shortValue: copy(lang, `${roundPercent(percent)} over`, `${roundPercent(percent)} por encima`),
      explanation: copy(lang, `For every $1.00 of work completed, about $${spentPerDollar.toFixed(2)} has been spent.`, `Por cada $1.00 de trabajo completado, se ha gastado aproximadamente $${spentPerDollar.toFixed(2)}.`),
    };
  }
  const percent = (1 - spentPerDollar) * 100;
  return {
    primaryValue: copy(lang, `${roundPercent(percent)} less spent than value earned`, `${roundPercent(percent)} menos gastado que valor ganado`),
    shortValue: copy(lang, `${roundPercent(percent)} under`, `${roundPercent(percent)} por debajo`),
    explanation: copy(lang, `For every $1.00 of work completed, about $${spentPerDollar.toFixed(2)} has been spent.`, `Por cada $1.00 de trabajo completado, se ha gastado aproximadamente $${spentPerDollar.toFixed(2)}.`),
  };
}

function describeSpi(value, lang = "en") {
  if (!isFiniteNumber(value) || Number(value) < 0) {
    return {
      primaryValue: copy(lang, "Not enough current information", "No hay suficiente información actual"),
      shortValue: copy(lang, "Need more records", "Faltan registros"),
      explanation: defaultUnavailable("spi", lang),
    };
  }
  const numeric = Number(value);
  if (Math.abs(numeric - 1) < 0.0001) {
    return {
      primaryValue: copy(lang, "On plan", "Según el plan"),
      shortValue: copy(lang, "On plan", "Según el plan"),
      explanation: copy(lang, "Completed work is matching the work value planned for this point.", "El trabajo completado coincide con el valor planificado para esta fecha."),
    };
  }
  if (numeric < 1) {
    const percent = (1 - numeric) * 100;
    return {
      primaryValue: copy(lang, `${roundPercent(percent)} behind planned progress`, `${roundPercent(percent)} detrás del avance planificado`),
      shortValue: copy(lang, `${roundPercent(percent)} behind`, `${roundPercent(percent)} detrás`),
      explanation: copy(lang, `The job has earned about ${roundPercent(numeric * 100)} of the work value planned by this point.`, `El trabajo ha ganado aproximadamente ${roundPercent(numeric * 100)} del valor del trabajo planificado para esta fecha.`),
    };
  }
  const percent = (numeric - 1) * 100;
  return {
    primaryValue: copy(lang, `${roundPercent(percent)} ahead of planned progress`, `${roundPercent(percent)} por delante del avance planificado`),
    shortValue: copy(lang, `${roundPercent(percent)} ahead`, `${roundPercent(percent)} delante`),
    explanation: copy(lang, `The job has earned about ${roundPercent(numeric * 100)} of the work value planned by this point.`, `El trabajo ha ganado aproximadamente ${roundPercent(numeric * 100)} del valor del trabajo planificado para esta fecha.`),
  };
}

function describeTcpi(value, lang = "en") {
  if (!isFiniteNumber(value) || Number(value) <= 0) {
    return {
      primaryValue: copy(lang, "Not enough current information", "No hay suficiente información actual"),
      shortValue: copy(lang, "Need more records", "Faltan registros"),
      explanation: defaultUnavailable("tcpi", lang),
    };
  }
  const numeric = Number(value);
  if (numeric <= 1) {
    return {
      primaryValue: copy(lang, "Current pace can still meet target", "El ritmo actual todavía puede cumplir la meta"),
      shortValue: copy(lang, "Target still reachable", "La meta sigue al alcance"),
      explanation: copy(lang, `The remaining work needs cost efficiency of ${formatRatio(numeric)} or better to hit the active target.`, `El trabajo restante necesita una eficiencia de costo de ${formatRatio(numeric)} o mejor para cumplir la meta activa.`),
    };
  }
  return {
    primaryValue: copy(lang, "A better finish pace is required", "Se requiere un mejor ritmo de cierre"),
    shortValue: copy(lang, "Better pace required", "Se requiere mejor ritmo"),
    explanation: copy(lang, `The remaining work needs cost efficiency of ${formatRatio(numeric)} to hit the active target.`, `El trabajo restante necesita una eficiencia de costo de ${formatRatio(numeric)} para cumplir la meta activa.`),
  };
}

export function buildMetricPresentation(metricKey, value, { confidence, status } = {}, lang = "en") {
  const key = normalizeMetricKey(metricKey);
  const meta = METRIC_META[key] || {
    primaryLabel: { en: String(metricKey || "Measure"), es: String(metricKey || "Medida") },
    technicalLabel: { en: String(metricKey || "Measure"), es: String(metricKey || "Medida") },
    kind: "text",
  };
  const technicalValue = meta.kind === "currency"
    ? formatMoney(value)
    : meta.kind === "percent"
      ? formatPercent(value)
      : formatRatio(value);

  let summary = {
    primaryValue: technicalValue,
    shortValue: technicalValue,
    explanation: copy(lang, "Current approved reading for this measure.", "Lectura aprobada actual de esta medida."),
  };
  if (value == null || value === "") {
    summary = {
      primaryValue: copy(lang, "Not enough current information", "No hay suficiente información actual"),
      shortValue: copy(lang, "Need more records", "Faltan registros"),
      explanation: defaultUnavailable(key, lang),
    };
  } else if (key === "cpi") {
    summary = describeCpi(value, lang);
  } else if (key === "spi") {
    summary = describeSpi(value, lang);
  } else if (key === "cv" || key === "sv") {
    summary = describeVariance(key, value, lang);
  } else if (key === "tcpi") {
    summary = describeTcpi(value, lang);
  } else if (["bac", "pv", "ev", "ac", "etc", "eac"].includes(key)) {
    summary = describeCurrencyMetric(key, value, lang);
  } else if (["planned_percent", "earned_percent"].includes(key)) {
    summary = {
      primaryValue: formatPercent(value),
      shortValue: formatPercent(value),
      explanation: key === "planned_percent"
        ? copy(lang, "How much progress the plan expected by this point.", "Cuánto avance esperaba el plan para esta fecha.")
        : copy(lang, "How much progress has been approved as completed so far.", "Cuánto avance se ha aprobado como completado hasta ahora."),
    };
  }

  return {
    metricKey: key,
    primaryLabel: meta.primaryLabel[lang] || meta.primaryLabel.en,
    technicalLabel: meta.technicalLabel[lang] || meta.technicalLabel.en,
    technicalValue,
    primaryValue: summary.primaryValue,
    shortValue: summary.shortValue,
    explanation: summary.explanation,
    confidenceLabel: operatorBandLabel(confidence, lang),
    statusLabel: operatorBandLabel(status, lang),
  };
}

export function buildFinancialRows(financial = {}, lang = "en") {
  return ["bac", "pv", "ev", "ac", "eac", "cpi", "spi"].map((metricKey) => ({
    metricKey,
    presentation: buildMetricPresentation(metricKey, financial?.[metricKey], { confidence: financial?.confidence, status: financial?.readiness || financial?.status }, lang),
    coverage: financial?.coverage,
  }));
}

export function operatorSourceLabel(value, lang = "en") {
  const key = String(value || "").trim().toLowerCase();
  const labels = {
    c6: copy(lang, "Project performance update", "Actualización del desempeño del proyecto"),
    c7: copy(lang, "Forecast update", "Actualización del pronóstico"),
    c8: copy(lang, "Cost and earned-value update", "Actualización de costo y valor ganado"),
  };
  return labels[key] || copy(lang, "Project update", "Actualización del proyecto");
}
