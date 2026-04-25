import React, { useRef } from "react";
import { Camera, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { compressImage } from "@/lib/utils";
import { toast } from "sonner";

export const PhotoUpload = ({ photos = [], onChange }) => {
  const inputRef = useRef(null);

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

  return (
    <div className="space-y-3" data-testid="photo-upload">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="w-full h-32 border-2 border-dashed border-slate-400 bg-slate-50 hover:bg-red-50 hover:border-red-700 transition-colors duration-150 rounded-md flex flex-col items-center justify-center gap-2 text-slate-700"
        data-testid="photo-upload-button"
      >
        <Camera className="w-8 h-8" />
        <span className="font-bold uppercase tracking-wide text-sm">
          Tap to add photos
        </span>
        <span className="text-xs text-slate-500">
          Camera or gallery · multiple supported
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
        data-testid="photo-upload-input"
      />
      {photos.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
          {photos.map((p, i) => (
            <div
              key={i}
              className="relative group aspect-square rounded-md overflow-hidden border-2 border-slate-200"
              data-testid={`photo-thumb-${i}`}
            >
              <img
                src={p}
                alt={`Finding ${i + 1}`}
                className="w-full h-full object-cover"
              />
              <Button
                type="button"
                onClick={() => removeAt(i)}
                size="icon"
                variant="destructive"
                className="absolute top-1 right-1 h-7 w-7"
                data-testid={`photo-remove-${i}`}
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
