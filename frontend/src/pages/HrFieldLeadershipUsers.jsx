// HrFieldLeadershipUsers.jsx — HR-side host for the Field Leadership
// Portal user-management panel (iter314). Same component as Admin uses;
// the backend route accepts either X-Admin-Token or X-HR-Token.
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, LogOut, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import AdminFieldLeadershipUsersPanel from "@/components/AdminFieldLeadershipUsersPanel";
import { clearHrToken } from "@/lib/hrAuth";
import { usePageTitle } from "@/lib/usePageTitle";
import { useT } from "@/lib/i18n";

export default function HrFieldLeadershipUsers() {
  const t = useT();
  const navigate = useNavigate();
  usePageTitle("Field Leadership Users · HR");
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b-2 border-purple-700 px-4 sm:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <MasciLogo className="h-8 w-auto" />
            <span className="text-sm font-semibold text-purple-800 uppercase tracking-wide">
              {t("Field Leadership Users")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            <Link to="/hr">
              <Button
                variant="outline"
                size="sm"
                className="text-purple-700 border-purple-700"
                data-testid="hr-fl-users-back-hub"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                {t("HR Hub")}
              </Button>
            </Link>
            <Button
              variant="outline"
              size="sm"
              className="text-rose-700 border-rose-300"
              data-testid="hr-fl-users-signout"
              onClick={() => { clearHrToken(); navigate("/hr/login"); }}
            >
              <LogOut className="h-4 w-4 mr-1" />
              {t("Sign Out")}
            </Button>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-6">
        <div className="mb-4 flex items-center gap-2 text-sm text-slate-600">
          <Users className="h-4 w-4 text-purple-700" />
          <span>
            {t(
              "Manage MASCI Field Leadership Portal accounts. Issue per-user temporary passwords, reset passwords, and deactivate field leaders. This is the governed per-user portal — distinct from the legacy shared-password document gate."
            )}
          </span>
        </div>
        <AdminFieldLeadershipUsersPanel />
      </main>
    </div>
  );
}
