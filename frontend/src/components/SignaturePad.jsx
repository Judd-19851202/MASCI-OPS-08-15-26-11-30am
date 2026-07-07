import React, { useRef, useEffect, useState } from "react";
import SignatureCanvas from "react-signature-canvas";
import { Button } from "@/components/ui/button";
import { Eraser } from "lucide-react";
import { useT } from "@/lib/i18n";

/**
 * Touch-friendly signature pad. Calls onChange(dataURL) when the user
 * finishes a stroke; emits "" when cleared.
 */
export const SignaturePad = ({ value, onChange, label, testId = "signature" }) => {
  const { t } = useT();
  const padRef = useRef(null);
  const containerRef = useRef(null);
  const [width, setWidth] = useState(600);

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setWidth(containerRef.current.clientWidth);
      }
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Re-render an existing signature when value is provided externally (view mode).
  useEffect(() => {
    if (value && padRef.current && padRef.current.fromDataURL) {
      padRef.current.fromDataURL(value, { width, height: 180 });
    }
  }, [value, width]);

  const handleEnd = () => {
    if (!padRef.current) return;
    if (padRef.current.isEmpty()) {
      onChange?.("");
    } else {
      const dataUrl = padRef.current.getCanvas().toDataURL("image/png");
      onChange?.(dataUrl);
    }
  };

  const handleClear = () => {
    padRef.current?.clear();
    onChange?.("");
  };

  return (
    <div className="space-y-2" data-testid={`${testId}-block`}>
      {label && (
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
            {label}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleClear}
            data-testid={`${testId}-clear`}
            className="text-slate-600 hover:text-red-600"
          >
            <Eraser className="w-4 h-4 mr-1" /> {t("Clear")}
          </Button>
        </div>
      )}
      <div
        ref={containerRef}
        className="border-2 border-slate-300 bg-white rounded-md touch-none"
        style={{ height: 180 }}
      >
        <SignatureCanvas
          ref={padRef}
          penColor="#0f172a"
          canvasProps={{
            width,
            height: 180,
            className: "rounded-md",
            "data-testid": `${testId}-canvas`,
          }}
          onEnd={handleEnd}
        />
      </div>
      <p className="text-xs text-slate-500">
        {t("Sign with your finger, stylus, or mouse above the line.")}
      </p>
    </div>
  );
};
