// src/services/api.ts

import axios, { AxiosInstance, AxiosResponse } from "axios";

/**
 * Base URL:
 *  - Local dev: falls back to http://localhost:8000/api
 *  - Prod (Vercel): use VITE_API_BASE_URL in .env
 */
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// Low-level Axios client
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
});

/**
 * Helper to unwrap Axios responses into plain data
 */
async function unwrap<T>(
  promise: Promise<AxiosResponse<T>>
): Promise<T> {
  const res = await promise;
  return res.data;
}

/**
 * High-level API wrapper used across the app.
 * All endpoints are relative to API_BASE_URL.
 */
const api = {
  get<T>(endpoint: string): Promise<T> {
    return unwrap<T>(apiClient.get(endpoint));
  },

  post<T>(endpoint: string, data?: any): Promise<T> {
    return unwrap<T>(apiClient.post(endpoint, data));
  },

  put<T>(endpoint: string, data?: any): Promise<T> {
    return unwrap<T>(apiClient.put(endpoint, data));
  },

  delete<T>(endpoint: string): Promise<T> {
    return unwrap<T>(apiClient.delete(endpoint));
  },

  /**
   * For file uploads: PDFs, docs, etc.
   */
  postMultipart<T>(endpoint: string, formData: FormData): Promise<T> {
    return unwrap<T>(
      apiClient.post(endpoint, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
    );
  },
};

export default api;
export { apiClient };
