import React, { useState } from "react";
import { X, Mail, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

/**
 * DistributionList — email chip input. Binds to a `distribution_list: string[]`
 * field on the parent form. Used on Incident + Daily Report pages so PM/GC/DOT
 * contacts who should receive a CC of the PDF can be captured explicitly and
 * printed on the final footer.
 */
export function DistributionList({ value = [], onChange, testIdPrefix = "dist" }) {
  const [input, setInput] = useState("");
  const list = value || [];

  const addEmail = (raw) => {
    const email = (raw || "").trim().toLowerCase();
    if (!email) return;
    if (!EMAIL_RE.test(email)) return;
    if (list.includes(email)) return;
    onChange([...list, email]);
    setInput("");
  };

  const removeEmail = (email) => {
    onChange(list.filter((e) => e !== email));
  };

  const onKey = (e) => {
    if (e.key === "Enter" || e.key === "," || e.key === " " || e.key === "Tab") {
      if (input.trim()) {
        e.preventDefault();
        addEmail(input);
      }
    } else if (e.key === "Backspace" && !input && list.length > 0) {
      e.preventDefault();
      removeEmail(list[list.length - 1]);
    }
  };

  return (
    <div data-testid={`${testIdPrefix}-wrapper`}>
      <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 flex items-center gap-1.5">
        <Mail className="w-3.5 h-3.5" />
        Distribution List
      </Label>
      <p className="text-xs text-slate-500 mt-0.5 mb-2">
        Extra emails that should receive this report (PM, GC, DOT inspector…). Prints on the PDF footer.
      </p>
      <div className="flex flex-wrap gap-1.5 mb-2" data-testid={`${testIdPrefix}-chips`}>
        {list.map((email) => (
          <span
            key={email}
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-100 text-slate-800 text-xs font-mono"
            data-testid={`${testIdPrefix}-chip-${email}`}
          >
            {email}
            <button
              type="button"
              onClick={() => removeEmail(email)}
              className="text-slate-500 hover:text-red-700"
              aria-label={`Remove ${email}`}
              data-testid={`${testIdPrefix}-remove-${email}`}
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          onBlur={() => input.trim() && addEmail(input)}
          placeholder="email@company.com — press Enter to add"
          className="h-11 text-sm border-2 border-slate-300"
          data-testid={`${testIdPrefix}-input`}
        />
        <Button
          type="button"
          variant="outline"
          onClick={() => addEmail(input)}
          disabled={!input.trim()}
          className="h-11 border-2 border-slate-300 hover:border-red-600"
          data-testid={`${testIdPrefix}-add-btn`}
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>
      {input && !EMAIL_RE.test(input.trim()) && (
        <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-amber-600 font-bold mt-1">
          Enter a valid email address
        </div>
      )}
    </div>
  );
}
