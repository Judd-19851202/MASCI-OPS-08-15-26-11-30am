// Field Leadership Hub — landing page after password gate.
// Lists 11 form tiles (10 Field Leadership forms + Safety Equipment Issuance link).
// Supervisor Notes is gated by admin login on top of the leadership password.

import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ShieldAlert, Lock, ListChecks, FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { isAdmin } from "@/lib/adminAuth";
import {
  getLeadershipToken,
  loginLeadership,
  clearLeadershipToken,
} from "@/lib/leadershipAuth";
import {
  FIELD_LEADERSHIP_FORMS,
  SAFETY_EQUIPMENT_ISSUANCE_LINK,
} from "@/lib/fieldLeadershipSchemas";

const ACCENT_BG = {
  red: "bg-red-50 text-red-700 border-red-200 hover:border-red-400",
  amber: "bg-amber-50 text-amber-800 border-amber-200 hover:border-amber-400",
  orange: "bg-orange-50 text-orange-800 border-orange-200 hover:border-orange-400",
  emerald: "bg-emerald-50 text-emerald-800 border-emerald-200 hover:border-emerald-400",
  blue: "bg-blue-50 text-blue-800 border-blue-200 hover:border-blue-400",
  purple: "bg-purple-50 text-purple-800 border-purple-200 hover:border-purple-400",
  lime: "bg-lime-50 text-lime-800 border-lime-200 hover:border-lime-400",
  indigo: "bg-indigo-50 text-indigo-800 border-indigo-200 hover:border-indigo-400",
  yellow: "bg-yellow-50 text-yellow-800 border-yellow-200 hover:border-yellow-400",
  slate: "bg-slate-100 text-slate-800 border-slate-300 hover:border-slate-500",
};

function PasswordGate({ onAuthed }) {
  const { t } = useT();
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!pw.trim()) return;
    setBusy(true);
    try {
      await loginLeadership(pw.trim());
      toast.success(t("Access granted"));
      onAuthed();
    } catch (err) {
      toast.error(t("Incorrect password"));
      setPw("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <Card className="w-full max-w-md p-8 border-2 border-slate-200">
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <Lock className="w-7 h-7 text-red-700" />
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            {t("MASCI HUB · Restricted")}
          </div>
          <h1 className="font-display text-2xl font-black mt-2">
            {t("Field Leadership")}
          </h1>
          <p className="text-sm text-slate-600 mt-3">
            {t("This section is restricted to MASCI field supervisors, foremen, superintendents, PMs, Safety, and Admin. Enter the leadership password to continue.")}
          </p>
        </div>
        <form onSubmit={submit} className="mt-6 space-y-3" data-testid="leadership-gate-form">
          <Input
            type="password"
            autoFocus
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            placeholder={t("Leadership password")}
            className="h-12 text-base border-2"
            data-testid="leadership-pw-input"
          />
          <Button
            type="submit"
            disabled={busy || !pw.trim()}
            className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
            data-testid="leadership-pw-submit"
          >
            {busy ? t("Verifying…") : t("Enter Field Leadership")}
          </Button>
        </form>
        <Link
          to="/"
          className="mt-6 flex items-center justify-center gap-2 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700"
        >
          <ArrowLeft className="w-3 h-3" /> {t("Back to Hub")}
        </Link>
      </Card>
    </main>
  );
}

export default function FieldLeadershipHub() {
  const { t, lang } = useT();
  const navigate = useNavigate();
  const [authed, setAuthed] = useState(() => Boolean(getLeadershipToken()));

  useEffect(() => {
    setAuthed(Boolean(getLeadershipToken()));
  }, []);

  if (!authed) {
    return <PasswordGate onAuthed={() => setAuthed(true)} />;
  }

  const signOut = () => {
    clearLeadershipToken();
    navigate("/");
  };

  const tiles = FIELD_LEADERSHIP_FORMS.map((f) => ({
    ...f,
    locked: f.admin_only && !isAdmin(),
  }));

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 text-white px-5 sm:px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-xs font-mono uppercase tracking-[0.2em] text-slate-300 hover:text-white">
            <ArrowLeft className="inline w-3 h-3 mr-1" /> {t("Hub")}
          </Link>
          <span className="text-slate-500">·</span>
          <span className="font-display text-base sm:text-lg font-black">{t("Field Leadership")}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline" className="h-9 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-amber-500 text-xs font-bold uppercase tracking-wide" data-testid="leadership-records-link">
            <Link to="/leadership/records"><ListChecks className="w-3.5 h-3.5 mr-1" />{t("Records")}</Link>
          </Button>
          <Button onClick={signOut} variant="outline" className="h-9 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 text-xs font-bold uppercase tracking-wide" data-testid="leadership-signout">
            {t("Sign Out")}
          </Button>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-8 pb-4">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">
          {t("Restricted · Crew Documentation")}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1 leading-tight">
          {t("Field Leadership")}
        </h1>
        <p className="text-slate-600 mt-3 max-w-2xl">
          {t("Crew accountability, employee documentation, equipment responsibility, recognition, and workforce management tools for MASCI field leadership.")}
        </p>
        <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-50 border border-amber-300 text-amber-900 text-xs font-mono uppercase tracking-[0.15em]">
          <ShieldAlert className="w-3.5 h-3.5" />
          {t("Forms must be factual, professional, and compliant with employment-documentation best practices.")}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-5 sm:px-8 pb-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {tiles.map((f) => {
            const Icon = f.icon;
            const cls = ACCENT_BG[f.accent] || ACCENT_BG.slate;
            const disabled = f.locked;
            const Inner = (
              <div className={`group p-5 rounded-lg border-2 transition-all ${disabled ? "bg-slate-50 border-slate-200 cursor-not-allowed opacity-60" : `${cls} cursor-pointer`}`}>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-md bg-white/60 border border-current/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-display text-base sm:text-lg font-bold leading-tight">
                      {f.title[lang] || f.title.en}
                    </div>
                    <p className="text-xs sm:text-sm mt-1 opacity-80 leading-snug">
                      {f.desc[lang] || f.desc.en}
                    </p>
                    {disabled && (
                      <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 bg-slate-200 text-slate-700 rounded text-[10px] font-mono uppercase tracking-[0.15em]">
                        <Lock className="w-3 h-3" /> {t("Admin Only")}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
            if (disabled) {
              return (
                <div key={f.kind} data-testid={`leadership-tile-${f.kind}`}>{Inner}</div>
              );
            }
            return (
              <Link key={f.kind} to={`/leadership/${f.kind}/new`} data-testid={`leadership-tile-${f.kind}`}>
                {Inner}
              </Link>
            );
          })}

          {/* Existing Safety Equipment Issuance form — link out */}
          <a
            href={SAFETY_EQUIPMENT_ISSUANCE_LINK.to}
            data-testid="leadership-tile-safety_equipment_issuance"
            className={`group p-5 rounded-lg border-2 transition-all ${ACCENT_BG[SAFETY_EQUIPMENT_ISSUANCE_LINK.accent]} cursor-pointer`}
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-md bg-white/60 border border-current/20 flex items-center justify-center flex-shrink-0">
                <SAFETY_EQUIPMENT_ISSUANCE_LINK.icon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-display text-base sm:text-lg font-bold leading-tight">
                  {SAFETY_EQUIPMENT_ISSUANCE_LINK.title[lang] || SAFETY_EQUIPMENT_ISSUANCE_LINK.title.en}
                </div>
                <p className="text-xs sm:text-sm mt-1 opacity-80 leading-snug">
                  {SAFETY_EQUIPMENT_ISSUANCE_LINK.desc[lang] || SAFETY_EQUIPMENT_ISSUANCE_LINK.desc.en}
                </p>
                <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 bg-white/60 text-current rounded text-[10px] font-mono uppercase tracking-[0.15em]">
                  <FileDown className="w-3 h-3" /> {t("Opens Safety Forms")}
                </div>
              </div>
            </div>
          </a>
        </div>
      </section>
    </main>
  );
}
