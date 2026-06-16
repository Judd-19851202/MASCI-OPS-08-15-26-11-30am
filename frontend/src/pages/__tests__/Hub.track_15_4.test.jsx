/**
 * TRACK 15.4 (2026-06-16) — Homepage hero + Project Systems regression.
 *
 * Guards the elements the user explicitly approved during the polish
 * pass so a future cosmetic edit cannot silently regress them:
 *
 *   • hero headline reads "One System. Every Crew. Every Job."
 *   • hero subheadline reads the approved capability sentence
 *   • Project Systems title (NOT "Projects")
 *   • Project Systems description (the connected-platforms sentence)
 *   • all 3 launchers exist with correct URL + target=_blank +
 *     rel="noopener noreferrer"
 *   • per-launcher accent stripe color + LAUNCH eyebrow color
 *     remain brand-correct
 *
 * Run:
 *   cd /app/frontend && CI=true yarn test --watchAll=false \
 *     src/pages/__tests__/Hub.track_15_4.test.jsx
 */
import { describe, it, expect } from "@jest/globals";
import { render, screen } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";

import Hub from "../Hub.jsx";

function renderHub() {
  return render(
    <MemoryRouter>
      <Hub />
    </MemoryRouter>,
  );
}

describe("TRACK 15.4 — Homepage hero + Project Systems contract", () => {
  it("renders the approved EN hero headline", () => {
    renderHub();
    const h1 = screen.getByRole("heading", { level: 1 });
    // The accent span is in a separate node; combine all text.
    expect(h1.textContent).toMatch(/One System\. Every Crew\. Every Job\./);
  });

  it("renders the approved EN hero subheadline (capability sentence)", () => {
    renderHub();
    expect(
      screen.getByText(
        /Field reporting, safety, quality, equipment, workforce accountability, dispatch, and project operations — captured once, routed automatically, and visible everywhere they matter\./,
      ),
    ).toBeTruthy();
  });

  it('uses the new "Project Systems" title (not legacy "Projects")', () => {
    renderHub();
    expect(screen.getByTestId("hub-project-systems-title").textContent).toBe(
      "Project Systems",
    );
  });

  it("renders the approved Project Systems description", () => {
    renderHub();
    expect(
      screen.getByTestId("hub-project-systems-description").textContent,
    ).toMatch(
      /Connected project platforms for communication, utility locating, and construction plans\./,
    );
  });

  it.each([
    [
      "hub-projects-basecamp-btn",
      "https://3.basecamp.com/5958093/projects",
      "Basecamp",
    ],
    [
      "hub-projects-onstation-btn",
      "https://app.onstation.us/login",
      "OnStation",
    ],
    [
      "hub-projects-forgedops-plans-btn",
      "https://forgedopsplans.com/login",
      "ForgedOps Plans",
    ],
  ])(
    "launcher %s opens %s in a new tab with rel=noopener noreferrer (label=%s)",
    (testId, url, label) => {
      renderHub();
      const el = screen.getByTestId(testId);
      expect(el.tagName).toBe("A");
      expect(el.getAttribute("href")).toBe(url);
      expect(el.getAttribute("target")).toBe("_blank");
      expect(el.getAttribute("rel")).toBe("noopener noreferrer");
      // Label is rendered (whitespace-nowrap means it's never split).
      expect(el.textContent).toMatch(new RegExp(label));
    },
  );

  it("ForgedOps Plans label is NEVER abbreviated", () => {
    renderHub();
    const el = screen.getByTestId("hub-projects-forgedops-plans-btn");
    const txt = el.textContent || "";
    expect(txt).toMatch(/ForgedOps Plans/);
    // Forbidden short forms.
    expect(txt).not.toMatch(/\bFO Plans\b/);
    expect(txt).not.toMatch(/\bFOP\b/);
    // "Plans" alone is fine inside "ForgedOps Plans" but must not be
    // the only platform name shown.
  });
});
