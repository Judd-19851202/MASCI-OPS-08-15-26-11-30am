import React, { useState, forwardRef } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Input } from "@/components/ui/input";

/**
 * Password field with a show/hide toggle. Drop-in replacement for a raw
 * `<Input type="password" />`. Pass any standard Input props through.
 *
 * Usage:
 *   <PasswordInput value={pw} onChange={e => setPw(e.target.value)} required />
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
        className={`pr-11 ${className}`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        tabIndex={-1}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        data-testid={toggleTestId}
      >
        <Icon className="w-4 h-4" />
      </button>
    </div>
  );
});

export default PasswordInput;
