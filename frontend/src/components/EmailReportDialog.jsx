import React, { useEffect, useState } from "react";
import { brandCompanyName } from "@/lib/brandFilename";
import { Mail, Loader2, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

const DEFAULT_KEY = "masci.defaultRecipients.v1";

const inputCls =
  "h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600";

const isValidEmail = (s) =>
  typeof s === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.trim());

/**
 * Email-report dialog.
 *
 * - Opens from any View page via the parent's open / setOpen state.
 * - Pre-fills "To" with addresses already saved on the record (gc_email,
 *   pm_email, dot_email, email_recipients[]) AND the office's saved
 *   default recipients in localStorage. The user can edit / add / remove
 *   any address before sending — that's the 3c "both" choice in action.
 * - Saves the *new* default-recipient list back to localStorage on
 *   successful send so subsequent reports prefill faster.
 */
export function EmailReportDialog({ open, onOpenChange, kind, record }) {
  const { t } = useT();
  const [recipients, setRecipients] = useState([""]);
  const [subject, setSubject] = useState("");
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);

  // Prime the dialog every time it opens
  useEffect(() => {
    if (!open || !record) return;
    const fromRecord = [
      record.gc_email,
      record.pm_email,
      record.dot_email,
      ...((Array.isArray(record.email_recipients) && record.email_recipients) ||
        []),
    ].filter(isValidEmail);

    let saved = [];
    try {
      const raw = window.localStorage.getItem(DEFAULT_KEY);
      if (raw) saved = JSON.parse(raw) || [];
    } catch {
      /* noop */
    }
    const merged = Array.from(
      new Set([...fromRecord, ...saved.filter(isValidEmail)])
    );
    setRecipients(merged.length > 0 ? merged : [""]);

    const proj = record.project_name || record.project || brandCompanyName("Project");
    const date = record.report_date || record.date || record.incident_date || "";
    const title =
      kind === "daily-report"
        ? t("Daily Job Report")
        : kind === "inspection"
        ? t("Site Inspection")
        : kind === "meeting"
        ? t("Safety Meeting")
        : kind === "jha"
        ? t("Job Hazard Plan")
        : t("Incident Report");
    setSubject(`${title} — ${proj}${date ? ` (${date})` : ""}`);
    setNote("");
  }, [open, record, kind]);

  const setAt = (i, v) =>
    setRecipients((r) => r.map((x, idx) => (idx === i ? v : x)));
  const addRow = () => setRecipients((r) => [...r, ""]);
  const removeRow = (i) =>
    setRecipients((r) =>
      r.length === 1 ? [""] : r.filter((_, idx) => idx !== i)
    );

  const send = async () => {
    const valid = recipients.map((s) => s.trim()).filter(isValidEmail);
    if (valid.length === 0) {
      toast.error(t("Add at least one recipient email"));
      return;
    }
    if (!subject.trim()) {
      toast.error(t("Subject is required"));
      return;
    }
    setSending(true);
    try {
      const res = await api.post("/email-report", {
        kind,
        record_id: record.id,
        recipients: valid,
        subject: subject.trim(),
        note: note.trim(),
      });
      // Persist the recipient list as new defaults
      try {
        window.localStorage.setItem(DEFAULT_KEY, JSON.stringify(valid));
      } catch {
        /* noop */
      }
      toast.success(
        `${t("Sent")} (${(res.data?.size_bytes / 1024 || 0).toFixed(0)} KB PDF) ${t("to")} ${valid.length} ${t(valid.length === 1 ? "recipient" : "recipients")}`
      );
      onOpenChange(false);
    } catch (e) {
      const msg =
        e?.response?.data?.detail || e?.message || t("Email send failed");
      toast.error(msg);
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-lg"
        data-testid="email-report-dialog"
      >
        <DialogHeader>
          <DialogTitle className="font-display text-2xl flex items-center gap-2">
            <Mail className="w-5 h-5 text-red-700" />
            {t("Send this report")}
          </DialogTitle>
          <DialogDescription>
            {t("Build a PDF, email it to the right people, and remember this list for next time.")}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 py-2">
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("To *")}
            </Label>
            <div className="mt-2 space-y-2">
              {recipients.map((r, i) => (
                <div key={i} className="flex gap-2">
                  <Input
                    type="email"
                    inputMode="email"
                    value={r}
                    onChange={(e) => setAt(i, e.target.value)}
                    placeholder={t("name@company.com")}
                    className={inputCls}
                    data-testid={`email-recipient-${i}`}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => removeRow(i)}
                    className="h-12 w-12 border-2 border-slate-300 text-slate-500 hover:text-red-700 hover:border-red-700 flex-shrink-0"
                    aria-label={t("Remove recipient")}
                    data-testid={`email-recipient-remove-${i}`}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={addRow}
                className="h-9 border-2 border-slate-300 text-slate-700 font-mono text-xs uppercase tracking-[0.2em] font-bold"
                data-testid="email-add-recipient"
              >
                {t("+ Add email")}
              </Button>
            </div>
          </div>

          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Subject *")}
            </Label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className={inputCls}
              data-testid="email-subject"
            />
          </div>

          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              {t("Note (optional)")}
            </Label>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={t("Add any job context or action request for the people receiving this report")}
              className="min-h-[90px] text-base border-2 border-slate-300 mt-1"
              data-testid="email-note"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={sending}
            data-testid="email-cancel"
          >
            {t("Cancel")}
          </Button>
          <Button
            onClick={send}
            disabled={sending}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900"
            data-testid="email-send"
          >
            {sending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Sending…")}
              </>
            ) : (
              <>
                <Mail className="w-4 h-4 mr-2" /> {t("Send report PDF")}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
