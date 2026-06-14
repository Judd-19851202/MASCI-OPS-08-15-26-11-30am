import React, { useState, useEffect } from "react";
import { ShieldAlert, Loader2, Lock } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

/**
 * AdminPasswordConfirm — destructive-action confirmation dialog.
 *
 * Renders an "Are you sure?" pane with a description, an admin-password
 * input, Cancel + Confirm buttons. The Confirm button is disabled until a
 * non-empty password is typed; on click it POSTs to
 * /api/admin/auth/verify-password (HMAC-checks against ADMIN_PASSWORD on
 * the backend, with brute-force lockout) and only then fires onConfirm().
 *
 * Usage:
 *   const [open, setOpen] = useState(false);
 *   <AdminPasswordConfirm
 *     open={open}
 *     onOpenChange={setOpen}
 *     title="Delete backup file?"
 *     description="This backup .zip will be permanently removed."
 *     confirmLabel="Delete backup"
 *     destructive
 *     onConfirm={async () => { await api.delete(...); }}
 *   />
 */
export default function AdminPasswordConfirm({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  destructive = true,
  onConfirm,
  testId = "admin-password-confirm",
}) {
  const { t } = useT();
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  // Reset state every time the dialog reopens so we don't leak the
  // previous attempt's password into the next confirmation.
  useEffect(() => {
    if (open) {
      setPassword("");
      setBusy(false);
    }
  }, [open]);

  const handleConfirm = async () => {
    if (!password || busy) return;
    setBusy(true);
    try {
      await api.post("/admin/auth/verify-password", { password });
    } catch (e) {
      const detail = e?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : t("Wrong password. Try again."));
      setBusy(false);
      return;
    }
    try {
      await onConfirm();
      onOpenChange?.(false);
    } catch {
      // onConfirm is responsible for its own error toasts.
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid={testId}>
        <DialogHeader>
          <DialogTitle
            className={`font-display font-black flex items-center gap-2 ${
              destructive ? "text-red-700" : "text-slate-900"
            }`}
          >
            <ShieldAlert className="w-5 h-5" />
            {title}
          </DialogTitle>
          <DialogDescription className="leading-relaxed">
            {description}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold flex items-center gap-1.5">
            <Lock className="w-3 h-3" /> {t("Re-enter admin password to continue")}
          </label>
          <input
            type="password"
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleConfirm();
            }}
            placeholder={t("Admin password")}
            className="w-full h-11 px-3 border-2 border-slate-300 focus:border-red-700 focus:outline-none rounded font-mono text-sm"
            data-testid={`${testId}-password-input`}
            disabled={busy}
          />
        </div>
        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
            disabled={busy}
            data-testid={`${testId}-cancel`}
          >
            {t("Cancel")}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!password || busy}
            className={`font-bold uppercase tracking-wide disabled:bg-slate-400 ${
              destructive
                ? "bg-red-700 hover:bg-red-800 text-white"
                : "bg-slate-900 hover:bg-slate-800 text-white"
            }`}
            data-testid={`${testId}-confirm`}
          >
            {busy ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-1" /> {t("Verifying…")}
              </>
            ) : (
              confirmLabel || t("Confirm")
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
