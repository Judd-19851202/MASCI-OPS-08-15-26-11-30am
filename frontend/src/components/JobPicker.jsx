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
import { useCmdkTouchGuard } from "@/lib/useCmdkTouchGuard";

// TRACK 24.8 · Touch-select vs scroll disambiguation, refactored
// in Track 24.9 Phase B into the shared `useCmdkTouchGuard` hook
// so every cmdk-based picker on the platform gets the same
// battle-tested iOS-Safari-safe commit path. History: Track 24.6
// commit-on-pointerdown fixed the input-blur race but introduced
// wrong-row selection on scroll — Track 24.8 replaced it with
// pointerdown/up + scroll-cancellation, and 24.9 promoted it to a
// reusable primitive.

// Module-level cache so every <JobPicker> on the page hits the API once.
let _jobsCache = null;
let _jobsPromise = null;
async function loadJobs() {
  if (_jobsCache) return _jobsCache;
  if (_jobsPromise) return _jobsPromise;
  _jobsPromise = api
    .get("/jobs", { skipSessionStatus: true })
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
  allowCustom = true,
  emptyHint = "",
  "data-testid": dataTestId,
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
    : allowCustom
    ? t("Pick a current job — or choose Custom")
    : t("Select Job");

  // TRACK 24.9 Phase B · Shared cmdk touch-guard hook. See
  // `/app/frontend/src/lib/useCmdkTouchGuard.js` for the full
  // scroll-vs-tap disambiguation logic.
  const { commitHandlersFor } = useCmdkTouchGuard(open);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          role="combobox"
          aria-expanded={open}
          variant="outline"
          className={cn(
            "wp17-control h-14 w-full justify-between rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-4 text-base font-normal hover:bg-white hover:border-[color:var(--brand-primary)]",
            "focus-visible:ring-2 focus-visible:ring-[color:var(--brand-primary)] focus-visible:ring-offset-2",
            className
          )}
          data-testid={dataTestId || "job-picker-trigger"}
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
        className="wp17-picker-panel w-[var(--radix-popover-trigger-width)] max-w-none p-0"
        align="start"
        data-testid="job-picker-content"
      >
        <Command
          className="bg-transparent"
          filter={(itemValue, search) =>
            itemValue.toLowerCase().includes(search.toLowerCase()) ? 1 : 0
          }
        >
          <CommandInput
            placeholder={t("Search by job #, name, route, or city...")}
            className="h-12 border-b border-slate-200 bg-transparent text-base text-slate-900 placeholder:text-slate-400"
            data-testid="job-picker-search"
          />
          <CommandList className="max-h-[55vh] p-1.5">
            <CommandEmpty className="wp17-picker-empty">
              {allowCustom
                ? t("No job matches that search.")
                : (emptyHint || t("I don't see this job — contact PM to add it."))}
            </CommandEmpty>

            {allowCustom && (
            <CommandGroup heading={t("Custom")} className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:font-bold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.18em] [&_[cmdk-group-heading]]:text-slate-500">
              <CommandItem
                value="custom job free form not in list"
                onSelect={() => {
                  onSelect(null);
                  setOpen(false);
                }}
                {...commitHandlersFor(
                  () => { onSelect(null); setOpen(false); },
                  "job-picker-custom",
                )}
                className="wp17-picker-option cursor-pointer rounded-[0.95rem] py-3 data-[selected=true]:bg-red-50 data-[selected=true]:text-slate-900"
                data-testid="job-picker-custom"
              >
                <div className="flex items-start gap-3 w-full">
                  <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-[0.9rem] border border-slate-200 bg-slate-900 text-white mt-0.5">
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
            )}

            <CommandGroup heading={`${t("MASCI Current Jobs")} · ${library.length}`} className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:font-bold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-[0.18em] [&_[cmdk-group-heading]]:text-slate-500">
              {library.map((j, jIdx) => (
                <CommandItem
                  key={j.id || `${j.project_number || "job"}-${jIdx}`}
                  value={`${j.project_number} ${j.project_name} ${j.location || ""} ${j.project_manager || ""} ${j.client || ""}`}
                  onSelect={() => {
                    onSelect(j);
                    setOpen(false);
                  }}
                  {...commitHandlersFor(
                    () => { onSelect(j); setOpen(false); },
                    `job-picker-item-${j.project_number}`,
                  )}
                  className="wp17-picker-option cursor-pointer rounded-[0.95rem] py-2.5 data-[selected=true]:bg-red-50 data-[selected=true]:text-slate-900"
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
                          {[j.location, j.client && `${t("Client:")} ${j.client}`, j.project_manager && `${t("PM:")} ${j.project_manager}`]
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
