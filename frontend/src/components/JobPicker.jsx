import React, { useState, useMemo, useEffect } from "react";
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
import { JOB_LIBRARY as STATIC_LIBRARY, CUSTOM_JOB_KEY } from "@/lib/jobLibrary";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

// Module-level cache so every <JobPicker> on the page hits the API once.
let _jobsCache = null;
let _jobsPromise = null;
async function loadJobs() {
  if (_jobsCache) return _jobsCache;
  if (_jobsPromise) return _jobsPromise;
  _jobsPromise = api
    .get("/jobs")
    .then((r) => {
      const items = Array.isArray(r.data?.items) ? r.data.items : [];
      _jobsCache = items.length ? items : STATIC_LIBRARY;
      return _jobsCache;
    })
    .catch(() => {
      // Network error — fall back to the static seed so the picker still works.
      _jobsCache = STATIC_LIBRARY;
      return _jobsCache;
    });
  return _jobsPromise;
}

export function JobPicker({
  projectName = "",
  projectNumber = "",
  onSelect,
  className = "",
}) {
  const [open, setOpen] = useState(false);
  const [library, setLibrary] = useState(STATIC_LIBRARY);
  const { t } = useT();

  useEffect(() => {
    let alive = true;
    loadJobs().then((jobs) => {
      if (alive) setLibrary(jobs);
    });
    return () => {
      alive = false;
    };
  }, []);

  // Match by project_number first (canonical key), then by exact name.
  const matched = useMemo(() => {
    if (projectNumber) {
      const byNum = library.find((j) => j.project_number === projectNumber);
      if (byNum) return byNum;
    }
    if (projectName) {
      return library.find((j) => j.project_name === projectName) || null;
    }
    return null;
  }, [projectName, projectNumber, library]);

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

            <CommandGroup heading={`MASCI Current Jobs · ${library.length}`}>
              {library.map((j) => (
                <CommandItem
                  key={j.project_number}
                  value={`${j.project_number} ${j.project_name} ${j.location || ""} ${j.project_manager || ""} ${j.client || ""}`}
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
                      {(j.location || j.client || j.project_manager) && (
                        <div className="text-xs text-slate-500 mt-0.5">
                          {[j.location, j.client && `Client: ${j.client}`, j.project_manager && `PM: ${j.project_manager}`]
                            .filter(Boolean)
                            .join("  ·  ")}
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
