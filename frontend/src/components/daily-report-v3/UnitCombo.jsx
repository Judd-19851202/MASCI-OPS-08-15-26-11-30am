import React from "react";
import { Check, ChevronDown } from "lucide-react";
import { useT } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";
import { useCmdkTouchGuard } from "@/lib/useCmdkTouchGuard";
import { preventAutoFocusOnTouch } from "@/lib/pickerTouchFocus";

export const DEFAULT_MATERIAL_UNITS = [
  { code: "EA", label: "Each", category: "Count", search: ["EA", "Each"] },
  { code: "LF", label: "Linear Feet", category: "Length", search: ["LF", "Linear Feet", "Linear Foot", "Linear Ft"] },
  { code: "FT", label: "Feet", category: "Length", search: ["FT", "Feet", "Foot"] },
  { code: "MI", label: "Miles", category: "Length", search: ["MI", "Miles", "Mile"] },
  { code: "SF", label: "Square Feet", category: "Area", search: ["SF", "Square Feet", "Square Foot", "Sq Ft"] },
  { code: "SY", label: "Square Yards", category: "Area", search: ["SY", "Square Yards", "Square Yard", "Sq Yd"] },
  { code: "AC", label: "Acres", category: "Area", search: ["AC", "Acre", "Acres"] },
  { code: "CY", label: "Cubic Yards", category: "Volume", search: ["CY", "Cubic Yards", "Cubic Yard", "Cu Yd"] },
  { code: "YD", label: "Yards", category: "Volume", search: ["YD", "Yards", "Yard"] },
  { code: "CF", label: "Cubic Feet", category: "Volume", search: ["CF", "Cubic Feet", "Cubic Foot", "Cu Ft"] },
  { code: "LB", label: "Pounds", category: "Weight", search: ["LB", "Pounds", "Pound"] },
  { code: "TON", label: "Tons", category: "Weight", search: ["TON", "Tons", "Ton"] },
  { code: "LOAD", label: "Loads", category: "Load-Based", search: ["LOAD", "Loads", "Load"] },
  { code: "TRIP", label: "Trips", category: "Load-Based", search: ["TRIP", "Trips", "Trip"] },
  { code: "DELIVERY", label: "Deliveries", category: "Load-Based", search: ["DELIVERY", "Deliveries", "Delivery"] },
  { code: "TRUCKLOAD", label: "Truckloads", category: "Load-Based", search: ["TRUCKLOAD", "TRUCK_LOAD", "Truckloads", "Truckload"] },
  { code: "ROLL_OFF", label: "Roll-Off Containers", category: "Load-Based", search: ["ROLL_OFF", "Roll Off", "Roll-Off", "Roll-Off Containers"] },
  { code: "DUMPSTER", label: "Dumpsters", category: "Load-Based", search: ["DUMPSTER", "Dumpsters", "Dumpster"] },
  { code: "GAL", label: "Gallons", category: "Liquids", search: ["GAL", "Gallons", "Gallon"] },
  { code: "L", label: "Liters", category: "Liquids", search: ["L", "Liter", "Liters"] },
  { code: "LF_PIPE", label: "LF Pipe", category: "Pipe", search: ["LF Pipe", "LF_PIPE", "Pipe"] },
  { code: "JOINT", label: "Joint", category: "Pipe", search: ["JOINT", "Joint", "Joints"] },
  { code: "SECTION", label: "Section", category: "Pipe", search: ["SECTION", "Section", "Sections"] },
  { code: "TON_ASPHALT", label: "TON Asphalt", category: "Paving", search: ["TON Asphalt", "TON_ASPHALT", "Asphalt"] },
  { code: "SY_MILLING", label: "SY Milling", category: "Paving", search: ["SY Milling", "SY_MILLING", "Milling"] },
  { code: "SY_TACK", label: "SY Tack", category: "Paving", search: ["SY Tack", "SY_TACK", "Tack"] },
  { code: "CY_CONCRETE", label: "CY Concrete", category: "Concrete", search: ["CY Concrete", "CY_CONCRETE", "Concrete"] },
  { code: "VALVE", label: "Valve", category: "Utilities", search: ["VALVE", "Valve", "Valves"] },
  { code: "STRUCTURE", label: "Structure", category: "Utilities", search: ["STRUCTURE", "Structure", "Structures"] },
  { code: "MANHOLE", label: "Manhole", category: "Utilities", search: ["MANHOLE", "Manhole", "Manholes"] },
  { code: "CATCH_BASIN", label: "Catch Basin", category: "Utilities", search: ["CATCH_BASIN", "Catch Basin", "Catch Basins"] },
  { code: "INLET", label: "Inlet", category: "Utilities", search: ["INLET", "Inlet", "Inlets"] },
  { code: "BOX", label: "Box", category: "General", search: ["BOX", "Box", "Boxes"] },
  { code: "SIGN", label: "Sign", category: "Traffic", search: ["SIGN", "Sign", "Signs"] },
  { code: "POLE", label: "Pole", category: "Traffic", search: ["POLE", "Pole", "Poles"] },
  { code: "DEVICE", label: "Device", category: "Traffic", search: ["DEVICE", "Device", "Devices"] },
  { code: "TREE", label: "Tree", category: "Vegetation", search: ["TREE", "Tree", "Trees"] },
  { code: "STUMP", label: "Stump", category: "Vegetation", search: ["STUMP", "Stump", "Stumps"] },
  { code: "SHRUB", label: "Shrub", category: "Vegetation", search: ["SHRUB", "Shrub", "Shrubs"] },
  { code: "PAIR", label: "Pair", category: "General", search: ["PAIR", "Pair", "Pairs"] },
  { code: "SET", label: "Set", category: "General", search: ["SET", "Set", "Sets"] },
  { code: "ROLL", label: "Roll", category: "General", search: ["ROLL", "Roll", "Rolls"] },
  { code: "BUNDLE", label: "Bundle", category: "General", search: ["BUNDLE", "Bundle", "Bundles"] },
  { code: "PALLET", label: "Pallet", category: "General", search: ["PALLET", "Pallet", "Pallets"] },
  { code: "OTHER", label: "Other", category: "General", search: ["OTHER", "Other"] },
];

const GROUP_ORDER = [
  "Count", "Length", "Area", "Volume", "Weight", "Load-Based", "Liquids",
  "Pipe", "Paving", "Concrete", "Utilities", "Traffic", "Vegetation", "General",
];

const groupedUnits = GROUP_ORDER.map((category) => ({
  category,
  items: DEFAULT_MATERIAL_UNITS.filter((u) => u.category === category),
})).filter((group) => group.items.length > 0);

export function UnitCombo({
  value,
  selectedCode,
  onChange,
  onPick,
  placeholder,
  testId,
  className = "",
}) {
  const { t } = useT();
  const [open, setOpen] = React.useState(false);
  const ph = placeholder != null ? placeholder : t("Unit");
  const selected = DEFAULT_MATERIAL_UNITS.find((u) => u.code === selectedCode) || null;
  const { commitHandlersFor, guardedOnSelect } = useCmdkTouchGuard(open);

  const resolveMatch = (raw) => {
    const needle = (raw || "").trim().toLowerCase();
    if (!needle) return null;
    return DEFAULT_MATERIAL_UNITS.find((u) =>
      [u.code, u.label, ...(u.search || [])].some((token) => token.toLowerCase() === needle),
    ) || null;
  };

  const displayValue = selected ? `${selected.code} — ${selected.label}` : (value || "");

  const selectUnit = (unit) => {
    onChange?.(unit.code);
    onPick?.(unit);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          role="combobox"
          aria-expanded={open}
          variant="outline"
          className={cn(
            "h-12 w-full justify-between rounded-xl border-slate-300 bg-white px-3 text-left text-[0.95rem] font-normal hover:bg-white",
            !displayValue && "text-slate-400",
            className,
          )}
          data-testid={testId}
        >
          <span className="truncate">{displayValue || ph}</span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 text-slate-500" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[var(--radix-popover-trigger-width)] p-0"
        align="start"
        data-testid={`${testId}-content`}
        onOpenAutoFocus={preventAutoFocusOnTouch}
      >
        <Command filter={(itemValue, search) => (itemValue.toLowerCase().includes(search.toLowerCase()) ? 1 : 0)}>
          <CommandInput
            placeholder={t("Search unit code or name...")}
            className="h-12 text-[0.95rem]"
            data-testid={`${testId}-search`}
          />
          <CommandList className="masci-selector-scroll max-h-[50vh]">
            <CommandEmpty>{t("No unit matches that search.")}</CommandEmpty>
            {groupedUnits.map((group) => (
              <CommandGroup key={group.category} heading={t(group.category)}>
                {group.items.map((u) => {
                  const synonyms = [u.code, u.label, ...(u.search || [])].join(" ");
                  return (
                    <CommandItem
                      key={u.code}
                      value={`${u.code} ${u.label} ${synonyms}`}
                      onSelect={guardedOnSelect(() => selectUnit(u))}
                      {...commitHandlersFor(() => selectUnit(u), `${testId}-${u.code}`)}
                      className="py-2"
                      data-testid={`${testId}-option-${u.code.toLowerCase()}`}
                    >
                      <div className="flex min-w-0 flex-1 items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="truncate font-medium text-slate-900">{u.code} — {u.label}</div>
                          <div className="truncate text-[11px] text-slate-500">{(u.search || []).join(" · ")}</div>
                        </div>
                        {selectedCode === u.code && <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />}
                      </div>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
