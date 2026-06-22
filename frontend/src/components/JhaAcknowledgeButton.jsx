/**
 * OMEGA · FOCP Release 2 · TR-0001 · JHP Acknowledgement Button
 *
 * Reusable employee-acknowledgement affordance for the public /jha
 * page. Renders inline with each JHP file row. Captures:
 *   - employee email (lookup key into db.employees)
 *   - typed signature (full name)
 * On success: surfaces a permanent ✓ for that file by re-reading
 * /api/jha-acknowledgements/me and bubbling state up via onChange.
 *
 * Bilingual via useT().
 */
import React, { useState } from "react";
import { CheckCircle2, FileSignature, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT, getLang } from "@/lib/i18n";

export function JhaAcknowledgeButton({
  projectNumber,
  fileId,
  filename,
  acked,
  defaultEmail,
  onAcknowledged,
}) {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState(defaultEmail || "");
  const [signature, setSignature] = useState("");
  const [busy, setBusy] = useState(false);

  if (acked) {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-3 h-10 rounded-md bg-emerald-50 text-emerald-800 border-2 border-emerald-300 font-mono text-[10px] uppercase tracking-[0.18em] font-bold"
        data-testid={`jha-ack-done-${fileId}`}
        title={t("You have acknowledged this Hazard Plan.")}
      >
        <CheckCircle2 className="w-3.5 h-3.5" /> {t("Acknowledged")}
      </span>
    );
  }

  const submit = async () => {
    const cleanEmail = (email || "").trim().toLowerCase();
    const cleanSig = (signature || "").trim();
    if (!cleanEmail) {
      toast.error(t("Enter your work email."));
      return;
    }
    if (cleanSig.length < 3) {
      toast.error(t("Type your full name as your signature."));
      return;
    }
    setBusy(true);
    try {
      const r = await api.post("/jha-acknowledgements", {
        project_number: projectNumber,
        jha_file_id: fileId,
        employee_email: cleanEmail,
        signature: cleanSig,
        locale: getLang(),
      });
      toast.success(t("Acknowledgement recorded."));
      setOpen(false);
      setSignature("");
      try {
        window.localStorage.setItem("masci.jha.email", cleanEmail);
      } catch {
        /* noop */
      }
      if (onAcknowledged) onAcknowledged(r.data?.acknowledgement, cleanEmail);
    } catch (err) {
      const code = err?.response?.data?.detail?.code || "";
      if (code === "employee_not_found") {
        toast.error(t("No employee on file matches that email. Get with your PM."));
      } else if (code === "employee_email_invalid") {
        toast.error(t("That email format isn't valid."));
      } else if (code === "signature_required_min3") {
        toast.error(t("Type your full name as your signature."));
      } else {
        toast.error(t("Acknowledgement failed. Try again."));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button
        type="button"
        onClick={() => {
          setEmail(defaultEmail || email || "");
          setSignature("");
          setOpen(true);
        }}
        className="h-10 px-4 rounded-md bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm uppercase tracking-wide"
        data-testid={`jha-ack-open-${fileId}`}
      >
        <FileSignature className="w-4 h-4 mr-1" />
        {t("Acknowledge")}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md" data-testid="jha-ack-modal">
          <DialogHeader>
            <DialogTitle>{t("Acknowledge Job Hazard Plan")}</DialogTitle>
            <DialogDescription>
              {t(
                "I have read this Hazard Plan and understand the site hazards, PPE requirements, and emergency response."
              )}
              <span className="block mt-2 font-mono text-[11px] text-slate-600">
                {filename}
                <br />
                {t("Project")}: <b>{projectNumber}</b>
              </span>
            </DialogDescription>
          </DialogHeader>

          <div className="py-2 space-y-3">
            <div>
              <Label htmlFor="jha-ack-email" className="text-xs uppercase tracking-wide font-bold">
                {t("Work email")}
              </Label>
              <Input
                id="jha-ack-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@yourcompany.com"
                className="mt-1.5 h-11 border-2 border-slate-300"
                data-testid="jha-ack-email-input"
                autoComplete="email"
              />
            </div>
            <div>
              <Label htmlFor="jha-ack-signature" className="text-xs uppercase tracking-wide font-bold">
                {t("Signature (type your full name)")}
              </Label>
              <Input
                id="jha-ack-signature"
                value={signature}
                onChange={(e) => setSignature(e.target.value)}
                placeholder={t("Full name")}
                className="mt-1.5 h-11 border-2 border-slate-300 font-display"
                data-testid="jha-ack-signature-input"
                autoComplete="name"
              />
            </div>
            <p className="text-[11px] text-slate-500 italic">
              {t("Your acknowledgement is permanent and visible to your supervisor.")}
            </p>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              data-testid="jha-ack-cancel"
            >
              {t("Cancel")}
            </Button>
            <Button
              onClick={submit}
              disabled={busy}
              className="bg-amber-700 hover:bg-amber-800 text-white"
              data-testid="jha-ack-confirm"
            >
              {busy ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <FileSignature className="w-4 h-4 mr-1" />
              )}
              {t("Sign and Acknowledge")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default JhaAcknowledgeButton;
