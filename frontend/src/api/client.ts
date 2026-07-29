import axios from "axios";
import {
  clearAuthTokens,
  getAccessToken,
  getRefreshToken,
  storeAuthTokens,
} from "../utils/authStorage";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = getRefreshToken();

      if (refreshToken) {
        try {
          const res = await axios.post("/api/auth/refresh", {
            refresh_token: refreshToken,
          });
          storeAuthTokens(res.data.access_token, res.data.refresh_token);
          original.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(original);
        } catch {
          clearAuthTokens();
          window.location.href = "/login";
        }
      } else {
        clearAuthTokens();
      }
    }

    return Promise.reject(error);
  }
);

export default api;
