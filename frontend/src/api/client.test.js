import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("API client", () => {
  it("uses the current origin when no API base URL is configured", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("[]", { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const { apiRequest } = await import("./client.js");
    await apiRequest("/api/v1/products");

    expect(fetchMock).toHaveBeenCalledWith(
      new URL("/api/v1/products", window.location.origin),
      expect.any(Object),
    );
  });
});
