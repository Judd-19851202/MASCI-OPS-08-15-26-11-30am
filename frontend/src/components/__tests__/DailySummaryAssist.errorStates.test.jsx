/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach */
import React from "react";
import "@testing-library/jest-dom";
import { act, render, screen, waitFor } from "@testing-library/react";
import DailySummaryAssist from "../daily-report/DailySummaryAssist";

jest.mock("@/lib/i18n", () => ({
  useT: () => ({ t: (x) => x }),
}));

jest.mock("@/lib/resiliency/actorId", () => ({
  getDeviceScopedActorId: () => "device-test",
  getStableActorIdentity: () => "actor-test",
}));

jest.mock("@/lib/resiliency/draftStore", () => ({
  saveDraft: jest.fn(async () => undefined),
}));

const mockPost = jest.fn();
jest.mock("@/lib/api", () => ({
  api: {
    post: (...args) => mockPost(...args),
    get: jest.fn(),
  },
}));

const BASE_DATA = {
  project_number: "DR-TEST",
  project_name: "Test Project",
  report_date: "2026-07-16",
  location: "North lot",
  production: [{ description: "Excavation work", quantity: 250, unit: "LF" }],
  masci_crews: [{ name: "Crew", hours: 8.5, start_time: "06:00", stop_time: "15:00", lunch_minutes: 30 }],
  equipment: [{ description: "Paver", hours_used: 6, idle_hours: 0 }],
  photos: ["data:image/jpeg;base64,photo-1"],
};

function renderAssist(extraProps = {}) {
  return render(
    <DailySummaryAssist
      data={BASE_DATA}
      formKey="draft-test"
      photoUploadState={{ inFlight: false, total: 1, completed: 1, failed: 0, phase: "complete" }}
      onAccept={jest.fn()}
      onStateChange={jest.fn()}
      {...extraProps}
    />,
  );
}

describe("DailySummaryAssist failure handling", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  test.each([
    ["detail object", { response: { status: 503, data: { detail: { error: "provider_unavailable", debug: { raw: true } } } } }],
    ["validation array", { response: { status: 422, data: { detail: [{ loc: ["body", "summary"], msg: "field required", type: "missing" }] } } }],
    ["provider 429", { response: { status: 429, data: { detail: "Rate limit exceeded" } } }],
    ["timeout", { code: "ECONNABORTED", message: "timeout of 60000ms exceeded" }],
    ["network failure", { code: "ERR_NETWORK", message: "Network Error" }],
    ["unknown object", { foo: "bar", deep: { bad: true } }],
    ["null error", null],
  ])("never renders raw object text for %s", async (_label, thrown) => {
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return { data: { status: "complete_with_observations", photo_count: 1, reviewed: 1, observations: [] } };
      }
      throw thrown;
    });

    renderAssist();

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-textarea").value).toContain("250 LF Excavation work");
    });

    expect(screen.queryByText("[object Object]")).not.toBeInTheDocument();
    expect(screen.getByTestId("daily-summary-assist-notice").textContent).toContain("visible summary is still available");
    expect(screen.queryByTestId("daily-summary-assist-error")).not.toBeInTheDocument();
  });

  test("keeps valid summary visible and approval usable during provider failure", async () => {
    const onAccept = jest.fn();
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return { data: { status: "complete_with_observations", photo_count: 1, reviewed: 1, observations: [] } };
      }
      throw { response: { status: 503, data: { detail: { error: "provider_unavailable" } } } };
    });

    renderAssist({ onAccept });

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-accept")).not.toBeDisabled();
    });

    screen.getByTestId("daily-summary-assist-accept").click();
    expect(onAccept).toHaveBeenCalledWith(
      expect.stringContaining("250 LF Excavation work"),
      expect.objectContaining({ source: "fallback" }),
    );
    expect(onAccept.mock.calls[0][1].accepted_at).toBeTruthy();
  });

  test("preserves exact labor parity in visible summary", async () => {
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return { data: { status: "complete_with_observations", photo_count: 1, reviewed: 1, observations: [] } };
      }
      return {
        data: {
          enabled: false,
          summary_text: "Work completed: 250 LF Excavation work.\n\nLabor and equipment: MASCI recorded 1 employee and 8.50 labor hours; 1 equipment unit logged 6.00 run hours and 0.00 idle hours.",
          warnings: [],
          evidence_refs: [],
          summary_input: { labor: { employee_count: 1, total_employee_hours: 8.5 } },
          photo_intelligence: { status: "complete_with_observations", photo_count: 1, reviewed: 1, observations: [] },
        },
      };
    });

    renderAssist();

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
    });

    await waitFor(() => {
      const text = screen.getByTestId("daily-summary-assist-textarea").value;
      expect(text).toContain("8.50 labor hours");
      expect(text).not.toContain("0.0 labor hours");
    });
  });

  test("never shows contradictory unavailable state while a visible summary exists", async () => {
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return { data: { status: "complete_with_observations", photo_count: 1, reviewed: 1, observations: [] } };
      }
      throw { response: { status: 500, data: { detail: { anything: "bad" } } } };
    });

    renderAssist();

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-textarea").value).toContain("250 LF Excavation work");
    });

    expect(screen.queryByTestId("daily-summary-assist-error")).not.toBeInTheDocument();
    expect(screen.getByTestId("daily-summary-assist-notice")).toBeInTheDocument();
  });
});