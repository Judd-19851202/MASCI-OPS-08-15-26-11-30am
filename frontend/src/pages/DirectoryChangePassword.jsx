// /app/frontend/src/pages/DirectoryChangePassword.jsx
//
// Track 15.14A · Layer 1+4 — Unified /change-password page used by
// /sign-in (master multi-portal login) when the directory user still
// owes a password rotation.
//
// Flow:
//   • /sign-in detects multi-login response with must_change_password=true
//     and portal_tokens={} → navigates here.
//   • This page reads the directory session_token from localStorage
//     (set by applyMultiLoginResponse) and calls
//     POST /api/auth/change-master-password.
//   • Backend rotates the master password, mints fresh portal_tokens,
//     and returns them. We fan them out via applyMultiLoginResponse
//     and land the user on the proper portal (landingFor).
//
// This is intentionally minimal — no animation, no marketing, no
// extra UX. It's a security gate.

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, KeyRound, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/PasswordInput";
import { PortalLoginShell } from "@/components/PortalLoginShell";
import { api } from "@/lib/api";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import {
  applyMultiLoginResponse,
  getDirectoryToken,
  getDirectoryUser,
  landingFor,
  stabilizeAdminPortalToken,
} from "@/lib/directoryAuth";
import { setMustChange, clearAllMustChange } from "@/lib/mustChangePassword";
import { toast } from "sonner";

export default function DirectoryChangePassword() {
  const navigate = useNavigate();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // If there is no directory session at all, send the user to /sign-in.
    if (!getDirectoryToken()) {
      navigate("/sign-in", { replace: true });
    }
  }, [navigate]);

  const user = getDirectoryUser() || {};

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!current || !next || !confirm) {
      toast.error("All fields are required");
      return;
    }
    if (next !== confirm) {
      toast.error("New password and confirmation do not match");
      return;
    }
    if (next.length < 8) {
      toast.error("New password must be at least 8 characters");
      return;
    }
    if (next === current) {
      toast.error("New password must be different from the current one");
      return;
    }
    setBusy(true);
    try {
      const res = await api.post(
        "/auth/change-master-password",
        { current_password: current, new_password: next },
        {
          timeout: 30000,
          headers: buildScopedPortalAuthHeaders([]),
        }
      );
      if (res?.data?.ok) {
        // Apply the freshly-minted portal tokens (backend Layer 4).
        const authResponse = {
          ok: true,
          session_token: getDirectoryToken(),
          portal_tokens: res.data.portal_tokens || {},
          user: res.data.user || user,
        };
        applyMultiLoginResponse(authResponse, true);
        await stabilizeAdminPortalToken(authResponse, true);
        // Clear every must-change flag — rotation is done.
        clearAllMustChange();
        setMustChange("directory", false);
        toast.success("Password updated · welcome");
        const next_user = res.data.user || user;
        navigate(landingFor(next_user), { replace: true });
        return;
      }
      toast.error("Password change failed");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      let msg;
      if (status === 401) msg = typeof detail === "string" ? detail : "Current password is incorrect";
      else if (status === 400) msg = typeof detail === "string" ? detail : "Invalid request";
      else msg = "Could not change password — try again";
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <PortalLoginShell
      headerBorderClass="border-red-700"
      backHoverClass="hover:text-red-300"
      backTestId="directory-change-password-back"
      rootTestId="directory-change-password-page"
      footerLabel="MASCI · Unified Sign-In"
      homeLink="/"
    >
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-md p-7 sm:p-9 shadow-xl">
          <div className="mb-3 inline-flex items-center rounded-md bg-red-50 border border-red-200 px-3 py-1.5 text-[11px] font-mono uppercase tracking-[0.18em] text-red-700 font-bold">
            Password change required
          </div>
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck className="w-6 h-6 text-red-700" />
            <h1 className="text-2xl font-black tracking-tight text-slate-900">
              Choose a new password
            </h1>
          </div>
          <p className="text-sm text-slate-600 mb-6 leading-relaxed">
            Your temporary password must be changed before you can access
            the platform. After you rotate, your portals will be available
            in one click.
          </p>
          {user?.email ? (
            <div className="mb-4 text-xs font-mono text-slate-500" data-testid="directory-change-password-email">
              {user.email}
            </div>
          ) : null}
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="dc-current" className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Temporary password
              </Label>
              <PasswordInput
                id="dc-current"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                placeholder="Enter the temporary password you received"
                data-testid="dc-current"
                autoComplete="current-password"
                disabled={busy}
                required
              />
            </div>
            <div>
              <Label htmlFor="dc-new" className="text-xs font-bold uppercase tracking-wider text-slate-700">
                New password
              </Label>
              <PasswordInput
                id="dc-new"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                placeholder="Minimum 8 characters"
                data-testid="dc-new"
                autoComplete="new-password"
                disabled={busy}
                required
                minLength={8}
              />
            </div>
            <div>
              <Label htmlFor="dc-confirm" className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Confirm new password
              </Label>
              <PasswordInput
                id="dc-confirm"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="Re-enter your new password"
                data-testid="dc-confirm"
                autoComplete="new-password"
                disabled={busy}
                required
                minLength={8}
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wider"
              data-testid="dc-submit"
              disabled={busy}
            >
              {busy ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating…
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4 mr-2" />
                  Change password
                </>
              )}
            </Button>
          </form>
        </div>
    </PortalLoginShell>
  );
}
