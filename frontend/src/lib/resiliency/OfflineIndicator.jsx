// OfflineIndicator.jsx — small header pill that appears when the
// browser reports offline. Subtle: no banner, no modal, no sound.

import React from "react";
import { CloudOff } from "lucide-react";
import { useOnlineStatus } from "./useOnlineStatus";

export default function OfflineIndicator() {
  const online = useOnlineStatus();
  if (online) return null;
  return (
    <div
      className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full border-2 border-amber-300 bg-amber-50 text-amber-900 text-[10px] font-mono uppercase tracking-wider font-bold"
      data-testid="offline-indicator"
      title="Working offline · changes will sync when reconnected"
    >
      <CloudOff className="w-3 h-3" />
      <span>Offline</span>
    </div>
  );
}
