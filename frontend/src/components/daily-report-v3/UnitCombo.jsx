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
  { code: "TON",  label: "Tons" },
  { code: "CY",   label: "Cubic Yards" },
  { code: "LF",   label: "Linear Feet" },
  { code: "SY",   label: "Square Yards" },
  { code: "EA",   label: "Each" },
  { code: "ACRE", label: "Acres" },
  { code: "OTHER", label: "Loads" },
  { code: "OTHER", label: "Truckloads" },
  { code: "OTHER", label: "Gallons" },
  { code: "OTHER", label: "Square Feet" },
  { code: "OTHER", label: "Cubic Feet" },
  { code: "OTHER", label: "Bag" },
  { code: "OTHER", label: "Pair" },
  { code: "OTHER", label: "Lot" },
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

  const handleChange = (e) => {
    const raw = e.target.value;
    onChange?.(raw);
    // If the user picked a preset (matches a label or code), notify.
    const match = DEFAULT_MATERIAL_UNITS.find(
      (u) =>
        u.label.toLowerCase() === raw.toLowerCase() ||
        u.code.toLowerCase() === raw.toLowerCase(),
    );
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
          <option key={u.code} value={u.label}>
            {u.code}
          </option>
        ))}
      </datalist>
    </>
  );
}
