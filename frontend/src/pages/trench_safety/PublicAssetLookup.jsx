// Public Asset Lookup card — typed asset_id navigates to the QR landing.
// Reusable on the public dashboard AND on the home page.
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, ArrowRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";

export default function PublicAssetLookup({ compact = false }) {
  const { t } = useT();
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  function submit(e) {
    if (e) e.preventDefault();
    const v = q.trim().toUpperCase();
    if (!v) return;
    navigate(`/trench-safety/assets/${encodeURIComponent(v)}`);
  }

  return (
    <form onSubmit={submit} className={compact ? "space-y-3" : "wp17-panel p-4 space-y-3"} data-testid="public-asset-lookup">
      {!compact && (
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-1">
          {t("Asset Lookup")}
        </div>
      )}
      {!compact && (
        <div className="text-sm text-slate-600 mb-2">
          {t("Type an Asset ID printed on the box (TB-07, EP-001, SP-001…) to see its status, last inspection, and tabulated data.")}
        </div>
      )}
      <div className="flex flex-col sm:flex-row items-stretch gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("Enter Asset ID (e.g. TB-07)")}
            className="pl-8 h-11 border-2 font-mono uppercase"
            data-testid="public-asset-lookup-input"
            aria-label={t("Asset ID")}
          />
        </div>
        <Button
          type="submit"
          disabled={!q.trim()}
          data-testid="public-asset-lookup-submit"
          className="sm:w-auto h-11 bg-cyan-700 hover:bg-cyan-800 disabled:bg-slate-300 text-white font-bold uppercase tracking-[0.12em] text-xs px-4 inline-flex items-center gap-1"
        >
          {t("Look Up")} <ArrowRight className="w-3.5 h-3.5" />
        </Button>
      </div>
    </form>
  );
}
