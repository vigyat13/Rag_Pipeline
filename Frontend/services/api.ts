// Frontend/services/api.ts
import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
} from "axios";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// ✅ Single axios client for the whole app
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// ✅ Attach token automatically on the client side
apiClient.interceptors.request.use((config) => {
  // Guard for SSR / build step so Vercel doesn't crash
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ✅ Common error handler: unwrap data or throw a clean Error(message)
async function unwrap<T>(promise: Promise<AxiosResponse<T>>): Promise<T> {
  try {
    const res = await promise;
    return res.data;
  } catch (error) {
    const err = error as AxiosError<any>;
    const msg =
      (err.response?.data as any)?.detail ||
      (err.response?.data as any)?.message ||
      err.message ||
      "Request failed";
    throw new Error(msg);
  }
}

// ✅ Helper API wrapper used by your pages (Login, Documents, etc.)
export const api = {
  get<T = unknown>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    return unwrap<T>(apiClient.get(endpoint, config));
  },

  post<T = unknown>(
    endpoint: string,
    body?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return unwrap<T>(apiClient.post(endpoint, body, config));
  },

  // Used by Documents: api.postMultipart(...)
  postMultipart<T = unknown>(
    endpoint: string,
    formData: FormData,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return unwrap<T>(
      apiClient.post(endpoint, formData, {
        ...(config || {}),
        headers: {
          ...(config?.headers || {}),
          "Content-Type": "multipart/form-data",
        },
      })
    );
  },

  delete<T = unknown>(
    endpoint: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return unwrap<T>(apiClient.delete(endpoint, config));
  },
};

// Optional default export
export default api;
