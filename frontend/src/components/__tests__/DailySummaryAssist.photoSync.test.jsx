/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach */
import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import DailySummaryAssist from "../daily-report/DailySummaryAssist";

jest.mock("@/lib/i18n", () => ({
  useT: () => ({ t: (x) => x }),
}));

jest.mock("@/lib/resiliency/actorId", () => ({
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

describe("DailySummaryAssist photo sync after upload", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return {
          data: {
            status: "queued",
            lifecycle_status: "queued",
            photo_count: 6,
            queued: 6,
            reviewed: 0,
            observations: [],
          },
        };
      }
      return {
        data: {
          enabled: false,
          summary_text: "Draft summary",
          warnings: ["draft_fast_path_deterministic"],
          evidence_refs: [],
          summary_input: {
            photos: {
              status: "queued",
              lifecycle_status: "queued",
            },
          },
          photo_intelligence: {
            status: "queued",
            lifecycle_status: "queued",
            photo_count: 6,
            queued: 6,
            reviewed: 0,
            observations: [],
          },
        },
      };
    });
  });

  test("promotes post-upload photo status out of no-photos without regenerate", async () => {
    const baseData = {
      project_number: "DR-TEST",
      project_name: "Test Project",
      report_date: "2026-07-16",
      production: [{ description: "Excavation work", quantity: 250, unit: "LF" }],
      masci_crews: [{ name: "Crew", hours: 8.5 }],
      photos: [],
    };

    const { rerender } = render(
      <DailySummaryAssist
        data={baseData}
        formKey="draft-test"
        photoUploadState={{ inFlight: true, total: 6, completed: 0, failed: 0, phase: "compressing" }}
      />,
    );

    rerender(
      <DailySummaryAssist
        data={{
          ...baseData,
          photos: Array.from({ length: 6 }, (_, i) => `data:image/jpeg;base64,photo-${i + 1}`),
        }}
        formKey="draft-test"
        photoUploadState={{ inFlight: false, total: 6, completed: 6, failed: 0, phase: "complete" }}
      />,
    );

    await act(async () => {
      jest.advanceTimersByTime(250);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-photo-status").textContent).toContain("Queued 6 photos for analysis.");
    });

    expect(screen.getByTestId("daily-summary-assist-photo-status").textContent).not.toContain("No photos attached yet.");
    expect(mockPost).toHaveBeenCalledWith(
      "/daily-reports/photo-intelligence/draft",
      expect.objectContaining({ form_key: "draft-test" }),
    );
  });
});