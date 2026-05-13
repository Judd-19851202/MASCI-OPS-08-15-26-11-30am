import React from "react";
import { AlertTriangle, RefreshCcw, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * PosterErrorBoundary — catches render-time crashes inside any of the
 * printable poster pages and shows a recoverable error card instead of
 * a blank page.
 *
 * Wraps:
 *   • /cheatsheet
 *   • /admin/trench-boxes/poster
 *   • /admin/jha-plans/poster
 *   • /admin/posters/print-all
 *
 * Why this exists: the JhaPlansPosterCard had an undeclared `hubHome`
 * reference that ReferenceError-crashed the React render and silently
 * blanked the JHP poster + Print-All pages. Without an error boundary
 * a crash like that hides behind a white screen — the user has no
 * signal anything went wrong, and the production team can't see the
 * stack trace without DevTools open. This boundary surfaces the error
 * with a one-click reload + a back-to-admin link.
 */
export default class PosterErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // Surface to the browser console so the team can see the stack
    // trace without DevTools React profiling enabled.
    // eslint-disable-next-line no-console
    console.error("PosterErrorBoundary caught:", error, info?.componentStack);
  }

  handleRetry = () => {
    // Hard reload — clears any stale module state and re-runs the
    // render with a fresh component tree. Cheaper than try/catching
    // the underlying root cause from this generic wrapper.
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    const errMsg =
      (this.state.error && (this.state.error.message || String(this.state.error))) ||
      "Unknown render error.";

    return (
      <div
        className="min-h-screen bg-slate-50 flex items-center justify-center p-6"
        data-testid="poster-error-boundary"
      >
        <div className="max-w-xl w-full bg-white border-2 border-red-700 rounded-md shadow-xl overflow-hidden">
          <div className="bg-red-700 text-white px-6 py-4 flex items-center gap-3">
            <AlertTriangle className="w-6 h-6" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] font-bold opacity-80">
                Render Error
              </div>
              <div className="font-display text-xl font-black">
                Something broke while drawing this poster.
              </div>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <p className="text-slate-700 leading-relaxed">
              The page hit an error before it could render. The team can fix
              this fast — please send a screenshot of this card to the
              MASCI Operations Platform admin so they have the message below to chase down.
            </p>
            <pre
              className="bg-slate-900 text-amber-300 text-xs font-mono leading-snug px-3 py-2 rounded overflow-x-auto whitespace-pre-wrap break-all"
              data-testid="poster-error-message"
            >
              {errMsg}
            </pre>
            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="button"
                onClick={this.handleRetry}
                className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs border-b-2 border-red-900 transition-colors"
                data-testid="poster-error-retry"
              >
                <RefreshCcw className="w-4 h-4" /> Retry
              </button>
              <Link
                to="/admin"
                className="inline-flex items-center gap-2 h-10 px-4 rounded-md border-2 border-slate-300 hover:border-slate-400 bg-white text-slate-800 font-bold uppercase tracking-wide text-xs transition-colors"
                data-testid="poster-error-back-admin"
              >
                <ArrowLeft className="w-4 h-4" /> Back to Admin
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
