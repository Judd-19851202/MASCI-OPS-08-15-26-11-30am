import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import JSZip from "jszip";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

/**
 * PhotoZipDownload
 * ----------------
 * Bundles every photo on a report into a single .zip download — no more
 * tap-each-photo-and-save for insurance / legal / claims requests.
 *
 * Props:
 *   photos:    string[]   (URL or base64 data: URI list)
 *   prefix:    string     (filename prefix — e.g. "MASCI_Inspection_abc12345")
 *   label:     string     (button label; defaults to "Save all (N) as zip")
 *   testId:    string     (data-testid)
 *
 * Works for both http(s) URLs AND data:image/... base64 URIs because
 * `fetch()` parses both shapes into Blobs natively.
 *
 * Auto-names entries 01.jpg, 02.jpg, … (zero-padded so they sort correctly
 * in Finder / File Explorer).
 */
export const PhotoZipDownload = ({
  photos = [],
  prefix = "MASCI_photos",
  label,
  testId = "photo-zip-download",
}) => {
  const [busy, setBusy] = useState(false);
  const count = photos?.length || 0;

  if (count === 0) return null;

  const run = async () => {
    setBusy(true);
    try {
      const zip = new JSZip();
      const folder = zip.folder(prefix) || zip;
      const pad = String(count).length;
      for (let i = 0; i < photos.length; i++) {
        const src = photos[i];
        if (!src) continue;
        try {
          const r = await fetch(src);
          const blob = await r.blob();
          const ext =
            (blob.type && blob.type.split("/")[1]) ||
            (src.startsWith("data:image/")
              ? src.slice(11, src.indexOf(";"))
              : "jpg");
          const name = `${String(i + 1).padStart(pad, "0")}.${ext.replace(
            "jpeg",
            "jpg"
          )}`;
          folder.file(name, blob);
        } catch {
          // skip individual failures so one bad URL doesn't kill the whole zip
        }
      }
      const out = await zip.generateAsync({ type: "blob" });
      const url = URL.createObjectURL(out);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${prefix}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1500);
      toast.success(`Saved ${count} photos as ${prefix}.zip`);
    } catch (e) {
      toast.error("Could not build zip — try saving photos individually");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Button
      type="button"
      onClick={run}
      disabled={busy}
      size="sm"
      variant="outline"
      className="h-8 text-xs font-mono uppercase tracking-wide border-2 border-slate-300 hover:border-red-700 hover:text-red-700 print:hidden"
      data-testid={testId}
    >
      {busy ? (
        <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
      ) : (
        <Download className="w-3.5 h-3.5 mr-1.5" />
      )}
      {label || `Save all (${count}) as zip`}
    </Button>
  );
};

export default PhotoZipDownload;
