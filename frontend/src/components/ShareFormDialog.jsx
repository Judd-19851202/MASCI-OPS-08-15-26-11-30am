import React, { useMemo, useState } from "react";
import { Share2, Copy, Check, ExternalLink, Printer } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export const ShareFormDialog = ({
  formType = "inspection",
  path = "/submit",
  title = "Share Inspection Form",
  description = "Give this link or QR code to anyone who needs to fill out a safety inspection. No login required — submissions show up here automatically.",
  testIdPrefix = "share",
}) => {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const publicUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    return `${window.location.origin}${path}`;
  }, [path]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl);
      setCopied(true);
      toast.success("Link copied");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy — long-press the link to copy manually");
    }
  };

  const nativeShare = async () => {
    const shareData = {
      title: "MASCI Job Site Safety Inspection",
      text: "Fill out today's safety inspection:",
      url: publicUrl,
    };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch {
        /* user cancelled */
      }
    } else {
      copy();
    }
  };

  const printQr = () => {
    const w = window.open("", "_blank");
    if (!w) {
      toast.error("Pop-up blocked — allow pop-ups to print the QR poster");
      return;
    }
    w.document.write(`<!doctype html>
<html><head><title>MASCI Operations Platform — Inspection QR</title>
<style>
  @page { size: Letter portrait; margin: 0.5in; }
  body { font-family: 'Chivo', Arial, sans-serif; text-align: center; padding: 24px; color: #000; }
  .stripe { background: repeating-linear-gradient(45deg,#c8102e,#c8102e 14px,#000 14px,#000 28px); height: 14px; margin-bottom: 24px; }
  h1 { font-size: 42px; margin: 8px 0 4px; font-weight: 900; letter-spacing: -0.02em; }
  .sub { font-size: 14px; letter-spacing: 0.25em; text-transform: uppercase; color: #c8102e; font-weight: 700; margin-bottom: 24px; }
  .qr { display: inline-block; padding: 24px; border: 4px solid #000; }
  .url { font-family: 'IBM Plex Mono', monospace; font-size: 13px; margin-top: 16px; word-break: break-all; }
  .tag { font-size: 18px; font-weight: 800; margin-top: 24px; }
  .foot { font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: #555; margin-top: 16px; }
</style></head><body>
  <div class="stripe"></div>
  <h1>MASCI SAFETY</h1>
  <div style="font-size:22px;font-weight:700;margin-bottom:18px">Scan to fill out today's<br/>Job Site Safety Inspection</div>
  <div class="qr">${document.getElementById("masci-share-qr")?.outerHTML || ""}</div>
  <div class="url">${publicUrl}</div>
  <div class="tag">POST IN TRAILER · TOOL BOX · TRUCK CAB</div>
  <div class="foot">Generated through MASCI Operations Platform &mdash; Powered by ForgedOps&trade; | &copy; 2026 ForgedOps&trade;</div>
  <div class="stripe" style="margin-top:24px"></div>
</body></html>`);
    w.document.close();
    setTimeout(() => w.print(), 400);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="h-12 sm:h-14 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 hover:text-white font-bold uppercase tracking-wide text-sm"
          data-testid={`${testIdPrefix}-form-btn`}
        >
          <Share2 className="w-4 h-4 mr-2" />
          <span className="hidden sm:inline">Share Form</span>
          <span className="sm:hidden">Share</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md" data-testid={`${testIdPrefix}-form-dialog`}>
        <DialogHeader>
          <DialogTitle className="font-display text-2xl">{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-5 pt-2">
          {/* QR Code */}
          <div className="flex flex-col items-center gap-3 py-4 bg-slate-50 border border-slate-200 rounded-md">
            <div className="bg-white p-3 border-2 border-slate-900 rounded">
              <QRCodeSVG
                id="masci-share-qr"
                value={publicUrl}
                size={180}
                level="H"
                marginSize={2}
                fgColor="#0f172a"
                data-testid={`${testIdPrefix}-qr`}
              />
            </div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
              Scan with phone camera
            </div>
          </div>

          {/* URL */}
          <div className="flex gap-2">
            <Input
              readOnly
              value={publicUrl}
              className="h-12 text-sm font-mono border-2 border-slate-300"
              data-testid={`${testIdPrefix}-url`}
              onFocus={(e) => e.target.select()}
            />
            <Button
              onClick={copy}
              className="h-12 px-4 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-sm"
              data-testid={`${testIdPrefix}-copy`}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>

          {/* Action buttons */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={nativeShare}
              className="h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid={`${testIdPrefix}-native`}
            >
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
            <Button
              onClick={printQr}
              variant="outline"
              className="h-12 border-2 border-slate-300 font-bold uppercase tracking-wide text-sm"
              data-testid={`${testIdPrefix}-print-qr`}
            >
              <Printer className="w-4 h-4 mr-2" />
              Print QR
            </Button>
          </div>

          <a
            href={publicUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1 text-sm text-slate-600 hover:text-red-700 font-mono uppercase tracking-wider"
            data-testid={`${testIdPrefix}-open`}
          >
            Preview the form <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </DialogContent>
    </Dialog>
  );
};
