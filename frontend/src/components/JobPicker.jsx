import React, { useState, useMemo } from "react";
import { Check, ChevronDown, Search, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";
import { JOB_LIBRARY, CUSTOM_JOB_KEY } from "@/lib/jobLibrary";
import { useT } from "@/lib/i18n";

/**
 * MASCI Current Jobs picker.
 *
 * Props:
 *   projectName            - current project name string
 *   projectNumber          - current project number string
 *   onSelect(job|null)     - called with chosen job ({project_name, project_number, location}) or null on Custom
 *   className              - optional wrapper class
 *
 * Behavior:
 *   - Shows the matching job by project_number (if any), otherwise the typed projectName.
 *   - "Custom Job" option clears the lock — user may type anything.
 *   - Caller is responsible for setting project_name / project_number from onSelect.
 */
export function JobPicker({
  projectName = "",
  projectNumber = "",
  onSelect,
  className = "",
}) {
  const [open, setOpen] = useState(false);
  const { t } = useT();

  // Match by project_number first (canonical key), then by exact name.
  const matched = useMemo(() => {
    if (projectNumber) {
      const byNum = JOB_LIBRARY.find((j) => j.project_number === projectNumber);
      if (byNum) return byNum;
    }
    if (projectName) {
      return JOB_LIBRARY.find((j) => j.project_name === projectName) || null;
    }
    return null;
  }, [projectName, projectNumber]);

  const triggerLabel = matched
    ? `${matched.project_name}  ·  #${matched.project_number}`
    : projectName
    ? `${projectName}${projectNumber ? `  ·  #${projectNumber}` : `  ·  ${t("Custom")}`}`
    : t("Pick a MASCI job — or choose Custom");

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          role="combobox"
          aria-expanded={open}
          variant="outline"
          className={cn(
            "h-14 w-full justify-between text-base font-normal",
            "border-2 border-slate-300 bg-white hover:bg-white hover:border-red-500",
            "focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2",
            className
          )}
          data-testid="job-picker-trigger"
        >
          <span className="flex items-center gap-2 truncate">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <span className="truncate text-slate-900 text-left">
              {triggerLabel}
            </span>
          </span>
          <ChevronDown className="w-4 h-4 text-slate-500 shrink-0 ml-2" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0 w-[var(--radix-popover-trigger-width)] max-w-none"
        align="start"
        data-testid="job-picker-content"
      >
        <Command
          filter={(itemValue, search) =>
            itemValue.toLowerCase().includes(search.toLowerCase()) ? 1 : 0
          }
        >
          <CommandInput
            placeholder={t("Search by job #, name, route, or city...")}
            className="h-12 text-base"
            data-testid="job-picker-search"
          />
          <CommandList className="max-h-[55vh]">
            <CommandEmpty>{t("No job matches that search.")}</CommandEmpty>

            <CommandGroup heading={t("Custom")}>
              <CommandItem
                value="custom job free form not in list"
                onSelect={() => {
                  onSelect(null);
                  setOpen(false);
                }}
                className="py-3 cursor-pointer"
                data-testid="job-picker-custom"
              >
                <div className="flex items-start gap-3 w-full">
                  <span className="inline-flex w-7 h-7 items-center justify-center rounded bg-slate-900 text-white shrink-0 mt-0.5">
                    <Pencil className="w-3.5 h-3.5" />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-slate-900">{t("Custom Job")}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {t("Type the project name and number manually")}
                    </div>
                  </div>
                  {matched == null && (projectName || projectNumber) && (
                    <Check className="w-4 h-4 text-red-700 shrink-0 mt-1" />
                  )}
                </div>
              </CommandItem>
            </CommandGroup>

            <CommandGroup heading={`MASCI Current Jobs · ${JOB_LIBRARY.length}`}>
              {JOB_LIBRARY.map((j) => (
                <CommandItem
                  key={j.project_number}
                  value={`${j.project_number} ${j.project_name} ${j.location}`}
                  onSelect={() => {
                    onSelect(j);
                    setOpen(false);
                  }}
                  className="py-2.5 cursor-pointer"
                  data-testid={`job-picker-item-${j.project_number}`}
                >
                  <div className="flex items-start gap-3 w-full">
                    <span className="inline-flex shrink-0 mt-0.5 px-1.5 py-0.5 bg-red-700 text-white text-[10px] font-mono font-bold uppercase tracking-wider rounded">
                      #{j.project_number}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-slate-900 leading-snug">
                        {j.project_name}
                      </div>
                      {j.location && (
                        <div className="text-xs text-slate-500 mt-0.5">
                          {j.location}
                        </div>
                      )}
                    </div>
                    {matched && matched.project_number === j.project_number && (
                      <Check className="w-4 h-4 text-red-700 shrink-0 mt-1" />
                    )}
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

export { CUSTOM_JOB_KEY };
