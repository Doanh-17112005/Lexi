import { apiFetch } from "./api";
import { ENV } from "./env";
import { UserProfile } from "./auth";

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  username: string;
  email: string;
  role?: string;
};

type BackendEnvelope<T> = { data: T };

const unwrapData = <T>(payload: T | BackendEnvelope<T>): T =>
  typeof payload === "object" && payload !== null && "data" in payload
    ? (payload as BackendEnvelope<T>).data
    : (payload as T);

export const loginRequest = async (email: string, password: string) => {
  const response = await apiFetch<LoginResponse | BackendEnvelope<LoginResponse>>(`${ENV.backendUrl}/auth/login`, {
    skipAuth: true,
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  return unwrapData(response);
};

export const googleLoginRequest = async (idToken: string) => {
  const response = await apiFetch<LoginResponse | BackendEnvelope<LoginResponse>>(`${ENV.backendUrl}/auth/google`, {
    skipAuth: true,
    method: "POST",
    body: JSON.stringify({ id_token: idToken, source: "admin" })
  });
  return unwrapData(response);
};

export const refreshTokenRequest = async (refreshToken: string) => {
  const response = await apiFetch<
    | { access_token: string; refresh_token: string; token_type: string }
    | BackendEnvelope<{ access_token: string; refresh_token: string; token_type: string }>
  >(
    `${ENV.backendUrl}/auth/refresh`,
    {
      skipAuth: true,
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken })
    }
  );
  return unwrapData(response);
};

export const getCurrentUser = async () => {
  const response = await apiFetch<UserProfile | BackendEnvelope<UserProfile>>(
    `${ENV.backendUrl}/auth/me`
  );
  return unwrapData(response);
};

export const logoutRequest = async (
  accessToken: string | null,
  refreshToken: string | null
) =>
  apiFetch(`${ENV.backendUrl}/auth/logout`, {
    skipAuth: true,
    method: "POST",
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    body: JSON.stringify({ refresh_token: refreshToken })
  });
