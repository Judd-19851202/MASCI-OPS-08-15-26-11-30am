import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { registerThumbCache } from "@/lib/thumbCache";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register the photo-thumbnail service worker (production HTTPS only).
// Failures are silent — the app still works with no SW, just no
// offline photo cache.
if (typeof window !== "undefined") {
  window.addEventListener("load", () => {
    registerThumbCache();
  });
}
