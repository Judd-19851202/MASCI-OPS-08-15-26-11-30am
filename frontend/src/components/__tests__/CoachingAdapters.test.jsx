import React from "react";
import { describe, expect, it, jest } from "@jest/globals";
import { render, screen } from "@testing-library/react";

jest.mock("@/lib/i18n", () => ({
  __esModule: true,
  useT: () => ({ t: (value) => value, lang: "en" }),
}));

jest.mock("@/lib/operatorLanguage", () => ({
  __esModule: true,
  sanitizeOperatorCopy: (value) => value,
}));

jest.mock("react-router-dom", () => ({
  __esModule: true,
  Link: ({ to, children, ...rest }) => <a href={typeof to === "string" ? to : "#"} {...rest}>{children}</a>,
}), { virtual: true });

import LifecycleGuide from "../LifecycleGuide";
import { PortalLoginHelp } from "../PortalLoginHelp";
import OshaCoachingBlock from "../trench/OshaCoachingBlock";
import CoachingPanel from "../oa/CoachingPanel";

describe("coaching adapter surfaces", () => {
  it("keeps LifecycleGuide collapsed by default", () => {
    render(
      <LifecycleGuide
        id="adapter-lifecycle"
        title="Lifecycle title"
        summary="Short summary"
        sections={[{ label: "Why", body: "Because" }]}
      />,
    );

    expect(screen.getByTestId("lifecycle-guide-toggle-adapter-lifecycle").getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByTestId("lifecycle-guide-body-adapter-lifecycle")).toBeNull();
  });

  it("keeps portal login help collapsed by default", () => {
    render(<PortalLoginHelp portal="admin" />);

    expect(screen.getByTestId("portal-login-help-admin-trigger").getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByTestId("portal-login-help-admin-panel")).toBeNull();
  });

  it("keeps OSHA coaching collapsed by default", () => {
    render(
      <OshaCoachingBlock
        title="Soil classification"
        why="Why this matters"
        requirement="Rule"
        testId="coach-adapter"
      />,
    );

    expect(screen.getByTestId("coach-adapter-toggle").getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByTestId("coach-adapter-body")).toBeNull();
  });

  it("keeps Operations Actions coaching collapsed by default", () => {
    render(<CoachingPanel compact />);

    expect(screen.getByTestId("oa-coaching-panel-trigger").getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByTestId("oa-coaching-panel-panel")).toBeNull();
  });
});