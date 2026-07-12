import React from "react";
import { useT } from "@/lib/i18n";

// TRACK 23.4B · Materials · unit picklist (searchable + custom entry).
//
// TRACK 26.02 · P0 recovery — the option `value` now carries the
// canonical CODE (matching backend `daily_reports.py::_UNIT_LABEL_TO_CODE`
// + Pydantic `unit: str`). The dropdown surface shows "CY — Cubic
// Yards" so operators still see the friendly label but the field
// value is the canonical code. Free-text units continue to work
// because a `<datalist>` is not a `<select>`.
export const DEFAULT_MATERIAL_UNITS = [
  { code: "LF", label: "Linear Feet", search: ["LF", "Linear Feet", "Linear Foot", "Linear Ft"] },
  { code: "SY", label: "Square Yards", search: ["SY", "Square Yards", "Square Yard", "Sq Yd"] },
  { code: "CY", label: "Cubic Yards", search: ["CY", "Cubic Yards", "Cubic Yard", "Cu Yd"] },
  { code: "TON", label: "Tons", search: ["TON", "Tons", "Ton"] },
  { code: "EA", label: "Each", search: ["EA", "Each"] },
  { code: "ACRE", label: "Acres", search: ["ACRE", "Acres", "Acre"] },
  { code: "OTHER", label: "Loads", search: ["Loads", "Load", "Truckloads", "Gallons", "Square Feet", "Cubic Feet", "Bag", "Pair", "Lot"] },
];

let _idSeed = 0;
function useDatalistId(prefix) {
  const [id] = React.useState(() => `${prefix}-${++_idSeed}`);
  return id;
}

export function UnitCombo({
  value,
  onChange,
  onPick,
  placeholder,
  testId,
  className = "",
}) {
  const { t } = useT();
  const listId = useDatalistId("dr-v3-unit");
  const ph = placeholder != null ? placeholder : t("Unit");

  const resolveMatch = (raw) => {
    const needle = (raw || "").trim().toLowerCase();
    if (!needle) return null;
    return DEFAULT_MATERIAL_UNITS.find((u) =>
      [u.code, u.label, ...(u.search || [])].some((token) => token.toLowerCase() === needle),
    ) || null;
  };

  const handleChange = (e) => {
    const raw = e.target.value;
    onChange?.(raw);
    const match = resolveMatch(raw);
    if (match) onPick?.(match);
  };

  return (
    <>
      <input
        type="text"
        list={listId}
        value={value ?? ""}
        onChange={handleChange}
        placeholder={ph}
        spellCheck={false}
        className={
          "w-full min-w-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm " +
          className
        }
        data-testid={testId}
        autoComplete="off"
      />
      <datalist id={listId}>
        {DEFAULT_MATERIAL_UNITS.map((u) => (
          <option key={`${u.code}-${u.label}`} value={`${u.code} — ${u.label}`}>
            {(u.search || []).join(" · ")}
          </option>
        ))}
      </datalist>
    </>
  );
}
