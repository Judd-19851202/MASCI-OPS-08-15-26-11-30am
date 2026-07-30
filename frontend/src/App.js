import React from "react";
import "@/App.css";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";
// Track 15.67 Phase 3 · tenant-safe branding context for the whole app.
import { BrandingProvider } from "@/lib/BrandingProvider";
// Chrome + system components (mounted around <BrowserRouter/> or inside as siblings of Routes).
import GlobalFooter from "@/components/GlobalFooter";
import ScrollToTop from "@/components/ScrollToTop";
import GlobalKeepalive from "@/components/GlobalKeepalive";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import SessionStatusOverlay from "@/components/SessionStatusOverlay";
import ClusterCapacityBanner from "@/components/ClusterCapacityBanner";
import BannerStrip from "@/components/BannerStrip";
import EnvBanner from "@/components/EnvBanner";
import SplashOverlay from "@/components/SplashOverlay";
import QueueStatusPill from "@/components/QueueStatusPill";
import OfflineBanner from "@/components/OfflineBanner";
import EnforcePortalScope from "@/components/EnforcePortalScope";
import MultiPortalHydrator from "@/components/MultiPortalHydrator";
import IdleTimeout from "@/components/IdleTimeout";
import { validateStoredTokens } from "@/lib/tokenValidation";
// Track 22.2 Phase B · route-group extraction — all <Route> declarations
// live in app/routing/AppRoutes so App.js remains a thin orchestration
// shell (providers + chrome + BrowserRouter + <AppRoutes/>).
import { AppRoutes } from "@/app/routing/AppRoutes";

function App() {
  // Validate any locally-stored auth tokens against the backend on app
  // load. If a password got rotated (or the HMAC secret changed) the
  // user's old token no longer works server-side — but `isAdmin()` etc.
  // only check for presence, so the UI keeps rendering gated surfaces
  // as "unlocked". We ping the four /check endpoints once, clear any
  // token the backend rejects with 401, then bump `authTick` so the
  // router fully remounts and every page re-reads localStorage.
  const [authTick, setAuthTick] = React.useState(0);
  React.useEffect(() => {
    let mounted = true;
    validateStoredTokens().then((cleared) => {
      if (mounted && cleared) setAuthTick((t) => t + 1);
    });
    // iter146 — wire fire-and-forget usage analytics. Safe to call
    // multiple times (the binder guards itself with a one-shot flag).
    import("@/lib/usageTracker").then(({ bindRouteChangeTracker }) => {
      bindRouteChangeTracker();
    }).catch(() => { /* silent */ });
    // iter166 — Phase J · purge stale (>14d) IndexedDB drafts on boot.
    // Fire-and-forget, never blocks app render.
    import("@/lib/resiliency").then(({ purgeStaleDrafts }) => {
      purgeStaleDrafts();
    }).catch(() => { /* silent */ });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <BrandingProvider>
    <div className="App min-h-screen flex flex-col">
      <SplashOverlay />
      <Toaster
        position="bottom-right"
        richColors
        closeButton
        offset={16}
        toastOptions={{
          classNames: {
            toast: "!rounded-[var(--radius-card)] !border !border-[color:var(--border-bold)] !bg-white !text-[color:var(--ink-strong)] !shadow-[var(--shadow-dialog)]",
            title: "!font-semibold !text-[color:var(--ink-strong)]",
            description: "!text-[color:var(--ink-soft)]",
            actionButton: "!bg-[color:var(--brand-primary)] !text-white",
            cancelButton: "!border !border-[color:var(--border-bold)] !bg-[color:var(--paper-card-muted)] !text-[color:var(--ink-strong)]",
          },
        }}
      />
      {/* R-BL-3 · Global queue visibility pill (visibility-only). */}
      <QueueStatusPill />
      {/* TRACK 14.0-RC1 · D3 — Global offline trust surface. Calm sky-blue
         ribbon that appears the moment navigator.onLine === false and
         auto-dismisses on reconnect. Pairs with QueueStatusPill: the
         pill shows what is queued, the banner shows why. */}
      <OfflineBanner />
      <GlobalKeepalive />
      <BackendStatusBanner />
      <ClusterCapacityBanner />
      <EnvBanner />
      <BannerStrip />
      <BrowserRouter key={authTick}>
        <ScrollToTop />
        <EnforcePortalScope />
        <MultiPortalHydrator />
        <IdleTimeout />
        {/* TRUST-DIAGNOSTICS-001 · Global session/error overlay.
            Mounted inside BrowserRouter so it can read location +
            navigate to the right login route on "Log Back In". */}
        <SessionStatusOverlay />
        <div className="flex-1 flex flex-col">
          <AppRoutes />
          <GlobalFooter />
        </div>
      </BrowserRouter>
    </div>
    </BrandingProvider>
  );
}

export default App;
