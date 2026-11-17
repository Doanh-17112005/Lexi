import { describe, expect, it } from "vitest";

import { ApiError } from "./api";
import { getAdminLoginErrorMessage } from "./adminLoginError";

describe("getAdminLoginErrorMessage", () => {
  it("maps invalid credentials to a clear Vietnamese message", () => {
    expect(
      getAdminLoginErrorMessage(new ApiError("Incorrect email or password", 401))
    ).toBe("Email hoặc mật khẩu không đúng.");
  });

  it("distinguishes disabled and unauthorized admin accounts", () => {
    expect(getAdminLoginErrorMessage(new ApiError("User account is inactive", 403))).toBe(
      "Tài khoản đã bị vô hiệu hóa."
    );
    expect(getAdminLoginErrorMessage(new ApiError("Admin privileges required", 403))).toBe(
      "Tài khoản không có quyền truy cập Admin Dashboard."
    );
  });

  it("maps service and browser network failures without exposing raw errors", () => {
    expect(getAdminLoginErrorMessage(new ApiError("Unavailable", 503))).toBe(
      "Dịch vụ xác thực tạm thời không khả dụng. Vui lòng thử lại."
    );
    expect(getAdminLoginErrorMessage(new TypeError("Failed to fetch"))).toBe(
      "Không thể kết nối Backend. Vui lòng kiểm tra dịch vụ và thử lại."
    );
  });
});
