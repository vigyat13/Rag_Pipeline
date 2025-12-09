// frontendrag/services/api.ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  withCredentials: false,
});

// 🔹 Axios instance used everywhere
export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// Attach token automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Common error handler
function unwrap<T>(promise: Promise<AxiosResponse<T>>): Promise<T> {
  return promise
    .then((res) => res.data)
    .catch((err: AxiosError<any>) => {
      const msg =
        (err.response?.data as any)?.detail ||
        (err.response?.data as any)?.message ||
        err.message ||
        "Request failed";
      throw new Error(msg);
    });
}

// 🔹 Helper API wrapper used by your pages (Login, Documents, etc.)
export const api = {
  get<T>(endpoint: string): Promise<T> {
    return unwrap<T>(apiClient.get(endpoint));
  },

  post<T>(endpoint: string, body: any): Promise<T> {
    return unwrap<T>(apiClient.post(endpoint, body));
  },

  // ✅ This is what Documents uses: api.postMultipart(...)
  postMultipart<T>(endpoint: string, formData: FormData): Promise<T> {
    return unwrap<T>(
      apiClient.post(endpoint, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
    );
  },

  delete<T>(endpoint: string): Promise<T> {
    return unwrap<T>(apiClient.delete(endpoint));
  },
};

// Optional default export (harmless, in case somewhere you did `import api from`)
export default api;
