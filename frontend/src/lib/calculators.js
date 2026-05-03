// Shared math + density data for the Material Calculators page at
// /field/calculators. All formulas follow the spec in the product brief.
//
// Density units: pounds per cubic foot (lb/ft³).
// All returned result fields are plain numbers — the page is responsible
// for rounding/displaying them. Division-by-zero returns 0, not NaN or
// Infinity, so the UI never shows garbage.

export const AGGREGATE_DENSITIES = [
  { key: "lime_rock", label: "Lime Rock Base", density: 120 },
  { key: "crushed_stone", label: "Crushed Stone", density: 100 },
  { key: "57_stone", label: "57 Stone", density: 95 },
  { key: "washed_shell", label: "Washed Shell", density: 85 },
  { key: "sand", label: "Sand", density: 100 },
  { key: "base_material", label: "Base Material", density: 120 },
  { key: "rap", label: "RAP (Recycled Asphalt)", density: 110 },
  { key: "custom", label: "Custom", density: 0 },
];

export const ASPHALT_DEFAULT_DENSITY = 145;
export const CONCRETE_DEFAULT_DENSITY = 145;

export function defaultDensityFor(materialKey) {
  const row = AGGREGATE_DENSITIES.find((r) => r.key === materialKey);
  return row && row.key !== "custom" ? row.density : 0;
}

/** Convert thickness to feet. Accepts "in" or "ft". */
export function thicknessToFeet(value, unit) {
  const v = Number(value) || 0;
  return unit === "ft" ? v : v / 12;
}

/** Round a number to N decimals, safe for NaN/Infinity. */
export function round(n, decimals = 2) {
  if (!Number.isFinite(n)) return 0;
  const f = Math.pow(10, decimals);
  return Math.round(n * f) / f;
}

function safeDiv(a, b) {
  return b > 0 ? a / b : 0;
}
void safeDiv;

/**
 * Aggregate calculator — length × width × thickness with density-based
 * weight and truck-load breakdown.
 */
export function calcAggregate({ length, width, thicknessValue, thicknessUnit, density, wastePct, truckCapTons }) {
  const L = Number(length) || 0;
  const W = Number(width) || 0;
  const T = thicknessToFeet(thicknessValue, thicknessUnit);
  const D = Number(density) || 0;
  const waste = Math.max(0, Number(wastePct) || 0) / 100;
  const cap = Math.max(0, Number(truckCapTons) || 0);

  const cubicFeet = L * W * T;
  const cubicYards = cubicFeet / 27;
  const pounds = cubicFeet * D;
  const tons = pounds / 2000;
  const tonsWithWaste = tons * (1 + waste);
  const truckLoads = cap > 0 ? Math.ceil(tonsWithWaste / cap) : 0;

  return {
    cubic_feet: round(cubicFeet),
    cubic_yards: round(cubicYards),
    tons: round(tons),
    tons_with_waste: round(tonsWithWaste),
    truck_loads: truckLoads,
  };
}

/**
 * Asphalt calculator — adds binder/aggregate weight splitting on top of
 * the aggregate math. Density defaults to 145 lb/ft³.
 */
export function calcAsphalt({ length, width, thicknessValue, thicknessUnit, density, wastePct, binderPct, truckCapTons }) {
  const agg = calcAggregate({ length, width, thicknessValue, thicknessUnit, density, wastePct, truckCapTons });
  const binderFraction = Math.min(1, Math.max(0, (Number(binderPct) || 0) / 100));
  const binderTons = agg.tons_with_waste * binderFraction;
  const aggregateTons = agg.tons_with_waste * (1 - binderFraction);
  return {
    ...agg,
    total_asphalt_tons: agg.tons_with_waste,
    binder_tons: round(binderTons),
    aggregate_tons: round(aggregateTons),
  };
}

/**
 * Concrete calculator — primarily cubic yards. Truck capacity is in CY
 * for the mixer. Optional coarse/fine aggregate percentage splits.
 */
export function calcConcrete({ length, width, thicknessValue, thicknessUnit, wastePct, mixerCapCy, coarseAggPct, fineAggPct }) {
  const L = Number(length) || 0;
  const W = Number(width) || 0;
  const T = thicknessToFeet(thicknessValue, thicknessUnit);
  const waste = Math.max(0, Number(wastePct) || 0) / 100;
  const cap = Math.max(0, Number(mixerCapCy) || 0);

  const cubicFeet = L * W * T;
  const cubicYards = cubicFeet / 27;
  const cubicYardsWithWaste = cubicYards * (1 + waste);
  const mixerLoads = cap > 0 ? Math.ceil(cubicYardsWithWaste / cap) : 0;

  const coarseFrac = Math.min(1, Math.max(0, (Number(coarseAggPct) || 0) / 100));
  const fineFrac = Math.min(1, Math.max(0, (Number(fineAggPct) || 0) / 100));
  const coarseCy = cubicYardsWithWaste * coarseFrac;
  const fineCy = cubicYardsWithWaste * fineFrac;

  return {
    cubic_feet: round(cubicFeet),
    cubic_yards: round(cubicYards),
    cubic_yards_with_waste: round(cubicYardsWithWaste),
    mixer_loads: mixerLoads,
    coarse_aggregate_cy: round(coarseCy),
    fine_aggregate_cy: round(fineCy),
  };
}

/**
 * Truck load calculator — accepts mixed units (tons/CY) and optionally
 * converts using a user-provided density.
 */
export function calcTruckLoads({ totalQty, totalUnit, truckCap, truckUnit, wastePct, density }) {
  const qty = Math.max(0, Number(totalQty) || 0);
  const cap = Math.max(0, Number(truckCap) || 0);
  const waste = Math.max(0, Number(wastePct) || 0) / 100;
  const D = Number(density) || 0;

  const adjusted = qty * (1 + waste);
  let normalizedQty = adjusted;

  if (totalUnit !== truckUnit) {
    // convert adjusted quantity into truckUnit using density
    if (totalUnit === "tons" && truckUnit === "cy") {
      // tons -> cubic yards: cy = (tons × 2000) / density / 27
      normalizedQty = D > 0 ? (adjusted * 2000) / D / 27 : 0;
    } else if (totalUnit === "cy" && truckUnit === "tons") {
      // cubic yards -> tons
      normalizedQty = (adjusted * 27 * D) / 2000;
    }
  }

  const whole = cap > 0 ? Math.floor(normalizedQty / cap) : 0;
  const remainder = cap > 0 ? normalizedQty - whole * cap : normalizedQty;
  const roundedUp = cap > 0 ? Math.ceil(normalizedQty / cap) : 0;

  return {
    adjusted_qty: round(adjusted, 3),
    normalized_qty: round(normalizedQty, 3),
    truck_loads: roundedUp,
    whole_loads: whole,
    partial_load_remaining: round(remainder, 3),
  };
}

/**
 * Yield / waste calculator — compare planned vs actual, derive yield %,
 * waste %, and recommend an adjusted order quantity.
 */
export function calcYieldWaste({ planned, actual, wastePct }) {
  const P = Number(planned) || 0;
  const A = Number(actual) || 0;
  const overrun = A - P;
  const yieldPct = P > 0 ? (A / P) * 100 : 0;
  const derivedWastePct = A > 0 ? ((A - P) / A) * 100 : 0; // overrun %
  const recommendedWaste = Math.max(0, Number(wastePct) || derivedWastePct);
  const recommendedOrder = P * (1 + recommendedWaste / 100);
  return {
    difference: round(overrun, 3),
    yield_pct: round(yieldPct, 2),
    waste_pct: round(derivedWastePct, 2),
    overrun: overrun >= 0 ? round(overrun, 3) : 0,
    underrun: overrun < 0 ? round(Math.abs(overrun), 3) : 0,
    recommended_order: round(recommendedOrder, 3),
  };
}

/**
 * Tons ↔ Cubic Yards conversion.
 *   Tons → CY: cy = (tons × 2000) / density / 27
 *   CY → Tons: tons = (cy × 27 × density) / 2000
 */
export function calcConversion({ quantity, direction, density }) {
  const Q = Number(quantity) || 0;
  const D = Number(density) || 0;

  if (direction === "tons_to_cy") {
    const cy = D > 0 ? (Q * 2000) / D / 27 : 0;
    return {
      converted: round(cy, 3),
      formula: `(${Q} × 2000) / ${D} / 27`,
      density_used: D,
      out_unit: "cubic yards",
    };
  }
  // cy_to_tons
  const tons = (Q * 27 * D) / 2000;
  return {
    converted: round(tons, 3),
    formula: `(${Q} × 27 × ${D}) / 2000`,
    density_used: D,
    out_unit: "tons",
  };
}
