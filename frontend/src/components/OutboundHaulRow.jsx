// TRACK 15.62 · OutboundHaulRow — canonical material picker + unit
// dropdown + hauler input. Replaces the raw three-input row that
// resulted in 50 production loads of "Dirt" being aggregable only
// by exact-string match. Free-text fallback preserved for materials
// outside the canonical vocabulary.
import React from "react";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Button } from "./ui/button";
import { X } from "lucide-react";

const DEFAULT_UNITS = ["Loads", "Trips", "Tons", "Cubic Yards", "Each"];

export function OutboundHaulRow({
  value = {}, onChange, onRemove,
  vocab = [], recentDestinations = [], testIdPrefix = "haul-row",
}) {
  const set = (k, v) => onChange?.({ ...value, [k]: v });
  const canonOptions = vocab.map((r) => r.canonical || r).filter(Boolean);
  const useCustomMaterial = canonOptions.length && !canonOptions.includes(value.material) && (value.material || "").trim();

  return (
    <div className="border rounded-md p-3 bg-white grid gap-3" data-testid={testIdPrefix}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="grid gap-1">
          <Label className="text-xs text-slate-600">Material</Label>
          <Select
            value={canonOptions.includes(value.material) ? value.material : (useCustomMaterial ? "__custom__" : "")}
            onValueChange={(v) => set("material", v === "__custom__" ? (value.material || "") : v)}
          >
            <SelectTrigger data-testid={`${testIdPrefix}-material`}>
              <SelectValue placeholder="Pick a material…" />
            </SelectTrigger>
            <SelectContent>
              {canonOptions.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
              <SelectItem value="__custom__">Other (type below)</SelectItem>
            </SelectContent>
          </Select>
          {(useCustomMaterial || value.material === "") && (
            <Input
              value={value.material || ""}
              onChange={(e) => set("material", e.target.value)}
              placeholder="Free-text material (used when not in vocabulary)"
              data-testid={`${testIdPrefix}-material-custom`}
              className="mt-1"
            />
          )}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="grid gap-1">
            <Label className="text-xs text-slate-600">Quantity</Label>
            <Input
              type="number" inputMode="numeric" min={0}
              value={value.quantity ?? ""}
              onChange={(e) => set("quantity", e.target.value)}
              data-testid={`${testIdPrefix}-quantity`}
              placeholder="0"
            />
          </div>
          <div className="grid gap-1">
            <Label className="text-xs text-slate-600">Unit</Label>
            <Select value={value.unit || "Loads"} onValueChange={(v) => set("unit", v)}>
              <SelectTrigger data-testid={`${testIdPrefix}-unit`}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DEFAULT_UNITS.map((u) => <SelectItem key={u} value={u}>{u}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="grid gap-1">
          <Label className="text-xs text-slate-600">Hauler</Label>
          <Input
            value={value.hauler || ""}
            onChange={(e) => set("hauler", e.target.value)}
            placeholder="Masci, or trucking company name"
            data-testid={`${testIdPrefix}-hauler`}
            list={`${testIdPrefix}-hauler-options`}
          />
          <datalist id={`${testIdPrefix}-hauler-options`}>
            <option value="Masci" />
          </datalist>
        </div>
        <div className="grid gap-1">
          <Label className="text-xs text-slate-600">Destination</Label>
          <Input
            value={value.destination || ""}
            onChange={(e) => set("destination", e.target.value)}
            placeholder="Where did the material go?"
            data-testid={`${testIdPrefix}-destination`}
            list={`${testIdPrefix}-dest-options`}
          />
          {recentDestinations.length > 0 && (
            <datalist id={`${testIdPrefix}-dest-options`}>
              {recentDestinations.map((d) => <option key={d} value={d} />)}
            </datalist>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-end">
        <div className="grid gap-1">
          <Label className="text-xs text-slate-600">Ticket / manifest # (optional)</Label>
          <Input
            value={value.ticket_or_manifest || ""}
            onChange={(e) => set("ticket_or_manifest", e.target.value)}
            data-testid={`${testIdPrefix}-ticket`}
          />
        </div>
        {onRemove && (
          <Button
            variant="ghost" type="button"
            onClick={onRemove}
            data-testid={`${testIdPrefix}-remove`}
            className="text-red-700 self-end justify-self-end"
          >
            <X className="w-4 h-4 mr-1" /> Remove
          </Button>
        )}
      </div>
    </div>
  );
}

export default OutboundHaulRow;
