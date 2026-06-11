import React, { useState, forwardRef } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Input } from "@/components/ui/input";

/**
 * Password field with a show/hide toggle. Drop-in replacement for a raw
 * `<Input type="password" />`. Pass any standard Input props through.
 *
 * Usage:
 *   <PasswordInput value={pw} onChange={e => setPw(e.target.value)} required />
 *
 * iter-RC1-FH · M-15 mobile touch-target hardening · the show/hide toggle
 * is the most frequent control on every login page · the hit area is
 * now a guaranteed 36×36 px (above the 32 px floor, comfortable with
 * gloves on field iPhones).
 */
export const PasswordInput = forwardRef(function PasswordInput(
  { className = "", toggleTestId, ...props },
  ref
) {
  const [visible, setVisible] = useState(false);
  const Icon = visible ? EyeOff : Eye;
  return (
    <div className="relative">
      <Input
        {...props}
        ref={ref}
        type={visible ? "text" : "password"}
        className={`pr-12 ${className}`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        tabIndex={-1}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute right-1 top-1/2 -translate-y-1/2 inline-flex items-center justify-center min-h-[36px] min-w-[36px] rounded text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        data-testid={toggleTestId}
      >
        <Icon className="w-4 h-4" />
      </button>
    </div>
  );
});

export default PasswordInput;
