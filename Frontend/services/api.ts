// src/services/api.ts

import axios, { AxiosInstance, AxiosResponse } from "axios";

/**
 * Determine backend base URL:
 *  - Prod:  from VITE_API_BASE_URL
 *  - Local: http://localhost:8000/api
 */
let base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// Normalize trailing slash
if (!base.endsWith("/")) base = base + "/";

const apiClient: AxiosInstance = axios.create({
  baseURL: base,
  withCredentials: false,
});

/**
 * Attach Authorization header when JWT exists
 */
apiClient.interceptors.request.use((config) => {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }
  return config;
});

/**
 * Clean unwrap helper
 */
const unwrap = async <T>(promise: Promise<AxiosResponse<T>>): Promise<T> => {
  const res = await promise;
  return res.data;
};

/**
 * High-level API wrapper
 */
const api = {
  get<T>(endpoint: string, config?: any): Promise<T> {
    return unwrap<T>(apiClient.get(endpoint, config));
  },

  post<T>(endpoint: string, data?: any, config?: any): Promise<T> {
    return unwrap<T>(apiClient.post(endpoint, data, config));
  },

  put<T>(endpoint: string, data?: any, config?: any): Promise<T> {
    return unwrap<T>(apiClient.put(endpoint, data, config));
  },

  delete<T>(endpoint: string, config?: any): Promise<T> {
    return unwrap<T>(apiClient.delete(endpoint, config));
  },

  // File uploads (PDFs etc.)
  postMultipart<T>(endpoint: string, formData: FormData): Promise<T> {
    return unwrap<T>(
      apiClient.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
    );
  },
};

export default api;
