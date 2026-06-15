// TRACK 14.0-RC1 · D3 Offline Trust Surface.
//
// One global banner. Listens to navigator `online` / `offline` browser
// events and renders a calm sky-blue ribbon at the top of the viewport
// while the device is offline.
//
// Why this exists:
//   - The existing `QueueStatusPill` shows queued/failed uploads AFTER
//     the user tries to submit. It cannot tell the user "you are
//     offline RIGHT NOW" before they attempt anything.
//   - `SessionStatusOverlay` only renders on response-failure. A user
//     who is offline but doesn't fire a request sees nothing.
//   - `classifyApiError` is offline-aware but only at error time.
//
// Doctrine:
//   - Calm, not panicky. No red, no flashing. Sky-blue ribbon.
//   - Local message: "You're offline — drafts and submits are queued
//     locally and will sync when you reconnect." Matches QueueStatusPill
//     language so the user understands they're in the same system.
//   - Auto-dismisses when navigator.onLine flips back to true.
//   - Mobile-safe: `safe-area-inset-top` honored so it doesn't sit
//     under the iOS status bar.
//   - Field-mode tested: 44px+ tall, high-contrast text on sky-50
//     background, readable in direct sun (matches TRACK 14.0-S2
//     contrast standards).
//
// Mount: ONCE globally in App.js next to QueueStatusPill.

import { useEffect, useState } from "react";
import { WifiOff } from "lucide-react";
import { useT } from "@/lib/i18n";

export default function OfflineBanner() {
  const { t } = useT();
  const [online, setOnline] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    // Initial sync — covers the rare case where the navigator state
    // changes between mount and the first event.
    setOnline(navigator.onLine);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);

  if (online) return null;

  return (
    <div
      data-testid="offline-banner"
      role="status"
      aria-live="polite"
      className="fixed top-0 inset-x-0 z-[60] bg-sky-50 border-b-2 border-sky-400 text-sky-900 px-4 py-3 shadow-md"
      style={{ paddingTop: "max(0.75rem, env(safe-area-inset-top))" }}
    >
      <div className="max-w-7xl mx-auto flex items-center gap-3 text-sm sm:text-base">
        <WifiOff className="w-5 h-5 shrink-0 text-sky-600" aria-hidden="true" />
        <p className="leading-tight font-medium">
          <span className="font-bold">{t("You're offline.")}</span>{" "}
          {t(
            "Drafts and submits are queued locally and will sync when you reconnect.",
          )}
        </p>
      </div>
    </div>
  );
}
