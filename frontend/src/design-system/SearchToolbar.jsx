import React from "react";
import { ResponsiveFilterRow } from "./responsive";

export function SearchToolbar({
  searchSlot,
  filters = null,
  actions = null,
  summary = null,
  className = "",
  "data-testid": testId = "ds-search-toolbar",
}) {
  return (
    <section className={`wp16-toolbar p-4 ${className}`} data-testid={testId}>
      <ResponsiveFilterRow testid={`${testId}-row`}>
        {searchSlot ? <div className="min-w-0 flex-1">{searchSlot}</div> : null}
        {filters ? <div className="flex flex-wrap items-center gap-2 min-w-0">{filters}</div> : null}
        {actions ? <div className="flex flex-wrap items-center gap-2 min-w-0 lg:ml-auto">{actions}</div> : null}
      </ResponsiveFilterRow>
      {summary ? <div className="mt-3 text-xs sm:text-sm text-zinc-600" data-testid={`${testId}-summary`}>{summary}</div> : null}
    </section>
  );
}

export default SearchToolbar;