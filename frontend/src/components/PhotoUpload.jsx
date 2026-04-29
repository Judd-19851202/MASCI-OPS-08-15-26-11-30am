import React, { useRef } from "react";
import { Camera, X, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { compressImage } from "@/lib/utils";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { PhotoLightbox } from "@/components/PhotoLightbox";

/**
 * PhotoUpload — gallery-or-camera picker.
 *
 * On iOS Safari, omitting the `capture` attribute lets users tap the input
 * and get the native action sheet:
 *   ◦ Photo Library (existing photos)
 *   ◦ Take Photo
 *   ◦ Choose File
 * If you want to *force* the camera open, pass `forceCamera`.
 */
export const PhotoUpload = ({
  photos = [],
  onChange,
  testIdBase = "photo-upload",
  forceCamera = false,
}) => {
  const { t } = useT();
  const galleryRef = useRef(null);
  const cameraRef = useRef(null);

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    const next = [...photos];
    for (const file of files) {
      if (!file.type.startsWith("image/")) continue;
      try {
        const dataUrl = await compressImage(file, 1280, 0.78);
        next.push(dataUrl);
      } catch {
        toast.error(`Could not process ${file.name}`);
      }
    }
    onChange?.(next);
  };

  const removeAt = (idx) => {
    const next = photos.filter((_, i) => i !== idx);
    onChange?.(next);
  };

  const openGallery = () => galleryRef.current?.click();
  const openCamera = () => cameraRef.current?.click();

  return (
    <div className="space-y-3" data-testid={testIdBase}>
      {forceCamera ? (
        <button
          type="button"
          onClick={openCamera}
          className="w-full h-32 border-2 border-dashed border-slate-400 bg-slate-50 hover:bg-red-50 hover:border-red-700 transition-colors duration-150 rounded-md flex flex-col items-center justify-center gap-2 text-slate-700"
          data-testid={`${testIdBase}-button`}
        >
          <Camera className="w-8 h-8" />
          <span className="font-bold uppercase tracking-wide text-sm">
            {t("Take photo")}
          </span>
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
              {t("From gallery")}
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
          >
            <Camera className="w-6 h-6" />
            <span className="font-bold uppercase tracking-wide text-xs text-center">
              {t("Take photo")}
            </span>
            <span className="text-[10px] text-slate-500">
              {t("Open camera")}
            </span>
          </button>
        </div>
      )}

      {/* Hidden file inputs — gallery (no capture) + camera (capture) */}
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
        data-testid={`${testIdBase}-input-gallery`}
      />
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
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
                  src={p}
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
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
