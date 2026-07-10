import axios from 'axios';

// Resolve backend API URL from Vite environment variable
const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor to attach authentication token or tracing headers dynamically
apiClient.interceptors.request.use(
  (config) => {
    // Pre-allocate space for Auth Header (used in Phase 2+)
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // You could also generate client-side trace IDs here if desired
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to format errors and extract request tracing headers
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const errorResponse = error.response;
    const requestDetails = {
      url: error.config?.url,
      method: error.config?.method,
      status: errorResponse?.status,
    };

    // Global error console intercept
    console.error('API Client error:', requestDetails, errorResponse?.data || error.message);

    // standard API response mapping
    if (errorResponse) {
      // Return structured response error
      return Promise.reject({
        status: errorResponse.status,
        message: errorResponse.data?.message || 'An unexpected error occurred.',
        error: errorResponse.data?.error || 'ApiException',
        requestId: errorResponse.headers['x-request-id'] || errorResponse.data?.request_id,
        details: errorResponse.data,
      });
    }

    return Promise.reject({
      status: 0,
      message: error.message || 'Network connectivity error.',
      error: 'NetworkError',
      requestId: null,
    });
  }
);
