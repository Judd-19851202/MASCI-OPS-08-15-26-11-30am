import React, { useState } from "react";
import { ArrowLeft, Printer, Mail, Loader2, X } from "lucide-react";
import { Link } from "react-router-dom";
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
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
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

const CARDS = [
  {
    key: "en-front",
    title: "English · Front",
    img: "/safety-cards/en-front.jpg",
    accent: "bg-red-700 border-red-800",
    label: "EN / FRONT",
  },
  {
    key: "en-back",
    title: "English · Back",
    img: "/safety-cards/en-back.jpg",
    accent: "bg-slate-800 border-slate-900",
    label: "EN / BACK",
  },
  {
    key: "es-front",
    title: "Español · Frente",
    img: "/safety-cards/es-front.jpg",
    accent: "bg-red-700 border-red-800",
    label: "ES / FRENTE",
  },
  {
    key: "es-back",
    title: "Español · Reverso",
    img: "/safety-cards/es-back.jpg",
    accent: "bg-slate-800 border-slate-900",
    label: "ES / REVERSO",
  },
];

const DEFAULT_KEY = "masci.defaultRecipients.v1";
const isValidEmail = (s) =>
  typeof s === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.trim());

function EmailCardDialog({ open, onOpenChange, card }) {
  const [recipients, setRecipients] = useState([""]);
  const [subject, setSubject] = useState("");
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);

  React.useEffect(() => {
    if (!open || !card) return;
    let saved = [];
    try {
      const raw = window.localStorage.getItem(DEFAULT_KEY);
      if (raw) saved = JSON.parse(raw) || [];
    } catch {
      /* noop */
    }
    const valid = saved.filter(isValidEmail);
    setRecipients(valid.length > 0 ? valid : [""]);
    setSubject(`MASCI Field Safety Card — ${card.title}`);
    setNote("");
  }, [open, card]);

  const setAt = (i, v) =>
    setRecipients((r) => r.map((x, idx) => (idx === i ? v : x)));
  const addRow = () => setRecipients((r) => [...r, ""]);
  const removeRow = (i) =>
    setRecipients((r) => (r.length === 1 ? [""] : r.filter((_, idx) => idx !== i)));

  const send = async () => {
    const valid = recipients.map((s) => s.trim()).filter(isValidEmail);
    if (valid.length === 0) {
      toast.error("Add at least one recipient email");
      return;
    }
    setSending(true);
    try {
      const res = await api.post("/safety-cards/email", {
        card: card.key,
        recipients: valid,
        subject: subject.trim(),
        note: note.trim(),
      });
      try {
        window.localStorage.setItem(DEFAULT_KEY, JSON.stringify(valid));
      } catch {
        /* noop */
      }
      toast.success(
        `Sent (${((res.data?.size_bytes || 0) / 1024).toFixed(0)} KB PDF) to ${valid.length} recipient${valid.length === 1 ? "" : "s"}`
      );
      onOpenChange(false);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Email send failed");
    } finally {
      setSending(false);
    }
  };

  if (!card) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="safety-card-email-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl flex items-center gap-2">
            <Mail className="w-5 h-5 text-red-700" /> Email Safety Card
          </DialogTitle>
          <DialogDescription>
            Sends the print-ready PDF of <strong>{card.title}</strong> as an attachment.
          </DialogDescription>
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
  const [emailing, setEmailing] = useState(null); // card object for dialog

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
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe no-print" />
      <header className="bg-slate-900 border-b-4 border-red-700 no-print">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/safety" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/safety" />
          <div className="flex items-center gap-2">
            <LangToggle />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12 no-print">
        <div className="mb-6">
          <Link
            to="/safety"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="safety-cards-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Safety")}
          </Link>
        </div>

        <div className="mb-10 flex items-start gap-4">
          <div className="flex-1">
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
              {t("Safety · Field Handouts")}
            </span>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-1">
              {t("Field Safety Cards")}
            </h1>
            <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
              {t(
                "Wallet-sized bilingual safety cards for every crew member. Print on 8.5 × 11 letter paper, fold, or hand out digitally by email."
              )}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-7">
          {CARDS.map((card) => (
            <article
              key={card.key}
              className="bg-white border-2 border-slate-300 rounded-md overflow-hidden flex flex-col shadow-sm hover:shadow-md hover:border-red-700 transition-all duration-150"
              data-testid={`safety-card-${card.key}`}
            >
              <div className="relative bg-slate-100 border-b-2 border-slate-200 aspect-[8.5/11] overflow-hidden">
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
              <div className="p-4 sm:p-5 flex items-center justify-between gap-3">
                <h3 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">
                  {card.title}
                </h3>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => handlePrint(card)}
                    className="h-10 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs border-b-2 border-black"
                    data-testid={`safety-card-print-${card.key}`}
                  >
                    <Printer className="w-3.5 h-3.5 mr-1" /> {t("Print")}
                  </Button>
                  <Button
                    onClick={() => setEmailing(card)}
                    className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs border-b-2 border-red-900"
                    data-testid={`safety-card-email-${card.key}`}
                  >
                    <Mail className="w-3.5 h-3.5 mr-1" /> {t("Email")}
                  </Button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </main>

      {/* Print-only wrapper: renders the single selected card edge-to-edge
          on a letter-size page so Cmd+P produces a clean single sheet. */}
      {printing && (
        <div className="print-only-card">
          <img
            src={CARDS.find((c) => c.key === printing)?.img}
            alt="Safety Card"
          />
        </div>
      )}

      <EmailCardDialog
        open={!!emailing}
        onOpenChange={(v) => !v && setEmailing(null)}
        card={emailing}
      />

      <style>{`
        .print-only-card { display: none; }
        @media print {
          @page { size: letter; margin: 0; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; background: white !important; }
          .no-print, .no-print * { display: none !important; }
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
    </div>
  );
}
