// AdminMfa.jsx — iter375 · Phase 4B · Super-admin TOTP MFA management
//
// Single-page super-admin self-service for MFA:
//   • View status (enabled / recovery codes remaining)
//   • Enroll: show QR + manual key + recovery codes
//   • Verify enrollment (enter first TOTP code)
//   • Disable (requires current TOTP)
//   • Regenerate recovery codes (requires current TOTP)
//
// Per the Simplicity directive: ONE page, no modal stacks, no excess
// onboarding choreography.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck, KeyRound, Loader2, AlertTriangle, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function AdminMfa() {
  const [status, setStatus] = useState(null);
  const [enroll, setEnroll] = useState(null); // { otpauth_uri, secret, qr_data_uri, recovery_codes }
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [confirmCode, setConfirmCode] = useState("");
  const [regenCodes, setRegenCodes] = useState(null);

  const loadStatus = async () => {
    try {
      const res = await api.get("/admin/mfa/status");
      setStatus(res.data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Unable to load MFA status");
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleEnrollStart = async () => {
    setSubmitting(true);
    try {
      const res = await api.post("/admin/mfa/enroll/start");
      setEnroll(res.data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Enrollment failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEnrollVerify = async () => {
    if (!code) {
      toast.error("Enter the 6-digit code from your authenticator app");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/admin/mfa/enroll/verify", { code });
      toast.success("MFA enrolled. Save your recovery codes now if you haven't.");
      setEnroll(null);
      setCode("");
      await loadStatus();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Invalid TOTP code");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDisable = async () => {
    if (!confirmCode) {
      toast.error("Enter your current TOTP code to disable MFA");
      return;
    }
    if (!window.confirm("Disable MFA for this account? You will sign in with password only until you re-enroll.")) {
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/admin/mfa/disable", { code: confirmCode });
      toast.success("MFA disabled.");
      setConfirmCode("");
      await loadStatus();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Disable failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegenRecovery = async () => {
    if (!confirmCode) {
      toast.error("Enter your current TOTP code to regenerate recovery codes");
      return;
    }
    if (!window.confirm("Regenerate recovery codes? Your existing codes will stop working immediately.")) {
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("/admin/mfa/regenerate-recovery", { code: confirmCode });
      setRegenCodes(res.data.recovery_codes);
      setConfirmCode("");
      await loadStatus();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Regeneration failed");
    } finally {
      setSubmitting(false);
    }
  };

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied");
    } catch {
      toast.error("Copy failed");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link to="/admin" className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide" data-testid="admin-mfa-back">
            <ArrowLeft className="w-4 h-4 mr-1" /> Admin Hub
          </Link>
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-300 font-bold">
            Operations Platform · Security
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 sm:px-8 py-10 space-y-6">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-red-700 text-white">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700">
              Phase 4B · Trust Reinforcement
            </div>
            <h1 className="font-display text-2xl font-black text-slate-900 leading-none mt-1">
              Multi-Factor Authentication
            </h1>
          </div>
        </div>

        <p className="text-slate-700 text-sm">
          TOTP-based MFA is available for super-admin accounts. Enroll once, scan the QR code into Google Authenticator, Authy, 1Password, or Microsoft Authenticator, and your next sign-in will prompt for a 6-digit code in addition to your password.
        </p>

        {/* Status panel */}
        <div className="bg-white border-2 border-slate-200 rounded-md p-5" data-testid="mfa-status-panel">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-2">
            Status
          </div>
          {status === null && <Loader2 className="w-4 h-4 animate-spin" />}
          {status && (
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-mono uppercase tracking-wide text-xs text-slate-600 mr-2">Account:</span>
                <span className="font-bold">{status.user_email}</span>
              </div>
              <div>
                <span className="font-mono uppercase tracking-wide text-xs text-slate-600 mr-2">MFA:</span>
                <span
                  className={
                    "inline-flex items-center px-2 py-0.5 rounded text-xs font-mono uppercase tracking-wide font-bold " +
                    (status.enabled ? "bg-green-100 text-green-800" : "bg-slate-200 text-slate-700")
                  }
                  data-testid="mfa-status-badge"
                >
                  {status.enabled ? "Enabled" : "Not enrolled"}
                </span>
              </div>
              {status.enabled && (
                <div>
                  <span className="font-mono uppercase tracking-wide text-xs text-slate-600 mr-2">Recovery codes remaining:</span>
                  <span className="font-bold">{status.recovery_codes_remaining}</span>
                  {status.recovery_codes_remaining <= 2 && (
                    <span className="ml-2 text-xs text-amber-700 inline-flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> regenerate soon
                    </span>
                  )}
                </div>
              )}
              {status.locked && (
                <div className="text-xs text-red-700 font-bold uppercase tracking-wide">
                  ⚠ MFA temporarily locked — wait or contact ops
                </div>
              )}
            </div>
          )}
        </div>

        {/* Enroll flow */}
        {status && !status.enabled && !enroll && (
          <Button
            onClick={handleEnrollStart}
            disabled={submitting}
            className="w-full h-12 bg-red-700 hover:bg-red-800 font-mono uppercase tracking-wide font-bold"
            data-testid="mfa-enroll-start-btn"
          >
            {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <KeyRound className="w-4 h-4 mr-2" />}
            Start MFA Enrollment
          </Button>
        )}

        {enroll && (
          <div className="bg-white border-2 border-red-700 rounded-md p-6 space-y-5" data-testid="mfa-enroll-panel">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">
                Step 1 · Scan QR code
              </div>
              <p className="text-xs text-slate-600 mb-3">
                Open your authenticator app, add a new account, and scan this code.
              </p>
              <div className="bg-slate-50 p-4 rounded-md inline-block">
                <img src={enroll.qr_data_uri} alt="MFA QR code" className="w-48 h-48" data-testid="mfa-enroll-qr" />
              </div>
            </div>

            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">
                Step 1b · Manual key (if you cannot scan)
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 font-mono text-sm bg-slate-100 px-3 py-2 rounded select-all break-all" data-testid="mfa-enroll-secret">
                  {enroll.secret}
                </code>
                <Button type="button" variant="outline" size="icon" onClick={() => copyText(enroll.secret)} data-testid="mfa-enroll-secret-copy">
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">
                Step 2 · Save recovery codes (one-time use)
              </div>
              <p className="text-xs text-red-700 font-bold mb-2">
                Store these somewhere safe. Each works once if you lose your authenticator.
              </p>
              <div className="bg-slate-900 text-green-300 font-mono text-xs p-3 rounded-md" data-testid="mfa-enroll-recovery-codes">
                {enroll.recovery_codes.map((c, i) => (
                  <div key={i}>{c}</div>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={() => copyText(enroll.recovery_codes.join("\n"))}
                className="mt-2 h-9 font-mono uppercase tracking-wide text-xs"
                data-testid="mfa-enroll-recovery-copy"
              >
                <Copy className="w-3 h-3 mr-1" /> Copy all
              </Button>
            </div>

            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mb-2">
                Step 3 · Confirm with first code
              </div>
              <Label className="text-xs text-slate-600">Enter the 6-digit code from your authenticator app</Label>
              <Input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456"
                className="mt-1 h-11 text-lg font-mono tracking-widest text-center max-w-[180px]"
                data-testid="mfa-enroll-code-input"
              />
              <Button
                onClick={handleEnrollVerify}
                disabled={submitting || code.length !== 6}
                className="mt-3 h-11 bg-red-700 hover:bg-red-800 font-mono uppercase tracking-wide font-bold"
                data-testid="mfa-enroll-verify-btn"
              >
                {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Complete Enrollment
              </Button>
            </div>
          </div>
        )}

        {/* Manage flows when enabled */}
        {status && status.enabled && !enroll && (
          <div className="bg-white border-2 border-slate-200 rounded-md p-5 space-y-4" data-testid="mfa-manage-panel">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
              Manage MFA
            </div>
            <p className="text-xs text-slate-600">
              Enter your current 6-digit TOTP code to disable MFA or regenerate recovery codes.
            </p>
            <Input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={confirmCode}
              onChange={(e) => setConfirmCode(e.target.value)}
              placeholder="Current TOTP code"
              className="h-11 text-lg font-mono tracking-widest text-center max-w-[200px]"
              data-testid="mfa-manage-code-input"
            />
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={handleRegenRecovery}
                disabled={submitting || confirmCode.length !== 6}
                variant="outline"
                className="font-mono uppercase tracking-wide font-bold text-xs"
                data-testid="mfa-regen-recovery-btn"
              >
                Regenerate Recovery Codes
              </Button>
              <Button
                onClick={handleDisable}
                disabled={submitting || confirmCode.length !== 6}
                variant="outline"
                className="font-mono uppercase tracking-wide font-bold text-xs border-red-700 text-red-700 hover:bg-red-50"
                data-testid="mfa-disable-btn"
              >
                Disable MFA
              </Button>
            </div>
            {regenCodes && (
              <div className="mt-4 bg-slate-900 text-green-300 font-mono text-xs p-3 rounded-md" data-testid="mfa-regen-codes-panel">
                <div className="text-amber-300 mb-2 font-bold">⚠ New recovery codes — save them now. Old codes are dead.</div>
                {regenCodes.map((c, i) => (
                  <div key={i}>{c}</div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => copyText(regenCodes.join("\n"))}
                  className="mt-2 h-8 font-mono uppercase tracking-wide text-xs bg-white text-slate-900"
                >
                  <Copy className="w-3 h-3 mr-1" /> Copy all
                </Button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
