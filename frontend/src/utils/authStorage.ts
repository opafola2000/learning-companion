const ACCESS_KEY = "hanz_lc_access_token";
const REFRESH_KEY = "hanz_lc_refresh_token";

/** Clear legacy un-namespaced tokens that could confuse sessions. */
function clearLegacyTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function clearAuthTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  clearLegacyTokens();
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY) || localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY) || localStorage.getItem("refresh_token");
}

export function storeAuthTokens(access: string, refresh: string) {
  clearAuthTokens();
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}
