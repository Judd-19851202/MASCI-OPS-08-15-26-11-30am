// Phase 10A-B · Employee Picker (Correction 3)
// Pulls from the certified /api/employees public roster.
// Single-select with name + role/trade subline.
import React, { useEffect, useMemo, useState } from "react";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

let _employeeCache = null;
let _employeePromise = null;
async function loadEmployees() {
  if (_employeeCache) return _employeeCache;
  if (_employeePromise) return _employeePromise;
  _employeePromise = api.get("/employees")
    .then((r) => { _employeeCache = Array.isArray(r.data?.items) ? r.data.items : []; return _employeeCache; })
    .catch(() => { _employeeCache = []; return _employeeCache; });
  return _employeePromise;
}

export default function EmployeePicker({ value, onSelect, placeholder = "Select…", testId = "employee-picker", role }) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [roster, setRoster] = useState([]);

  useEffect(() => { loadEmployees().then(setRoster); }, []);

  const filtered = useMemo(() => {
    if (!role) return roster;
    const r = role.toLowerCase();
    // Loose match on role/trade — but always return full list so foreman
    // can pick anyone if the roster doesn't have explicit role tagging.
    const tagged = roster.filter((e) => (e.role || "").toLowerCase().includes(r) || (e.trade || "").toLowerCase().includes(r));
    return tagged.length ? tagged : roster;
  }, [roster, role]);

  const selected = roster.find((e) => e.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="h-11 w-full justify-between text-sm font-normal border-2 border-slate-300 bg-white hover:border-cyan-600"
          data-testid={`${testId}-trigger`}
        >
          <span className="flex items-center gap-2 truncate">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <span className="truncate text-slate-900 text-left">
              {selected ? `${selected.name}${selected.role ? `  ·  ${selected.role}` : selected.trade ? `  ·  ${selected.trade}` : ""}` : t(placeholder)}
            </span>
          </span>
          <ChevronsUpDown className="w-4 h-4 text-slate-500 shrink-0 ml-2" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0 w-[var(--radix-popover-trigger-width)] max-w-none"
        align="start"
        data-testid={`${testId}-content`}
      >
        <Command filter={(itemValue, search) => itemValue.toLowerCase().includes(search.toLowerCase()) ? 1 : 0}>
          <CommandInput placeholder={t("Search by name, role, or trade…")} className="h-11" data-testid={`${testId}-search`} />
          <CommandList className="max-h-[55vh]">
            <CommandEmpty>{t("No employee matches that search.")}</CommandEmpty>
            <CommandGroup heading={`${t("MASCI Roster")} · ${filtered.length}`}>
              {filtered.map((e) => (
                <CommandItem
                  key={e.id}
                  value={`${e.name} ${e.employee_id || ""} ${e.role || ""} ${e.trade || ""} ${e.crew || ""}`}
                  onSelect={() => { onSelect(e); setOpen(false); }}
                  className="py-2 cursor-pointer"
                  data-testid={`${testId}-item-${e.id}`}
                >
                  <div className="flex items-start gap-2 w-full">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-slate-900 leading-snug truncate">{e.name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {[e.role, e.trade, e.crew && `Crew: ${e.crew}`, e.employee_id && `#${e.employee_id}`].filter(Boolean).join(" · ")}
                      </div>
                    </div>
                    {selected?.id === e.id && <Check className="w-4 h-4 text-cyan-700 shrink-0 mt-0.5" />}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
