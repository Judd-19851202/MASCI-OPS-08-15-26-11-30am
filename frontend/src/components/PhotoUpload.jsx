import React, { useEffect, useRef, useState } from "react";
import { Camera, X, ImageIcon, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { compressImage, HeicDecodeError } from "@/lib/utils";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { PhotoLightbox } from "@/components/PhotoLightbox";
import { resolvePhotoSrc } from "@/lib/photoSrc";

// TRACK 24.11 · Image-extension fallback for files that arrive with
// an empty `.type` (iOS Files app, Android share intents, some
// gallery apps). Without this, `startsWith("image/")` silently drops
// photos the user just picked — the "camera works but nothing
// appears" P0 bug on field iPhones.
const IMAGE_EXTENSIONS = /\.(jpe?g|png|gif|webp|heic|heif|avif|bmp|tiff?|svg)$/i;
function _looksLikeImage(file) {
  if (!file) return false;
  if (file.type && file.type.startsWith("image/")) return true;
  if (file.name && IMAGE_EXTENSIONS.test(file.name)) return true;
  return false;
}

// Track 20.7 · Universal Photo Capture guardrail.
// A device qualifies for camera capture ONLY if the browser exposes a
// video-capable media device. We probe once at mount time and cache the
// result. This is what lets the desktop "Take photo" button fall back
// to the plain file picker instead of silently no-oping when the user
// clicks it on a computer that has no webcam or has camera permission
// blocked — the exact failure reported against the Daily Report.
function useCameraSupport() {
  const [supported, setSupported] = useState(null); // null=unknown|true|false
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // 1. Fast-path: no mediaDevices API at all → definitely no camera.
        if (typeof navigator === "undefined" || !navigator.mediaDevices
            || !navigator.mediaDevices.enumerateDevices) {
          if (!cancelled) setSupported(false);
          return;
        }
        // 2. Enumerate device kinds. This does NOT prompt the user for
        //    permission and works in all evergreen browsers.
        const devices = await navigator.mediaDevices.enumerateDevices();
        const hasVideo = devices.some((d) => d.kind === "videoinput");
        if (!cancelled) setSupported(!!hasVideo);
      } catch {
        // 3. On any error (SecurityError on HTTP, etc.), fall back to the
        //    safe assumption: no camera → file picker is the truth.
        if (!cancelled) setSupported(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);
  return supported;
}

/**
 * PhotoUpload — gallery-or-camera picker.
 *
 * On iOS Safari, omitting the `capture` attribute lets users tap the input
 * and get the native action sheet:
 *   ◦ Photo Library (existing photos)
 *   ◦ Take Photo
 *   ◦ Choose File
 * If you want to *force* the camera open, pass `forceCamera`.
 *
 * Compression UX: when the user picks N > 1 photos, on-phone compression of
 * 1280px max-dim JPEGs at q=0.78 takes ~0.3–1.5s per photo. We surface a
 * live progress bar and reveal thumbnails progressively so the user can
 * see the work happening (otherwise the UI looks frozen for 10–30s on a
 * batch of 20+ photos and they spam-tap Submit).
 */
export const PhotoUpload = ({
  photos = [],
  onChange,
  photoStatuses = [],
  onBatchStateChange,
  onPhotoReady,
  testIdBase = "photo-upload",
  forceCamera = false,
}) => {
  const { t } = useT();
  const galleryRef = useRef(null);
  const cameraRef = useRef(null);
  const [progress, setProgress] = useState(null);
  // TRACK 24.12 Phase A1 · Photo append fix.
  //
  // Prior bug: `handleFiles` snapshotted the `photos` prop into a
  // local `next = [...photos]` at call-time. If the user picked
  // batch #1 (3 photos), then re-opened the picker and picked batch
  // #2 (2 photos) BEFORE React had propagated batch #1 through the
  // parent's `setState({...data, photos: p})`, the batch #2 closure
  // still saw `photos = []` and overwrote batch #1 — the exact
  // "gallery reopens replaces prior photos" P0 report.
  //
  // Fix: mirror the incoming `photos` prop into a ref that we
  // ALSO advance in-place as each batch commits. Every new
  // `handleFiles` invocation reads from the ref, so it sees the
  // freshest list whether or not the parent has re-rendered yet.
  const photosRef = useRef(photos);
  useEffect(() => { photosRef.current = photos; }, [photos]);
  // Track 20.7 · when unsupported (desktop w/o webcam · permission blocked
  // · non-secure context), the "Take photo" button transparently falls
  // back to the gallery file picker so the user is never trapped.
  const cameraSupported = useCameraSupport();
  const cameraKnownUnsupported = cameraSupported === false;
  const statusByIndex = (photoStatuses || []).reduce((acc, item, index) => {
    acc[index] = item;
    return acc;
  }, {});

  const statusLabel = (status) => {
    switch (status) {
      case "analyzing": return t("Analyzing…");
      case "complete": return t("Complete");
      case "cited": return t("Cited");
      case "failed": return t("Retry needed");
      case "unavailable": return t("Unavailable");
      default: return t("Queued");
    }
  };

  const statusTone = (status) => {
    switch (status) {
      case "analyzing": return "bg-sky-600 text-white";
      case "complete": return "bg-emerald-600 text-white";
      case "cited": return "bg-amber-500 text-slate-950";
      case "failed": return "bg-red-600 text-white";
      case "unavailable": return "bg-slate-500 text-white";
      default: return "bg-slate-900/80 text-white";
    }
  };

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    // TRACK 24.11 · Accept files whose `.type` is empty as long as
    // their filename ends in a known image extension. iOS Files app,
    // Android share sheets, and some gallery apps hand us MIME-less
    // Files that would otherwise be dropped by the strict prefix
    // filter — that's the "picked a photo but nothing shows up" P0
    // reported against production.
    const imageFiles = files.filter(_looksLikeImage);
    if (imageFiles.length === 0) return;

    const total = imageFiles.length;
    setProgress({ current: 0, total });
    onBatchStateChange?.({ inFlight: true, total, completed: 0, failed: 0, phase: "compressing" });

    // TRACK 24.12 Phase A1 · Read the FRESHEST photo list from the
    // ref, not the stale `photos` prop closure. Also mutate the ref
    // as each photo commits so a rapid second batch picked
    // mid-flight sees this batch's progress and appends to it
    // instead of overwriting.
    const startLen = photosRef.current.length;
    const next = [...photosRef.current];
    let failed = 0;
    let heicFailed = 0;
    for (let i = 0; i < imageFiles.length; i += 1) {
      const file = imageFiles[i];
      setProgress({ current: i + 1, total });
      onBatchStateChange?.({ inFlight: true, total, completed: i, failed, phase: "compressing" });
      try {
        const dataUrl = await compressImage(file, 1280, 0.78);
        next.push(dataUrl);
        photosRef.current = [...next];  // ← keep ref current in-flight
        onChange?.([...next]);
        onBatchStateChange?.({ inFlight: true, total, completed: i + 1, failed, phase: "compressing" });
        onPhotoReady?.({
          dataUrl,
          photos: [...next],
          completed: i + 1,
          total,
          failed,
          phase: "compressing",
        });
      } catch (err) {
        failed += 1;
        // TRACK 24.11 · Actionable HEIC error — the previous silent
        // "Could not process" toast blocked field iPhone users from
        // knowing they had a fixable device setting.
        const mime = (err && err.mime) || file?.type || "";
        const isHeic = err instanceof HeicDecodeError
          || /heic|heif/i.test(mime)
          || /\.(heic|heif)$/i.test(file?.name || "");
        if (isHeic) {
          heicFailed += 1;
        } else {
          toast.error(`Could not process ${file.name || "photo"}`);
        }
      }
    }
    setProgress(null);
    onBatchStateChange?.({ inFlight: false, total, completed: total - failed, failed, phase: "complete" });

    if (heicFailed > 0) {
      // TRACK 24.11B · client-side heic2any now handles HEIC on
      // every browser — this toast only fires when BOTH the
      // converter and the browser's native decoder fail (extremely
      // rare, typically corrupted HEIC or non-standard variant).
      toast.error(
        t("Some photos couldn't be read (HEIC conversion failed)") + " — " +
        t("Try retaking the photo, or convert to JPEG on your device"),
        { duration: 10000 },
      );
    }

    const added = next.length - startLen;
    if (added > 1) {
      toast.success(`${added} ${t("photos added")}`);
    } else if (added === 0 && failed > 0 && heicFailed === 0) {
      toast.error(t("No photos could be added"));
    }
  };

  const removeAt = (idx) => {
    // Use the ref-mirrored list so a mid-flight batch doesn't
    // resurrect a deleted photo.
    const source = photosRef.current;
    const next = source.filter((_, i) => i !== idx);
    photosRef.current = next;
    onChange?.(next);
  };

  const openGallery = () => galleryRef.current?.click();
  // Track 20.7 · fall through to the plain file picker when camera is
  // known-unsupported. This is the surgical fix for the Daily Report
  // desktop failure: no more silent no-op on desktops without a webcam
  // or with camera permission blocked.
  const openCamera = () => {
    if (cameraKnownUnsupported) {
      galleryRef.current?.click();
      return;
    }
    cameraRef.current?.click();
  };

  // TRACK 24.11B · Desktop drag-and-drop.
  // Toughbooks / Windows laptops / Mac users drop files directly onto
  // the picker area. `dragOver` state drives the visual affordance so
  // the drop target is unambiguous. Same `handleFiles` pipeline as the
  // mobile picker — HEIC conversion, MIME/extension fallback, error
  // surfacing all identical.
  const [dragOver, setDragOver] = useState(false);
  const onDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };
  const onDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };
  const onDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    const files = Array.from(e.dataTransfer?.files || []);
    handleFiles(files);
  };

  return (
    <div
      className="space-y-3"
      data-testid={testIdBase}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {dragOver && (
        <div
          className="rounded-md border-2 border-dashed border-red-500 bg-red-50 px-4 py-6 text-center text-red-800 font-semibold text-sm"
          data-testid={`${testIdBase}-drop-target`}
        >
          {t("Drop photos here to upload")}
        </div>
      )}
      {/* Compression progress bar — only shows when a batch is in flight.
          Always-visible counter + fill so the user can see thumbnails
          appearing one-by-one underneath while the bar fills. */}
      {progress && (
        <div
          className="elite-glass-panel border-2 border-blue-300 rounded-[1rem] p-3"
          data-testid={`${testIdBase}-progress`}
        >
          <div className="flex items-center gap-2 mb-2">
            <Loader2 className="w-4 h-4 text-blue-700 animate-spin shrink-0" />
            <span className="font-mono text-xs uppercase tracking-[0.18em] text-blue-900 font-bold">
              {t("Compressing")} {progress.current} {t("of")} {progress.total}…
            </span>
            <span className="ml-auto font-mono text-[10px] text-blue-700">
              {Math.round((progress.current / progress.total) * 100)}%
            </span>
          </div>
          <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-700 transition-all duration-150"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
              data-testid={`${testIdBase}-progress-fill`}
            />
          </div>
        </div>
      )}

      {forceCamera ? (
        <button
          type="button"
          onClick={openCamera}
          className="w-full h-32 border-2 border-dashed border-slate-400 bg-slate-50 hover:bg-red-50 hover:border-red-700 transition-colors duration-150 rounded-md flex flex-col items-center justify-center gap-2 text-slate-700"
          data-testid={`${testIdBase}-button`}
        >
          <Camera className="w-8 h-8" />
          <span className="font-bold uppercase tracking-wide text-sm">
            {cameraKnownUnsupported ? t("Choose photo / file") : t("Take photo")}
          </span>
          {cameraKnownUnsupported && (
            <span
              className="text-[10px] text-slate-500"
              data-testid={`${testIdBase}-camera-fallback-hint`}
            >
              {t("Camera unavailable — choose a file instead")}
            </span>
          )}
        </button>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={openGallery}
            className="h-28 border-2 border-dashed border-slate-400 bg-slate-50 hover:bg-red-50 hover:border-red-700 transition-colors duration-150 rounded-md flex flex-col items-center justify-center gap-1.5 text-slate-700 px-2"
            data-testid={`${testIdBase}-gallery`}
          >
            <ImageIcon className="w-6 h-6" />
            <span className="font-bold uppercase tracking-wide text-xs text-center">
              {t("Choose photo / file")}
            </span>
            <span className="text-[10px] text-slate-500">
              {t("Pick existing photos")}
            </span>
          </button>
          <button
            type="button"
            onClick={openCamera}
            className="h-28 border-2 border-dashed border-slate-400 bg-slate-50 hover:bg-red-50 hover:border-red-700 transition-colors duration-150 rounded-md flex flex-col items-center justify-center gap-1.5 text-slate-700 px-2"
            data-testid={`${testIdBase}-camera`}
            title={cameraKnownUnsupported
              ? t("Camera unavailable on this device — opens the file picker instead")
              : t("Open camera")}
          >
            <Camera className="w-6 h-6" />
            <span className="font-bold uppercase tracking-wide text-xs text-center">
              {cameraKnownUnsupported ? t("Choose from files") : t("Take photo")}
            </span>
            <span
              className="text-[10px] text-slate-500"
              data-testid={`${testIdBase}-camera-hint`}
            >
              {cameraKnownUnsupported
                ? t("Camera unavailable — choose a file instead")
                : t("Open camera")}
            </span>
          </button>
        </div>
      )}

      {/* Hidden file inputs — gallery (no capture) + camera (capture).
          TRACK 24.11 · `accept` explicitly lists HEIC/HEIF so iOS
          Safari surfaces iPhone camera-native photos in the picker
          even when the OS reports them without a MIME hint. */}
      <input
        ref={galleryRef}
        type="file"
        accept="image/*,image/heic,image/heif,.heic,.heif"
        multiple
        className="hidden"
        onChange={(e) => {
          const snapshot = Array.from(e.target.files || []);
          e.target.value = "";
          handleFiles(snapshot);
        }}
        data-testid={`${testIdBase}-input-gallery`}
      />
      <input
        ref={cameraRef}
        type="file"
        accept="image/*,image/heic,image/heif,.heic,.heif"
        capture="environment"
        multiple
        className="hidden"
        onChange={(e) => {
          const snapshot = Array.from(e.target.files || []);
          e.target.value = "";
          handleFiles(snapshot);
        }}
        data-testid={`${testIdBase}-input-camera`}
      />

      {photos.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
          {photos.map((p, i) => (
            <div
              key={i}
              className="relative group aspect-square rounded-md overflow-hidden border-2 border-slate-200"
              data-testid={`${testIdBase}-thumb-${i}`}
            >
              <PhotoLightbox
                src={p}
                alt={`Photo ${i + 1}`}
                filename={`MASCI_upload_${Date.now()}_${i + 1}.jpg`}
                className="absolute inset-0 w-full h-full"
                testId={`${testIdBase}-lightbox-${i}`}
              >
                <img
                  src={resolvePhotoSrc(p)}
                  alt={`Photo ${i + 1}`}
                  className="w-full h-full object-cover"
                />
              </PhotoLightbox>
              <Button
                type="button"
                onClick={() => removeAt(i)}
                size="icon"
                variant="destructive"
                className="absolute top-1 right-1 h-7 w-7 z-10"
                data-testid={`${testIdBase}-remove-${i}`}
                aria-label="Remove photo"
                title="Remove photo"
              >
                <X className="w-4 h-4" />
              </Button>
              <div
                className={`absolute bottom-1 left-1 z-10 rounded-full px-2 py-1 text-[10px] font-semibold shadow ${statusTone(statusByIndex[i]?.status)}`}
                data-testid={`${testIdBase}-status-${i}`}
              >
                {statusLabel(statusByIndex[i]?.status)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
