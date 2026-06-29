// Phase 10A-B · Employee Picker (Correction 3)
// FV-7.2 · When role="competent" we pull from the dedicated
// designated-CP roster (`/api/employees/competent-persons`) so the
// foreman cannot pick an undesignated employee from the normal list.
// All other roles still pull from the canonical HR roster
// (`/api/hr/employee-roster` — Track 19.03 · HR is gospel).
import React, { useEffect, useMemo, useState } from "react";
import { Check, ChevronsUpDown, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { fetchHrRoster, subscribeHrRoster } from "@/lib/hrRoster";

// Competent-persons roster: separate Trench Safety endpoint backed by
// `db.employees`. Less volatile than the main roster — short-lived
// in-flight de-dup only, no persistent cache (Track 19.03 doctrine).
let _cpPromise = null;
async function loadCompetentPersons() {
  if (_cpPromise) return _cpPromise;
  _cpPromise = api.get("/employees/competent-persons")
    .then((r) => Array.isArray(r.data?.items) ? r.data.items : [])
    .catch(() => [])
    .finally(() => { _cpPromise = null; });
  return _cpPromise;
}

export default function EmployeePicker({ value, onSelect, placeholder = "Select…", testId = "employee-picker", role }) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [roster, setRoster] = useState([]);
  const isCpMode = (role || "").toLowerCase() === "competent";

  useEffect(() => {
    let alive = true;
    if (isCpMode) {
      loadCompetentPersons().then((items) => { if (alive) setRoster(items); });
      return () => { alive = false; };
    }
    // Canonical HR roster — live updates via `hr:roster-changed` bus.
    const apply = (items) => { if (alive) setRoster(items || []); };
    const unsub = subscribeHrRoster(apply);
    fetchHrRoster().then(apply);
    return () => { alive = false; unsub(); };
  }, [isCpMode]);

  const filtered = useMemo(() => {
    if (!role || isCpMode) return roster;
    const r = role.toLowerCase();
    // Loose match on role/trade — but always return full list so foreman
    // can pick anyone if the roster doesn't have explicit role tagging.
    const tagged = roster.filter((e) => (e.role || "").toLowerCase().includes(r) || (e.trade || "").toLowerCase().includes(r));
    return tagged.length ? tagged : roster;
  }, [roster, role, isCpMode]);

  const selected = roster.find((e) => e.id === value);
  const headingLabel = isCpMode
    ? `${t("Designated Competent Persons")} · ${filtered.length}`
    : `${t("MASCI Roster")} · ${filtered.length}`;

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
            {isCpMode ? <ShieldCheck className="w-4 h-4 text-cyan-700 shrink-0" /> : <Search className="w-4 h-4 text-slate-500 shrink-0" />}
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
          <CommandInput placeholder={t(isCpMode ? "Search designated CPs…" : "Search by name, role, or trade…")} className="h-11" data-testid={`${testId}-search`} />
          <CommandList className="max-h-[55vh]">
            <CommandEmpty>
              {isCpMode
                ? t("No designated Competent Persons. Ask Admin to designate one.")
                : t("No employee matches that search.")}
            </CommandEmpty>
            <CommandGroup heading={headingLabel}>
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
                      <div className="font-medium text-slate-900 leading-snug truncate">
                        {e.name}
                        {isCpMode && <span className="ml-1 inline-flex items-center gap-0.5 text-[10px] font-mono uppercase tracking-[0.1em] text-cyan-700"><ShieldCheck className="w-3 h-3" /> CP</span>}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {[e.role, e.trade, e.crew && `Crew: ${e.crew}`, e.employee_id && `#${e.employee_id}`,
                          isCpMode && e.cp_approval_date && `Approved ${e.cp_approval_date}`,
                          isCpMode && e.cp_expiration_date && `Exp ${e.cp_expiration_date}`].filter(Boolean).join(" · ")}
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
