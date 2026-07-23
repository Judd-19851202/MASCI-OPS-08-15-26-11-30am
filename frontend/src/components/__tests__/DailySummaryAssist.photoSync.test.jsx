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
const mockGet = jest.fn();
jest.mock("@/lib/api", () => ({
  api: {
    post: (...args) => mockPost(...args),
    get: (...args) => mockGet(...args),
  },
}));

describe("DailySummaryAssist photo sync after upload", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockGet.mockReset();
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
    mockGet.mockResolvedValue({ data: { status: "completed", result: { ok: true, enabled: false, summary_text: "Draft summary", photo_intelligence: { status: "queued", lifecycle_status: "queued", photo_count: 6, reviewed: 0, observations: [] } } } });
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
      const photoStatus = screen.getByTestId("daily-summary-assist-photo-status").textContent || "";
      expect(photoStatus.includes("Queued 6 photos for analysis.") || photoStatus.includes("AI is citing 0 of 6 photos...")).toBe(true);
    });

    expect(screen.getByTestId("daily-summary-assist-photo-status").textContent).not.toContain("No photos attached yet.");
    expect(mockPost).toHaveBeenCalledWith(
      "/daily-reports/photo-intelligence/draft",
      expect.objectContaining({ form_key: "draft-test" }),
      expect.objectContaining({ skipSessionStatus: true }),
    );
  });

  test("does not requeue summary generation while photo analysis status churns", async () => {
    let photoIntelCalls = 0;
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        photoIntelCalls += 1;
        if (photoIntelCalls === 1) {
          return {
            data: {
              status: "queued",
              lifecycle_status: "queued",
              photo_count: 3,
              queued: 3,
              reviewed: 0,
              observations: [],
            },
          };
        }
        if (photoIntelCalls === 2) {
          return {
            data: {
              status: "partially_analyzed",
              lifecycle_status: "partially_analyzed",
              photo_count: 3,
              queued: 1,
              processing: 1,
              reviewed: 1,
              observations: [{ description: "Excavator at trench line" }],
            },
          };
        }
        return {
          data: {
            status: "complete_with_observations",
            lifecycle_status: "complete_with_observations",
            photo_count: 3,
            queued: 0,
            processing: 0,
            reviewed: 3,
            observations: [{ description: "Crew staging pipe in trench" }],
          },
        };
      }
      return {
        data: {
          ok: true,
          enabled: false,
          mode: "deterministic_fallback",
          summary_text: "Crew installed 180 LF of pipe with three jobsite photos attached.",
          warnings: [],
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
            photo_count: 3,
            queued: 3,
            reviewed: 0,
            observations: [],
          },
        },
      };
    });

    render(
      <DailySummaryAssist
        data={{
          project_number: "DR-TEST",
          project_name: "Test Project",
          report_date: "2026-07-16",
          location: "North lot",
          production: [{ description: "Pipe installation", quantity: 180, unit: "LF" }],
          masci_crews: [{ name: "Crew", hours: 8.5 }],
          photos: Array.from({ length: 3 }, (_, i) => `data:image/jpeg;base64,photo-${i + 1}`),
        }}
        formKey="draft-test"
        photoUploadState={{ inFlight: false, total: 3, completed: 3, failed: 0, phase: "complete" }}
      />,
    );

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-textarea").value).toContain("three jobsite photos attached");
    });

    await act(async () => {
      jest.advanceTimersByTime(7000);
      await Promise.resolve();
      await Promise.resolve();
    });

    const summaryCalls = mockPost.mock.calls.filter(([url]) => url === "/daily-reports/summary/draft");
    const intelCalls = mockPost.mock.calls.filter(([url]) => url === "/daily-reports/photo-intelligence/draft");

    expect(summaryCalls).toHaveLength(1);
    expect(intelCalls.length).toBeGreaterThan(1);
  });

  test("never shows no-photos copy when local photos already exist", async () => {
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return {
          data: {
            status: "no_photos",
            lifecycle_status: "no_photos",
            photo_count: 0,
            queued: 0,
            reviewed: 0,
            observations: [],
          },
        };
      }
      return {
        data: {
          ok: true,
          enabled: false,
          mode: "deterministic_fallback",
          summary_text: "Crew installed 60 LF of pipe and uploaded supporting photos.",
          warnings: [],
          evidence_refs: [],
          summary_input: {
            photos: {
              status: "no_photos",
              lifecycle_status: "no_photos",
            },
          },
          photo_intelligence: {
            status: "no_photos",
            lifecycle_status: "no_photos",
            photo_count: 0,
            reviewed: 0,
            observations: [],
          },
        },
      };
    });

    render(
      <DailySummaryAssist
        data={{
          project_number: "DR-TEST",
          project_name: "Test Project",
          report_date: "2026-07-16",
          location: "North lot",
          production: [{ description: "Pipe installation", quantity: 60, unit: "LF" }],
          masci_crews: [{ name: "Crew", hours: 8.5 }],
          photos: ["data:image/jpeg;base64,photo-1", "data:image/jpeg;base64,photo-2"],
        }}
        formKey="draft-test"
        photoUploadState={{ inFlight: false, total: 2, completed: 2, failed: 0, phase: "complete" }}
      />,
    );

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-photo-status").textContent).not.toContain("No photos attached yet.");
    });
  });

  test("keeps polling through transient job-not-found responses and hydrates completed photo status", async () => {
    let pollCount = 0;
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return {
          data: {
            status: "queued",
            lifecycle_status: "queued",
            photo_count: 3,
            queued: 3,
            reviewed: 0,
            observations: [],
          },
        };
      }
      return {
        data: {
          ok: true,
          job_id: "job-123",
          status: "queued",
          status_url: "/api/jobs/job-123/status",
          message: "AI is citing 0 of 3 photos...",
          details: { total_photos: 3, cited_photos: 0 },
        },
      };
    });
    mockGet.mockImplementation(async () => {
      pollCount += 1;
      if (pollCount <= 2) {
        const err = new Error("job not found");
        err.response = { status: 404 };
        throw err;
      }
      return {
        data: {
          status: "completed",
          result: {
            ok: true,
            enabled: true,
            summary_text: "Completed summary from final job state.",
            photo_intelligence: {
              status: "complete_with_observations",
              lifecycle_status: "complete_with_observations",
              photo_count: 3,
              reviewed: 3,
              observations: [{ description: "Crew staged pipe" }],
            },
          },
        },
      };
    });

    render(
      <DailySummaryAssist
        data={{
          project_number: "DR-TEST",
          project_name: "Test Project",
          report_date: "2026-07-16",
          location: "North lot",
          production: [{ description: "Pipe installation", quantity: 180, unit: "LF" }],
          masci_crews: [{ name: "Crew", hours: 8.5 }],
          photos: Array.from({ length: 3 }, (_, i) => `data:image/jpeg;base64,photo-${i + 1}`),
        }}
        formKey="draft-test"
        photoUploadState={{ inFlight: false, total: 3, completed: 3, failed: 0, phase: "complete" }}
      />,
    );

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
      await Promise.resolve();
      jest.advanceTimersByTime(1600);
      await Promise.resolve();
      await Promise.resolve();
      jest.advanceTimersByTime(1600);
      await Promise.resolve();
      await Promise.resolve();
      jest.advanceTimersByTime(1600);
      await Promise.resolve();
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByTestId("daily-summary-assist-textarea").value).toContain("Completed summary from final job state.");
      expect(screen.getByTestId("daily-summary-assist-photo-status").textContent).toContain("3 photos reviewed");
    });
  });

  test("treats cited photo state as reviewed instead of unavailable", async () => {
    mockPost.mockImplementation(async (url) => {
      if (url === "/daily-reports/photo-intelligence/draft") {
        return {
          data: {
            status: "cited",
            lifecycle_status: "cited",
            photo_count: 3,
            reviewed: 3,
            analyzed: 3,
            observations: [{ description: "Crew staged pipe" }],
          },
        };
      }
      return {
        data: {
          ok: true,
          enabled: true,
          summary_text: "Completed summary with cited photos.",
          photo_intelligence: {
            status: "cited",
            lifecycle_status: "cited",
            photo_count: 3,
            reviewed: 3,
            analyzed: 3,
            observations: [{ description: "Crew staged pipe" }],
          },
          summary_input: {
            photos: {
              status: "cited",
              lifecycle_status: "cited",
              photo_count: 3,
              analyzed: 3,
            },
          },
        },
      };
    });

    render(
      <DailySummaryAssist
        data={{
          project_number: "DR-TEST",
          project_name: "Test Project",
          report_date: "2026-07-16",
          location: "North lot",
          production: [{ description: "Pipe installation", quantity: 180, unit: "LF" }],
          masci_crews: [{ name: "Crew", hours: 8.5 }],
          photos: Array.from({ length: 3 }, (_, i) => `data:image/jpeg;base64,photo-${i + 1}`),
        }}
        formKey="draft-test"
        photoUploadState={{ inFlight: false, total: 3, completed: 3, failed: 0, phase: "complete" }}
      />,
    );

    await act(async () => {
      jest.advanceTimersByTime(1200);
      await Promise.resolve();
      await Promise.resolve();
    });

    await waitFor(() => {
      const text = screen.getByTestId("daily-summary-assist-photo-status").textContent || "";
      expect(text).toContain("3 photos reviewed");
      expect(text).not.toContain("Photo analysis unavailable");
    });
  });
});