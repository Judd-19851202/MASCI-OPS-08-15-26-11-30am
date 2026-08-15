import React, { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import {
  subscribeReleaseState,
  applyUpdateNow,
  RELEASE_STATES,
} from "@/lib/releaseUpdate";

// Non-blocking release banner. It ONLY appears when a new release was detected
// while the operator has unsaved field work (UPDATE_PENDING_DIRTY_WORK). Clean
// clients update silently (auto-reload); this banner never blocks input and
// never shows fingerprints/SHAs/cache/service-worker jargon to field users.
export default function ReleaseUpdateBanner() {
  const [state, setState] = useState(RELEASE_STATES.UNKNOWN);

  useEffect(() => subscribeReleaseState(({ state: s }) => setState(s)), []);

  const pending = state === RELEASE_STATES.UPDATE_PENDING_DIRTY_WORK;
  const required = state === RELEASE_STATES.UPDATE_REQUIRED;
  const failed = state === RELEASE_STATES.UPDATE_FAILED;
  if (!pending && !required && !failed) return null;

  return (
    <div
      className="fixed inset-x-0 bottom-0 z-[1100] flex justify-center px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pointer-events-none"
      role="status"
      aria-live="polite"
      data-testid="release-update-banner"
      data-release-state={state}
    >
      <div className={`pointer-events-auto flex w-full max-w-xl items-center gap-3 rounded-2xl border px-4 py-3 shadow-[0_18px_40px_rgba(15,23,42,0.18)] backdrop-blur-xl ${required ? "border-amber-300 bg-amber-50/95" : "border-slate-200 bg-white/95"}`}>
        <RefreshCw className={`h-4 w-4 shrink-0 ${required ? "text-amber-600" : "text-slate-500"} ${failed ? "" : "animate-spin"}`} />
        <div className="min-w-0 flex-1 text-sm text-slate-800">
          {failed ? (
            <>MASCI OPS couldn't finish updating on its own. Your work is safe — tap Reload when you're ready.</>
          ) : required ? (
            <>This version of MASCI OPS is no longer supported. <span className="font-semibold">Your current work is protected</span> — save this record and MASCI OPS will update automatically.</>
          ) : (
            <>A new version of MASCI OPS is ready. <span className="font-semibold">Your current work is protected</span> — finish or save this record and it will update automatically.</>
          )}
        </div>
        <button
          type="button"
          onClick={applyUpdateNow}
          className="shrink-0 rounded-full border border-slate-300 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700"
          data-testid="release-update-apply"
        >
          {failed ? "Reload" : "Update now"}
        </button>
      </div>
    </div>
  );
}
