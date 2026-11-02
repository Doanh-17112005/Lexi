import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetchMock } = vi.hoisted(() => ({ apiFetchMock: vi.fn() }));

vi.mock("./api", () => ({ apiFetch: apiFetchMock }));
vi.mock("./env", () => ({
  ENV: { backendUrl: "https://backend.example/api/v1" },
}));

import { generateAiLesson } from "./aiContentApi";

describe("aiContentApi", () => {
  beforeEach(() => apiFetchMock.mockReset());

  it("sends the source text to the authenticated backend endpoint", async () => {
    apiFetchMock.mockResolvedValueOnce({ success: true });
    const request = {
      topic: "Job interviews",
      cefr_level: "B2" as const,
      source_text: "A sufficiently long source passage for a generated lesson.",
    };

    await generateAiLesson(request);

    expect(apiFetchMock).toHaveBeenCalledWith(
      "https://backend.example/api/v1/admin/ai-content/generate-lesson",
      { method: "POST", body: JSON.stringify(request) },
    );
  });
});
