import React, { useMemo, useState } from "react";
import {
  Calculator,
  Layers,
  Truck,
  Droplet,
  BarChart3,
  Repeat,
  Save,
  RotateCcw,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InformationCard } from "@/components/CanonicalCard";
import { SectionHeading } from "@/components/SectionHeading";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { HelpTipBlock } from "@/components/HelpTip";
import { PortalShell } from "@/design-system/PortalShell";
import { cn } from "@/lib/utils";
import {
  AGGREGATE_DENSITIES,
  ASPHALT_DEFAULT_DENSITY,
  defaultDensityFor,
  calcAggregate,
  calcAsphalt,
  calcConcrete,
  calcTruckLoads,
  calcYieldWaste,
  calcConversion,
} from "@/lib/calculators";

/**
 * MaterialCalculators — single-page, tab-driven Field tool at
 * /field/calculators. Six calculators share the same page-header,
 * footer, and save-calculation flow so there's one screen to learn.
 *
 * Language: driven 100% by the global LangToggle. No local toggle,
 * no duplicate translate button.
 */
export default function MaterialCalculators() {
  const { t, lang } = useT();
  const [active, setActive] = useState("aggregate");

  const tabs = [
    { key: "aggregate", label: t("Aggregate"), icon: Layers },
    { key: "asphalt", label: t("Asphalt"), icon: Droplet },
    { key: "concrete", label: t("Concrete"), icon: Calculator },
    { key: "truck_load", label: t("Truck Load"), icon: Truck },
    { key: "yield_waste", label: t("Yield / Waste"), icon: BarChart3 },
    { key: "conversion", label: t("Tons ↔ CY"), icon: Repeat },
  ];
  const activeTab = tabs.find((tab) => tab.key === active);

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Field"
      pageTitle={t("Material Calculators")}
      homeHref="/field/calculators"
      backHref="/field"
      showBack
      showSearch={false}
      showNotifications={false}
      showPortalSwitcher={false}
      showSignOut={false}
    >
      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-8 sm:py-10">
        <InformationCard
          icon={Calculator}
          tone="amber"
          eyebrow={t("Field tools")}
          title={t("Material Calculators")}
          description={t("Fast field math for aggregate, asphalt, concrete, truck loads, yield, waste, and tons-to-cubic-yard conversions.")}
          testId="calc-summary"
          className="mb-8"
        />

        <SectionHeading
          index="01"
          title={t("Choose a calculator")}
          subtitle={t("Open one estimating tool at a time, then calculate, reset, or save the result when you are ready.")}
          testId="calc-tabs-heading"
        />

        <div
          className="wp17-panel mb-6 flex flex-wrap gap-2 p-3 sm:p-4 print:hidden"
          data-testid="calc-tabs"
        >
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = active === tab.key;
            return (
              <Button
                key={tab.key}
                type="button"
                onClick={() => setActive(tab.key)}
                data-testid={`calc-tab-${tab.key}`}
                variant={isActive ? "default" : "outline"}
                size="sm"
                className={cn(
                  "min-h-[2.75rem] gap-2 font-mono text-[11px] uppercase tracking-[0.15em]",
                  isActive ? "shadow-[0_16px_28px_rgba(15,23,42,0.14)]" : "bg-white"
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </Button>
            );
          })}
        </div>

        {activeTab ? (
          <p className="mb-6 text-sm text-slate-600" data-testid="calc-active-tool-label">
            {t("Current tool")}: <span className="font-semibold text-slate-900">{activeTab.label}</span>
          </p>
        ) : null}

        {active === "aggregate" && <AggregatePanel lang={lang} t={t} />}
        {active === "asphalt" && <AsphaltPanel lang={lang} t={t} />}
        {active === "concrete" && <ConcretePanel lang={lang} t={t} />}
        {active === "truck_load" && <TruckLoadPanel lang={lang} t={t} />}
        {active === "yield_waste" && <YieldWastePanel lang={lang} t={t} />}
        {active === "conversion" && <ConversionPanel lang={lang} t={t} />}

        {/* iter215 · pre-job planning coaching · public scope. Lives
            below the active calculator so it never blocks the work, but
            sits in the user's path before they sign a PO. */}
        <div className="mt-8 max-w-3xl">
          <HelpTipBlock formKey="material-calculator" showCounter />
        </div>
        {active === "yield_waste" && (
          <div className="mt-3 max-w-3xl">
            <HelpTipBlock formKey="material-calculator.waste" />
          </div>
        )}

        <p className="text-[11px] text-slate-500 mt-10 italic border-t border-slate-200 pt-4 max-w-3xl">
          {t(
            "Calculations are estimates for planning purposes only. Actual quantities may vary based on field conditions, material density, moisture, compaction, yield, mix design, waste, and project specifications.",
          )}
        </p>
      </div>
    </PortalShell>
  );
}

/* --------------------------------------------------------------------- */
/* Shared small components                                                */
/* --------------------------------------------------------------------- */

function Field({ label, children, testid, hint }) {
  return (
    <label className="block" data-testid={testid}>
      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
        {label}
      </span>
      <div className="mt-1">{children}</div>
      {hint && <p className="text-[11px] text-slate-500 mt-1">{hint}</p>}
    </label>
  );
}

function NumberInput({ value, onChange, min = 0, step = "any", testid, placeholder }) {
  return (
    <Input
      type="number"
      inputMode="decimal"
      min={min}
      step={step}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-12 text-base"
      data-testid={testid}
      placeholder={placeholder}
    />
  );
}

function Result({ label, value, unit, testid, strong }) {
  return (
    <div
      className={
        "rounded border-2 px-3 py-3 " +
        (strong ? "border-amber-500 bg-amber-50" : "border-slate-300 bg-slate-50")
      }
      data-testid={testid}
    >
      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-600 font-bold">
        {label}
      </div>
      <div className="font-display text-xl sm:text-2xl font-black text-slate-900 tabular-nums mt-0.5">
        {value}{" "}
        <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-slate-500 font-normal">
          {unit}
        </span>
      </div>
    </div>
  );
}

function CalculatorPanel({ title, testId, children }) {
  return (
    <Card className="wp17-card-family--form-section" data-testid={testId}>
      <CardHeader className="pb-4">
        <CardTitle className="text-xl sm:text-2xl">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {children}
      </CardContent>
    </Card>
  );
}

function ThicknessRow({ value, setValue, unit, setUnit, t, testid }) {
  return (
    <div className="flex items-end gap-2">
      <div className="flex-1">
        <Field label={t("Thickness")} testid={`${testid}-field`}>
          <NumberInput value={value} onChange={setValue} testid={`${testid}-value`} />
        </Field>
      </div>
      <div>
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold block mb-1">
          {t("Unit")}
        </span>
        <div className="inline-flex rounded border-2 border-slate-300 overflow-hidden">
          <button
            type="button"
            className={
              "px-3 h-12 font-mono text-xs font-bold uppercase tracking-[0.15em] " +
              (unit === "in" ? "bg-slate-900 text-white" : "bg-white text-slate-600")
            }
            onClick={() => setUnit("in")}
            data-testid={`${testid}-unit-in`}
          >
            {t("inches")}
          </button>
          <button
            type="button"
            className={
              "px-3 h-12 font-mono text-xs font-bold uppercase tracking-[0.15em] " +
              (unit === "ft" ? "bg-slate-900 text-white" : "bg-white text-slate-600")
            }
            onClick={() => setUnit("ft")}
            data-testid={`${testid}-unit-ft`}
          >
            {t("feet")}
          </button>
        </div>
      </div>
    </div>
  );
}

function ActionRow({ onCalc, onReset, onSave, saved, t, testidPrefix }) {
  return (
    <div className="flex flex-wrap gap-2 mt-4">
      <Button
        onClick={onCalc}
        className="h-11 px-5 bg-amber-600 hover:bg-amber-700 text-white font-bold"
        data-testid={`${testidPrefix}-calc`}
      >
        <Calculator className="w-4 h-4 mr-2" />
        {t("Calculate")}
      </Button>
      <Button
        onClick={onReset}
        variant="outline"
        className="h-11 px-5 font-bold"
        data-testid={`${testidPrefix}-reset`}
      >
        <RotateCcw className="w-4 h-4 mr-2" />
        {t("Reset")}
      </Button>
      <Button
        onClick={onSave}
        variant="outline"
        className="h-11 px-5 font-bold border-slate-400"
        data-testid={`${testidPrefix}-save`}
        disabled={saved}
      >
        {saved ? (
          <>
            <CheckCircle2 className="w-4 h-4 mr-2 text-emerald-600" />
            {t("Saved")}
          </>
        ) : (
          <>
            <Save className="w-4 h-4 mr-2" />
            {t("Save Calculation")}
          </>
        )}
      </Button>
    </div>
  );
}

async function saveRun(type, lang, inputs, outputs, jobInfo = {}) {
  try {
    await api.post("/calculators/save", {
      calculator_type: type,
      language: lang || "en",
      inputs,
      outputs,
      ...jobInfo,
    });
    return true;
  } catch {
    return false;
  }
}

function validate({ t, rules }) {
  for (const r of rules) {
    if (!r.ok) {
      toast.error(r.msg || t("Check your inputs — required values must be greater than 0."));
      return false;
    }
  }
  return true;
}

/* --------------------------------------------------------------------- */
/* 1. Aggregate                                                           */
/* --------------------------------------------------------------------- */

function AggregatePanel({ lang, t }) {
  const [length, setLength] = useState("");
  const [width, setWidth] = useState("");
  const [thickness, setThickness] = useState("");
  const [thicknessUnit, setThicknessUnit] = useState("in");
  const [material, setMaterial] = useState("lime_rock");
  const [density, setDensity] = useState(defaultDensityFor("lime_rock"));
  const [wastePct, setWastePct] = useState(10);
  const [truckCap, setTruckCap] = useState(20);
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  function onMaterialChange(k) {
    setMaterial(k);
    if (k !== "custom") setDensity(defaultDensityFor(k));
    else setDensity("");
  }

  function run() {
    if (!validate({
      t,
      rules: [
        { ok: Number(length) > 0, msg: t("Length must be greater than 0.") },
        { ok: Number(width) > 0, msg: t("Width must be greater than 0.") },
        { ok: Number(thickness) > 0, msg: t("Thickness must be greater than 0.") },
        { ok: Number(density) > 0, msg: t("Density must be greater than 0.") },
      ],
    })) return;
    const r = calcAggregate({
      length, width, thicknessValue: thickness, thicknessUnit, density, wastePct, truckCapTons: truckCap,
    });
    setResult(r);
    setSaved(false);
  }
  function reset() {
    setLength(""); setWidth(""); setThickness(""); setThicknessUnit("in");
    setMaterial("lime_rock"); setDensity(defaultDensityFor("lime_rock"));
    setWastePct(10); setTruckCap(20); setResult(null); setSaved(false);
  }
  async function onSave() {
    if (!result) { toast.info(t("Calculate first, then save.")); return; }
    const ok = await saveRun("aggregate", lang, {
      length, width, thickness, thicknessUnit, material, density, wastePct, truck_capacity_tons: truckCap,
    }, result);
    if (ok) { setSaved(true); toast.success(t("Saved.")); }
    else toast.error(t("Could not save. Try again."));
  }

  return (
    <CalculatorPanel title={t("Aggregate Calculator")} testId="calc-panel-aggregate">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <Field label={t("Length (ft)")}><NumberInput value={length} onChange={setLength} testid="agg-length" /></Field>
        <Field label={t("Width (ft)")}><NumberInput value={width} onChange={setWidth} testid="agg-width" /></Field>
        <ThicknessRow value={thickness} setValue={setThickness} unit={thicknessUnit} setUnit={setThicknessUnit} t={t} testid="agg-thickness" />
        <Field label={t("Material")}>
          <select
            value={material}
            onChange={(e) => onMaterialChange(e.target.value)}
            className="h-12 w-full border-2 border-slate-300 rounded px-3 text-base bg-white"
            data-testid="agg-material"
          >
            {AGGREGATE_DENSITIES.map((d) => (
              <option key={d.key} value={d.key}>{t(d.label)}</option>
            ))}
          </select>
        </Field>
        <Field label={t("Density (lb/ft³)")} hint={t("Override if mix/lab report differs.")}>
          <NumberInput value={density} onChange={setDensity} testid="agg-density" />
        </Field>
        <Field label={t("Waste %")}>
          <NumberInput value={wastePct} onChange={setWastePct} testid="agg-waste" />
        </Field>
        <Field label={t("Truck capacity (tons)")}>
          <NumberInput value={truckCap} onChange={setTruckCap} testid="agg-truck-cap" />
        </Field>
      </div>

      <ActionRow onCalc={run} onReset={reset} onSave={onSave} saved={saved} t={t} testidPrefix="agg" />

      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-6" data-testid="agg-results">
          <Result label={t("Cubic Feet")} value={result.cubic_feet} unit="ft³" testid="agg-cf" />
          <Result label={t("Cubic Yards")} value={result.cubic_yards} unit={t("cy")} testid="agg-cy" />
          <Result label={t("Tons")} value={result.tons} unit={t("tons")} testid="agg-tons" />
          <Result label={t("Tons + Waste")} value={result.tons_with_waste} unit={t("tons")} testid="agg-tons-waste" strong />
          <Result label={t("Truck Loads")} value={result.truck_loads} unit={t("loads")} testid="agg-loads" strong />
        </div>
      )}
    </CalculatorPanel>
  );
}

/* --------------------------------------------------------------------- */
/* 2. Asphalt                                                             */
/* --------------------------------------------------------------------- */

function AsphaltPanel({ lang, t }) {
  const [length, setLength] = useState("");
  const [width, setWidth] = useState("");
  const [thickness, setThickness] = useState("");
  const [thicknessUnit, setThicknessUnit] = useState("in");
  const [density, setDensity] = useState(ASPHALT_DEFAULT_DENSITY);
  const [wastePct, setWastePct] = useState(5);
  const [binderPct, setBinderPct] = useState(5);
  const [truckCap, setTruckCap] = useState(20);
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  function run() {
    if (!validate({
      t,
      rules: [
        { ok: Number(length) > 0, msg: t("Length must be greater than 0.") },
        { ok: Number(width) > 0, msg: t("Width must be greater than 0.") },
        { ok: Number(thickness) > 0, msg: t("Thickness must be greater than 0.") },
        { ok: Number(density) > 0, msg: t("Density must be greater than 0.") },
      ],
    })) return;
    setResult(calcAsphalt({
      length, width, thicknessValue: thickness, thicknessUnit, density, wastePct, binderPct, truckCapTons: truckCap,
    }));
    setSaved(false);
  }
  function reset() {
    setLength(""); setWidth(""); setThickness(""); setThicknessUnit("in");
    setDensity(ASPHALT_DEFAULT_DENSITY); setWastePct(5); setBinderPct(5); setTruckCap(20);
    setResult(null); setSaved(false);
  }
  async function onSave() {
    if (!result) { toast.info(t("Calculate first, then save.")); return; }
    const ok = await saveRun("asphalt", lang, {
      length, width, thickness, thicknessUnit, density, wastePct, binderPct, truck_capacity_tons: truckCap,
    }, result);
    if (ok) { setSaved(true); toast.success(t("Saved.")); }
    else toast.error(t("Could not save. Try again."));
  }

  return (
    <CalculatorPanel title={t("Asphalt Calculator")} testId="calc-panel-asphalt">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <Field label={t("Length (ft)")}><NumberInput value={length} onChange={setLength} testid="asp-length" /></Field>
        <Field label={t("Width (ft)")}><NumberInput value={width} onChange={setWidth} testid="asp-width" /></Field>
        <ThicknessRow value={thickness} setValue={setThickness} unit={thicknessUnit} setUnit={setThicknessUnit} t={t} testid="asp-thickness" />
        <Field label={t("Density (lb/ft³)")} hint={t("Standard HMA ≈ 145 lb/ft³.")}>
          <NumberInput value={density} onChange={setDensity} testid="asp-density" />
        </Field>
        <Field label={t("Waste %")}><NumberInput value={wastePct} onChange={setWastePct} testid="asp-waste" /></Field>
        <Field label={t("Asphalt binder %")}>
          <NumberInput value={binderPct} onChange={setBinderPct} testid="asp-binder" />
        </Field>
        <Field label={t("Truck capacity (tons)")}>
          <NumberInput value={truckCap} onChange={setTruckCap} testid="asp-truck-cap" />
        </Field>
      </div>
      <ActionRow onCalc={run} onReset={reset} onSave={onSave} saved={saved} t={t} testidPrefix="asp" />
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-6" data-testid="asp-results">
          <Result label={t("Cubic Feet")} value={result.cubic_feet} unit="ft³" testid="asp-cf" />
          <Result label={t("Cubic Yards")} value={result.cubic_yards} unit={t("cy")} testid="asp-cy" />
          <Result label={t("Total Asphalt")} value={result.total_asphalt_tons} unit={t("tons")} testid="asp-total" strong />
          <Result label={t("Truck Loads")} value={result.truck_loads} unit={t("loads")} testid="asp-loads" strong />
          <Result label={t("Binder")} value={result.binder_tons} unit={t("tons")} testid="asp-binder-t" />
          <Result label={t("Aggregate in Mix")} value={result.aggregate_tons} unit={t("tons")} testid="asp-agg-t" />
          <Result label={t("Base Tons (no waste)")} value={result.tons} unit={t("tons")} testid="asp-tons-base" />
          <Result label={t("Tons + Waste")} value={result.tons_with_waste} unit={t("tons")} testid="asp-tons-waste" />
        </div>
      )}
    </CalculatorPanel>
  );
}

/* --------------------------------------------------------------------- */
/* 3. Concrete                                                            */
/* --------------------------------------------------------------------- */

function ConcretePanel({ lang, t }) {
  const [length, setLength] = useState("");
  const [width, setWidth] = useState("");
  const [thickness, setThickness] = useState("");
  const [thicknessUnit, setThicknessUnit] = useState("in");
  const [wastePct, setWastePct] = useState(10);
  const [mixerCap, setMixerCap] = useState(10);
  const [coarsePct, setCoarsePct] = useState("");
  const [finePct, setFinePct] = useState("");
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  function run() {
    if (!validate({
      t,
      rules: [
        { ok: Number(length) > 0, msg: t("Length must be greater than 0.") },
        { ok: Number(width) > 0, msg: t("Width must be greater than 0.") },
        { ok: Number(thickness) > 0, msg: t("Thickness must be greater than 0.") },
      ],
    })) return;
    setResult(calcConcrete({
      length, width, thicknessValue: thickness, thicknessUnit, wastePct, mixerCapCy: mixerCap, coarseAggPct: coarsePct, fineAggPct: finePct,
    }));
    setSaved(false);
  }
  function reset() {
    setLength(""); setWidth(""); setThickness(""); setThicknessUnit("in");
    setWastePct(10); setMixerCap(10); setCoarsePct(""); setFinePct("");
    setResult(null); setSaved(false);
  }
  async function onSave() {
    if (!result) { toast.info(t("Calculate first, then save.")); return; }
    const ok = await saveRun("concrete", lang, {
      length, width, thickness, thicknessUnit, wastePct, mixer_capacity_cy: mixerCap, coarse_agg_pct: coarsePct, fine_agg_pct: finePct,
    }, result);
    if (ok) { setSaved(true); toast.success(t("Saved.")); }
    else toast.error(t("Could not save. Try again."));
  }

  return (
    <CalculatorPanel title={t("Concrete Calculator")} testId="calc-panel-concrete">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <Field label={t("Length (ft)")}><NumberInput value={length} onChange={setLength} testid="con-length" /></Field>
        <Field label={t("Width (ft)")}><NumberInput value={width} onChange={setWidth} testid="con-width" /></Field>
        <ThicknessRow value={thickness} setValue={setThickness} unit={thicknessUnit} setUnit={setThicknessUnit} t={t} testid="con-thickness" />
        <Field label={t("Waste %")}><NumberInput value={wastePct} onChange={setWastePct} testid="con-waste" /></Field>
        <Field label={t("Mixer capacity (cy)")} hint={t("Typical ready-mix truck ≈ 10 cy.")}>
          <NumberInput value={mixerCap} onChange={setMixerCap} testid="con-mixer" />
        </Field>
        <Field label={t("Coarse aggregate % (optional)")}>
          <NumberInput value={coarsePct} onChange={setCoarsePct} testid="con-coarse" />
        </Field>
        <Field label={t("Fine aggregate % (optional)")}>
          <NumberInput value={finePct} onChange={setFinePct} testid="con-fine" />
        </Field>
      </div>
      <ActionRow onCalc={run} onReset={reset} onSave={onSave} saved={saved} t={t} testidPrefix="con" />
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-6" data-testid="con-results">
          <Result label={t("Cubic Feet")} value={result.cubic_feet} unit="ft³" testid="con-cf" />
          <Result label={t("Cubic Yards")} value={result.cubic_yards} unit={t("cy")} testid="con-cy" />
          <Result label={t("CY + Waste")} value={result.cubic_yards_with_waste} unit={t("cy")} testid="con-cy-waste" strong />
          <Result label={t("Mixer Loads")} value={result.mixer_loads} unit={t("loads")} testid="con-loads" strong />
          {Number(result.coarse_aggregate_cy) > 0 && (
            <Result label={t("Coarse Aggregate")} value={result.coarse_aggregate_cy} unit={t("cy")} testid="con-coarse-cy" />
          )}
          {Number(result.fine_aggregate_cy) > 0 && (
            <Result label={t("Fine Aggregate")} value={result.fine_aggregate_cy} unit={t("cy")} testid="con-fine-cy" />
          )}
        </div>
      )}
    </CalculatorPanel>
  );
}

/* --------------------------------------------------------------------- */
/* 4. Truck Load                                                          */
/* --------------------------------------------------------------------- */

function TruckLoadPanel({ lang, t }) {
  const [totalQty, setTotalQty] = useState("");
  const [totalUnit, setTotalUnit] = useState("tons");
  const [truckCap, setTruckCap] = useState("");
  const [truckUnit, setTruckUnit] = useState("tons");
  const [wastePct, setWastePct] = useState(0);
  const [density, setDensity] = useState(120);
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  const needsDensity = totalUnit !== truckUnit;

  function run() {
    const rules = [
      { ok: Number(totalQty) > 0, msg: t("Enter a quantity greater than 0.") },
      { ok: Number(truckCap) > 0, msg: t("Truck capacity must be greater than 0.") },
    ];
    if (needsDensity) rules.push({ ok: Number(density) > 0, msg: t("Density required for unit conversion.") });
    if (!validate({ t, rules })) return;
    setResult(calcTruckLoads({ totalQty, totalUnit, truckCap, truckUnit, wastePct, density }));
    setSaved(false);
  }
  function reset() {
    setTotalQty(""); setTotalUnit("tons"); setTruckCap(""); setTruckUnit("tons");
    setWastePct(0); setDensity(120); setResult(null); setSaved(false);
  }
  async function onSave() {
    if (!result) { toast.info(t("Calculate first, then save.")); return; }
    const ok = await saveRun("truck_load", lang, {
      totalQty, totalUnit, truckCap, truckUnit, wastePct, density,
    }, result);
    if (ok) { setSaved(true); toast.success(t("Saved.")); }
    else toast.error(t("Could not save. Try again."));
  }

  return (
    <CalculatorPanel title={t("Truck Load Calculator")} testId="calc-panel-truck-load">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <Field label={t("Total material needed")}>
          <NumberInput value={totalQty} onChange={setTotalQty} testid="tl-qty" />
        </Field>
        <Field label={t("Unit")}>
          <select value={totalUnit} onChange={(e) => setTotalUnit(e.target.value)}
            className="h-12 w-full border-2 border-slate-300 rounded px-3 text-base bg-white" data-testid="tl-unit">
            <option value="tons">{t("tons")}</option>
            <option value="cy">{t("cubic yards")}</option>
          </select>
        </Field>
        <Field label={t("Truck capacity")}>
          <NumberInput value={truckCap} onChange={setTruckCap} testid="tl-cap" />
        </Field>
        <Field label={t("Truck capacity unit")}>
          <select value={truckUnit} onChange={(e) => setTruckUnit(e.target.value)}
            className="h-12 w-full border-2 border-slate-300 rounded px-3 text-base bg-white" data-testid="tl-cap-unit">
            <option value="tons">{t("tons")}</option>
            <option value="cy">{t("cubic yards")}</option>
          </select>
        </Field>
        <Field label={t("Waste %")}>
          <NumberInput value={wastePct} onChange={setWastePct} testid="tl-waste" />
        </Field>
        {needsDensity && (
          <Field label={t("Density (lb/ft³) for conversion")}>
            <NumberInput value={density} onChange={setDensity} testid="tl-density" />
          </Field>
        )}
      </div>
      <ActionRow onCalc={run} onReset={reset} onSave={onSave} saved={saved} t={t} testidPrefix="tl" />
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-6" data-testid="tl-results">
          <Result label={t("Adjusted Qty")} value={result.adjusted_qty} unit={t(totalUnit === "tons" ? "tons" : "cy")} testid="tl-adjusted" />
          <Result label={t("Qty in Truck Unit")} value={result.normalized_qty} unit={t(truckUnit === "tons" ? "tons" : "cy")} testid="tl-normalized" />
          <Result label={t("Truck Loads")} value={result.truck_loads} unit={t("loads")} testid="tl-loads" strong />
          <Result label={t("Partial Remaining")} value={result.partial_load_remaining} unit={t(truckUnit === "tons" ? "tons" : "cy")} testid="tl-partial" />
        </div>
      )}
    </CalculatorPanel>
  );
}

/* --------------------------------------------------------------------- */
/* 5. Yield / Waste                                                       */
/* --------------------------------------------------------------------- */

function YieldWastePanel({ lang, t }) {
  const [planned, setPlanned] = useState("");
  const [actual, setActual] = useState("");
  const [unit, setUnit] = useState("tons");
  const [wastePct, setWastePct] = useState("");
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  function run() {
    if (!validate({
      t,
      rules: [
        { ok: Number(planned) > 0, msg: t("Planned must be greater than 0.") },
        { ok: Number(actual) >= 0, msg: t("Actual must be 0 or greater.") },
      ],
    })) return;
    setResult(calcYieldWaste({ planned, actual, wastePct }));
    setSaved(false);
  }
  function reset() {
    setPlanned(""); setActual(""); setUnit("tons"); setWastePct(""); setResult(null); setSaved(false);
  }
  async function onSave() {
    if (!result) { toast.info(t("Calculate first, then save.")); return; }
    const ok = await saveRun("yield_waste", lang, { planned, actual, unit, wastePct }, result);
    if (ok) { setSaved(true); toast.success(t("Saved.")); }
    else toast.error(t("Could not save. Try again."));
  }

  return (
    <CalculatorPanel title={t("Yield / Waste Factor")} testId="calc-panel-yield-waste">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <Field label={t("Planned quantity")}>
          <NumberInput value={planned} onChange={setPlanned} testid="yw-planned" />
        </Field>
        <Field label={t("Actual installed quantity")}>
          <NumberInput value={actual} onChange={setActual} testid="yw-actual" />
        </Field>
        <Field label={t("Unit")}>
          <select value={unit} onChange={(e) => setUnit(e.target.value)}
            className="h-12 w-full border-2 border-slate-300 rounded px-3 text-base bg-white" data-testid="yw-unit">
            <option value="tons">{t("tons")}</option>
            <option value="cy">{t("cubic yards")}</option>
            <option value="cf">{t("cubic feet")}</option>
          </select>
        </Field>
        <Field label={t("Target waste % (optional override)")}>
          <NumberInput value={wastePct} onChange={setWastePct} testid="yw-waste" />
        </Field>
      </div>
      <ActionRow onCalc={run} onReset={reset} onSave={onSave} saved={saved} t={t} testidPrefix="yw" />
      {result && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-6" data-testid="yw-results">
          <Result label={t("Difference")} value={result.difference} unit={t(unit === "tons" ? "tons" : unit === "cy" ? "cy" : "cf")} testid="yw-diff" />
          <Result label={t("Yield %")} value={result.yield_pct + "%"} unit="" testid="yw-yield" strong />
          <Result label={t("Waste %")} value={result.waste_pct + "%"} unit="" testid="yw-wastepct" />
          <Result label={t("Overrun")} value={result.overrun} unit={t(unit === "tons" ? "tons" : unit === "cy" ? "cy" : "cf")} testid="yw-overrun" />
          <Result label={t("Underrun")} value={result.underrun} unit={t(unit === "tons" ? "tons" : unit === "cy" ? "cy" : "cf")} testid="yw-underrun" />
          <Result label={t("Recommended Order")} value={result.recommended_order} unit={t(unit === "tons" ? "tons" : unit === "cy" ? "cy" : "cf")} testid="yw-rec" strong />
        </div>
      )}
    </CalculatorPanel>
  );
}

/* --------------------------------------------------------------------- */
/* 6. Tons ↔ Cubic Yards Conversion                                       */
/* --------------------------------------------------------------------- */

function ConversionPanel({ lang, t }) {
  const [direction, setDirection] = useState("tons_to_cy");
  const [quantity, setQuantity] = useState("");
  const [material, setMaterial] = useState("lime_rock");
  const [density, setDensity] = useState(defaultDensityFor("lime_rock"));
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);

  function onMaterialChange(k) {
    setMaterial(k);
    if (k !== "custom") setDensity(defaultDensityFor(k));
    else setDensity("");
  }

  const fromUnit = useMemo(() => (direction === "tons_to_cy" ? t("tons") : t("cubic yards")), [direction, t]);

  function run() {
    if (!validate({
      t,
      rules: [
        { ok: Number(quantity) > 0, msg: t("Quantity must be greater than 0.") },
        { ok: Number(density) > 0, msg: t("Density must be greater than 0.") },
      ],
    })) return;
    setResult(calcConversion({ quantity, direction, density }));
    setSaved(false);
  }
  function reset() {
    setDirection("tons_to_cy"); setQuantity(""); setMaterial("lime_rock");
    setDensity(defaultDensityFor("lime_rock")); setResult(null); setSaved(false);
  }
  async function onSave() {
    if (!result) { toast.info(t("Calculate first, then save.")); return; }
    const ok = await saveRun("conversion", lang, { direction, quantity, material, density }, result);
    if (ok) { setSaved(true); toast.success(t("Saved.")); }
    else toast.error(t("Could not save. Try again."));
  }

  return (
    <CalculatorPanel title={t("Tons ↔ Cubic Yards Conversion")} testId="calc-panel-conversion">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <Field label={t("Direction")}>
          <select value={direction} onChange={(e) => setDirection(e.target.value)}
            className="h-12 w-full border-2 border-slate-300 rounded px-3 text-base bg-white" data-testid="conv-direction">
            <option value="tons_to_cy">{t("Tons → Cubic Yards")}</option>
            <option value="cy_to_tons">{t("Cubic Yards → Tons")}</option>
          </select>
        </Field>
        <Field label={`${t("Quantity")} (${fromUnit})`}>
          <NumberInput value={quantity} onChange={setQuantity} testid="conv-qty" />
        </Field>
        <Field label={t("Material")}>
          <select value={material} onChange={(e) => onMaterialChange(e.target.value)}
            className="h-12 w-full border-2 border-slate-300 rounded px-3 text-base bg-white" data-testid="conv-material">
            {AGGREGATE_DENSITIES.map((d) => (
              <option key={d.key} value={d.key}>{t(d.label)}</option>
            ))}
          </select>
        </Field>
        <Field label={t("Density (lb/ft³)")}>
          <NumberInput value={density} onChange={setDensity} testid="conv-density" />
        </Field>
      </div>
      <ActionRow onCalc={run} onReset={reset} onSave={onSave} saved={saved} t={t} testidPrefix="conv" />
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 mt-6" data-testid="conv-results">
          <Result label={t("Result")} value={result.converted} unit={t(result.out_unit)} testid="conv-result" strong />
          <Result label={t("Formula")} value={result.formula} unit="" testid="conv-formula" />
          <Result label={t("Density used")} value={result.density_used} unit="lb/ft³" testid="conv-density-used" />
        </div>
      )}
    </CalculatorPanel>
  );
}
