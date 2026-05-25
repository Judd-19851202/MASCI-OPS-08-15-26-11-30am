/**
 * components/auth/PasskeyEnrollPrompt.jsx · iter422 · Phase 24
 * ───────────────────────────────────────────────────────────────────
 * Calm, dismissible, post-login affordance offering Face ID / Touch ID /
 * Windows Hello enrollment for the current device.
 *
 * Self-gates on FOUR conditions — surfaces ONLY when ALL are true:
 *   1. Browser supports WebAuthn (passkeySupported)
 *   2. A platform authenticator exists (Face ID / Touch ID / Hello)
 *   3. Current directory session is present (getDirectoryToken)
 *   4. The user has NOT already enrolled a passkey on this account
 *   5. The user has NOT previously dismissed this prompt on this device
 *
 * Doctrine: calm, restrained, single-card, never nags. One "Not now"
 * click silences this device forever (per-device localStorage flag).
 */
import React, { useEffect, useState } from "react";
import { Fingerprint, X, Loader2 } from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  passkeySupported,
  platformAuthenticatorAvailable,
  listPasskeys,
  registerPasskey,
} from "@/lib/passkeys";
import { getDirectoryToken } from "@/lib/directoryAuth";
import { toast } from "sonner";

const DISMISS_KEY = "masci.passkey.enroll.dismissed";

export function PasskeyEnrollPrompt() {
  const { t } = useT();
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Gate 5 · user dismissed
        if (typeof localStorage !== "undefined"
            && localStorage.getItem(DISMISS_KEY) === "1") return;
        // Gate 1
        if (!passkeySupported()) return;
        // Gate 2
        const hasAuth = await platformAuthenticatorAvailable();
        if (cancelled || !hasAuth) return;
        // Gate 3
        if (!getDirectoryToken()) return;
        // Gate 4 · already enrolled
        let existing = [];
        try { existing = await listPasskeys(); } catch { return; }
        if (cancelled) return;
        const live = (existing || []).filter((p) => !p.disabled);
        if (live.length > 0) return;
        setShow(true);
      } catch {
        /* silent · operational continuity */
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const onDismiss = () => {
    try { localStorage.setItem(DISMISS_KEY, "1"); } catch { /* noop */ }
    setShow(false);
  };

  const onEnroll = async () => {
    setBusy(true);
    try {
      await registerPasskey({ friendlyName: "This device" });
      toast.success(t("Device sign-in enabled."), { duration: 4000 });
      try { localStorage.removeItem(DISMISS_KEY); } catch { /* noop */ }
      setShow(false);
    } catch (err) {
      const name = err?.name || "";
      const msg = err?.message || t("Device sign-in failed");
      if (name === "NotAllowedError" || /cancel/i.test(msg)) {
        // user cancelled · stay calm · keep prompt for next time
      } else {
        toast.error(msg, { duration: 5000 });
      }
    } finally {
      setBusy(false);
    }
  };

  if (!show) return null;

  return (
    <div
      data-testid="passkey-enroll-prompt"
      className="relative rounded-lg border-2 border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 shadow-sm"
    >
      <button
        type="button"
        onClick={onDismiss}
        aria-label={t("Not now")}
        data-testid="passkey-enroll-dismiss"
        className="absolute top-2 right-2 p-1.5 text-slate-400 hover:text-slate-700 rounded"
      >
        <X className="w-4 h-4" />
      </button>
      <div className="flex items-start gap-3 pr-6">
        <div className="shrink-0 w-10 h-10 rounded-md bg-red-50 border border-red-200 flex items-center justify-center">
          <Fingerprint className="w-5 h-5 text-red-700" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold text-slate-900">
            {t("Enable faster sign-in on this device?")}
          </div>
          <p className="mt-1 text-xs text-slate-600 leading-snug">
            {t("Your device's secure unlock will sign you in next time.")}
            {" "}
            {t("Your device handles Face ID / Touch ID securely. MASCI never stores biometric information.")}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={onEnroll}
              disabled={busy}
              data-testid="passkey-enroll-confirm"
              className="inline-flex items-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wide text-white bg-red-700 hover:bg-red-800 rounded disabled:opacity-50"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Fingerprint className="w-3.5 h-3.5" />}
              {busy ? t("Verifying device…") : t("Enable device sign-in")}
            </button>
            <button
              type="button"
              onClick={onDismiss}
              disabled={busy}
              data-testid="passkey-enroll-skip"
              className="px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-600 hover:text-slate-900"
            >
              {t("Not now")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
