import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiFetch } = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("./api", () => ({ apiFetch }));
vi.mock("./env", () => ({
  ENV: { backendUrl: "http://127.0.0.1:8000/api/v1" },
}));

import { getCurrentUser, googleLoginRequest, loginRequest, logoutRequest } from "./authApi";

describe("auth API contract", () => {
  beforeEach(() => apiFetch.mockReset());

  it("unwraps the backend login envelope", async () => {
    apiFetch.mockResolvedValue({
      data: {
        access_token: "access",
        refresh_token: "refresh",
        token_type: "bearer",
        user_id: "user-id",
        username: "admin",
        email: "admin@example.com",
        role: "super_admin",
      },
    });

    const result = await loginRequest("admin@example.com", "Password!1");

    expect(result.access_token).toBe("access");
    expect(result.role).toBe("super_admin");
  });

  it("unwraps the current-user envelope", async () => {
    apiFetch.mockResolvedValue({
      data: { id: "user-id", email: "admin@example.com", role_slug: "admin" },
    });

    const result = await getCurrentUser();

    expect(result.role_slug).toBe("admin");
  });

  it("unwraps the backend Google login envelope", async () => {
    apiFetch.mockResolvedValue({
      data: {
        access_token: "google-access",
        refresh_token: "google-refresh",
        token_type: "bearer",
        user_id: "user-id",
        username: "admin",
        email: "admin@example.com",
        role: "admin",
      },
    });

    const result = await googleLoginRequest("real-id-token-shape-not-validated-here");

    expect(result.access_token).toBe("google-access");
    expect(apiFetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/google",
      expect.objectContaining({
        skipAuth: true,
        method: "POST",
        body: JSON.stringify({
          id_token: "real-id-token-shape-not-validated-here",
          source: "admin",
        }),
      })
    );
  });

  it("sends both tokens to backend logout without refreshing first", async () => {
    apiFetch.mockResolvedValue({ data: { message: "Logged out successfully" } });

    await logoutRequest("access", "refresh");

    expect(apiFetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/logout",
      expect.objectContaining({
        skipAuth: true,
        method: "POST",
        headers: { Authorization: "Bearer access" },
        body: JSON.stringify({ refresh_token: "refresh" }),
      })
    );
  });
});
