/**
 * AdminProfile.jsx · iter430 · Phase 28.2 · Part 3B.
 *
 * Route: /admin/profile
 *
 * Doctrine
 * --------
 * Calm, single-card admin profile page. The ONLY new feature in this
 * phase is the "Your devices" section — a read-only list of enrolled
 * passkeys with a revoke action. No security dashboard, no
 * geo-tracking, no fingerprinting beyond what the WebAuthn ceremony
 * already records (authenticator label + last_used_at).
 *
 * Operational language only:
 *   • "Your devices"               (not "Credentials" or "Authenticators")
 *   • "Enabled · last used …"      (not "Active · trusted device")
 *   • "Remove from this account"   (not "Revoke" or "Deauthorize")
 */
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, KeyRound, Smartphone, Trash2, Shield } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";
import { listPasskeys, revokePasskey } from "@/lib/passkeys";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";

const _fmt = (iso) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

export default function AdminProfile() {
  usePageTitle("Admin profile · MASCI");
  const { t } = useT();

  const [passkeys, setPasskeys] = useState(null); // null = loading
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  const refresh = async () => {
    setError("");
    try {
      const list = await listPasskeys();
      setPasskeys(Array.isArray(list) ? list : []);
    } catch (e) {
      setError(String(e?.response?.data?.detail || e?.message || e));
      setPasskeys([]);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onRemove = async (pk) => {
    if (!pk?.credential_id) return;
    if (!window.confirm(t("Remove this device from your account?"))) return;
    setBusyId(pk.credential_id);
    setError("");
    try {
      await revokePasskey(pk.credential_id);
      await refresh();
    } catch (e) {
      setError(String(e?.response?.data?.detail || e?.message || e));
    } finally {
      setBusyId("");
    }
  };

  return (
    <AdminShell>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6" data-testid="admin-profile-page">
        {/* Back link */}
        <div className="mb-4">
          <Link
            to="/admin"
            data-testid="admin-profile-back"
            className="inline-flex items-center text-xs text-slate-500 hover:text-slate-800"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" /> {t("Back to Admin")}
          </Link>
        </div>

        <header className="mb-6">
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold">
            {t("Your profile")}
          </div>
          <h1 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-tight">
            {t("Admin Profile")}
          </h1>
          <p className="text-sm text-slate-600 mt-1 leading-relaxed">
            {t("Manage how you sign in to MASCI on this and other devices.")}
          </p>
        </header>

        {/* Optional · self-gated passkey enrollment prompt */}
        <div className="mb-6">
          <PasskeyEnrollPrompt />
        </div>

        {/* "Your devices" section */}
        <section
          className="rounded-lg border border-slate-200 bg-white shadow-sm"
          data-testid="admin-profile-devices-card"
        >
          <header className="px-5 py-4 border-b border-slate-200 flex items-center gap-2">
            <Smartphone className="w-4 h-4 text-slate-600" />
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">
              {t("Your devices")}
            </h2>
          </header>

          {error && (
            <div
              data-testid="admin-profile-error"
              className="mx-5 mt-4 rounded-md bg-rose-50 border border-rose-200 px-3 py-2 text-xs text-rose-800"
            >
              {error}
            </div>
          )}

          {passkeys === null ? (
            <div className="px-5 py-8 text-sm text-slate-500" data-testid="admin-profile-devices-loading">
              {t("Loading devices…")}
            </div>
          ) : passkeys.length === 0 ? (
            <div className="px-5 py-8 text-sm text-slate-600" data-testid="admin-profile-devices-empty">
              <p className="leading-relaxed">
                {t("No devices enabled for faster sign-in yet.")}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {t("Use the prompt above to enable Face ID / Touch ID / Windows Hello on this device.")}
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100" data-testid="admin-profile-devices-list">
              {passkeys.map((pk) => (
                <li
                  key={pk.credential_id || pk.id}
                  className="flex items-start justify-between px-5 py-4"
                  data-testid={`admin-profile-device-row-${pk.credential_id}`}
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <KeyRound className="w-4 h-4 text-emerald-700 mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-slate-900 truncate">
                        {pk.label || pk.authenticator_label || t("Device")}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {t("Enabled")} · {_fmt(pk.created_at)}
                        {pk.last_used_at ? (
                          <>
                            {" · "}
                            <span>
                              {t("last used")} {_fmt(pk.last_used_at)}
                            </span>
                          </>
                        ) : null}
                      </div>
                      {pk.transport ? (
                        <div className="text-[10px] uppercase tracking-wide text-slate-400 mt-1">
                          {Array.isArray(pk.transport) ? pk.transport.join(" · ") : pk.transport}
                        </div>
                      ) : null}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemove(pk)}
                    disabled={busyId === pk.credential_id}
                    data-testid={`admin-profile-device-remove-${pk.credential_id}`}
                    className="text-rose-700 hover:bg-rose-50 hover:text-rose-800"
                  >
                    <Trash2 className="w-3.5 h-3.5 mr-1" />
                    {busyId === pk.credential_id ? t("Removing…") : t("Remove")}
                  </Button>
                </li>
              ))}
            </ul>
          )}

          <footer className="px-5 py-3 border-t border-slate-100 bg-slate-50/60 text-[11px] text-slate-500 flex items-center gap-2 rounded-b-lg">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            {t("Removing a device only stops it from being used to sign in. Your password is unaffected.")}
          </footer>
        </section>
      </div>
    </AdminShell>
  );
}
