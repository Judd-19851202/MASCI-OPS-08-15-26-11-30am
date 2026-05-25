// StagedPhotoBadge.jsx — iter435 · Phase 31 · Pass B · Part 3.
//
// Tiny calm count badge: "N photos waiting to send". Renders nothing
// when the count is zero. NO retry button, NO list, NO action menu —
// just operational truth in one line. Photos retry automatically on
// `online` / `focus` via photoStaging.flushStaged().

import React, { useEffect, useState } from "react";
import { CloudUpload } from "lucide-react";
import { useT } from "@/lib/i18n";
import { listStagedFor, onStagedChange, flushStaged } from "./photoStaging";

export default function StagedPhotoBadge({
  hostKind, hostId, testId = "staged-photo-badge",
}) {
  const { t } = useT();
  const [count, setCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const staged = await listStagedFor(hostKind, hostId);
        if (!cancelled) setCount(staged.length);
      } catch { /* silent · operational continuity */ }
    }
    refresh();
    const unsub = onStagedChange(refresh);
    // Best-effort flush attempt on mount in case we just regained signal.
    flushStaged().catch(() => { /* silent */ });
    return () => { cancelled = true; unsub(); };
  }, [hostKind, hostId]);

  if (!count) return null;
  return (
    <span
      data-testid={testId}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 text-[11px] font-mono uppercase tracking-wider font-bold"
      title={t("Photos waiting to send will upload when connection returns.")}
    >
      <CloudUpload className="w-3 h-3" />
      <span>{count} {t("waiting to send")}</span>
    </span>
  );
}
