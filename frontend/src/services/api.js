const ACCESS_KEY = "field_sales_access";
const REFRESH_KEY = "field_sales_refresh";
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
const pendingGets = new Map();

export function saveTokens({ access, refresh }) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;
  const response = await fetch(API_BASE + "/auth/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    clearTokens();
    return null;
  }
  const data = await response.json();
  localStorage.setItem(ACCESS_KEY, data.access);
  if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
  return data.access;
}

async function performApiRequest(path, options = {}, allowRefresh = true) {
  const access = localStorage.getItem(ACCESS_KEY);
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (access) headers.Authorization = "Bearer " + access;
  const response = await fetch(API_BASE + path, { ...options, headers });
  if (response.status === 401 && allowRefresh && localStorage.getItem(REFRESH_KEY)) {
    const newAccess = await refreshAccessToken();
    if (newAccess) return performApiRequest(path, options, false);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error("درخواست انجام نشد.");
    error.data = data;
    error.status = response.status;
    throw error;
  }
  return data;
}

export function apiRequest(path, options = {}, allowRefresh = true) {
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET") return performApiRequest(path, options, allowRefresh);
  const key = `${localStorage.getItem(ACCESS_KEY) || "anonymous"}:${path}`;
  if (pendingGets.has(key)) return pendingGets.get(key);
  const request = performApiRequest(path, options, allowRefresh).finally(() => pendingGets.delete(key));
  pendingGets.set(key, request);
  return request;
}

export async function apiBlob(path, allowRefresh = true) {
  const access = localStorage.getItem(ACCESS_KEY);
  const headers = access ? { Authorization: "Bearer " + access } : {};
  const response = await fetch(API_BASE + path, { headers });
  if (response.status === 401 && allowRefresh && localStorage.getItem(REFRESH_KEY)) {
    const newAccess = await refreshAccessToken();
    if (newAccess) return apiBlob(path, false);
  }
  if (!response.ok) {
    const error = new Error("دریافت فایل انجام نشد.");
    error.status = response.status;
    throw error;
  }
  return response.blob();
}

export function getErrorMessage(error) {
  if (typeof navigator !== "undefined" && !navigator.onLine) return "اینترنت قطع است؛ عملیات انجام نشد.";
  const data = error?.data;
  if (!data) return "ارتباط با سرور برقرار نشد. دوباره تلاش کنید.";
  if (typeof data.detail === "string") return data.detail;
  const firstValue = Object.values(data)[0];
  if (Array.isArray(firstValue)) return firstValue[0];
  if (typeof firstValue === "string") return firstValue;
  if (firstValue && typeof firstValue === "object") {
    const nestedValue = Object.values(firstValue)[0];
    if (Array.isArray(nestedValue)) return nestedValue[0];
  }
  return "اطلاعات واردشده را بررسی کنید.";
}
