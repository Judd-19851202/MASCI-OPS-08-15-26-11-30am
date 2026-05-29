// Equipment Return — multi-line entry with serial lookup against existing
// open equipment_checkout records. Auto-fills the original line's
// manufacturer / model / qty / replacement value so the foreman only
// has to record return condition + photos. Auto-flags damage / loss
// against the original replacement value.

import React, { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, Search, AlertTriangle, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { PhotoUpload } from "@/components/PhotoUpload";
import { toast } from "sonner";

const inputCls =
  "h-11 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600";
const smallCls =
  "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600";

const RETURN_CONDITIONS = [
  { en: "Good", es: "Bueno" },
  { en: "Fair", es: "Aceptable" },
  { en: "Damaged", es: "Dañado" },
  { en: "Missing", es: "Faltante" },
  { en: "Lost", es: "Perdido" },
];

const DAMAGE_RC = ["Damaged", "Missing", "Lost"];

const blankReturnLine = () => ({
  // Mirror checkout shape
  catalog_id: null,
  checkout_id: null,
  line_index: null,
  name: "",
  manufacturer: "",
  model: "",
  serial: "",
  qty: 1,
  replacement_value: 0,
  condition: "",          // ISSUED condition (read-only after lookup)
  return_condition: "",   // RETURN condition (foreman records)
  return_notes: "",
  return_photos: [],
  damage_amount: "",      // optional foreman override
  original_photos: [],    // snapshot of original checkout photos (read-only)
});

const fmtMoney = (n) =>
  `$${(Number(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export function EquipmentReturnLines({ value, onChange, lang, t }) {
  const lines = Array.isArray(value) ? value : [];
  const [serialSearch, setSerialSearch] = useState("");
  const [searching, setSearching] = useState(false);

  const updateLine = (idx, patch) =>
    onChange(lines.map((l, i) => (i === idx ? { ...l, ...patch } : l)));

  const removeLine = (idx) => onChange(lines.filter((_, i) => i !== idx));

  // Look up an open checkout line by serial / asset ID
  const lookupSerial = async () => {
    const s = serialSearch.trim();
    if (!s) {
      toast.error(t("Enter a serial / asset ID to look up"));
      return;
    }
    setSearching(true);
    try {
      const r = await api.get("/field-leadership/equipment-checkout-lookup", { params: { serial: s } });
      const matches = r.data?.matches || [];
      if (matches.length === 0) {
        toast.error(t("No open checkout found for that serial"));
        return;
      }
      // Prefer the most-recent. Pre-fill a new line.
      const m = matches[0];
      const ln = m.line || {};
      const newLine = {
        ...blankReturnLine(),
        catalog_id: ln.catalog_id || null,
        checkout_id: m.checkout_id,
        line_index: m.line_index,
        name: ln.name || "",
        manufacturer: ln.manufacturer || "",
        model: ln.model || "",
        serial: ln.serial || s,
        qty: ln.qty || 1,
        replacement_value: ln.replacement_value || 0,
        condition: ln.condition || "",
        return_condition: "",
        return_notes: "",
        return_photos: [],
        // Carry the original checkout photos forward so the foreman can
        // visually compare "what was checked out" vs. "what came back" on
        // the same screen — and so the PDF generator can render them
        // side-by-side on the return form. These are NEVER edited from
        // the return form; they're a snapshot of the original record.
        original_photos: Array.isArray(ln.photos) ? ln.photos : [],
      };
      onChange([...lines, newLine]);
      setSerialSearch("");
      toast.success(t("Loaded original checkout — record return condition + photos"));
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Lookup failed"));
    } finally {
      setSearching(false);
    }
  };

  const addManual = () => onChange([...lines, blankReturnLine()]);

  const totals = useMemo(() => {
    let value = 0;
    let damage = 0;
    for (const l of lines) {
      const qty = Number(l.qty) || 0;
      const rv = Number(l.replacement_value) || 0;
      value += qty * rv;
      const rc = (l.return_condition || "").trim();
      const override = l.damage_amount;
      const overrideNum = override === "" || override === null || override === undefined
        ? null : Number(override);
      if (overrideNum !== null && !Number.isNaN(overrideNum)) {
        damage += overrideNum;
      } else if (DAMAGE_RC.includes(rc)) {
        damage += qty * rv;
      }
    }
    return { value, damage };
  }, [lines]);

  return (
    <div className="space-y-4" data-testid="equipment-return-lines">
      {/* Lookup bar */}
      <div className="border-2 border-blue-300 bg-blue-50 rounded-md p-4">
        <Label className="font-mono text-xs uppercase tracking-[0.2em] text-blue-900 font-bold">
          {t("Look Up by Serial / Asset ID")}
        </Label>
        <p className="text-xs text-blue-800 mt-1">
          {t("Scan or type the serial / asset ID stamped on the equipment to pull the original checkout record.")}
        </p>
        <div className="flex gap-2 mt-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
            <Input
              value={serialSearch}
              onChange={(e) => setSerialSearch(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); lookupSerial(); } }}
              placeholder={t("e.g. RL200-789")}
              className={`${inputCls} pl-9`}
              data-testid="equipment-return-serial-input"
            />
          </div>
          <Button
            type="button"
            onClick={lookupSerial}
            disabled={searching}
            className="h-11 bg-blue-700 hover:bg-blue-800 text-white font-bold uppercase tracking-wide"
            data-testid="equipment-return-lookup"
          >
            {searching ? t("Searching…") : t("Look Up")}
          </Button>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={addManual}
          className="mt-2 h-9 border-2 text-xs"
          data-testid="equipment-return-add-manual"
        >
          <Plus className="w-3.5 h-3.5 mr-1" />{t("Add Manual Entry")}
        </Button>
      </div>

      {lines.length === 0 && (
        <div className="border-2 border-dashed border-slate-300 rounded-md p-6 text-center text-slate-500 text-sm" data-testid="equipment-return-empty">
          {t("No items yet. Look up a serial or add a manual entry.")}
        </div>
      )}

      {lines.map((line, idx) => {
        const qty = Number(line.qty) || 0;
        const rv = Number(line.replacement_value) || 0;
        const lineValue = qty * rv;
        const rc = (line.return_condition || "").trim();
        const isDamage = DAMAGE_RC.includes(rc);
        const overrideNum = line.damage_amount === "" || line.damage_amount === null || line.damage_amount === undefined
          ? null : Number(line.damage_amount);
        const lineDamage = overrideNum !== null && !Number.isNaN(overrideNum)
          ? overrideNum
          : (isDamage ? lineValue : 0);
        return (
          <div
            key={idx}
            className={`border-2 rounded-md p-4 sm:p-5 bg-white shadow-sm ${isDamage ? "border-red-400" : "border-slate-300"}`}
            data-testid={`equipment-return-line-${idx}`}
          >
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center px-2 py-1 rounded bg-blue-50 text-blue-800 font-mono text-[10px] uppercase tracking-[0.2em] font-bold">
                  {t("Item")} #{idx + 1}
                </span>
                {line.checkout_id && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-emerald-50 text-emerald-800 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
                    <CheckCircle2 className="w-3 h-3" />{t("Matched checkout")}
                  </span>
                )}
                {isDamage && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-50 text-red-800 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
                    <AlertTriangle className="w-3 h-3" />{t("Damage flagged")}
                  </span>
                )}
              </div>
              <Button type="button" variant="outline" size="sm" onClick={() => removeLine(idx)} className="border-red-300 text-red-700 hover:bg-red-50 h-8" data-testid={`equipment-return-remove-${idx}`}>
                <Trash2 className="w-3.5 h-3.5 mr-1" />{t("Remove")}
              </Button>
            </div>

            {/* Read-only original checkout summary */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3 text-sm">
              <div>
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Equipment")}</span>
                <Input
                  value={line.name || ""}
                  onChange={(e) => updateLine(idx, { name: e.target.value })}
                  className={smallCls}
                  data-testid={`equipment-return-name-${idx}`}
                />
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Manufacturer")}</span>
                <Input
                  value={line.manufacturer || ""}
                  onChange={(e) => updateLine(idx, { manufacturer: e.target.value })}
                  className={smallCls}
                  data-testid={`equipment-return-mfg-${idx}`}
                />
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{t("Model")}</span>
                <Input
                  value={line.model || ""}
                  onChange={(e) => updateLine(idx, { model: e.target.value })}
                  className={smallCls}
                  data-testid={`equipment-return-model-${idx}`}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Serial / Asset ID")}<span className="text-red-700 ml-1">*</span>
                </Label>
                <Input
                  value={line.serial || ""}
                  onChange={(e) => updateLine(idx, { serial: e.target.value })}
                  className={smallCls}
                  data-testid={`equipment-return-serial-${idx}`}
                />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Qty")}</Label>
                <Input type="number" min="1" step="1" value={line.qty}
                  onChange={(e) => updateLine(idx, { qty: Number(e.target.value) || 0 })}
                  className={smallCls} data-testid={`equipment-return-qty-${idx}`} />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Issued Cond.")}</Label>
                <Input value={line.condition || ""} disabled className={`${smallCls} bg-slate-50`} data-testid={`equipment-return-issued-cond-${idx}`} />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Replacement $")}</Label>
                <div className="h-10 px-3 flex items-center font-mono text-base font-bold text-slate-900 bg-slate-50 border border-slate-200 rounded-md" data-testid={`equipment-return-rv-${idx}`}>
                  {fmtMoney(rv)}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 mb-3">
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Return Condition")}<span className="text-red-700 ml-1">*</span>
                </Label>
                <Select value={line.return_condition || ""} onValueChange={(v) => updateLine(idx, { return_condition: v })}>
                  <SelectTrigger className={inputCls} data-testid={`equipment-return-cond-${idx}`}>
                    <SelectValue placeholder={t("Select…")} />
                  </SelectTrigger>
                  <SelectContent>
                    {RETURN_CONDITIONS.map((o) => (
                      <SelectItem key={o.en} value={o.en}>{lang === "es" ? o.es : o.en}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                  {t("Loss / Damage Amount")} {isDamage ? <span className="text-red-700">{fmtMoney(lineDamage)}</span> : <span className="text-slate-400">{fmtMoney(0)}</span>}
                </Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={line.damage_amount}
                  onChange={(e) => updateLine(idx, { damage_amount: e.target.value })}
                  placeholder={isDamage ? t("Defaults to full replacement") : t("Auto-zero unless damaged/lost")}
                  className={smallCls}
                  data-testid={`equipment-return-damage-${idx}`}
                />
              </div>
            </div>

            <div className="mb-3">
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">{t("Return Notes")}</Label>
              <Textarea rows={2} value={line.return_notes || ""}
                onChange={(e) => updateLine(idx, { return_notes: e.target.value })}
                className="border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600"
                data-testid={`equipment-return-notes-${idx}`} />
            </div>

            {/* Original checkout photos — read-only side-by-side comparison */}
            {Array.isArray(line.original_photos) && line.original_photos.length > 0 && (
              <div className="mb-3 bg-emerald-50 border-2 border-emerald-300 rounded-md p-3">
                <Label className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-900 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {t("Original checkout photos")}{" "}
                  <span className="text-emerald-700 normal-case font-sans tracking-normal">
                    ({line.original_photos.length} {t("on file")})
                  </span>
                </Label>
                <p className="text-[10px] text-emerald-800 font-mono uppercase tracking-[0.15em] mt-1">
                  {t("Use these to compare against return condition. Tap to enlarge.")}
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2" data-testid={`equipment-return-original-photos-${idx}`}>
                  {line.original_photos.slice(0, 8).map((src, pi) => (
                    <a
                      key={pi}
                      href={src}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block aspect-square rounded overflow-hidden border-2 border-emerald-200 bg-white hover:border-emerald-500 transition-colors"
                      data-testid={`equipment-return-original-photo-${idx}-${pi}`}
                    >
                      <img
                        src={src}
                        alt={`Original ${pi + 1}`}
                        loading="lazy"
                        decoding="async"
                        className="w-full h-full object-cover"
                      />
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div>
              <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
                {t("Return Photos")}<span className="text-red-700 ml-1">*</span>
                <span className="ml-2 font-sans normal-case tracking-normal text-[10px] text-slate-500">
                  {t("(Minimum 2 photos required)")}
                </span>
              </Label>
              <PhotoUpload
                photos={line.return_photos || []}
                onChange={(p) => updateLine(idx, { return_photos: p })}
                testIdBase={`equipment-return-photos-${idx}`}
              />
              {(line.return_photos || []).length < 2 && (
                <p className="text-xs text-red-700 mt-1 font-mono uppercase tracking-[0.15em]" data-testid={`equipment-return-photos-warning-${idx}`}>
                  {t("Need")} {2 - (line.return_photos || []).length} {t("more photo(s)")}
                </p>
              )}
            </div>
          </div>
        );
      })}

      {lines.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <div className="rounded-md border-2 border-slate-300 bg-white px-5 py-4 flex items-center justify-between">
            <div>
              <div className="font-mono text-xs uppercase tracking-[0.25em] text-slate-700 font-bold">{t("Total Replacement Value")}</div>
              <div className="text-xs text-slate-500 mt-0.5">{lines.length} {lines.length === 1 ? t("item") : t("items")}</div>
            </div>
            <div className="font-display text-2xl font-black text-slate-900 tabular-nums" data-testid="equipment-return-total-value">{fmtMoney(totals.value)}</div>
          </div>
          <div className={`rounded-md border-4 px-5 py-4 flex items-center justify-between ${totals.damage > 0 ? "border-red-500 bg-red-50" : "border-emerald-300 bg-emerald-50"}`}>
            <div>
              <div className={`font-mono text-xs uppercase tracking-[0.25em] font-bold ${totals.damage > 0 ? "text-red-800" : "text-emerald-800"}`}>{t("Total Loss / Damage")}</div>
              <div className={`text-xs mt-0.5 ${totals.damage > 0 ? "text-red-900" : "text-emerald-900"}`}>{totals.damage > 0 ? t("Auto-flagged on return") : t("Clean return — no damage")}</div>
            </div>
            <div className={`font-display text-2xl sm:text-3xl font-black tabular-nums ${totals.damage > 0 ? "text-red-700" : "text-emerald-700"}`} data-testid="equipment-return-total-damage">{fmtMoney(totals.damage)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
