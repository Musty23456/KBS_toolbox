import axios, { AxiosError } from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

const TOKEN_STORAGE_KEY = "kbs_toolbox_access_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Centralized 401 handling: any expired/invalid token clears local state and
 * sends the user back to login, rather than every page having to handle it.
 */
export function installUnauthorizedHandler(onUnauthorized: () => void) {
  apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        setStoredToken(null);
        onUnauthorized();
      }
      return Promise.reject(error);
    }
  );
}

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (typeof d === "string" ? d : d.message ? `${d.question ?? ""}: ${d.message}` : JSON.stringify(d)))
        .join("; ");
    }
    if (error.message) return error.message;
  }
  return "Something went wrong. Please try again.";
}
