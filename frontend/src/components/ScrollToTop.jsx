import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * ScrollToTop — global route-change scroll reset.
 *
 * React Router v6 does NOT reset scroll position on navigation by
 * default. That means: click tile at the bottom of the Hub → new
 * page loads but the browser keeps the old scroll offset, so the
 * user lands partway or at the bottom of the next page. This
 * component listens to every `pathname` change and scrolls to top.
 *
 * Exceptions: hash links (e.g. "/legal/terms#section-5") still jump
 * to their anchor — we only reset when the hash is empty.
 *
 * Mount once, inside <BrowserRouter>, above <Routes>.
 */
export default function ScrollToTop() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) return; // let the browser resolve #anchor targets
    window.scrollTo(0, 0);
  }, [pathname, hash]);

  return null;
}
