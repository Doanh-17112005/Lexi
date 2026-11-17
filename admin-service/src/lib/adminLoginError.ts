type HttpLikeError = Error & { status?: number };

export const getAdminLoginErrorMessage = (error: unknown): string => {
  const candidate = error as Partial<HttpLikeError> | null;
  const status = candidate?.status;
  const message = typeof candidate?.message === "string" ? candidate.message : "";
  const normalized = message.toLowerCase();

  if (status === 401) {
    return "Email hoặc mật khẩu không đúng.";
  }
  if (status === 403 && normalized.includes("inactive")) {
    return "Tài khoản đã bị vô hiệu hóa.";
  }
  if (status === 403) {
    return "Tài khoản không có quyền truy cập Admin Dashboard.";
  }
  if (status === 503) {
    return "Dịch vụ xác thực tạm thời không khả dụng. Vui lòng thử lại.";
  }
  if (
    error instanceof TypeError ||
    normalized.includes("failed to fetch") ||
    normalized.includes("không thể kết nối") ||
    normalized.includes("network") ||
    normalized.includes("connection")
  ) {
    return "Không thể kết nối Backend. Vui lòng kiểm tra dịch vụ và thử lại.";
  }

  return "Đăng nhập thất bại. Vui lòng thử lại.";
};
