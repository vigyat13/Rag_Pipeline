// src/services/api.ts

import axios, { AxiosInstance, AxiosResponse } from "axios";

/**
 * Base URL:
 *  - Local dev: falls back to http://localhost:8000/api
 *  - Prod (Vercel): use VITE_API_BASE_URL in .env
 */
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://rag-pipeline-m6en.onrender.com/api";

// Low-level Axios client (internal only)
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
  // Normal axios shape: { data: ... }
  return (res.data as T) ?? (res as any);
}

/**
 * High-level API wrapper used across the app.
 * All endpoints are relative to API_BASE_URL.
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
// ❌ DO NOT export apiClient anymore
