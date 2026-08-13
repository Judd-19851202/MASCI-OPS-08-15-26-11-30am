// QueueRecoveryNotice.jsx — P0-QUEUE-2026-08-13.
// Calm, dismissible operator confirmation shown ONLY after previously stranded
// device-queued submissions reach a CONFIRMED server 2xx after redeploy.
// No raw technical language. EN/ES via the shared i18n layer. Not persistent.
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { onQueueRecovery } from "@/lib/resiliency";

export default function QueueRecoveryNotice() {
  const t = useT();
  const lastShown = useRef(0);

  useEffect(() => {
    const unsub = onQueueRecovery(({ recovered, remaining }) => {
      // Only announce genuinely-confirmed recoveries, and de-dupe repeats.
      if (!recovered || recovered <= lastShown.current) return;
      lastShown.current = recovered;
      const title = t("Saved submissions synchronized");
      const okMsg = t("{n} previously saved submissions were successfully synchronized.")
        .replace("{n}", String(recovered));
      const partialMsg = t("{n} saved submissions synchronized. {r} still need attention — please keep them on this device.")
        .replace("{n}", String(recovered))
        .replace("{r}", String(remaining));
      toast.success(title, {
        description: remaining > 0 ? partialMsg : okMsg,
        duration: 8000,
        dismissible: true,
        closeButton: true,
        "data-testid": "queue-recovery-notice",
      });
    });
    return unsub;
  }, [t]);

  return null;
}
