import { useState } from "react";
import { Download, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { resolvePhotoSrc } from "@/lib/photoSrc";

/**
 * PhotoLightbox
 * -------------
 * Wraps any thumbnail. Click → full-size modal preview with a "Save" button
 * that downloads the original image standalone (works for http URLs AND
 * base64 `data:` URIs). Used everywhere field photos are shown so crews can
 * pull a photo off any inspection / daily report / incident / meeting /
 * equipment record without screenshotting.
 *
 * Props
 * - src:        photo URL or data: URI (required)
 * - alt:        accessibility label / caption shown in the modal toolbar
 * - filename:   suggested filename when saved (defaults to masci-photo-<ts>.jpg)
 * - className:  applied to the trigger <button> (so the parent grid layout
 *               survives — typically "absolute inset-0 …" identical to the
 *               original <img> wrapper)
 * - children:   the thumbnail <img> (kept as-is so existing styles win)
 *
 * Hidden in print — the modal trigger is a <button>, but the parent print
 * styles already collapse its overlay; the underlying <img> still prints.
 */
export const PhotoLightbox = ({
  src,
  alt = "",
  filename,
  className = "",
  children,
  testId = "photo-lightbox",
}) => {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  // Iter64: src may be a photo:// ref (R2-backed). Resolve to an actual
  // browser-loadable URL before rendering or fetching. resolvePhotoSrc
  // pass-throughs data: URLs and http(s) URLs unchanged, so this is safe
  // for every legacy and new caller.
  const resolvedSrc = resolvePhotoSrc(src);

  const download = async () => {
    if (!resolvedSrc) return;
    setBusy(true);
    try {
      // fetch supports both http(s) and data: URIs and gives us a Blob.
      const r = await fetch(resolvedSrc);
      const blob = await r.blob();
      const ext =
        (blob.type && blob.type.split("/")[1]) ||
        (resolvedSrc.startsWith("data:image/")
          ? resolvedSrc.slice(11, resolvedSrc.indexOf(";"))
          : "jpg");
      const fname =
        filename || `masci-photo-${Date.now()}.${ext.replace("jpeg", "jpg")}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      a.remove();
      // give the browser a tick before revoking
      setTimeout(() => URL.revokeObjectURL(url), 1500);
      toast.success("Saved to your device");
    } catch {
      // Cross-origin or unsupported — open in a new tab so the user can
      // long-press / right-click "Save image as…".
      window.open(resolvedSrc, "_blank", "noopener");
      toast.message("Opened in a new tab — long-press / right-click to save");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`block cursor-zoom-in print:cursor-default ${className}`}
        aria-label={alt ? `Open ${alt}` : "Open photo"}
        data-testid={`${testId}-trigger`}
      >
        {children}
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="max-w-[96vw] sm:max-w-4xl p-0 overflow-hidden bg-slate-950 border-2 border-slate-800 print:hidden"
          data-testid={`${testId}-modal`}
        >
          {/* a11y — screen readers want a title even when visually hidden */}
          <DialogTitle className="sr-only">{alt || "Photo preview"}</DialogTitle>

          <div className="relative">
            <img
              src={resolvedSrc}
              alt={alt}
              className="block w-full max-h-[78vh] object-contain bg-black"
              data-testid={`${testId}-img`}
            />
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="absolute top-2 right-2 inline-flex items-center justify-center w-9 h-9 rounded-full bg-black/60 text-white hover:bg-black/80 backdrop-blur"
              aria-label="Close"
              data-testid={`${testId}-close`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center justify-between gap-3 p-3 bg-slate-900 text-white">
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300 truncate">
              {alt || "Photo"}
            </span>
            <Button
              onClick={download}
              disabled={busy}
              size="sm"
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs h-9 px-3 border-b-2 border-red-900"
              data-testid={`${testId}-download`}
            >
              <Download className="w-3.5 h-3.5 mr-1.5" />
              {busy ? "Saving…" : "Save"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default PhotoLightbox;
