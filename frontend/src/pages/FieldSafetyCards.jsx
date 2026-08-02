import React, { useState } from "react";
import { Printer, Mail, MailPlus, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";

/**
 * Field Safety Cards — four bilingual wallet-sized handouts (EN front/back,
 * ES front/back) that crews carry. Shown as JPG previews (NOT raw PDFs)
 * per the owner's request so the screen stays quick and visual. Each
 * card offers:
 *   • Print   → window.print() on a print-only wrapper that shows ONLY
 *               the selected card image, letter-size, edge-to-edge.
 *   • Email   → sends the high-res PDF attachment via Resend.
 */

const CARD_SPECS = [
  {
    key: "en-front",
    titleKey: "English · Front",
    img: "/safety-cards/en-front.jpg",
    accent: "bg-red-700 border-red-800",
    labelKey: "EN / FRONT",
  },
  {
    key: "en-back",
    titleKey: "English · Back",
    img: "/safety-cards/en-back.jpg",
    accent: "bg-slate-800 border-slate-900",
    labelKey: "EN / BACK",
  },
  {
    key: "es-front",
    titleKey: "Español · Frente",
    img: "/safety-cards/es-front.jpg",
    accent: "bg-red-700 border-red-800",
    labelKey: "ES / FRENTE",
  },
  {
    key: "es-back",
    titleKey: "Español · Reverso",
    img: "/safety-cards/es-back.jpg",
    accent: "bg-slate-800 border-slate-900",
    labelKey: "ES / REVERSO",
  },
];

const DEFAULT_KEY = "masci.defaultRecipients.v1";
const isValidEmail = (s) =>
  typeof s === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.trim());

function EmailCardDialog({ open, onOpenChange, card, mode = "single" }) {
  const { t } = useT();
  // mode: "single" → email one card.  "all" → email all 4 cards.
  const [recipients, setRecipients] = useState([""]);
  const [subject, setSubject] = useState("");
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);

  React.useEffect(() => {
    if (!open) return;
    let saved = [];
    try {
      const raw = window.localStorage.getItem(DEFAULT_KEY);
      if (raw) saved = JSON.parse(raw) || [];
    } catch {
      /* noop */
    }
    const valid = saved.filter(isValidEmail);
    setRecipients(valid.length > 0 ? valid : [""]);
    if (mode === "all") {
      setSubject(t("MASCI Field Safety Cards — Full Bilingual Set"));
    } else if (card) {
      setSubject(`${t("MASCI Field Safety Card")} — ${card.title}`);
    }
    setNote("");
  }, [open, card, mode, t]);

  const setAt = (i, v) =>
    setRecipients((r) => r.map((x, idx) => (idx === i ? v : x)));
  const addRow = () => setRecipients((r) => [...r, ""]);
  const removeRow = (i) =>
    setRecipients((r) => (r.length === 1 ? [""] : r.filter((_, idx) => idx !== i)));

  const send = async () => {
    const valid = recipients.map((s) => s.trim()).filter(isValidEmail);
    if (valid.length === 0) {
      toast.error(t("Add at least one recipient email"));
      return;
    }
    setSending(true);
    try {
      const endpoint =
        mode === "all" ? "/safety-cards/email-all" : "/safety-cards/email";
      const payload =
        mode === "all"
          ? { recipients: valid, subject: subject.trim(), note: note.trim() }
          : {
              card: card.key,
              recipients: valid,
              subject: subject.trim(),
              note: note.trim(),
            };
      const res = await api.post(endpoint, payload);
      try {
        window.localStorage.setItem(DEFAULT_KEY, JSON.stringify(valid));
      } catch {
        /* noop */
      }
      if (mode === "all") {
        const kb = ((res.data?.total_size_bytes || 0) / 1024).toFixed(0);
        toast.success(
          `Sent all ${res.data?.card_count || 4} cards (${kb} KB) to ${valid.length} recipient${valid.length === 1 ? "" : "s"}`
        );
      } else {
        const kb = ((res.data?.size_bytes || 0) / 1024).toFixed(0);
        toast.success(
          `Sent (${kb} KB PDF) to ${valid.length} recipient${valid.length === 1 ? "" : "s"}`
        );
      }
      onOpenChange(false);
    } catch (e) {
      toast.error(operationalError(e,
        "Email send temporarily unavailable. Try again in a moment.",
        "Your session expired. Please sign in again."));
    } finally {
      setSending(false);
    }
  };

  // In single mode without a card, render nothing (used as placeholder).
  if (mode === "single" && !card) return null;

  const titleText =
    mode === "all" ? t("Email All Safety Cards") : t("Email Safety Card");
  const descText =
    mode === "all"
      ? t("Sends the complete bilingual set (EN front+back, ES front+back) as 4 PDF attachments — perfect for onboarding a new hire in one tap.")
      : (
          <>
            {t("Sends the print-ready PDF of")} <strong>{card?.title}</strong> {t("as an attachment.")}
          </>
        );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="safety-card-email-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl flex items-center gap-2">
            {mode === "all" ? (
              <MailPlus className="w-5 h-5 text-red-700" />
            ) : (
              <Mail className="w-5 h-5 text-red-700" />
            )}{" "}
            {titleText}
          </DialogTitle>
          <DialogDescription>{descText}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-3 py-2">
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              To *
            </Label>
            <div className="mt-2 space-y-2">
              {recipients.map((r, i) => (
                <div key={i} className="flex gap-2">
                  <Input
                    type="email"
                    inputMode="email"
                    value={r}
                    onChange={(e) => setAt(i, e.target.value)}
                    placeholder="name@company.com"
                    className="h-12 text-base border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-600"
                    data-testid={`safety-card-email-to-${i}`}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeRow(i)}
                    className="h-12 w-12 text-slate-400 hover:text-red-700"
                    data-testid={`safety-card-email-rm-${i}`}
                    aria-label="Remove email recipient"
                    title="Remove"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addRow}
              className="mt-2 font-mono text-xs uppercase tracking-[0.2em]"
              data-testid="safety-card-email-add"
            >
              + Add recipient
            </Button>
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Subject
            </Label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="h-12 text-base mt-2 border-2 border-slate-300"
              data-testid="safety-card-email-subject"
            />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700">
              Note (optional)
            </Label>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              className="text-base mt-2 border-2 border-slate-300"
              data-testid="safety-card-email-note"
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={sending}
            data-testid="safety-card-email-cancel"
          >
            Cancel
          </Button>
          <Button
            onClick={send}
            disabled={sending}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
            data-testid="safety-card-email-send"
          >
            {sending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Sending…
              </>
            ) : (
              <>
                <Mail className="w-4 h-4 mr-2" /> Send
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function FieldSafetyCards() {
  const { t } = useT();
  const [printing, setPrinting] = useState(null); // card.key currently being printed
  const [emailing, setEmailing] = useState(null); // card object for single dialog
  const [emailingAll, setEmailingAll] = useState(false); // bulk dialog open?
  const cards = React.useMemo(
    () => CARD_SPECS.map((card) => ({
      ...card,
      title: t(card.titleKey),
      label: t(card.labelKey),
    })),
    [t],
  );

  const handlePrint = (card) => {
    // Swap in the print-only card, fire window.print(), then clear.
    setPrinting(card.key);
    // Give React a tick to render the print-only image, then print.
    setTimeout(() => {
      window.print();
      setTimeout(() => setPrinting(null), 500);
    }, 120);
  };

  return (
    <OperationalPageFrame
      testId="safety-cards-page"
      backTo="/safety"
      backLabel={t("Back to Safety")}
      accent="red"
      familyLabel={t("Safety")}
      familyMeta={t("Crew handouts")}
      mainWidthClass="max-w-6xl"
      heroIcon={MailPlus}
      kicker={t("Safety · Field Handouts")}
      title={t("Field Safety Cards")}
      description={t("Wallet-sized bilingual handouts for every crew member. Print a single card on demand or send the full four-card set to onboarding, supervisors, or subcontractors in one step.")}
      heroMeta={(
        <>
          <OperationalStatusBadge tone="red" testId="safety-cards-print-ready">{t("Print-ready PDFs")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="cyan" testId="safety-cards-bilingual">{t("English + Spanish")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="amber" testId="safety-cards-crew-use">{t("Crew distribution")}</OperationalStatusBadge>
        </>
      )}
      heroAside={(
        <div className="rounded-[1.75rem] border border-slate-900/70 bg-slate-950 px-5 py-5 text-white shadow-[0_24px_60px_rgba(15,23,42,0.22)]" data-testid="safety-cards-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-white/55">{t("Fast distribution")}</div>
          <div className="mt-2 text-lg font-semibold leading-tight">{t("Send the full bilingual pack in one tap.")}</div>
          <p className="mt-2 text-sm leading-6 text-white/74">
            {t("Use the full set when a new hire, foreman, or external crew needs the same field guidance immediately.")}
          </p>
          <Button
            onClick={() => setEmailingAll(true)}
            className="mt-4 h-12 w-full bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-[0.16em] text-xs"
            data-testid="safety-cards-email-all-btn"
          >
            <MailPlus className="w-4 h-4 mr-2" />
            {t("Email All 4 Cards")}
          </Button>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Crew-safe distribution")}
    >
      <div className="no-print space-y-5">
        <section className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-7" data-testid="safety-cards-grid">
          {cards.map((card) => (
            <article
              key={card.key}
              className="wp17-public-card overflow-hidden flex flex-col border border-slate-200/85 hover:border-red-400 transition-colors duration-150"
              data-testid={`safety-card-${card.key}`}
            >
              <div className="relative bg-slate-100/90 border-b border-slate-200 aspect-[8.5/11] overflow-hidden">
                <img
                  src={card.img}
                  alt={card.title}
                  className="absolute inset-0 w-full h-full object-contain"
                  loading="lazy"
                />
                <span
                  className={`absolute top-3 left-3 ${card.accent} text-white font-mono text-[10px] uppercase tracking-[0.25em] font-bold px-2.5 py-1 rounded border-b-2`}
                >
                  {card.label}
                </span>
              </div>
              <div className="p-4 sm:p-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="space-y-1">
                  <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">
                    {card.title}
                  </h2>
                  <p className="text-sm text-slate-600">
                    {t("Use the same card crews carry in the field — print it or email the PDF instantly.")}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    onClick={() => handlePrint(card)}
                    className="h-10 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs"
                    data-testid={`safety-card-print-${card.key}`}
                  >
                    <Printer className="w-3.5 h-3.5 mr-1" /> {t("Print")}
                  </Button>
                  <Button
                    onClick={() => setEmailing(card)}
                    className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs"
                    data-testid={`safety-card-email-${card.key}`}
                  >
                    <Mail className="w-3.5 h-3.5 mr-1" /> {t("Email")}
                  </Button>
                </div>
              </div>
            </article>
          ))}
        </section>
      </div>

      {/* Print-only wrapper: renders the single selected card edge-to-edge
          on a letter-size page so Cmd+P produces a clean single sheet. */}
      {printing && (
        <div className="print-only-card">
          <img
            src={cards.find((c) => c.key === printing)?.img}
            alt="Safety Card"
          />
        </div>
      )}

      <EmailCardDialog
        open={!!emailing}
        onOpenChange={(v) => !v && setEmailing(null)}
        card={emailing}
        mode="single"
      />

      <EmailCardDialog
        open={emailingAll}
        onOpenChange={setEmailingAll}
        card={null}
        mode="all"
      />

      <style>{`
        .print-only-card { display: none; }
        @media print {
          @page { size: letter; margin: 0; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; background: white !important; }
          .no-print, .no-print * { display: none !important; }
          [data-testid="safety-cards-page"],
          [data-testid="safety-cards-page"] * { display: none !important; }
          .print-only-card {
            display: block !important;
            position: fixed;
            inset: 0;
            width: 100%;
            height: 100%;
            background: white;
            z-index: 999999;
          }
          .print-only-card img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
          }
        }
      `}</style>
    </OperationalPageFrame>
  );
}

