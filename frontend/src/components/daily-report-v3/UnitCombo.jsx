import React from "react";
import { useT } from "@/lib/i18n";

// TRACK 23.4B · Materials · unit picklist (searchable + custom entry).
//
// Uses a native `<datalist>` to keep the mobile keyboard fast, iOS
// safe, and zero-JS-cost. Common heavy-civil units are pre-listed;
// operators can also type any custom unit (stored verbatim as
// `unit` on the material row + surfaced as `unit_snapshot` for
// downstream reporting).
export const DEFAULT_MATERIAL_UNITS = [
  { code: "TN",   label: "Tons" },
  { code: "CY",   label: "Cubic Yards" },
  { code: "LD",   label: "Loads" },
  { code: "EA",   label: "Each" },
  { code: "LF",   label: "Linear Feet" },
  { code: "SY",   label: "Square Yards" },
  { code: "GAL",  label: "Gallons" },
  { code: "TL",   label: "Truckloads" },
  { code: "TON",  label: "Ton" },
  { code: "SF",   label: "Square Feet" },
  { code: "CF",   label: "Cubic Feet" },
  { code: "BAG",  label: "Bag" },
  { code: "PAIR", label: "Pair" },
  { code: "LOT",  label: "Lot" },
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
