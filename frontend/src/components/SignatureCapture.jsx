// SignatureCapture.jsx — Iter154 (Phase F). The shared signature
// component used by every form in the MASCI Operations Platform.
//
// Props:
//   sourceModule (required) — e.g. "safety.corrective_actions"
//   sourceRecordId (required) — UUID of the parent record
//   signatureType (default "employee")
//   signerName (controlled string) + onSignerNameChange (optional)
//   onCaptured (callback) — receives the persisted signature row
//   className — optional wrapper class
//   allowRefusal (default true)
//
// Renders:
//   * Title bar with type label
//   * Signer name input (controlled when callbacks given, internal otherwise)
//   * Canvas pad (touch + mouse) + Clear button
//   * "Refuse to sign" checkbox + reason textarea (when checked)
//   * Capture button → POST /api/signatures → onCaptured(sig)
//   * Confirmation block after capture
//
// Notes:
//   * Canvas runs at 2x devicePixelRatio for crisp PDF embedding.
//   * Exported as data:image/png;base64 — no R2 dependency for v1.
//   * Refusal path skips canvas validation entirely.

import React, { useEffect, useRef, useState } from "react";
import { Eraser, PenTool, X, Check, AlertOctagon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { captureSignature } from "@/lib/signaturesApi";
import { friendlyError } from "@/lib/friendlyErrors";
import { toast } from "sonner";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

export default function SignatureCapture({
  sourceModule,
  sourceRecordId,
  signatureType = "employee",
  signerName: signerNameProp,
  onSignerNameChange,
  signerEmployeeId,
  signerRole,
  onCaptured,
  className = "",
  allowRefusal = true,
  testIdPrefix = "sig",
}) {
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [hasStrokes, setHasStrokes] = useState(false);
  const [internalName, setInternalName] = useState("");
  const [refusal, setRefusal] = useState(false);
  const [refusalReason, setRefusalReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [captured, setCaptured] = useState(null);

  const signerName = onSignerNameChange ? signerNameProp : internalName;
  const setSignerName = onSignerNameChange || setInternalName;

  // Set up canvas at device-pixel-ratio resolution
  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const rect = c.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    c.width = rect.width * dpr;
    c.height = rect.height * dpr;
    const ctx = c.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#0f172a";
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, rect.width, rect.height);
  }, []);

  const getXY = (e) => {
    const c = canvasRef.current;
    const rect = c.getBoundingClientRect();
    if (e.touches && e.touches[0]) {
      return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
    }
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };
  const start = (e) => {
    e.preventDefault();
    const { x, y } = getXY(e);
    const ctx = canvasRef.current.getContext("2d");
    ctx.beginPath();
    ctx.moveTo(x, y);
    setDrawing(true);
  };
  const move = (e) => {
    if (!drawing) return;
    e.preventDefault();
    const { x, y } = getXY(e);
    const ctx = canvasRef.current.getContext("2d");
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasStrokes(true);
  };
  const end = () => setDrawing(false);

  const clearPad = () => {
    const c = canvasRef.current;
    const ctx = c.getContext("2d");
    const rect = c.getBoundingClientRect();
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, rect.width, rect.height);
    setHasStrokes(false);
  };

  const submit = async () => {
    if (!signerName?.trim()) {
      toast.error("Signer name is required");
      return;
    }
    if (refusal) {
      if (!refusalReason.trim()) {
        toast.error("Refusal reason required.");
        return;
      }
    } else if (!hasStrokes) {
      toast.error("Sign the pad, or mark 'refuse to sign'.");
      return;
    }
    setSaving(true);
    try {
      const body = {
        source_module: sourceModule,
        source_record_id: sourceRecordId,
        signer_name: signerName.trim(),
        signer_employee_id: signerEmployeeId || null,
        signer_role: signerRole || null,
        signature_type: signatureType,
        refusal,
        refusal_reason: refusal ? refusalReason.trim() : null,
        signature_image: refusal ? null : canvasRef.current.toDataURL("image/png"),
      };
      const sig = await captureSignature(body);
      setCaptured(sig);
      toast.success(refusal ? "Refusal recorded" : "Signature captured");
      onCaptured?.(sig);
    } catch (e) {
      toast.error(friendlyError(e, "Could not save signature"));
    } finally {
      setSaving(false);
    }
  };

  if (captured) {
    return (
      <div
        className={`border-2 border-emerald-300 bg-emerald-50 rounded-md p-3 ${className}`}
        data-testid={`${testIdPrefix}-captured`}
      >
        <div className="flex items-start gap-2">
          <Check className="w-4 h-4 text-emerald-700 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-700 font-bold">
              {captured.refusal ? "Refusal Recorded" : "Signature Captured"}
            </div>
            <div className="font-bold text-slate-900 text-sm mt-0.5">{captured.signer_name}</div>
            <div className="font-mono text-[10px] text-slate-500 mt-0.5">
              {captured.signature_type} · {formatPlatformTime(captured.created_at)}
            </div>
            {captured.refusal && captured.refusal_reason && (
              <div className="text-xs text-slate-700 mt-1.5">
                <span className="font-bold">Reason:</span> {captured.refusal_reason}
              </div>
            )}
            {!captured.refusal && captured.signature_image && (
              <img
                src={captured.signature_image}
                alt={`Signature by ${captured.signer_name}`}
                className="mt-2 max-h-20 bg-white border border-slate-200 rounded"
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`border-2 border-slate-300 bg-white rounded-md p-3 sm:p-4 ${className}`} data-testid={`${testIdPrefix}-capture`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">
          <PenTool className="w-3.5 h-3.5" /> {signatureType} signature
        </div>
        {allowRefusal && !refusal && (
          <label className="text-[11px] text-slate-600 cursor-pointer flex items-center gap-1">
            <input
              type="checkbox"
              checked={refusal}
              onChange={(e) => setRefusal(e.target.checked)}
              data-testid={`${testIdPrefix}-refusal-toggle`}
            />
            Refuse to sign
          </label>
        )}
      </div>

      <div className="mb-2">
        <Label htmlFor={`${testIdPrefix}-name`} className="text-[11px]">Signer name *</Label>
        <Input
          id={`${testIdPrefix}-name`}
          value={signerName}
          onChange={(e) => setSignerName(e.target.value)}
          className="h-9 text-sm"
          placeholder="Print full name"
          data-testid={`${testIdPrefix}-name-input`}
        />
      </div>

      {refusal ? (
        <div className="space-y-2">
          <div className="bg-amber-50 border border-amber-200 rounded-md p-2 text-xs flex items-start gap-1.5" data-testid={`${testIdPrefix}-refusal-block`}>
            <AlertOctagon className="w-3.5 h-3.5 text-amber-700 mt-0.5 shrink-0" />
            <div>
              <div className="font-bold text-amber-800">Refusal-to-sign will be permanently recorded</div>
              <div className="text-amber-700">A reason is required and visible to HR, Safety, and Admin.</div>
            </div>
          </div>
          <Textarea
            value={refusalReason}
            onChange={(e) => setRefusalReason(e.target.value)}
            rows={3}
            placeholder="Reason for refusal"
            className="text-sm"
            data-testid={`${testIdPrefix}-refusal-reason`}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => { setRefusal(false); setRefusalReason(""); }}
            className="text-xs"
            data-testid={`${testIdPrefix}-cancel-refusal`}
          >
            <X className="w-3.5 h-3.5 mr-1" /> Cancel refusal
          </Button>
        </div>
      ) : (
        <>
          <div className="relative">
            <canvas
              ref={canvasRef}
              onMouseDown={start} onMouseMove={move} onMouseUp={end} onMouseLeave={end}
              onTouchStart={start} onTouchMove={move} onTouchEnd={end}
              className="w-full h-32 sm:h-40 border border-slate-300 rounded touch-none bg-white"
              style={{ touchAction: "none" }}
              data-testid={`${testIdPrefix}-canvas`}
            />
            {!hasStrokes && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none text-slate-300 text-xs italic">
                Sign here
              </div>
            )}
          </div>
          <div className="flex gap-2 mt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={clearPad}
              disabled={!hasStrokes}
              className="text-xs"
              data-testid={`${testIdPrefix}-clear`}
            >
              <Eraser className="w-3.5 h-3.5 mr-1" /> Clear
            </Button>
          </div>
        </>
      )}

      <div className="mt-3">
        <Button
          type="button"
          onClick={submit}
          disabled={saving}
          className="w-full sm:w-auto text-xs"
          data-testid={`${testIdPrefix}-submit`}
        >
          {saving ? "Saving…" : (refusal ? "Record refusal" : "Capture signature")}
        </Button>
      </div>
    </div>
  );
}
