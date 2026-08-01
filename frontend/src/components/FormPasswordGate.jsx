import React, { useState, useEffect } from "react";
import { Lock, Unlock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/PasswordInput";
import { CanonicalHeader } from "@/components/CanonicalHeader";

/**
 * <FormPasswordGate>
 *   storageKey — sessionStorage key used to remember the unlock for the tab session
 *   password   — the plain-text password to match (case-sensitive)
 *   formLabel  — human-readable name shown on the gate ("Site Inspection")
 *
 * Once unlocked, stays unlocked for the rest of the browser tab session
 * (sessionStorage). Closing the tab re-prompts on next visit.
 */
export function FormPasswordGate({
  storageKey = "masci.gate.unlocked",
  password,
  formLabel,
  children,
}) {
  const [unlocked, setUnlocked] = useState(false);
  const [pw, setPw] = useState("");
  const [err, setErr] = useState(false);

  useEffect(() => {
    try {
      if (sessionStorage.getItem(storageKey) === "1") setUnlocked(true);
    } catch {
      /* ignore storage errors */
    }
  }, [storageKey]);

  if (unlocked) return children;

  const onSubmit = (e) => {
    e.preventDefault();
    if (pw === password) {
      try { sessionStorage.setItem(storageKey, "1"); } catch { /* ignore */ }
      setUnlocked(true);
    } else {
      setErr(true);
      setPw("");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="caution-stripe" />
      <CanonicalHeader
        portalLabel="MASCI Operations Platform"
        pageLabel="Restricted form access"
        accent="red"
        homeTo="/"
        showHomeLink={false}
        showLangToggle={false}
        containerClassName="max-w-3xl"
        testIdPrefix="form-password-gate"
      />

      <main className="flex-1 flex items-center justify-center px-5 sm:px-8 py-12">
        <form
          onSubmit={onSubmit}
          className="max-w-md w-full bg-white border border-slate-200 rounded-md p-8 sm:p-10 text-center"
          data-testid="form-password-gate"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-900 mb-5">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            Restricted Form
          </span>
          <h1 className="font-display text-3xl font-black tracking-tight text-slate-900 mt-2">
            {formLabel}
          </h1>
          <p className="text-slate-600 text-sm mt-3 leading-relaxed">
            This form is restricted. Enter the access code provided by your supervisor.
          </p>

          <div className="mt-6 text-left">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
              Access Code
            </label>
            <PasswordInput
              value={pw}
              onChange={(e) => { setPw(e.target.value); if (err) setErr(false); }}
              autoFocus
              autoComplete="off"
              inputMode="numeric"
              className={`mt-1 h-12 text-center text-lg font-mono tracking-[0.25em] border-2 ${
                err ? "border-red-700 bg-red-50" : "border-slate-300"
              }`}
              data-testid="form-gate-input"
              toggleTestId="form-gate-toggle"
            />
            {err && (
              <div className="mt-2 flex items-center gap-1.5 text-red-700 text-sm font-bold">
                <AlertCircle className="w-4 h-4" /> Wrong code. Try again.
              </div>
            )}
          </div>

          <Button
            type="submit"
            className="mt-6 w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900"
            data-testid="form-gate-submit"
          >
            <Unlock className="w-4 h-4 mr-2" /> Unlock Form
          </Button>

          <div className="mt-8 pt-5 border-t-2 border-slate-100 font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold flex items-center justify-center gap-2 flex-wrap" hidden>
            <span>No Guesswork.</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span>No Missed Steps.</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span>No Excuses.</span>
          </div>
        </form>
      </main>
    </div>
  );
}
