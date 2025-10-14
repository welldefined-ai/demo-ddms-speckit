/**
 * API utility for making HTTP requests
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get authorization headers with token
 */
const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * API helper object with common HTTP methods
 * Returns objects with { data, response } for easier consumption
 */
const api = {
  get: async (endpoint: string, options?: any) => {
    // Handle query params
    let url = `${API_BASE_URL}${endpoint}`;
    if (options?.params) {
      const params = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
      url += `?${params.toString()}`;
      delete options.params;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
      ...options
    });

    if (!response.ok) {
      const error: any = new Error(`HTTP ${response.status}`);
      error.response = { status: response.status };
      throw error;
    }

    const data = await response.json();
    return { data, response };
  },

  post: async (endpoint: string, data?: any, options?: RequestInit) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    if (!response.ok) {
      const error: any = new Error(`HTTP ${response.status}`);
      error.response = { status: response.status };
      throw error;
    }

    const responseData = await response.json();
    return { data: responseData, response };
  },

  put: async (endpoint: string, data?: any, options?: RequestInit) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    if (!response.ok) {
      const error: any = new Error(`HTTP ${response.status}`);
      error.response = { status: response.status };
      throw error;
    }

    const responseData = await response.json();
    return { data: responseData, response };
  },

  delete: async (endpoint: string, options?: RequestInit) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      ...options
    });

    if (!response.ok) {
      const error: any = new Error(`HTTP ${response.status}`);
      error.response = { status: response.status };
      throw error;
    }

    // DELETE might return empty response
    let responseData;
    try {
      responseData = await response.json();
    } catch (e) {
      responseData = null;
    }
    return { data: responseData, response };
  }
};

export default api;
