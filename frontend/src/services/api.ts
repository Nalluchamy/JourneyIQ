import axios from 'axios';

// Resolve backend API URL from Vite environment variable
const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Generate or retrieve session UUID for storefront journey tracking
export const getOrCreateSessionId = (): string => {
  let sessionId = sessionStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
    sessionStorage.setItem('session_id', sessionId);
  }
  return sessionId;
};

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor to attach authentication token and tracing headers dynamically
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    config.headers['X-Session-ID'] = getOrCreateSessionId();
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

    console.error('API Client error:', requestDetails, errorResponse?.data || error.message);

    if (errorResponse) {
      return Promise.reject({
        status: errorResponse.status,
        message: errorResponse.data?.detail || errorResponse.data?.message || 'An unexpected error occurred.',
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

// API Endpoints Services Wrapper
export const authApi = {
  login: async (credentials: any) => {
    // Standard OAuth2 form submission
    const params = new URLSearchParams();
    params.append('username', credentials.email);
    params.append('password', credentials.password);
    const res = await apiClient.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return res.data;
  },
  register: async (userData: any) => {
    const res = await apiClient.post('/api/v1/auth/register', userData);
    return res.data;
  },
  getProfile: async () => {
    const res = await apiClient.get('/api/v1/users/me');
    return res.data.data; // Unwrap envelope
  },
  updateProfile: async (data: any) => {
    const res = await apiClient.patch('/api/v1/users/me', data);
    return res.data.data; // Unwrap envelope
  },
};

export const productsApi = {
  getProducts: async (params: any) => {
    const res = await apiClient.get('/api/v1/products', { params });
    return res.data;
  },
  getProduct: async (id: number) => {
    const res = await apiClient.get(`/api/v1/products/${id}`);
    return res.data;
  },
};

export const reviewsApi = {
  getReviews: async (productId: number) => {
    const res = await apiClient.get(`/api/v1/products/${productId}/reviews`);
    return res.data.data;
  },
  createReview: async (productId: number, data: any) => {
    const res = await apiClient.post(`/api/v1/products/${productId}/reviews`, data);
    return res.data.data;
  },
};

export const wishlistApi = {
  getWishlist: async () => {
    const res = await apiClient.get('/api/v1/wishlist');
    return res.data.data;
  },
  addToWishlist: async (productId: number) => {
    const res = await apiClient.post('/api/v1/wishlist', { product_id: productId });
    return res.data.data;
  },
  removeFromWishlist: async (productId: number) => {
    const res = await apiClient.delete(`/api/v1/wishlist/${productId}`);
    return res.data;
  },
};

export const cartApi = {
  getCart: async () => {
    const res = await apiClient.get('/api/v1/cart');
    return res.data.data;
  },
  addToCart: async (productId: number, quantity: number = 1) => {
    const res = await apiClient.post('/api/v1/cart', { product_id: productId, quantity });
    return res.data.data;
  },
  updateQuantity: async (productId: number, quantity: number) => {
    const res = await apiClient.put(`/api/v1/cart/${productId}`, { quantity });
    return res.data.data;
  },
  removeFromCart: async (productId: number) => {
    const res = await apiClient.delete(`/api/v1/cart/${productId}`);
    return res.data;
  },
  clearCart: async () => {
    const res = await apiClient.delete('/api/v1/cart');
    return res.data;
  },
};

export const eventsApi = {
  trackEvent: async (eventType: string, pagePath: string, productId?: number, metadata?: any) => {
    try {
      await apiClient.post('/api/v1/events', {
        event_type: eventType,
        page: pagePath,
        product_id: productId,
        metadata: metadata || null,
      });
    } catch (e) {
      console.warn('Silent event tracking failure:', e);
    }
  },
  getRecentViews: async (sessionId: string) => {
    const res = await apiClient.get(`/api/v1/events/recent-views?session_id=${sessionId}`);
    return res.data.data;
  },
};

export const ordersApi = {
  getMyOrders: async () => {
    const res = await apiClient.get('/api/v1/orders/history');
    return res.data; // returns paginated results
  },
  getOrderDetails: async (id: number) => {
    const res = await apiClient.get(`/api/v1/orders/${id}`);
    return res.data;
  },
  cancelOrder: async (id: number) => {
    const res = await apiClient.patch(`/api/v1/orders/${id}/cancel`);
    return res.data;
  },
  getInvoice: async (id: number) => {
    const res = await apiClient.get(`/api/v1/orders/${id}/invoice`);
    return res.data;
  },
};

export const addressesApi = {
  getAddresses: async () => {
    const res = await apiClient.get('/api/v1/addresses');
    return res.data;
  },
  createAddress: async (data: any) => {
    const res = await apiClient.post('/api/v1/addresses', data);
    return res.data;
  },
  updateAddress: async (id: number, data: any) => {
    const res = await apiClient.put(`/api/v1/addresses/${id}`, data);
    return res.data;
  },
  deleteAddress: async (id: number) => {
    const res = await apiClient.delete(`/api/v1/addresses/${id}`);
    return res.data;
  },
};

export const couponsApi = {
  getCoupons: async () => {
    const res = await apiClient.get('/api/v1/coupons');
    return res.data;
  },
  applyCoupon: async (code: string, cartTotal: number) => {
    const res = await apiClient.post('/api/v1/checkout/apply-coupon', { code, cart_total: cartTotal });
    return res.data;
  },
};

export const checkoutApi = {
  getSummary: async (couponCode?: string) => {
    const params = couponCode ? { coupon_code: couponCode } : {};
    const res = await apiClient.get('/api/v1/cart/summary', { params });
    return res.data;
  },
  checkout: async (data: { shipping_address_id: number; coupon_code?: string }) => {
    const res = await apiClient.post('/api/v1/checkout', data);
    return res.data;
  },
};

export const paymentsApi = {
  mockSuccess: async (orderId: number) => {
    const res = await apiClient.post(`/api/v1/payments/mock-success/${orderId}`);
    return res.data;
  },
  mockFailure: async (orderId: number) => {
    const res = await apiClient.post(`/api/v1/payments/mock-failure/${orderId}`);
    return res.data;
  },
};

export const recommendationsApi = {
  getPersonalized: async () => {
    const res = await apiClient.get('/api/v1/recommendations');
    return res.data.data;
  },
  getTrending: async () => {
    const res = await apiClient.get('/api/v1/recommendations/trending');
    return res.data.data;
  },
  getPopular: async () => {
    const res = await apiClient.get('/api/v1/recommendations/popular');
    return res.data.data;
  },
  getSimilar: async (productId: number) => {
    const res = await apiClient.get(`/api/v1/products/${productId}/similar`);
    return res.data.data;
  },
};

export const assistantApi = {
  chat: async (message: string, sessionId?: string) => {
    const res = await apiClient.post('/api/v1/assistant/chat', { message, session_id: sessionId });
    return res.data.data;
  },
  getSuggestions: async () => {
    const res = await apiClient.get('/api/v1/assistant/suggestions');
    return res.data.data;
  },
  getSentiment: async () => {
    const res = await apiClient.get('/api/v1/assistant/sentiment');
    return res.data.data;
  },
};

export const generativeApi = {
  generateMarketing: async (segment: string, campaignType: string, productContext?: string) => {
    const res = await apiClient.post('/api/v1/generative/marketing', { segment, campaign_type: campaignType, product_context: productContext });
    return res.data.data;
  },
  generateLayout: async (segment?: string) => {
    const res = await apiClient.post('/api/v1/generative/layout', { segment });
    return res.data.data;
  },
  simulateJourney: async (segment: string) => {
    const res = await apiClient.post('/api/v1/generative/journey', { segment });
    return res.data.data;
  },
  generateImagePrompt: async (style: string, productContext: string, colors: string[]) => {
    const res = await apiClient.post('/api/v1/generative/image-prompt', { style, product_context: productContext, colors });
    return res.data.data;
  },
};

export const agentApi = {
  getStatus: async () => {
    const res = await apiClient.get('/api/v1/agent/status');
    return res.data.data;
  },
  getHistory: async () => {
    const res = await apiClient.get('/api/v1/agent/history');
    return res.data.data;
  },
  getPending: async () => {
    const res = await apiClient.get('/api/v1/agent/pending');
    return res.data.data;
  },
  approveAction: async (actionId: string) => {
    const res = await apiClient.post(`/api/v1/agent/actions/${actionId}/approve`);
    return res.data.data;
  },
  rejectAction: async (actionId: string) => {
    const res = await apiClient.post(`/api/v1/agent/actions/${actionId}/reject`);
    return res.data.data;
  },
};
